"""Rev H: is the cantilevered mount (bearing module + head + drive hung off ring 1) OK under its own weight,
handling/transport loads and in combination with the cutting load cases?  Masses and CGs come from the detailed model.
x = 0 at ring 1 front face; seat (split-flange bearing face) at x = 35; ring 1 rear face x = 110.
"""
import math, importlib.util, json
import cadquery as cq
import build_revH_detail as M
from paths import SRC, CALC

pi, g = math.pi, 9.81
spec = importlib.util.spec_from_file_location("ch", str(SRC / "calc_revH.py"))


def mass_cg(keys, override=None):
    m_tot, mx = 0.0, 0.0
    for k in keys:
        wp = M.parts[k][2]
        shp = wp.val() if len(wp.vals()) == 1 else cq.Compound.makeCompound(wp.vals())
        m = shp.Volume() * 7.85e-6
        if override and k in override:
            m = override[k]
        if k in ("seallip",):
            m *= 0.16
        if k == "elast":
            m *= 0.15
        x = cq.Shape.centerOfMass(shp).x
        m_tot += m
        mx += m * x
    return m_tot, mx / m_tot


grp = {}
for k, p in M.parts.items():
    if p[5] == "Fixture":
        continue
    grp.setdefault(p[5], []).append(k)
module = [k for k in grp["Bearing module"]]
head = grp["Cutterhead"]
drive = grp["Drive"]
mm, xm = mass_cg(module)
mh, xh = mass_cg(head)
md, xd = mass_cg(drive, {"motor": 152.0})
ms, xs = mass_cg(grp["Shell weldment"])
X_SEAT, X_R1B = 35.0, 110.0
# fins are modelled in the shell weldment group (fin30/90/270/330 + finwelds); add them only if absent
fin_mass = 0.0 if any(k.startswith("fin") for k in grp["Shell weldment"]) else 4 * 20 * 60 * 990 * 7.85e-6
out = {"module": (mm, xm), "head": (mh, xh), "drive": (md, xd), "shell": (ms, xs)}
print("Masses and CGs (kg, x mm)")
for k, (m_, x_) in out.items():
    print(f"  {k:8s} {m_:7.1f} kg at x = {x_:7.1f}")
m_all = mm + mh + md + ms + fin_mass
x_all = (mm * xm + mh * xh + md * xd + ms * xs + fin_mass * 645) / m_all
if fin_mass:
    print(f"  fins     {fin_mass:7.1f} kg at x ≈ 645 (not in the model)")
print(f"  machine  {m_all:7.1f} kg, CG x = {x_all:.0f} (shield runs x = -128 to 1157)")

# ---------- gravity moment at the ring 1 seat ----------
def moment(parts, x_ref):
    return sum(m_ * g * (x_ - x_ref) for m_, x_ in parts) / 1e6        # kNm


hung = [(mm, xm), (mh, xh), (md, xd)]
hung_nohead = [(mm, xm), (md, xd)]
W_hung = (mm + mh + md) * g / 1e3
M_seat = moment(hung, X_SEAT)
M_seat_nh = moment(hung_nohead, X_SEAT)
M_ad = md * g * (xd - 615.0) / 1e6
print(f"\nHung off ring 1: {mm + mh + md:.0f} kg = {W_hung:.2f} kN")
print(f"Gravity moment at the seat, horizontal: {M_seat:.2f} kNm (head on), {M_seat_nh:.2f} kNm (head off)")
print(f"Gravity moment at the adapter joint (x = 615): {M_ad:.2f} kNm")

M_jam = 64.3
rows = []


def add(item, case, val, allow, unit="", fos=None):
    rows.append((item, case, val, allow, unit, fos if fos is not None else (allow / val if val else float("inf"))))


cases = [("1 g static", 1.0), ("3 g transport / handling", 3.0)]
Mg = max(M_seat, M_seat_nh)
n_b, D_b, P0 = 16, 370.0, 0.7 * 84.3 * 830 / 1e3      # M12 10.9 preload kN
A_s = pi * (200 ** 2 - 159.25 ** 2); S_s = pi * (200 ** 4 - 159.25 ** 4) / (4 * 200)
for c, f in cases:
    Mc = Mg * f
    add("moment at the seat vs jam design moment 64.3 kNm", c, Mc, M_jam, "kNm")
    add("M12 bolt tension added (4M / nD) vs preload", c, 4 * Mc * 1e6 / (n_b * D_b) / 1e3, P0, "kN")
    add("seat clamp needed to stay closed vs 16 × M12 clamp", c, Mc * 1e6 * A_s / S_s / 1e3, n_b * P0, "kN")
    add("weight shear vs flange friction (μ 0.30, 16 × M12)", c, W_hung * f, 0.30 * n_b * P0, "kN")
    add("ring 1 bore bearing, weight on Ø318.5 × 75", c, W_hung * f * 1e3 / (318.5 * 75), 0.9 * 345, "MPa")
    Sw = pi * 292.1 ** 2 * 0.707 * 14
    add("ring 1 weld (14 mm fillet) from gravity moment", c, Mc * 1e6 / Sw + W_hung * f * 1e3 / (pi * 292.1 * 0.707 * 14), 145, "MPa")
    St = pi * (318 ** 4 - 250 ** 4) / (32 * 318)
    Mt = (mm * g * max(xm - X_R1B, 0) + md * g * (xd - X_R1B)) / 1e6 * f
    add("cartridge tube bending behind ring 1", c, Mt * 1e6 / St, 0.6 * 355, "MPa")
    add("adapter joint, M16 tension added vs preload", c, 4 * M_ad * f * 1e6 / (12 * 280) / 1e3, 0.7 * 157 * 830 / 1e3, "kN")

# ring 1 plate under gravity and under jam + gravity (stepped-plate model from calc_revH)
ch = importlib.util.module_from_spec(spec)
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(ch)
def ring_web(P, Mx):
    res = ch.stepped_plate(P + 2 * Mx * 1e6 / 180.0, 292.1, 180.0, 200.0, 75.0, 110.0)
    return max(max(abs(a), abs(b)) for r_, a, b, t in res if t == 75.0)
P_ch = 0.1 * pi / 4 * 584.2 ** 2
add("ring 1 web, gravity only (3 g)", "3 g transport / handling", ring_web(0.0, 3 * Mg), 207, "MPa")
add("ring 1 web, LC3 800 kN + 64.3 kNm", "design", ring_web(800e3 + P_ch, M_jam), 207, "MPa")
add("ring 1 web, LC3 + gravity moment added", "design + 1 g", ring_web(800e3 + P_ch, M_jam + Mg), 207, "MPa")
need = (M_jam + Mg) * 1e6 * A_s / S_s - 590e3
add("seat clamp needed, LC2 jam + gravity", "design + 1 g", need / 1e3, n_b * P0, "kN")

# sag of the drive end (cartridge tube as a cantilever from ring 1 rear face; ring 1 rotation ignored)
E, I = 200e3, pi / 64 * (318 ** 4 - 250 ** 4)
L1 = xd - X_R1B
P_d = md * g
sag = P_d * L1 ** 3 / (3 * E * I) + (mm * g) * (xm - X_R1B) ** 3 / (3 * E * I) if xm > X_R1B else P_d * L1 ** 3 / (3 * E * I)
print(f"\nSag at the drive CG from tube bending (1 g): {sag:.3f} mm")

# operating fatigue: M12 bolt stress amplitude (load factor 0.2) and M12 endurance (VDI 2230 rolled thread)
sa_lim = 0.85 * (150 / 12 + 45)
for name, Mop in (("operating, 10 kNm moment swing", 10.0), ("jam, 64.3 kNm swing", 64.3)):
    Fa = 0.2 * 4 * Mop * 1e6 / (n_b * D_b) / 2
    add(f"M12 bolt stress amplitude, {name}", "fatigue", Fa / 84.3, sa_lim, "MPa")
print("\nChecks")
print(f"  {'item':58s} {'case':24s} {'value':>8s} {'limit':>8s}  FoS")
for it, c, v, a, u, f in rows:
    print(f"  {it:58s} {c:24s} {v:8.2f} {a:8.1f}  {f:5.1f} {u}")
json.dump({"masses": out, "M_seat": M_seat, "M_seat_nohead": M_seat_nh, "rows": rows, "machine": [m_all, x_all], "sag": sag},
          open(CALC / "calc_support.json", "w"), indent=1, default=float)
