"""Rev H first checks. ASD: 0.6 Fy bending/axial, 0.4 Fy shear, 0.9 Fy bearing on machined faces.
Materials: ring 1, flange, spider, gussets, hub ring A572-50 / S355 (Fy 345); tube E355 seamless (Fy 355);
shaft and journal sleeve 4140 QT (Fy 655) / S355 sleeve where noted. Loads: LC2 jam 590 kN + 62 kNm, LC3 800 kN,
chamber 1 bar on ring 1, torque 20 kNm (2 x 10 kNm interlock). Head moment at the hub 62 + 2.28 kNm (as rev G).
"""
import math, importlib.util
from paths import SRC
spec = importlib.util.spec_from_file_location("d", str(SRC / "calc_revD.py"))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
pi = math.pi
P_ch = 0.1 * pi / 4 * 584.2 ** 2
M = 62e6 + 2.28e6
T = 20e6
Fy, Fy_t, Fy_s = 345.0, 355.0, 655.0
rows = []
nu = d.nu


def stepped_plate(P, a, b, Rs, t1, t2, n=300):
    """axisymmetric plate: line load P at b (guided, slope 0), thickness t1 for b..Rs and t2 for Rs..a, pinned at a."""
    import numpy as np
    k = P / (2 * pi)
    E = 200e3
    D1, D2 = E * t1 ** 3 / (12 * (1 - nu ** 2)), E * t2 ** 3 / (12 * (1 - nu ** 2))
    f = lambda r_: r_ / 2 * math.log(r_) - r_ / 4
    kM = lambda r_: k * (0.5 * math.log(r_) + 0.25) + nu * k * (0.5 * math.log(r_) - 0.25)
    gM = lambda r_: ((1 + nu) / 2, (nu - 1) / r_ ** 2)
    A = np.zeros((4, 4)); B = np.zeros(4)
    A[0, :2] = (b / 2, 1 / b); B[0] = -k * f(b)
    A[1] = (Rs / 2 / D1, 1 / Rs / D1, -Rs / 2 / D2, -1 / Rs / D2); B[1] = -k * f(Rs) / D1 + k * f(Rs) / D2
    g = gM(Rs); A[2] = (g[0], g[1], -g[0], -g[1]); B[2] = 0.0
    g = gM(a); A[3, 2:] = g; B[3] = -kM(a)
    c = np.linalg.solve(A, B)
    out = []
    for i in range(n + 1):
        r_ = b + (a - b) * i / n
        c1, c2, t = (c[0], c[1], t1) if r_ <= Rs else (c[2], c[3], t2)
        thD = k * f(r_) + c1 * r_ / 2 + c2 / r_
        dthD = k * (0.5 * math.log(r_) + 0.25) + c1 / 2 - c2 / r_ ** 2
        Mr, Mt = dthD + nu * thD / r_, thD / r_ + nu * dthD
        out.append((r_, 6 * Mr / t ** 2, 6 * Mt / t ** 2, t))
    return out


# self-check: equal thicknesses must reproduce the uniform-plate solution
_u = d.annular_plate(1e6, 292.1, 180.0, 70.0, "pinned")
_s = stepped_plate(1e6, 292.1, 180.0, 200.0, 70.0, 70.0)
assert abs(_u[0][1] - _s[0][1]) < 1e-6 * max(1, abs(_u[0][1])), (_u[0], _s[0])


def add(grp, item, case, val, allow, unit="MPa"):
    rows.append((grp, item, case, val, allow, unit))


cases = (("LC2 jam", 590e3), ("LC3 envelope", 800e3))

# 1 locking assembly + hub
T_LA, F_LA, p_hub, D_LA, W_LA = 28.161e6, 402.3e3, 165.0, 190.0, 50.0     # Fenner B-LOC B400 140 mm (catalogue)
add("Locking assembly", "B-LOC B400 140 × 190: torque 20 kNm vs 28.2 kNm rating", "torque", T / 1e6, T_LA / 1e6, "kNm")
DN = D_LA * math.sqrt((Fy + p_hub) / (Fy - p_hub))
add("Locking assembly", f"hub ring OD needed (A572-50, p 165 MPa): {DN:.0f} mm, fitted 340", "geometry", DN, 340.0, "mm")
lever = (-108.0 - 31.0) * -1                                             # LA centre x-108 to sleeve bore-fit centre x+31
F_c = M / lever
add("Hub on shaft", f"moment couple, LA zone ↔ sleeve rear (lever {lever:.0f}): edge bearing on 140 × 40", "LC2", F_c / (140 * 40), 0.9 * Fy)
p_shaft = p_hub * D_LA / 140
add("Hub on shaft", "couple pressure under LA vs LA grip on shaft (no lift-off if < grip)", "LC2", F_c / (140 * W_LA), p_shaft)
add("Shaft", "Ø140 at front 23228, bending (no spline step)", "LC2", 32 * M / (pi * 140 ** 3), 0.6 * Fy_s)
tau_d = 16 * T / (pi * 130 ** 3)
add("Shaft", "Ø130 plain drive end, torsion", "torque", tau_d, 0.4 * Fy_s)

for c, P in cases:
    # 2 split flange / tube
    A_lip = pi * (159.0 ** 2 - 148.2 ** 2)
    S_lip = pi * (159.0 ** 4 - 148.2 ** 4) / (4 * 159.0)
    add("Split flange", "land on flange lip, contact P/A + M/S (lip captured both faces)", c, P / A_lip + M / S_lip, 0.9 * Fy)
    add("Split flange", "land shear at R148 over 20", c, P / (2 * pi * 148 * 20), 0.4 * Fy_t)
    add("Split flange", "lip root shear at R159 over 15 (flange 35 thk)", c, P / (2 * pi * 159 * 15), 0.4 * Fy)
    A_g = pi * (148.0 ** 2 - 125.0 ** 2); S_g = pi * (148.0 ** 4 - 125.0 ** 4) / (4 * 148.0)
    add("Cartridge tube", "groove root Ø296 × Ø250: tension + bending", c, P / A_g + M / S_g, 0.6 * Fy_t)
    A_t = pi / 4 * (318 ** 2 - 250 ** 2); S_t = pi * (318 ** 4 - 250 ** 4) / (32 * 318)
    add("Cartridge tube", "body Ø318 × Ø250 at front seat: tension + bending", c, P / A_t + M / S_t, 0.6 * Fy_t)
    add("Cartridge tube", "29328N housing washer on stock shoulder (Ø204–240)", c, P / (pi * (120 ** 2 - 102 ** 2)), 0.9 * Fy_t)
    add("Cartridge tube", "shoulder root shear Ø241 × 30", c, P / (pi * 241 * 30), 0.4 * Fy_t)
    A_s = pi * (200 ** 2 - 159.25 ** 2); S_s = pi * (200 ** 4 - 159.25 ** 4) / (4 * 200)
    need = M * A_s / S_s - (P + 0)
    add("Split flange", f"clamp needed on ring 1 seat (M·A/S − P) vs 16 × M12 10.9 at 70% proof", c, need / 1e3, 16 * 0.7 * 84.3 * 830 / 1e3, "kN")
    # 5 ring 1 (load enters at the seat, centroid ~R180; 70 thick under the counterbore)
    Peq = P + P_ch + 2 * M / 180
    res = stepped_plate(Peq, 292.1, 180.0, 200.0, 75.0, 110.0)
    s1 = max(max(abs(a1), abs(a2)) for rr, a1, a2, tt in res if tt == 75.0)
    r245 = min(res, key=lambda x: abs(x[0] - 245))
    s245 = 2.5 * max(abs(r245[1]), abs(r245[2]))
    add("Ring 1", "web under the seat, 75 thk R159–200 / 110 thk beyond, load at R180", c, s1, 0.6 * Fy)
    add("Ring 1", "pipe holes R245 (110 thk, Kt 2.5)", c, s245, 0.6 * Fy)
    resG = stepped_plate(P + P_ch + 2 * M / 185, 292.1, 185.0, 200.0, 70.0, 110.0)
    add("Ring 1", "rev G, same model (load at R185, contact R170–200)", c, max(max(abs(a1), abs(a2)) for rr, a1, a2, tt in resG if tt == 70.0), 0.6 * Fy)
    res1 = d.annular_plate(Peq, 292.1, 180.0, 75.0, "pinned")
    add("Ring 1", "upper bound: 75 thk all the way to the weld", c, max(abs(res1[0][1]), abs(res1[0][2])), 0.6 * Fy)
    # 6 cutterhead: arm + gusset T-beam at the hub ring (R165)
    n, Rc = 8, 238.0
    F_arm = P / n + 2 * M / (n * Rc)
    Mr = F_arm * (Rc - 165)
    A1, y1, I1 = 76 * 50.8, 25.4, 76 * 50.8 ** 3 / 12
    A2, y2, I2 = 25 * 125, 50.8 + 62.5, 25 * 125 ** 3 / 12
    yn = (A1 * y1 + A2 * y2) / (A1 + A2)
    I = I1 + A1 * (yn - y1) ** 2 + I2 + A2 * (y2 - yn) ** 2
    add("Cutterhead", f"arm + gusset at R165, thrust bending (arm load {F_arm/1e3:.0f} kN)", c, Mr * max(yn, 175.8 - yn) / I, 0.6 * Fy)
    Q = A1 * (yn - y1)
    q = F_arm * Q / I
    add("Cutterhead", "gusset-to-arm fillets 2 × 12, shear flow", c, q / (2 * 0.707 * 12), 0.3 * 482)
F_t = T / 8 / 238.0
Mt = F_t * (238 - 165)
S_weak = 50.8 * 76 ** 2 / 6 + 125 * 25 ** 2 / 6
add("Cutterhead", "arm + gusset at R165, torque bending (weak axis)", "torque", Mt / S_weak, 0.6 * Fy)
P_cap = 7 * 800e3 / 24
add("Cutterhead", "centre cap 30 thk, 7 bits on a Ø200 opening (simply supported)", "LC3", 3 * 3.3 * P_cap / (8 * pi * 30 ** 2), 0.6 * Fy)
# 7 torque path cartridge -> ring 1
Fp = T / (4 * 159.0)
add("Torque", "anti-rotation pins 4 × Ø16 (hardened), shear", "torque", Fp / (pi / 4 * 16 ** 2), 400.0)
add("Torque", "pin bearing on tube land (13 mm engagement)", "torque", Fp / (16 * 13), 0.9 * Fy_t)
# 8 bearings
add("Bearings", "23228 s0 at L = 400", "LC2", 1250e3 / (1.3 * 62e6 / 400), 2.0, "–")
add("Bearings", "29328N s0 = C0 / Fa", "LC3", 2850e3 / 800e3, 2.0, "–")

print(f"{'group':18s} {'item':78s} {'case':13s} {'value':>8s} {'allow':>8s}  FoS")
for g, it, c, v, a, u in rows:
    fos = (a / v) if g not in ("Bearings",) else (v / a)
    if g == "Locking assembly" and "OD" in it:
        fos = a / v
    print(f"{g:18s} {it:78s} {c:13s} {v:8.1f} {a:8.1f}  {fos:4.2f}  {u}")

# ---------------- drive (rev H detailed): Poclain MS18 2,812 cc + jaw coupling + bell adapter ----------------
print("\nDrive")
Nm_bar = 44.71                                   # catalogue, 2,812 cc/rev, theoretical
for Tq in (6e3, 10e3):
    print(f"  pressure for {Tq/1e3:.0f} kNm: {Tq/Nm_bar:.0f} bar theoretical, {Tq/(Nm_bar*0.95):.0f} bar at 95 % mechanical efficiency")
print(f"  flow at 12 rpm: {2.812*12:.1f} L/min (+ leakage); shaft power at 6 kNm: {6e3*12*2*pi/60/1e3:.1f} kW")
Rm, t_ad, T = (355.6 - 12.7) / 2, 12.7, 20e6
tau = T / (2 * pi * Rm ** 2 * t_ad)
print(f"  adapter tube 14 in XS torsion at 20 kNm: {tau:.1f} MPa; with windows (net 76 %, Kt 3): {tau/0.76*3:.0f} MPa vs 0.4 Fy = 138")
P16 = 0.7 * 157 * 830
for mu in (0.30, 0.15):
    cap_ = 12 * P16 * mu * 140.0
    print(f"  adapter to cartridge 12 x M16 10.9 slip, mu {mu}: {cap_/1e6:.1f} kNm, FoS {cap_/T:.2f}")
print(f"  3 x dia 16 dowels alone (single shear 0.4 x 1,100 MPa hardened): FoS {3*0.4*1100*pi/4*16**2*140.0/T:.2f}")
P20 = 0.7 * 245 * 830
for mu in (0.30, 0.15):
    cap_ = 8 * P20 * mu * 167.5
    print(f"  motor to adapter 8 x M20 10.9 slip, mu {mu}: {cap_/1e6:.1f} kNm, FoS {cap_/T:.2f}")
x_tip, x_mot, x_shield = -225.8, 1225.0, 1157.0
print(f"  overall bit tip to motor rear: {x_mot - x_tip:.0f} (limit 1,340: +{x_mot - x_tip - 1340:.0f}); motor rear past shield rear: {x_mot - x_shield:.0f}")
print(f"  overhung motor 152 kg at ~180 mm: {152*9.81*0.18/1e3:.2f} kNm on the adapter")
