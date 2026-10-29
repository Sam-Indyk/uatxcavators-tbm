"""UATXSync add-in entry point (loader).

Two ways to install (see fusion/README.md):
  1. Copy this file, UATXSync.manifest and a config.json {"repo": "<path to the clone>"} into
     Fusion's AddIns folder (%APPDATA%/Autodesk/Autodesk Fusion 360/API/AddIns/UATXSync).
  2. Add the folder fusion/UATXSync of the clone in Utilities > Add-Ins > Scripts and Add-Ins (+).

Everything else lives in the clone (fusion/UATXSync/uatx_sync). After a pull that changes that package,
the core fires the reload event and this loader stops it, re-imports it from disk and starts it again.
This file only changes rarely; reinstall it when it does (the Status command reports a mismatch).
"""
import importlib
import json
import os
import sys
import traceback

import adsk.core

HERE = os.path.dirname(os.path.abspath(__file__))
RELOAD_EVENT = "uatxsync.reload"
PKG = "uatx_sync"
_app = adsk.core.Application.get()
_ui = _app.userInterface
_state = {"core": None, "event": None, "handler": None, "pkg_dir": None}


def _config():
    path = os.path.join(HERE, "config.json")
    cfg = {}
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    if not cfg.get("repo"):                       # running from inside the clone: walk up to the .git folder
        d = HERE
        while True:
            if os.path.exists(os.path.join(d, ".git")):
                cfg["repo"] = d
                break
            nd = os.path.dirname(d)
            if nd == d:
                break
            d = nd
    cfg["config_path"] = path
    cfg["loader_path"] = os.path.abspath(__file__)
    return cfg


def _purge():
    for name in [m for m in list(sys.modules) if m == PKG or m.startswith(PKG + ".")]:
        del sys.modules[name]


def _start_core():
    _purge()
    importlib.invalidate_caches()
    core = importlib.import_module(PKG + ".core")
    _state["core"] = core
    core.start(_config(), _request_reload)


def _request_reload():
    _app.fireCustomEvent(RELOAD_EVENT, "")


class _ReloadHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        try:
            if _state["core"]:
                _state["core"].stop()
                _state["core"] = None
            _start_core()
        except Exception:
            _ui.messageBox("UATXSync: reload failed\n\n" + traceback.format_exc())


def run(context):
    try:
        cfg = _config()
        if not cfg.get("repo") or not os.path.isdir(cfg["repo"]):
            _ui.messageBox('UATXSync: set "repo" (path to the uatxcavators-tbm clone) in\n' + cfg["config_path"])
            return
        pkg_dir = os.path.join(cfg["repo"], "fusion", "UATXSync")
        if pkg_dir not in sys.path:
            sys.path.insert(0, pkg_dir)
        _state["pkg_dir"] = pkg_dir
        ev = _app.registerCustomEvent(RELOAD_EVENT)
        h = _ReloadHandler()
        ev.add(h)
        _state["event"], _state["handler"] = ev, h
        _start_core()
    except Exception:
        _ui.messageBox("UATXSync: start failed\n\n" + traceback.format_exc())


def stop(context):
    try:
        if _state["core"]:
            _state["core"].stop()
            _state["core"] = None
        if _state["event"]:
            _state["event"].remove(_state["handler"])
            _app.unregisterCustomEvent(RELOAD_EVENT)
            _state["event"] = _state["handler"] = None
        if _state["pkg_dir"] in sys.path:
            sys.path.remove(_state["pkg_dir"])
        _purge()
    except Exception:
        _ui.messageBox("UATXSync: stop failed\n\n" + traceback.format_exc())
