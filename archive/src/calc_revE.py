"""Rev E spindle mount (single ring): load path, joint and torque-transfer check.
AISC 360 ASD / AWS D1.1; welds as a line; ring 1 as an axisymmetric annular plate (pinned at weld, guided at r = 200).
Torque path: drive housing -> 12 x M16 -> cartridge -> 16 x M12 (+ 2 dowels) -> ring 1 -> weld -> shell.
Units N, mm, MPa.
"""
import math
import importlib.util

spec = importlib.util.spec_from_file_location("d", "/home/claude/cad/calc_revD.py")
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
annular_plate, weld_line = d.annular_plate, d.weld_line
pi = math.pi

# ---------- inputs ----------
P_ch = 0.1 * pi / 4 * 584.2 ** 2
cases = {"LC2 jam": 590e3 + P_ch, "LC3 envelope": 800e3 + P_ch}
M_head = 62e6
T = 20e6                                   # 10 kNm interlock x 2
L = 400.0
R_brg = M_head / L
W_drive = 200 * 9.81 * 2                   # drive allowance x2 dynamic
M_drive = W_drive * 580.0                  # drive CG ~580 behind ring 1 face
M_fl = M_head + M_drive                    # whole couple passes the flange in rev E
F_EXX, Fy_pl, Fy_r1, Fy_sh, Fy_shaft = 483.0, 250.0, 345.0, 240.0, 655.0
tau_w = 0.30 * F_EXX
fb_r1 = 0.60 * Fy_r1

# bolts (ISO 10.9): stress area, preload 70 % proof (830 MPa)
As = {"M12": 84.3, "M16": 157.0}
pre = {k: 0.70 * v * 830 for k, v in As.items()}
V_allow_bolt = {k: 0.45 * 1040 * v / 2.0 for k, v in As.items()}    # bearing-type, threads in shear plane, ASD
dowel_allow = 0.40 * 1100 * pi / 4 * 16 ** 2                       # Ø16 hardened dowel, single shear, ASD-style

rows = []


def add(group, item, mode, s, allow, unit="MPa"):
    rows.append((group, item, mode, s, allow, (allow / s) if (allow and s > 0) else None, unit))


# ---------- torque transfer joints ----------
for name, size, n, R in (("Drive to cartridge rear face", "M16", 12, 140.0),
                         ("Cartridge disc to ring 1", "M12", 16, 185.0)):
    Vb = T / (n * R)
    for mu, cond in ((0.30, "clean, dry machined"), (0.15, "oily / greased")):
        add("Torque joints", f"{name}, {n} × {size}", f"slip per bolt, μ {mu} ({cond})", Vb / 1e3, mu * pre[size] / 1e3, "kN")
    add("Torque joints", f"{name}, {n} × {size}", "bolt shear if slipped", Vb / 1e3, V_allow_bolt[size] / 1e3, "kN")
add("Torque joints", "Cartridge disc to ring 1, 2 × Ø16 dowels", "dowels alone carry torque", T / (2 * 185.0) / 1e3, dowel_allow / 1e3, "kN")
add("Torque joints", "Drive to cartridge, 3 × Ø16 dowels", "dowels alone carry torque", T / (3 * 140.0) / 1e3, dowel_allow / 1e3, "kN")
J = pi / 32 * (310 ** 4 - 250 ** 4)
add("Torque joints", "Cartridge tube Ø310/Ø250", "torsion", T * 155 / J, 0.40 * Fy_pl)

# ---------- shaft and bearings (as rev D) ----------
dsh = 140.0
sig = 32 * M_head / (pi * dsh ** 3); tau = 16 * T / (pi * dsh ** 3)
vm = math.sqrt(sig ** 2 + 3 * tau ** 2)
add("Shaft", "Ø140 at front 23228", "von Mises nominal", vm, Fy_shaft)
add("Shaft", "Ø140 at collar, Kt 1.5", "von Mises", 1.5 * vm, Fy_shaft)

for case, P in cases.items():
    # flange joint, contact r = 170-200, 16 x M12
    A = pi * (200 ** 2 - 170 ** 2) - 16 * pi / 4 * 13.5 ** 2
    S = pi / 64 * (400 ** 4 - 340 ** 4) / 200
    s_min = P / A - M_fl / S
    clamp_need = max(0.0, M_fl * A / S - P)
    rows.append(("Flange joint", f"Disc on ring 1 ({case})", "min contact without preload", s_min, None, None, "MPa"))
    if clamp_need > 0:
        add("Flange joint", f"Disc on ring 1 ({case})", "clamp needed vs 16 × M12 preload (kN)", clamp_need / 1e3, 16 * pre["M12"] / 1e3, "kN")
    add("Flange joint", f"Disc on ring 1 ({case})", "max contact with preload", (P + 16 * pre["M12"]) / A + M_fl / S, 0.9 * Fy_r1)
    add("Flange joint", f"29328N washer on disc ({case})", "bearing", P / (pi / 4 * (240 ** 2 - 200 ** 2)), 0.9 * Fy_pl)
    # ring 1 plate
    for t in (70.0,):
        Peq = P + 2 * M_fl / 200.0
        res = annular_plate(Peq, 292.1, 200.0, t, "pinned")
        smax = max(max(abs(a), abs(b)) for _, a, b in res)
        r245 = min(res, key=lambda x: abs(x[0] - 245))
        add("Ring 1", f"70 thk A572-50 ({case})", "bending max", smax, fb_r1)
        add("Ring 1", f"70 thk A572-50 ({case})", "bending at pipe holes, Kt 2.5", 2.5 * max(abs(r245[1]), abs(r245[2])), fb_r1)
    # ring 1 weld, single front fillet
    f = weld_line(P, M_fl, T, W_drive + 133 * 9.81 * 2, 292.1)
    for leg in (12.0, 14.0):
        add("Ring 1 weld", f"1 × {leg:.0f} fillet ({case})", "throat", f / (0.707 * leg), tau_w)
        add("Ring 1 weld", f"1 × {leg:.0f} fillet ({case})", "shell base metal", f / leg, 0.40 * Fy_sh)
    As_ = 2 * pi * 298.45 * 12.7; Ss = pi * 298.45 ** 2 * 12.7
    add("Shell", f"at ring 1 ({case})", "axial + bending", P / As_ + M_fl / Ss, 0.6 * Fy_sh)

# cartridge welds (thrust bypasses both)
f_front = weld_line(0, R_brg * (178 - 59), 0, R_brg, 155.0)
add("Cartridge welds", "Front sleeve to disc, 1 × 12 fillet", "throat", f_front / (0.707 * 12), tau_w)
f_rear = weld_line(0, R_brg * (459 - 233) + M_drive, T, R_brg, 155.0)
add("Cartridge welds", "Rear sleeve to disc, 1 × 12 fillet", "throat", f_rear / (0.707 * 12), tau_w)
add("Cartridge welds", "Rear sleeve to disc, groove, 30 wall", "base metal shear", f_rear / 30, 0.40 * Fy_pl)
add("Shell", "torsion", "shear", T / (2 * pi * 298.45 ** 2 * 12.7), 0.40 * Fy_sh)

if __name__ == "__main__":
    print(f"R_brg {R_brg/1e3:.0f} kN; moment through flange {M_fl/1e6:.1f} kNm; P_ch {P_ch/1e3:.1f} kN")
    for g, it, m, s, a, fos, u in rows:
        a_s = "" if a is None else f"{a:8.1f}"
        f_s = "" if fos is None else f"{fos:6.2f}"
        print(f"{g:15s} | {it:50s} | {m:44s} | {s:8.1f} | {a_s} | {f_s} {u}")
