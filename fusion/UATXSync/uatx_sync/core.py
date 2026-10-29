"""UATXSync core: repo -> Fusion sync, Fusion -> repo export, toolbar commands.

Threads: a background thread runs git (fetch, fast-forward) on a timer. It never touches the Fusion API; it
fires custom events, and the handlers do all Fusion work on the main thread.

Repo -> Fusion: fusion/sync/manifest.json (written by tools/fusion_manifest.py) lists every part's STEP file
and SHA-256 plus the design constants. The design "UATX scripts reference" (in the active project unless
configured) holds one component per group and one sub-component per part, tagged with attributes
uatx/key and uatx/sha256. Only parts whose hash changed are re-imported; parts no longer listed are
deleted; user parameters are created or updated. Other designs are never modified. Insert the reference
design into the model of record (Insert into Current Design) to use it as an external reference, or Derive
its parameters.

Fusion -> repo: "Export to repo" writes the active design as STEP plus a JSON of its user parameters and
component mass properties to fusion/export/<design name>/. Commit or push is optional (export_git).
"""
import datetime
import hashlib
import json
import os
import re
import threading
import time
import traceback

import adsk.core
import adsk.fusion

from . import gitops

VERSION = "1.0.0"
EV_MAIN = "uatxsync.main"
WS_ID, TAB_ID, PANEL_ID = "FusionSolidEnvironment", "ToolsTab", "uatxSyncPanel"
DEFAULTS = {
    "branch": "main",
    "remote": "origin",
    "auto_pull": True,
    "poll_seconds": 120,
    "auto_apply": True,
    "reference_doc": "UATX scripts reference",
    "reference_project": "",          # Fusion project for the reference design; empty: the active project
    "reference_folder": "",           # sub-folder path in that project, e.g. "Scripts/Sync"; empty: project root
    "export_dir": "fusion/export",
    "export_git": "off",              # off | commit | push
    "git": "",                        # path to git.exe if it is not on PATH
}
MANIFEST = "fusion/sync/manifest.json"
PKG_PREFIX = "fusion/UATXSync/uatx_sync/"
LOADER_REL = "fusion/UATXSync/UATXSync.py"

_app = adsk.core.Application.get()
_ui = _app.userInterface
_S = None                              # the running Sync instance


# ---------------------------------------------------------------------------- utilities
def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _safe(name):
    return re.sub(r"[^A-Za-z0-9._ -]+", "_", name).strip() or "design"


def _items(coll):
    """Index-based iteration over a Fusion API collection."""
    return [coll.item(i) for i in range(coll.count)]


def _attr(entity, name):
    a = entity.attributes.itemByName("uatx", name)
    return a.value if a else None


def _normalize_step(path):
    with open(path, encoding="latin-1") as f:
        s = f.read()
    s = re.sub(r"(FILE_NAME\('[^']*',')\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d", r"\g<1>2000-01-01T00:00:00", s, count=1)
    with open(path, "w", encoding="latin-1", newline="\n") as f:
        f.write(s)


# ---------------------------------------------------------------------------- the sync object
class Sync:
    def __init__(self, cfg, request_reload):
        self.cfg = dict(DEFAULTS)
        self.cfg.update({k: v for k, v in cfg.items() if v is not None})
        self.repo = os.path.abspath(cfg["repo"])
        self.request_reload = request_reload
        self.git = gitops.find_git(self.cfg.get("git") or None)
        self.dir = os.path.join(self.repo, ".fusion-sync")
        os.makedirs(self.dir, exist_ok=True)
        self.log_path = os.path.join(self.dir, "uatxsync.log")
        self.state_path = os.path.join(self.dir, "state.json")
        self.state = self._load_state()
        self.lock = threading.Lock()
        self.stop_evt = threading.Event()
        self.sync_requested = threading.Event()
        self.apply_pending = False
        self.next_retry = 0.0
        self.busy = False
        self.handlers = []                     # custom-event handler (kept referenced)
        self.cmd_handlers = []                 # command handlers (kept referenced)
        self.event = None
        self.thread = None
        self.last_pull = {"time": None, "msg": "not yet run"}

    # ---------------- persistence and log
    def _load_state(self):
        try:
            with open(self.state_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _save_state(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=1)
        os.replace(tmp, self.state_path)

    def log(self, msg):
        line = f"{_now()}  {msg}"
        with self.lock:
            try:
                if os.path.isfile(self.log_path) and os.path.getsize(self.log_path) > 1_000_000:
                    os.replace(self.log_path, self.log_path + ".1")
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except OSError:
                pass
        try:
            _app.log("UATXSync: " + msg)
        except Exception:
            pass

    def save_config(self, **changes):
        path = self.cfg.get("config_path")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                cur = json.load(f)
        except (OSError, ValueError):
            cur = {}
        cur.update(changes)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cur, f, indent=1)
        self.cfg.update(changes)

    # ---------------- start / stop
    def start(self):
        self.event = _app.registerCustomEvent(EV_MAIN)
        h = _MainHandler()
        self.event.add(h)
        self.handlers.append(h)
        self._add_ui()
        self.log(f"started v{VERSION}; repo {self.repo}; git {self.git or 'NOT FOUND'}; "
                 f"auto_pull {self.cfg['auto_pull']} every {self.cfg['poll_seconds']} s; auto_apply {self.cfg['auto_apply']}")
        self.thread = threading.Thread(target=self._loop, name="UATXSync", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_evt.set()
        if self.thread:
            self.thread.join(5.0)
        self._remove_ui()
        if self.event:
            for h in self.handlers:
                self.event.remove(h)
            _app.unregisterCustomEvent(EV_MAIN)
            self.event = None
        self.handlers, self.cmd_handlers = [], []
        self.log("stopped")

    def fire(self, action, **kw):
        if not self.stop_evt.is_set():
            _app.fireCustomEvent(EV_MAIN, json.dumps(dict(kw, action=action)))

    # ---------------- background thread (git only)
    def _loop(self):
        next_poll = 0.0
        first = True
        while not self.stop_evt.is_set():
            manual = self.sync_requested.is_set()
            if manual or (self.cfg["auto_pull"] and time.time() >= next_poll) or first:
                self.sync_requested.clear()
                next_poll = time.time() + max(30, float(self.cfg["poll_seconds"]))
                try:
                    self._pull(manual, first)
                except Exception:
                    self.log("pull error:\n" + traceback.format_exc())
                first = False
            elif self.apply_pending and self.cfg["auto_apply"] and time.time() >= self.next_retry:
                self.next_retry = time.time() + 10.0    # retried every 10 s until Fusion is idle
                self.fire("apply", manual=False)
            self.stop_evt.wait(1.0)

    def _pull(self, manual, first):
        if not self.git:
            self.last_pull = {"time": _now(), "msg": "git not found: set \"git\" in config.json"}
            self.log(self.last_pull["msg"])
            return
        if first and not manual and not self.cfg["auto_pull"]:
            res = {"ok": True, "msg": "auto-pull off", "changed": []}
        else:
            res = gitops.update(self.git, self.repo, self.cfg["branch"], self.cfg["remote"])
        self.last_pull = {"time": _now(), "msg": res["msg"]}
        if res["changed"] or not res["ok"] or manual:
            self.log("pull: " + res["msg"] + (f" ({len(res['changed'])} files)" if res["changed"] else ""))
        if any(p.startswith(PKG_PREFIX) for p in res["changed"]):
            self.log("add-in code changed: reloading")
            self.request_reload()                       # the new core checks the manifest after it starts
            self.stop_evt.wait(30.0)
            return
        if LOADER_REL in res["changed"]:
            self.log("the loader UATXSync.py changed in the repo: reinstall it (see fusion/README.md)")
        if self._manifest_changed() or manual:
            if self.cfg["auto_apply"] or manual:
                self.apply_pending = True
                self.next_retry = time.time() + 10.0
                self.fire("apply", manual=manual)
            else:
                self.log("manifest changed; auto_apply is off: use Sync now")

    def _manifest_changed(self):
        p = os.path.join(self.repo, MANIFEST)
        return os.path.isfile(p) and _sha_file(p) != self.state.get("applied_manifest_sha")

    # ---------------- main thread: dispatch
    def on_main(self, info):
        d = json.loads(info or "{}")
        a = d.get("action")
        if a == "apply":
            self.apply(manual=d.get("manual", False))
        elif a == "export":
            try:
                self.export_active()
            except Exception:
                tb = traceback.format_exc()
                self.log("export failed:\n" + tb)
                _ui.messageBox("UATXSync: export failed\n\n" + tb)

    # ---------------- reference design
    def _target_folder(self):
        name = self.cfg.get("reference_project") or ""
        folder = None
        if name:
            for p in _items(_app.data.dataProjects):
                if p.name == name:
                    folder = p.rootFolder
                    break
            if folder is None:
                raise RuntimeError(f"Fusion project '{name}' not found (reference_project in config.json)")
        else:
            try:
                folder = _app.data.activeProject.rootFolder
            except Exception:
                raise RuntimeError("no active Fusion project: set reference_project in config.json")
        for part in [x for x in (self.cfg.get("reference_folder") or "").replace("\\", "/").split("/") if x]:
            sub = folder.dataFolders.itemByName(part)
            folder = sub if sub else folder.dataFolders.add(part)
        return folder

    def _find_reference(self):
        fid = self.state.get("reference_file_id")
        if fid:
            try:
                f = _app.data.findFileById(fid)
                if f:
                    return f
            except Exception:
                pass
        folder = self._target_folder()
        for f in _items(folder.dataFiles):
            if f.name == self.cfg["reference_doc"] and f.fileExtension == "f3d":
                self.state["reference_file_id"] = f.id
                self._save_state()
                return f
        return None

    def _open_reference(self):
        """Returns (document, opened_here, created)."""
        f = self._find_reference()
        if f:
            for d in _items(_app.documents):
                try:
                    if d.dataFile and d.dataFile.id == f.id:
                        d.activate()
                        return d, False, False
                except Exception:
                    continue
            return _app.documents.open(f, True), True, False
        doc = _app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        return doc, True, True

    # ---------------- apply the manifest
    def apply(self, manual=False):
        if self.busy:
            return
        if _ui.activeCommand not in ("SelectCommand", ""):
            if manual:
                _ui.messageBox("UATXSync: close the active command first, then run Sync now again.")
            self.apply_pending = True
            return
        man_path = os.path.join(self.repo, MANIFEST)
        if not os.path.isfile(man_path):
            self.apply_pending = False
            self.log(f"no manifest at {MANIFEST}")
            return
        self.busy = True
        self.apply_pending = False
        prev = _app.activeDocument
        doc = None
        opened = created = False
        bar = _ui.progressBar
        try:
            with open(man_path, encoding="utf-8") as f:
                man = json.load(f)
            man_sha = _sha_file(man_path)
            commit = gitops.last_commit_of(self.git, self.repo, MANIFEST) if self.git else ""
            doc, opened, created = self._open_reference()
            if doc.isModified and not created:
                raise RuntimeError(f"'{doc.name}' has unsaved changes; save or revert it first")
            des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            root = des.rootComponent
            groups, existing = {}, {}
            for occ in _items(root.occurrences):
                g = _attr(occ.component, "group")
                if g is None:
                    continue
                groups[g] = occ
                for sub in _items(occ.component.occurrences):
                    k = _attr(sub.component, "key")
                    if k:
                        existing[k] = sub
            wanted = {p["key"]: p for p in man["parts"]}
            todo = [p for p in man["parts"] if p["key"] not in existing or _attr(existing[p["key"]].component, "sha256") != p["sha256"]]
            gone = [k for k in existing if k not in wanted]
            n = len(todo) + len(gone)
            if n:
                bar.show("UATXSync: %v of %m parts", 0, n)
            done = 0
            for k in gone:
                existing[k].deleteMe()
                done += 1
                bar.progressValue = done
            for p in todo:
                g = p["group"]
                if g not in groups:
                    go = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
                    go.component.name = g
                    go.component.attributes.add("uatx", "group", g)
                    groups[g] = go
                if p["key"] in existing:
                    existing[p["key"]].deleteMe()
                occ = self._import_step(os.path.join(self.repo, p["step"]), groups[g].component)
                occ.component.name = f"{p['name']} [{p['key']}]"
                occ.component.attributes.add("uatx", "key", p["key"])
                occ.component.attributes.add("uatx", "sha256", p["sha256"])
                done += 1
                bar.progressValue = done
                adsk.doEvents()
            np_ = self._apply_parameters(des, man.get("parameters", []))
            changed = bool(n or np_)
            des.attributes.add("uatx", "manifest_sha256", man_sha)
            des.attributes.add("uatx", "commit", commit)
            if created:
                ok = doc.saveAs(self.cfg["reference_doc"], self._target_folder(), f"UATXSync: created from {commit or 'working tree'}", "")
                self.log(f"created '{self.cfg['reference_doc']}' (save {'ok' if ok else 'FAILED'})")
            elif changed:
                ok = doc.save(f"UATXSync: {commit or 'working tree'}: {len(todo)} parts imported, {len(gone)} removed, {np_} parameters")
                self.log(f"saved new version (save {'ok' if ok else 'FAILED'})")
            self.state.update(applied_manifest_sha=man_sha, last_apply=_now(), last_apply_commit=commit,
                              last_apply_summary=f"{len(todo)} imported, {len(gone)} removed, {np_} parameters")
            self._save_state()
            msg = f"applied manifest {commit}: {len(todo)} parts imported, {len(gone)} removed, {np_} parameters changed"
            self.log(msg)
            if manual:
                _ui.messageBox("UATXSync\n\n" + msg)
        except Exception:
            tb = traceback.format_exc()
            self.state["last_error"] = f"{_now()} {tb.strip().splitlines()[-1]}"
            self._save_state()
            self.log("apply failed:\n" + tb)
            if manual:
                _ui.messageBox("UATXSync: apply failed\n\n" + tb)
        finally:
            bar.hide()
            self.busy = False
            try:
                if doc and opened and not created and not doc.isModified:
                    doc.close(False)
                if prev and prev.isValid:
                    prev.activate()
            except Exception:
                self.log("restore of the previous document failed:\n" + traceback.format_exc())

    def _import_step(self, path, target):
        im = _app.importManager
        opts = im.createSTEPImportOptions(path)
        try:
            opts.isViewFit = False
        except Exception:
            pass
        before = {o.entityToken for o in _items(target.occurrences)}
        res = None
        try:
            res = im.importToTarget2(opts, target)
        except AttributeError:
            im.importToTarget(opts, target)
        if res is not None and res.count:
            return adsk.fusion.Occurrence.cast(res.item(0))
        new = [o for o in _items(target.occurrences) if o.entityToken not in before]
        if not new:
            raise RuntimeError(f"STEP import produced no occurrence: {path}")
        return new[0]

    def _apply_parameters(self, des, rows):
        ups = des.userParameters
        changed = 0
        for r in rows:
            expr = f"{r['value']} {r['unit']}".strip()
            for name in (r["name"], "uatx_" + r["name"]):
                try:
                    p = ups.itemByName(name)
                    if p is None:
                        ups.add(name, adsk.core.ValueInput.createByString(expr), r["unit"], r.get("comment", ""))
                        changed += 1
                    elif p.expression != expr or p.comment != r.get("comment", ""):
                        p.expression = expr
                        p.comment = r.get("comment", "")
                        changed += 1
                    break
                except Exception:
                    if name.startswith("uatx_"):
                        self.log(f"parameter {r['name']} = {expr} rejected:\n" + traceback.format_exc())
        return changed

    # ---------------- Fusion -> repo
    def export_active(self):
        doc = _app.activeDocument
        des = adsk.fusion.Design.cast(_app.activeProduct)
        if not des:
            _ui.messageBox("UATXSync: the active document is not a design.")
            return
        name = _safe(doc.dataFile.name if doc.dataFile else doc.name)
        rel = f"{self.cfg['export_dir']}/{name}"
        out = os.path.join(self.repo, *rel.split("/"))
        os.makedirs(out, exist_ok=True)
        step = os.path.join(out, "model.step")
        em = des.exportManager
        em.execute(em.createSTEPExportOptions(step, des.rootComponent))
        _normalize_step(step)
        acc = adsk.fusion.CalculationAccuracy.LowCalculationAccuracy
        comps = []
        for occ in _items(des.rootComponent.allOccurrences):
            try:
                pp = occ.getPhysicalProperties(acc) if hasattr(occ, "getPhysicalProperties") else occ.physicalProperties
                cg = pp.centerOfMass
                comps.append({"path": occ.fullPathName, "component": occ.component.name, "kg": round(pp.mass, 3),
                              "volume_cm3": round(pp.volume, 2), "cg_mm": [round(cg.x * 10, 1), round(cg.y * 10, 1), round(cg.z * 10, 1)],
                              "visible": occ.isVisible})
            except Exception:
                comps.append({"path": occ.fullPathName, "component": occ.component.name, "error": "physical properties failed"})
        pp = des.rootComponent.getPhysicalProperties(acc)
        cg = pp.centerOfMass
        data = {
            "document": doc.name, "version": doc.dataFile.versionNumber if doc.dataFile else None,
            "file_id": doc.dataFile.id if doc.dataFile else None, "exported": _now(), "fusion": _app.version,
            "units": "mm, kg; Fusion world frame of the design",
            "total": {"kg": round(pp.mass, 3), "cg_mm": [round(cg.x * 10, 1), round(cg.y * 10, 1), round(cg.z * 10, 1)]},
            "user_parameters": [{"name": p.name, "expression": p.expression, "unit": p.unit, "value_internal": p.value,
                                 "comment": p.comment} for p in _items(des.userParameters)],
            "components": comps,
        }
        with open(os.path.join(out, "model.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        msg = f"exported '{doc.name}' to {rel}/ (model.step, model.json)"
        mode = self.cfg.get("export_git", "off")
        if mode in ("commit", "push") and self.git:
            ok, gm = gitops.commit_paths(self.git, self.repo, [rel], f"fusion: export {doc.name}", push=(mode == "push"),
                                         branch=self.cfg["branch"], remote=self.cfg["remote"])
            msg += f"; git: {gm}"
        self.log(msg)
        _ui.messageBox("UATXSync\n\n" + msg)

    # ---------------- status
    def status_text(self):
        gi = gitops.info(self.git, self.repo) if self.git else {"branch": "?", "head": "git not found", "status": ""}
        loader_note = ""
        lp = self.cfg.get("loader_path")
        repo_loader = os.path.join(self.repo, *LOADER_REL.split("/"))
        if lp and os.path.isfile(repo_loader) and os.path.abspath(lp) != os.path.abspath(repo_loader):
            if _sha_file(lp) != _sha_file(repo_loader):
                loader_note = "\nLoader: OUT OF DATE, reinstall UATXSync.py from the repo"
        s = self.state
        return (f"UATXSync {VERSION}\nRepo: {self.repo}\nBranch: {gi['branch']}   HEAD: {gi['head']}\n"
                f"Local changes (tracked): {len(gi['status'].splitlines()) if gi['status'] else 0}\n"
                f"Auto-pull: {'on' if self.cfg['auto_pull'] else 'off'} every {self.cfg['poll_seconds']} s; "
                f"auto-apply: {'on' if self.cfg['auto_apply'] else 'off'}\n"
                f"Last pull: {self.last_pull['time']}: {self.last_pull['msg']}\n"
                f"Last apply: {s.get('last_apply')} ({s.get('last_apply_commit')}): {s.get('last_apply_summary')}\n"
                f"Pending: {'yes' if (self.apply_pending or self._manifest_changed()) else 'no'}\n"
                f"Reference design: {self.cfg['reference_doc']}\nLast error: {s.get('last_error', 'none')}\n"
                f"Log: {self.log_path}{loader_note}")

    # ---------------- toolbar
    def _add_ui(self):
        res = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
        cmds = [
            ("uatxSyncNow", "Sync now", "Pull the repo and import changed parts into the reference design.", "sync", self._cmd_sync),
            ("uatxSyncExport", "Export to repo", "Write the active design as STEP + JSON to fusion/export/ in the clone.", "export", self._cmd_export),
            ("uatxSyncToggle", "Auto-sync on/off", "Turn the timed pull + import on or off (saved in config.json).", "toggle", self._cmd_toggle),
            ("uatxSyncStatus", "Status", "Repo, last pull, last import, pending changes, log file.", "status", self._cmd_status),
        ]
        ws = _ui.workspaces.itemById(WS_ID)
        tab = ws.toolbarTabs.itemById(TAB_ID) if ws else None
        panel = None
        if tab:
            panel = tab.toolbarPanels.itemById(PANEL_ID) or tab.toolbarPanels.add(PANEL_ID, "UATX Sync")
        for cid, name, tip, icon, fn in cmds:
            cd = _ui.commandDefinitions.itemById(cid)
            if cd:
                cd.deleteMe()
            folder = os.path.join(res, icon)
            cd = _ui.commandDefinitions.addButtonDefinition(cid, name, tip, folder if os.path.isdir(folder) else "")
            h = _CreatedHandler(fn)
            cd.commandCreated.add(h)
            self.cmd_handlers.append(h)
            if panel and not panel.controls.itemById(cid):
                c = panel.controls.addCommand(cd)
                c.isPromoted = cid == "uatxSyncNow"

    def _remove_ui(self):
        try:
            ws = _ui.workspaces.itemById(WS_ID)
            tab = ws.toolbarTabs.itemById(TAB_ID) if ws else None
            panel = tab.toolbarPanels.itemById(PANEL_ID) if tab else None
            for cid in ("uatxSyncNow", "uatxSyncExport", "uatxSyncToggle", "uatxSyncStatus"):
                if panel:
                    c = panel.controls.itemById(cid)
                    if c:
                        c.deleteMe()
                cd = _ui.commandDefinitions.itemById(cid)
                if cd:
                    cd.deleteMe()
            if panel:
                panel.deleteMe()
        except Exception:
            self.log("UI cleanup failed:\n" + traceback.format_exc())

    def _cmd_sync(self):
        self.sync_requested.set()
        self.log("Sync now requested")

    def _cmd_export(self):
        self.fire("export")                     # runs after the command closes (no file I/O inside command events)

    def _cmd_toggle(self):
        on = not self.cfg["auto_pull"]
        self.save_config(auto_pull=on, auto_apply=on)
        self.log(f"auto-sync {'on' if on else 'off'}")
        _ui.messageBox(f"UATXSync: auto-sync is now {'ON' if on else 'OFF'}")

    def _cmd_status(self):
        _ui.messageBox(self.status_text(), "UATXSync status")


# ---------------------------------------------------------------------------- event handlers
class _MainHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        try:
            if _S:
                _S.on_main(args.additionalInfo)
        except Exception:
            if _S:
                _S.log("main-thread handler failed:\n" + traceback.format_exc())


class _ExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def notify(self, args):
        try:
            self.fn()
        except Exception:
            _ui.messageBox("UATXSync:\n\n" + traceback.format_exc())


class _CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def notify(self, args):
        h = _ExecuteHandler(self.fn)          # no inputs: Fusion fires execute right after this
        args.command.execute.add(h)
        if _S:
            _S.cmd_handlers.append(h)


# ---------------------------------------------------------------------------- module API (called by the loader)
def start(cfg, request_reload):
    global _S
    _S = Sync(cfg, request_reload)
    _S.start()


def stop():
    global _S
    if _S:
        _S.stop()
        _S = None


def instance():
    return _S
