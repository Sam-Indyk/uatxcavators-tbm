# UATXcavators TBM: mechanical design scripts

UATXcavators (UATX) is building a DN600 slurry microTBM (micro tunnel boring machine, ~0.6 m bore) for The Boring Company's Not-a-Boring Competition, March 2027. Sam Indyk is mechanical lead.

**Fusion 360 is the model of record.** This folder holds the supporting scripts: CadQuery models that are exported as STEP and imported into Fusion, hand calculations, a three.js viewer with an assembly animation, and a collision audit of that animation.

- Design record: `docs/spindle-mount.md`. Add a dated section for each change and keep its "Open" list current. The thrust ring has its own record, `docs/thrust-ring.md`, kept the same way.
- Team priorities: `docs/mechanical-priorities.md`.
- Competition rules (NABC 2027 Full Rules Rev A2, PDF) are in the claude.ai project "UATXcavators" and are not copied here.
- `docs/*.md` are mirrored with the claude.ai project docs `claude/*.md`. Follow "Docs sync" below at the start and end of every session.
- Published viewer (claude.ai artifact): https://claude.ai/artifact/9CTeunW3jLoUrd8VnANaB9. It is republished from a claude.ai session as the page plus `data/<tag>.json`. From here, view it locally (see below).

## Current design: Rev H spindle mount + drive + anti-roll fins

- **Cartridge:** seamless tube 323.9 × 60 (E355), turned to Ø318. It is held in ring 1 by a split flange that sits in a groove on the tube.
- **Cutterhead to shaft:** B-LOC B400 140 × 190 locking assembly. A locking assembly is a keyless clamp ring: tightening its screws squeezes the hub onto the shaft.
- **Bearings:**
  - 2 × 23228 spherical roller bearings, at x = 70 and x = 470.
  - 29328N spherical thrust bearing.
  - KM28 nut with MB28 lock washer.
- **Drive:**
  - Poclain MS18 hydraulic motor.
  - Bolted-on adapter bell housing.
  - Jaw coupling. The spindle-side hub holds an internal 130 × 180 locking assembly; the motor-side hub has a W90 spline.
- **Anti-roll fins:** 4 fins, each 20 × 70 × 990, at 1, 3, 9 and 11 o'clock.
- **Thrust ring (Rev A, launch):** A572-50, 76.2 thick, Ø609.6 × Ø400. Modelled on the shield rear end (x = 1157 to 1233.2) as at launch, before the first jacking pipe. 4 × Chief WT 5 × 24 cylinders sit in welded saddles at R260, 2, 4, 8 and 10 o'clock; the cylinders are an envelope (outer shape only).

Full numbers are in the docs.

## Conventions

- **Units:** mm, N, MPa, kN, kNm. Steel density is 7.85e-6 kg/mm³.
- **Machine frame:** axis +X runs rearward; x = 0 is the ring 1 front face. Angles are measured around the axis, with 0° = 12 o'clock and 90° = 3 o'clock.
- **Viewer and assembly frame:** +Y is up and the floor is y = 0.
  - Group pose = rotation `th` about world Z plus translation `t`.
  - Named poses: FU = −90 (front up), RU = +90 (rear up), H = 0 (horizontal).
  - All groups share a common pivot at x = 300.
- **Allowables (ASD, allowable stress design):**
  - Bending and axial: 0.6 Fy.
  - Shear: 0.4 Fy.
  - Bearing on machined faces: 0.9 Fy.
  - Fillet welds: 0.3 × 482 = 145 MPa.
  - Yield strengths: Fy 345 for A572-50 / S355; 355 for the E355 tube; 655 for 4140 QT.
- **Load cases:**

  | Case | Load |
  |---|---|
  | LC2 jam | 590 kN + 62 kNm (64.28 kNm at the head joint) |
  | LC3 | 800 kN thrust |
  | Chamber | 1 bar on ring 1 (26.8 kN) |
  | Torque | 20 kNm (2 × the 10 kNm interlock) |

- Every check prints value, allowable and FoS (factor of safety).

## How Sam wants output

- Numbers-only deliverables, with no advice sections.
- A professional, neutral tone.
- Each piece of jargon explained in plain words the first time it appears.

## Docs sync (claude.ai project ↔ this repo)

Chats in the claude.ai project "UATXcavators" edit the project docs `claude/<name>.md`. This repo holds the same docs as `docs/<name>.md`. `docs/.sync.json` records each doc's content hash at the last sync, so `tools/docsync.py` can tell which side changed.

Project memory is shared automatically between those chats and Claude Code sessions attached to the project. Design decisions made in chats appear there; read it before changing the design.

**At the start of a session**, if the Projects tool is available:
1. Run `project_info` and list the docs under `claude/`.
2. For each doc, `project_read` it into a scratch file, then run `python tools/docsync.py compare <name> <scratch file>`. Act on the result:

   | Result | Action |
   |---|---|
   | `pull` or `new-in-project` | Copy the project text into `docs/<name>.md`, then run `python tools/docsync.py mark <name>`. |
   | `push` or `new-in-repo` | `project_write` `docs/<name>.md` to `claude/<name>.md`, then mark it. |
   | `conflict` | Overwrite neither side. Show Sam the diff and ask which version to keep. |
   | `in-sync` | Nothing to do. |

3. Commit any pulled docs as `docs: sync from claude.ai project`.

**After changing a doc in this repo**, `project_write` it to `claude/<name>.md` and mark it in the same session.

Without the Projects tool, say that the docs may be behind the project. The nightly scheduled task "UATXcavators docs sync" reconciles them and opens a pull request.

## Setup

Use 64-bit Python 3.11–3.13. The models were built with CadQuery 2.8.0.

```
python -m venv .venv
.venv\Scripts\activate                # Windows  (source .venv/bin/activate elsewhere)
pip install -r requirements.txt
python -m playwright install chromium # only for tools/shoot_viewer.py
```

If `pip install cadquery` fails on Windows, install CadQuery from conda-forge in a conda environment instead.

If the system Python is newer than 3.13, `uv venv --python 3.13 --seed .venv` downloads a 3.13 interpreter for the venv (`--seed` adds pip).

## Pipeline (run from the repo root)

| Step | Command | Output / time |
|---|---|---|
| 1. Build and check every part for interference | `python src/build_revH_detail.py --check` | Interference volumes in cm³, ~1 min. Expected non-zero values are listed below this table. |
| 2. Meshes, assembly steps, detailed STEP | `python src/asm_revH.py` | `viewer/data/H.json`, `out/step/spindle_mount_revH_detail.step`, `out/step/thrust_ring_revA.step` |
| 3. Simple rev H model | `python src/build_revH.py` | `out/step/spindle_mount_revH.step`, `out/mesh/mesh_revH.json` |
| 4. Calcs | `python src/calc_revH.py` · `python src/calc_support.py` · `python src/calc_fins.py` | Printed tables; `out/calc/calc_support.json` |
| 5. Collision audit of the animation | `python src/audit_asm.py 0.3 out/audit/audit.json` | ~20 min on 2 cores |
| 6. View | `python -m http.server 8000 -d viewer`, then http://localhost:8000/#revh or `#assembly` | |
| 7. Headless screenshots and console errors | `python tools/shoot_viewer.py assembly --steps 0,9,52`, `--mid 38`, `revh --views iso,side` | `out/shots/` |

Expected non-zero interference values in step 1 (all others are 0):
- `adscrews/tube_thread` 14.14: screw threads in tapped holes.
- `eye/shaft` 10.56: eye bolt thread in the M30 nose thread.
- `pipewelds/ring1` 0.03.

Known conflict, open (not a modelling artefact): `tring/gsupply` 5.98. The seal-purge supply line at R209 passes through the thrust ring annulus (bore R200).

Collision audit (step 5): it replays every motion and flags any pair whose mid-motion overlap exceeds its finished-state overlap by more than 0.3 cm³. Latest result (Oct 27, 55 steps, thrust ring included; 4.5 min on this machine): 0 collisions, in `out/audit/audit_final.json` and `audit_final.log`.

Rerun step 2 after any geometry change, and step 5 after any change to geometry or to the step list. Steps 1 and 5 are the checks.

## Code map

- `src/paths.py`: output folders. Importing it also sets UTF-8 stdout, because the scripts print Ø, ×, ° and ≈.
- `src/detail_lib.py`: shape helpers and catalogue-style parts:
  - ISO 4762 socket screws: `shcs` and `axial_screws`.
  - 23228 and 29328 bearings with rollers and cage.
  - Lip seals, KM nut, MB washer, fillets.
- `src/build_opts.py`: helpers from the option studies (`revolve`, `ring`, `holes`, `drive_parts`, `vol`, `export`).
- `src/build_revH_detail.py`: every rev H part.
  - Each part is a tuple `(key, name, workplane, colour, explode_dx, viewer_group, assembly_group)` in the list `P` and the dict `parts`.
  - Design constants sit near their parts, for example `FIN_*`, `A_PURGE` and the thrust ring's `TR_*`, `SD_*`, `EAR_*`.
  - Thrust ring parts are in the viewer groups "Thrust ring" and "Jacking cylinders". `calc_support.py` reads only the shell, module, head and drive groups, so the ring does not enter the machine weight.
  - `--check` runs the interference matrix.
- `src/asm_revH.py`: assembly groups and the step list.
  - Steps are defined with `st(phase, title, text, add, remove, moves, focus, dur)`.
  - `add` and `remove` offsets are in world (viewer) coordinates. `moves` are waypoint lists of poses.
  - Motor mass is overridden to 152 kg (catalogue); the modelled motor is an envelope. The cylinders are overridden to 4 × 52.6 kg the same way.
  - Phase 7 (steps 53–55) adds the thrust ring, cylinders and pins with the machine horizontal on the cradle.
- `src/audit_asm.py`: the collision replay. It must use the same easing and pose interpolation as the viewer (`ease`, `lerp_pose`); change both together.
- `src/calc_revD.py`: annular plate solver. `calc_revH.py` loads it and adds `stepped_plate`, a two-thickness plate model of ring 1.
- `src/calc_support.py`: weight of the cantilevered module, head and drive. Masses and CGs come from the detailed model.
- `src/calc_fins.py`: anti-roll fin sizing, T_resist = Σ Nc·cu × A_eff × R. Only fin height beyond the 10.2 mm overcut counts.
- `viewer/index.html`: the single-page viewer.
  - Tabs are at the top. Page text and check tables live in the JS object `PAGES`; edit them in place.
  - Each revision's meshes are in `viewer/data/<tag>.json` (B–H, S).
  - three@0.160.0 loads from jsdelivr through an importmap.
- `tools/docsync.py`: three-way hash check behind the docs sync.
- `archive/`: rev B–G scripts, STEP files and old viewer templates. Kept for history only and not maintained; they still contain old absolute paths.

## Gotchas

- `cq.Solid.makeSphere` gives a hemisphere by default. Pass `angleDegrees1=-90, angleDegrees2=90` for a full sphere band.
- `build_opts.vol()` returns 0 when a boolean fails, so a 0 can hide a failure. Treat unexpected zeros as suspect.
- In assembly steps, groups that move together need the same pivot, or they drift apart mid-motion.
- Viewer CSS: the global `[hidden]{display:none !important}` rule must stay.
- Motor flange pattern, pilot and body are placeholders until Poclain's certified drawing arrives (8 × M20 on Ø335 assumed).
