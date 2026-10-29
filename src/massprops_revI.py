"""Rev I mass properties from the detailed model: every part's mass and CG, group totals, machine CG, and the
weight moments the structure carries. Writes out/calc/massprops_revI.json (read by calc_revI.py and tools/make_manual.py).

Mass overrides (the modelled shape is an envelope, the catalogue mass is used): motor 152 kg; 4 cylinders 4 x 52.6 kg.
Non-steel parts: seal lips (NBR) x 0.16, coupling spider (PU) x 0.15 of the steel-density mass.
x = 0 at ring 1 front face, +x rearward.
"""
import json
import math

import cadquery as cq

import build_revI_detail as M
from paths import CALC

RHO = 7.85e-6
G = 9.81
KG_OVERRIDE = {"motor": 152.0, "jcyl": 4 * 52.6}
DENSITY_FACTOR = {"seallip": 0.16, "elast": 0.15}
X_SEAT = M.CB                                     # split-flange bearing face on ring 1


def shape_of(wp):
    v = wp.vals()
    return v[0] if len(v) == 1 else cq.Compound.makeCompound(v)


parts = []
for key, name, wp, col, dx, grp, ag in M.P:
    shp = shape_of(wp)
    vol = shp.Volume()
    m = KG_OVERRIDE.get(key, vol * RHO * DENSITY_FACTOR.get(key, 1.0))
    c = cq.Shape.centerOfMass(shp)
    bb = shp.BoundingBox()
    parts.append({"key": key, "name": name, "group": grp, "kg": round(m, 2), "cg": [round(c.x, 1), round(c.y, 1), round(c.z, 1)],
                  "n_solids": len(wp.vals()), "bbox_x": [round(bb.xmin, 1), round(bb.xmax, 1)],
                  "bbox_r": round(max(math.hypot(bb.ymin, bb.zmin), math.hypot(bb.ymax, bb.zmax), abs(bb.ymin), abs(bb.ymax), abs(bb.zmin), abs(bb.zmax)), 1)})


def total(keys_or_groups, by="group"):
    sel = [p for p in parts if (p[by] in keys_or_groups)]
    m = sum(p["kg"] for p in sel)
    cg = [sum(p["kg"] * p["cg"][i] for p in sel) / m for i in range(3)] if m else [0, 0, 0]
    return m, cg


groups = {}
for p in parts:
    groups.setdefault(p["group"], []).append(p["key"])
gtot = {g: total([g]) for g in groups}
machine_groups = [M.SH, M.BM, M.CH, M.DR]
m_machine, cg_machine = total(machine_groups)
m_hung, cg_hung = total([M.BM, M.CH, M.DR])
m_shell, cg_shell = gtot[M.SH]
m_tr, cg_tr = total([M.TR])
m_jk, cg_jk = total([M.JK])
# weight moments about the seat with the machine horizontal (module + head + drive hang off ring 1)
mom = lambda g_list, x_ref: sum(gtot[g][0] * G * (gtot[g][1][0] - x_ref) for g_list_ in [g_list] for g in g_list_) / 1e6
M_seat = sum(gtot[g][0] * G * (gtot[g][1][0] - X_SEAT) for g in (M.BM, M.CH, M.DR)) / 1e6       # kNm
M_seat_headoff = sum(gtot[g][0] * G * (gtot[g][1][0] - X_SEAT) for g in (M.BM, M.DR)) / 1e6
# lifting: 4 bosses at x = LIFT_X, symmetric pairs at +-18 deg
xf, xr = M.LIFT_X
share_rear = (cg_machine[0] - xf) / (xr - xf)
res = {
    "parts": parts,
    "groups": {g: {"kg": round(m, 1), "cg": [round(c, 1) for c in cg], "keys": groups[g]} for g, (m, cg) in gtot.items()},
    "machine": {"kg": round(m_machine, 1), "cg": [round(c, 1) for c in cg_machine], "groups": machine_groups},
    "hung_off_ring1": {"kg": round(m_hung, 1), "cg_x": round(cg_hung[0], 1), "M_seat_kNm": round(M_seat, 3),
                       "M_seat_head_off_kNm": round(M_seat_headoff, 3)},
    "shell_weldment": {"kg": round(m_shell, 1), "cg_x": round(cg_shell[0], 1)},
    "thrust_ring": {"kg": round(m_tr, 1), "cg_x": round(cg_tr[0], 1)},
    "cylinders": {"kg": round(m_jk, 1)},
    "lifting": {"x_front": xf, "x_rear": xr, "angles_deg": list(M.LIFT_A), "share_rear": round(share_rear, 4),
                "kg_per_front_point": round(m_machine * (1 - share_rear) / 2, 1), "kg_per_rear_point": round(m_machine * share_rear / 2, 1)},
}
CALC.mkdir(parents=True, exist_ok=True)
(CALC / "massprops_revI.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
if __name__ == "__main__":
    for g, (m, cg) in gtot.items():
        print(f"{g:18s} {m:8.1f} kg  CG x = {cg[0]:7.1f}")
    print(f"machine (shell + module + head + drive) {m_machine:.1f} kg = {m_machine * 2.20462:.0f} lb, CG x = {cg_machine[0]:.1f}, "
          f"y = {cg_machine[1]:.2f}")
    print(f"hung off ring 1: {m_hung:.1f} kg at x = {cg_hung[0]:.1f}; weight moment at the seat {M_seat:.2f} kNm (head off {M_seat_headoff:.2f})")
    print(f"lifting: rear share {share_rear:.3f}; per point front {res['lifting']['kg_per_front_point']} kg, rear {res['lifting']['kg_per_rear_point']} kg")
