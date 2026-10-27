"""Rev F cutterhead pyramid frame: first check of struts, hub ring, arm nodes. A572-50 (Fy 345). ASD: 0.6 Fy bending/axial, 0.4 Fy shear.
Conservative: struts carry all thrust and moment (centre tube ignored). Arm bending between nodes is Daniel's head check, not covered here.
"""
import math
pi = math.pi
Fy = 345.0
fa, fv = 0.6 * Fy, 0.4 * Fy
P_ch = 0.1 * pi / 4 * 584.2 ** 2
cases = {"LC2 jam": (590e3, 62e6), "LC3 envelope": (800e3, 62e6)}
T = 20e6
n = 8
R_hub, x_hub = 175.0, -220.0
R_arm, x_arm = 245.0, -315.0
dr, dx = R_arm - R_hub, x_hub - x_arm
Ls = math.hypot(dr, dx)
th = math.atan2(dr, dx)
A_s, S_s = 60.0 * 60.0, 60.0 * 60.0 ** 2 / 6
A_hub = 40.0 * (210 - 85) - 40 * 21 * 2
rows = []
print(f"strut length {Ls:.0f} mm, angle to axis {math.degrees(th):.1f} deg")
for c, (P, M) in cases.items():
    ax = P / n + 2 * M / (n * R_arm)            # max axial share at an arm node
    F = ax / math.cos(th)                        # strut compression
    Fr = F * math.sin(th)                        # radial component at each node
    Vt = T / (n * R_arm)                         # torque, tangential per strut
    sig = F / A_s + Vt * Ls / S_s
    hoop = Fr / (2 * math.sin(pi / n))
    rows += [
        (c, "strut force (kN)", F / 1e3, None),
        (c, "strut 60 × 60: axial + torque bending (MPa)", sig, fa),
        (c, "strut end CJP (base metal) (MPa)", sig, fa),
        (c, "hub ring 40 × 125 hoop compression (MPa)", hoop / A_hub, fa),
        (c, "arm radial tension at node, 76 × 50.8 (MPa)", Fr / (76 * 50.8), fa),
    ]
KL_r = Ls / (60 / math.sqrt(12))
rows.append(("—", "strut slenderness KL/r (no buckling below ~25)", KL_r, None))
for c, it, v, a in rows:
    print(f"{c:13s} {it:52s} {v:8.1f} " + (f"{a:6.0f}  FoS {a / v:5.2f}" if a else ""))
