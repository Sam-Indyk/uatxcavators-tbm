"""Fusion sync package for the UATXSync add-in (fusion/UATXSync).

Writes one STEP file per part of the Rev I model to out/step/parts/<key>.step and the manifest
fusion/sync/manifest.json: part list (key, name, group, colour, file, SHA-256) and the design constants of
src/build_revI_detail.py as Fusion user parameters (name, value, unit, comment).

The add-in pulls the repo, compares the hashes with the ones stored in the Fusion reference design
("UATX scripts reference") and re-imports only the parts that changed.

STEP files are written deterministically (single product per file, fixed header timestamp), so an unchanged
part keeps its hash and is not re-imported. Coordinates: machine frame, mm (+X rearward, x = 0 at the ring 1
front face).

Run from the repo root after any geometry change:  python tools/fusion_manifest.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import paths  # noqa: E402,F401  (UTF-8 stdout)
import cadquery as cq  # noqa: E402
from OCP.Quantity import Quantity_Color, Quantity_TypeOfColor  # noqa: E402
from OCP.STEPCAFControl import STEPCAFControl_Writer  # noqa: E402
from OCP.STEPControl import STEPControl_AsIs  # noqa: E402
from OCP.TCollection import TCollection_ExtendedString  # noqa: E402
from OCP.TDataStd import TDataStd_Name  # noqa: E402
from OCP.TDocStd import TDocStd_Document  # noqa: E402
from OCP.XCAFDoc import XCAFDoc_ColorType, XCAFDoc_DocumentTool  # noqa: E402

import build_revI_detail as M  # noqa: E402

SRC = ROOT / "src" / "build_revI_detail.py"
PARTS_DIR = ROOT / "out" / "step" / "parts"
MANIFEST = ROOT / "fusion" / "sync" / "manifest.json"
DEG = {"A_PURGE", "FIN_ANGS", "LIFT_A", "TR_ANGS", "GD_HALF", "GD_SA"}   # angle constants; all others are lengths in mm
RENAME = {"L": "L_BRG"}                                                  # Fusion parameter names that would read as units
NOTE = {                                                                 # comments where the source line has none or a shared one
    "SH_ID": "Shield shell ID (24 in x 0.500 in pipe)", "SH_OD": "Shield shell OD (24 in pipe)",
    "L": "Bearing spacing, 23228 front to 23228 rear", "LIFT_X": "Lifting boss x stations (symmetric about the CG)",
    "LIFT_A": "Lifting boss angles from 12 o'clock", "GD_HALF": "Window guard half-angle", "GD_SA": "Guard screw angle from the window centre",
    "TR_ANGS": "Cylinder angles from 12 o'clock (2, 4, 8, 10 o'clock)", "FIN_ANGS": "Anti-roll fin angles from 12 o'clock",
    "CAS_CB": "Shield rear counterbore depth (seat for the thrust ring register spigot)",
}


def ascii_name(s):
    s = s.replace("Ø", "D").replace("×", "x").replace("°", " deg").replace("’", "").replace("'", "")
    return re.sub(r"[^A-Za-z0-9 _.,()+\-=/]", "", s).strip()


def write_step(shape, name, rgb, path):
    """One product named `name`, surface colour `rgb`; header timestamp fixed so identical geometry gives an identical file."""
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    lab = st.AddShape(shape.wrapped, False)
    TDataStd_Name.Set_s(lab, TCollection_ExtendedString(name))
    ct.SetColor(lab, Quantity_Color(*rgb, Quantity_TypeOfColor.Quantity_TOC_RGB), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    w = STEPCAFControl_Writer()
    w.SetColorMode(True)
    w.SetNameMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    w.Write(str(path))
    s = path.read_text(encoding="latin-1")
    s = re.sub(r"(FILE_NAME\('[^']*',')\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d", r"\g<1>2000-01-01T00:00:00", s, count=1)
    path.write_text(s, encoding="latin-1", newline="\n")
    return hashlib.sha256(s.encode("latin-1")).hexdigest()


def comments():
    """Trailing '# ...' comment of each constant's assignment line in build_revI_detail.py."""
    out = {}
    for line in SRC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9_]*(?:\s*,\s*[A-Z][A-Z0-9_]*)*)\s*=.*?#\s*(.+)$", line)
        if m:
            for nm in re.split(r"\s*,\s*", m.group(1)):
                out.setdefault(nm, m.group(2).strip()[:200])
    return out


def parameters():
    com = comments()
    rows = []
    for k, v in vars(M).items():
        if not k.isupper() or isinstance(v, bool):
            continue
        vals = [v] if isinstance(v, (int, float)) else (list(v) if isinstance(v, tuple) and v and all(
            isinstance(x, (int, float)) and not isinstance(x, bool) for x in v) else None)
        if vals is None:
            continue
        unit = "deg" if k in DEG else "mm"
        base = RENAME.get(k, k)
        for i, x in enumerate(vals):
            name = base if len(vals) == 1 else f"{base}_{i + 1}"
            c = NOTE.get(k) or com.get(k, "")
            rows.append({"name": name, "value": round(float(x), 4), "unit": unit,
                         "comment": (f"[{k}[{i}]] " if len(vals) > 1 else "") + (c or "build_revI_detail.py")})
    return rows


def main():
    PARTS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    parts = []
    keep = set()
    for key, name, wp, col, dx, grp, ag in M.P:
        v = wp.vals()
        shp = v[0] if len(v) == 1 else cq.Compound.makeCompound(v)
        rgb = [int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        f = PARTS_DIR / f"{key}.step"
        sha = write_step(shp, ascii_name(name) or key, rgb, f)
        keep.add(f.name)
        parts.append({"key": key, "name": name, "group": grp, "color": col, "step": f.relative_to(ROOT).as_posix(),
                      "sha256": sha, "solids": len(v)})
    for f in PARTS_DIR.glob("*.step"):
        if f.name not in keep:
            f.unlink()
    man = {"format": 1, "rev": "I", "source": "src/build_revI_detail.py",
           "frame": "machine frame, mm: +X rearward, x = 0 at the ring 1 front face; angles about the axis, 0 = 12 o'clock",
           "parts": parts, "parameters": parameters()}
    MANIFEST.write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(parts)} parts -> {PARTS_DIR.relative_to(ROOT)}, {len(man['parameters'])} parameters -> {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
