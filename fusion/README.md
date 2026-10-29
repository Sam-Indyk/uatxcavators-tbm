# Fusion link

Two parts connect Fusion to this repo.

| Part | What it does | Where it runs |
|---|---|---|
| Autodesk Fusion MCP server | Lets Claude run Fusion API scripts in the open Fusion session, read documents and take screenshots. MCP (Model Context Protocol) is the standard way an AI app talks to another program's tools. | Built into Fusion (Preferences → General → API → Fusion MCP Server, `127.0.0.1:27182`); reached through the "Autodesk Fusion" extension of the Claude desktop app |
| `UATXSync` add-in (this folder) | Pulls the GitHub repo on a timer, imports changed scripted parts and the design constants into the Fusion design **UATX scripts reference**, and exports Fusion designs back to the repo. Its code loads from the local clone, so a pull also updates the add-in itself. | Fusion, on each team member's computer |

Fusion is the model of record. The add-in writes only to the design "UATX scripts reference"; it never modifies any other design.

## How the sync works

```
CadQuery scripts (src/)  ──python tools/fusion_manifest.py──▶  out/step/parts/<key>.step  +  fusion/sync/manifest.json
        │                                                                     │  git push
        ▼                                                                     ▼
GitHub main  ──UATXSync: fetch + fast-forward every 120 s──▶  local clone  ──▶  "UATX scripts reference" (new version saved)
                                                                                     │
                                                       Insert into Current Design /  │  Derive (parameters)
                                                                                     ▼
                                                                         model of record (your designs)
```

- **Parts.** One STEP file per part, written deterministically: an unchanged part keeps its SHA-256 hash (a fingerprint of the file content) and is not re-imported. In the reference design each group (Shell weldment, Bearing module, Cutterhead, Drive, Thrust ring, Jacking cylinders, Fixture) is a component; each part is a sub-component named `<part name> [<key>]` and tagged with the attributes `uatx/key` and `uatx/sha256`. Parts removed from the scripts are deleted. Coordinates are the machine frame in mm: +X rearward, x = 0 at the ring 1 front face.
- **Parameters.** The numeric design constants of `src/build_revI_detail.py` become user parameters of the reference design with the same names (`T_R1`, `CB`, `R_CB`, `NOTCH_W`, ...). Tuples become `NAME_1`, `NAME_2`, ...; `L` becomes `L_BRG`. Angles are in deg, everything else in mm. The comment of each parameter is the comment on its line in the script.
- **Using it in the model of record.** Insert "UATX scripts reference" into a design as an external reference (an xref: a linked copy that Fusion flags as out of date when the source gets a new version), or Derive its parameters into `Params`. When the add-in saves a new version, Fusion shows the update on the xref or derive.
- **Git.** Fast-forward only. Nothing is pulled while another branch is checked out, while the clone has local commits not on GitHub, or while local edits touch files the update changes. The add-in reports these cases in Status and in the log instead of resolving them.
- **Hot update.** After a pull that changes `fusion/UATXSync/uatx_sync/`, the add-in stops, reloads its code from the clone and starts again. The loader `UATXSync.py` in Fusion's AddIns folder changes rarely; Status reports when it differs from the repo copy.
- **Fusion → repo.** Utilities → UATX Sync → Export to repo writes the active design to `fusion/export/<design name>/model.step` and `model.json` (user parameters; mass, volume and centre of gravity of every occurrence; totals). With `export_git` set to `commit` or `push` it also commits (and pushes) those two files.

## Install (once per computer)

Requirements: Fusion, Git for Windows (or git on macOS), a clone of this repo on `main`.

1. In Fusion's AddIns folder, `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns` on Windows or `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns` on macOS, create the folder `UATXSync` and copy into it `UATXSync.py` and `UATXSync.manifest` from this folder.
2. Next to them, create `config.json`:

   ```json
   {
    "repo": "C:/Users/<you>/Workspace/uatxcavators-tbm/uatxcavators-tbm",
    "reference_project": "Shamir V1"
   }
   ```

3. In Fusion: Utilities → Add-Ins → Scripts and Add-Ins → Add-Ins tab → UATXSync → Run, and tick Run on Startup.

The commands appear in the Design workspace under Utilities → UATX Sync: **Sync now**, **Export to repo**, **Auto-sync on/off**, **Status**.

Alternative to steps 1-2: add the folder `fusion/UATXSync` of the clone directly with the + button in Scripts and Add-Ins. The add-in then finds the repo by walking up to `.git`; put any `config.json` settings in that folder (it is git-ignored).

## Settings (`config.json` next to `UATXSync.py`)

| Key | Default | Meaning |
|---|---|---|
| `repo` | the clone that contains the add-in | Path of the local clone |
| `branch`, `remote` | `main`, `origin` | What is pulled |
| `auto_pull` | `true` | Fetch and fast-forward every `poll_seconds` |
| `poll_seconds` | `120` | Poll interval (minimum 30) |
| `auto_apply` | `true` | Import into the reference design after a pull that changes the manifest. Opens the reference design in a tab, saves a version, closes it, and returns to the design you had open. Postponed while a command dialog is open |
| `reference_doc` | `UATX scripts reference` | Name of the reference design |
| `reference_project` | the active project | Fusion project of the reference design |
| `reference_folder` | project root | Sub-folder path in that project, created if missing |
| `export_dir` | `fusion/export` | Where Export to repo writes |
| `export_git` | `off` | `off`, `commit` or `push` after Export to repo |
| `git` | found on PATH | Path to `git.exe` |

Auto-sync on/off writes `auto_pull` and `auto_apply` to `config.json`.

## Files the add-in writes in the clone (git-ignored)

- `.fusion-sync/uatxsync.log`: one line per pull, import, export and error (rotated at 1 MB).
- `.fusion-sync/state.json`: hash of the last imported manifest, id of the reference design, last result.

## Regenerating the sync package

After any geometry change, in the pipeline after `src/asm_revI.py`:

```
python tools/fusion_manifest.py
```

Then commit `out/step/parts/` and `fusion/sync/manifest.json` with the script change.
