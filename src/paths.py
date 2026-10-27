"""Project paths, resolved from this file so scripts run from any working directory on Windows, macOS or Linux.
Importing this module also switches stdout to UTF-8 (the scripts print Ø, ×, °, ≈ and a Windows console
defaults to cp1252)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "out"
STEP = OUT / "step"
CALC = OUT / "calc"
AUDIT = OUT / "audit"
MESH = OUT / "mesh"
VIEWER_DATA = ROOT / "viewer" / "data"

for _d in (STEP, CALC, AUDIT, MESH, VIEWER_DATA):
    _d.mkdir(parents=True, exist_ok=True)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass
