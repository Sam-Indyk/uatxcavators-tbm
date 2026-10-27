"""Rev C spindle mount: joint and weld check, thrust path and torque path.
Method: AISC 360 ASD / AWS D1.1 'weld treated as a line'. Units N, mm, MPa.
"""
import math

pi = math.pi
# ---------------- materials / allowables ----------------
F_EXX = 483.0                 # E70 / ER70S-6 filler
tau_w = 0.30 * F_EXX          # fillet weld, shear on throat (ASD)  = 145
Fy_plate = 250.0              # A36 rings, plates, cartridge (conservative)
Fy_shell = 240.0              # A53 Gr B shell (assumed grade)
tau_base_shell = 0.40 * Fy_shell   # base metal shear at weld fusion face
tau_base_plate = 0.40 * Fy_plate
f_bend = 0.60 * Fy_plate
f_bear = 0.90 * Fy_plate      # bearing on finished surfaces

# ---------------- geometry ----------------
R_w = 584.2 / 2               # ring-to-shell weld line radius
L_w = 2 * pi * R_w            # weld length per fillet
R_fl, t_bp, span_bp = 210.0, 40.0, 40.0
t_shell, R_shell_m = 12.7, (609.6 - 12.7) / 2

# ---------------- load cases (thrust side) ----------------
P_ch = 0.1 * pi / 4 * 584.2 ** 2          # 1 bar chamber pressure on bulkhead, N
cases = {
    "LC1 structural thrust": dict(P=800e3 + P_ch, M=0.0),
    "LC2 jam":               dict(P=590e3 + P_ch, M=62e6),
    "LC3 envelope":          dict(P=800e3 + P_ch, M=62e6),
}
W_mod = 306 * 9.81 * 2.0                  # bulkhead module weight, dynamic factor 2
T_ring1 = 0.2e6                           # bearing friction torque reaching ring 1

# torque side
T_design = 10e6 * 2.0                     # 10 kNm interlock x 2 shock factor
W_mot = 198 * 9.81 * 2.0                  # motor module weight, dynamic factor 2
e_mot = 240.0                             # motor CG behind ring 2 face


def weld_line(P_ax, M, T, V, R):
    """force per unit length (N/mm) on a circular weld line of radius R"""
    f_ax = P_ax / (2 * pi * R) + M / (pi * R ** 2)   # axial: direct + bending (S_w = pi R^2)
    f_t = T / (2 * pi * R ** 2)                      # torsion (J_w = 2 pi R^3)
    f_v = V / (pi * R)                               # transverse shear, peak
    return math.sqrt(f_ax ** 2 + f_t ** 2 + f_v ** 2), f_ax, f_t, f_v


rows = []


def add(joint, case, mode, stress, allow):
    rows.append((joint, case, mode, stress, allow, allow / stress if stress else float("inf")))


for name, c in cases.items():
    P, M = c["P"], c["M"]
    # 1 thrust bearing housing washer on cartridge shoulder (moment goes to radial bearings)
    A_sh = pi / 4 * (240 ** 2 - 196 ** 2)
    add("29328N washer on shoulder", name, "compression (bearing)", P / A_sh, f_bear)
    add("Cartridge shoulder root, Ø241 × 30", name, "shear", P / (pi * 241 * 30), tau_base_plate)
    # 2 cartridge tube in tension, min section Ø310 / Ø252
    add("Cartridge tube, Ø310/Ø252", name, "tension", P / (pi / 4 * (310 ** 2 - 252 ** 2)), f_bend)
    # 3 cartridge flange on bulkhead plate: contact Ø310–420 less holes and scallops
    A_fl = pi / 4 * (420 ** 2 - 310 ** 2) - 12 * pi / 4 * 17.5 ** 2 - 2 * 3000
    S_fl = pi / 64 * (420 ** 4 - 310 ** 4) / 210
    s_max, s_min = P / A_fl + M / S_fl, P / A_fl - M / S_fl
    add("Flange on plate", name, "compression (bearing)", s_max, f_bear)
    rows.append(("Flange on plate", name, "min contact stress (≥0 = no gap)", s_min, 0.0, None))
    # 4 bulkhead plate between flange edge and ring
    q = P / (2 * pi * R_fl) + M / (pi * R_fl ** 2)   # peak line load at flange edge
    add("Bulkhead plate, 40 thk", name, "shear", q / t_bp, tau_base_plate)
    add("Bulkhead plate, 40 thk", name, "bending (fixed-guided)", 6 * (q * span_bp / 2) / t_bp ** 2, f_bend)
    # 5 plate on ring 1 / gasket band R250–280
    A_r = pi * (280 ** 2 - 250 ** 2)
    S_r = pi / 64 * (560 ** 4 - 500 ** 4) / 280
    add("Plate on ring 1 (gasket band)", name, "compression (bearing)", P / A_r + M / S_r, f_bear)
    rows.append(("Plate on ring 1 (gasket band)", name, "min contact stress (≥0 = no gap)", P / A_r - M / S_r, 0.0, None))
    # 6 ring 1 weld
    f, fa, ft, fv = weld_line(P, M, T_ring1, W_mod, R_w)
    for leg, nw in ((10, 1), (12, 1), (10, 2)):
        lab = f"Ring 1 weld, {nw} × {leg} mm fillet"
        add(lab, name, "weld throat shear", f / (nw * 0.707 * leg), tau_w)
        add(lab, name, "shell base metal at fusion face", f / (nw * leg), tau_base_shell)
    # 7 shell wall axial + bending
    A_s = 2 * pi * R_shell_m * t_shell
    S_s = pi * R_shell_m ** 2 * t_shell
    add("Shell wall", name, "axial + bending", P / A_s + M / S_s, f_bend)

# torque side, one case
f, fa, ft, fv = weld_line(0.0, W_mot * e_mot, T_design, W_mot, R_w)
add("Ring 2 weld, 1 × 8 mm fillet", "LC4 torque 20 kNm", "weld throat shear", f / (0.707 * 8), tau_w)
add("Ring 2 weld, 1 × 8 mm fillet", "LC4 torque 20 kNm", "shell base metal at fusion face", f / 8, tau_base_shell)
mu = 0.30
pre_M12 = 0.70 * 84.3 * 830
pre_M20 = 0.70 * 245 * 830
add("Motor plate to ring 2, 16 × M12", "LC4 torque 20 kNm", "slip, per bolt (kN)",
    T_design / (16 * 271) / 1e3, mu * pre_M12 / 1e3)
add("Motor to plate, 12 × M20", "LC4 torque 20 kNm", "slip, per bolt (kN)",
    T_design / (12 * 190) / 1e3, mu * pre_M20 / 1e3)
add("Shell wall", "LC4 torque 20 kNm", "torsion", T_design / (2 * pi * R_shell_m ** 2 * t_shell), 0.4 * Fy_shell)

# cartridge flange bolts if contact gaps (LC2): conservative moment-only bolt tension
add("Cartridge to plate, 12 × M16", "LC2 jam", "tension, per bolt (kN)", 2 * 62e6 / (12 * 190) / 1e3, 0.7 * 157 * 830 / 1e3)

if __name__ == "__main__":
    print(f"tau_w={tau_w:.0f}  P_ch={P_ch/1e3:.1f} kN")
    w = max(len(r[0]) for r in rows)
    for r in rows:
        fos = "" if r[5] is None else f"{r[5]:6.2f}"
        print(f"{r[0]:{w}s} | {r[1]:22s} | {r[2]:34s} | {r[3]:7.1f} | {r[4]:6.0f} | {fos}")
