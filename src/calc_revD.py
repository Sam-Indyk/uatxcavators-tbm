"""Rev D spindle mount: load path and joint check.
AISC 360 ASD / AWS D1.1; fillet welds treated as a line; ring 1 as an axisymmetric Kirchhoff annular plate.
Units N, mm, MPa. Edit inputs at the top.
"""
import paths  # noqa: F401  (UTF-8 stdout, output folders)
import math

pi = math.pi
# ---------- inputs ----------
P_jam, P_str = 590e3, 800e3            # axial: jam, structural design case
M_head = 62e6                          # jam overturning moment at front bearing
T_shock = 20e6                         # 10 kNm interlock x 2
P_ch = 0.1 * pi / 4 * 584.2 ** 2       # 1 bar on the bulkhead area
L = 400.0                              # 23228 centre to centre
lev_flange = 218.0 - 59.0              # front 23228 centre to cartridge flange face
lev_sleeve = 178.0 - 59.0              # front 23228 centre to sleeve/disc weld
lev_ring2 = 520.0 - 459.0              # rear 23228 centre to ring 2 weld face
W_rear = (80.4 + 4.2 + 200) * 9.81 * 2  # rear plate + drive (200 kg allowance), x2 dynamic
R_w = 584.2 / 2

F_EXX, Fy_pl, Fy_sh, Fy_shaft = 483.0, 250.0, 240.0, 655.0
tau_w = 0.30 * F_EXX
a_bend, a_shear, a_bear = 0.60 * Fy_pl, 0.40 * Fy_pl, 0.90 * Fy_pl
a_base_shell = 0.40 * Fy_sh
nu = 0.3

R_brg = M_head / L                     # radial reaction at each 23228

rows = []


def add(group, item, case, mode, s, allow, unit="MPa"):
    fos = allow / s if s > 0 else float("inf")
    rows.append((group, item, case, mode, s, allow, fos, unit))


def weld_line(P_ax, M, T, V, R):
    f_ax = P_ax / (2 * pi * R) + M / (pi * R ** 2)
    f_t = T / (2 * pi * R ** 2)
    f_v = V / (pi * R)
    return math.sqrt(f_ax ** 2 + f_t ** 2 + f_v ** 2)


def annular_plate(P, a, b, t, outer="pinned", n=400):
    """axisymmetric plate, line load P (total) at inner radius b, inner edge guided (slope 0).
    returns list of (r, sigma_r, sigma_t) at the faces."""
    k = P / (2 * pi)
    # theta*D = k(r/2 ln r - r/4) + c1 r/2 + c2 / r ; dtheta*D = k(0.5 ln r + 0.25) + c1/2 - c2/r^2
    th = lambda r_, c1, c2: k * (r_ / 2 * math.log(r_) - r_ / 4) + c1 * r_ / 2 + c2 / r_
    dth = lambda r_, c1, c2: k * (0.5 * math.log(r_) + 0.25) + c1 / 2 - c2 / r_ ** 2
    # linear system in c1, c2
    def row_theta(r_):
        return (r_ / 2, 1 / r_, -k * (r_ / 2 * math.log(r_) - r_ / 4))
    def row_Mr(r_):
        return (0.5 + nu * 0.5, -1 / r_ ** 2 + nu / r_ ** 2,
                -(k * (0.5 * math.log(r_) + 0.25) + nu * k * (0.5 * math.log(r_) - 0.25)))
    e1 = row_theta(b)
    e2 = row_theta(a) if outer == "fixed" else row_Mr(a)
    det = e1[0] * e2[1] - e1[1] * e2[0]
    c1 = (e1[2] * e2[1] - e1[1] * e2[2]) / det
    c2 = (e1[0] * e2[2] - e1[2] * e2[0]) / det
    out = []
    for i in range(n + 1):
        r_ = b + (a - b) * i / n
        Mr = dth(r_, c1, c2) + nu * th(r_, c1, c2) / r_
        Mt = th(r_, c1, c2) / r_ + nu * dth(r_, c1, c2)
        out.append((r_, 6 * Mr / t ** 2, 6 * Mt / t ** 2))
    return out


cases = {"LC2 jam": P_jam + P_ch, "LC3 envelope": P_str + P_ch}

# ---------- shaft (moment at the front 23228 seat) ----------
d = 140.0
sig = 32 * M_head / (pi * d ** 3)
tau = 16 * T_shock / (pi * d ** 3)
vm = math.sqrt(sig ** 2 + 3 * tau ** 2)
add("Shaft", "Ø140 at front 23228 seat", "LC2", "von Mises, nominal", vm, Fy_shaft)
add("Shaft", "Ø140 at collar fillet, Kt 1.5", "LC2", "von Mises", vm * 1.5, Fy_shaft)
add("Shaft", "Ø130 spline at drive end", "LC4", "torsion, nominal", 16 * T_shock / (pi * 130 ** 3), 0.577 * Fy_shaft)

# ---------- bearings: required static ratings ----------
Fa_23 = 0.15 * R_brg                                    # friction on the sliding outer ring
P0_23 = R_brg + 2.0 * Fa_23                             # Y0 ~ 2 for 23228 (confirm in catalogue)
rows.append(("Bearings", "23228 front/rear", "LC2", f"P0 (kN); C0 required at s0 = 2: {2*P0_23/1e3:.0f} kN", P0_23 / 1e3, None, None, "kN"))
rows.append(("Bearings", "29328N", "LC2", f"P0 (kN); C0 required at s0 = 2: {2*P_jam/1e3:.0f} kN", P_jam / 1e3, None, None, "kN"))
rows.append(("Bearings", "Radial reaction per 23228", "LC2", "62 kNm / L", R_brg / 1e3, None, None, "kN"))

for case, P in cases.items():
    M_fl = R_brg * lev_flange
    # thrust bearing housing washer on disc face (Ø200 bore to Ø240)
    add("Thrust path", "29328N washer on disc face", case, "bearing", P / (pi / 4 * (240 ** 2 - 200 ** 2)), a_bear)
    add("Thrust path", "Disc shoulder root shear, Ø241 × 40", case, "shear", P / (pi * 241 * 40), a_shear)
    # flange disc on ring 1: contact R130-200 less 12 holes
    A = pi * (200 ** 2 - 130 ** 2) - 12 * pi / 4 * 17.5 ** 2 - 12 * pi / 4 * (27 ** 2 - 17.5 ** 2) * 0
    S = pi / 64 * (400 ** 4 - 260 ** 4) / 200
    add("Thrust path", "Disc on ring 1", case, "bearing (max)", P / A + M_fl / S, a_bear)
    rows.append(("Thrust path", "Disc on ring 1", case, "min contact stress (> 0: no gap)", P / A - M_fl / S, None, None, "MPa"))
    # ring 1 plate
    for t in (50.0, 60.0):
        P_eq = P + 2 * M_fl / 200.0
        res = annular_plate(P_eq, 292.1, 200.0, t, "pinned")
        smax = max(max(abs(sr), abs(st)) for _, sr, st in res)
        r245 = min(res, key=lambda x: abs(x[0] - 245))
        s245 = max(abs(r245[1]), abs(r245[2]))
        add("Ring 1", f"Ring 1 plate {t:.0f} thk, pinned at weld", case, "bending, max (at r = 200)", smax, a_bend)
        add("Ring 1", f"Ring 1 plate {t:.0f} thk, at pipe holes r = 245, Kt 2.5", case, "bending", 2.5 * s245, a_bend)
    add("Ring 1", "Ring 1 shear at r = 200, 60 thk", case, "shear", (P + 2 * M_fl / 200) / (2 * pi * 200 * 60), a_shear)
    # ring 1 weld, single front fillet
    f = weld_line(P, M_fl, 0.2e6, R_brg, R_w)
    for leg in (12.0, 14.0):
        add("Welds", f"Ring 1, 1 × {leg:.0f} fillet", case, "throat shear", f / (0.707 * leg), tau_w)
        add("Welds", f"Ring 1, 1 × {leg:.0f} fillet", case, "shell base metal", f / leg, a_base_shell)
    # shell between rings: carries the bearing couple
    A_s = 2 * pi * 298.45 * 12.7
    S_s = pi * 298.45 ** 2 * 12.7
    add("Shell", "Shell at ring 1", case, "axial + bending", P / A_s + M_fl / S_s, a_bend)

# cartridge sleeve and its weld (radial reaction only; thrust bypasses the weld)
M_sl = R_brg * lev_sleeve
S_sl = pi * (310 ** 4 - 252 ** 4) / (32 * 310)
add("Cartridge", "Sleeve Ø310/Ø252 at disc", "LC2", "bending", M_sl / S_sl, a_bend)
f_sl = weld_line(0.0, M_sl, 0.0, R_brg, 155.0)
add("Welds", "Sleeve to disc, 1 × 12 fillet", "LC2", "throat shear", f_sl / (0.707 * 12), tau_w)
# cartridge screws: joint stays closed, screws carry shear by friction only
pre16 = 0.70 * 157 * 830
add("Fasteners", "Cartridge 12 × M16 10.9", "LC2", "friction vs radial reaction (kN)", R_brg / 1e3, 12 * 0.30 * pre16 / 1e3, "kN")

# ring 2 / rear plate
f2 = weld_line(0.0, (R_brg + W_rear) * lev_ring2, T_shock, R_brg + W_rear, R_w)
add("Welds", "Ring 2, 1 × 10 fillet", "LC2+LC4", "throat shear", f2 / (0.707 * 10), tau_w)
add("Welds", "Ring 2, 1 × 10 fillet", "LC2+LC4", "shell base metal", f2 / 10, a_base_shell)
pre20 = 0.70 * 245 * 830
v_bolt = (R_brg + W_rear) / 12 + T_shock / (12 * 255)
add("Fasteners", "Rear plate 12 × M20 10.9", "LC2+LC4", "shear per screw vs friction (kN)", v_bolt / 1e3, 0.30 * pre20 / 1e3, "kN")
add("Rear plate", "Hub Ø310/Ø250 under rear 23228", "LC2", "bearing on seat (proj. area)", R_brg / (250 * 88), a_bear)
add("Shell", "Shell torsion", "LC4", "shear", T_shock / (2 * pi * 298.45 ** 2 * 12.7), a_base_shell)

if __name__ == "__main__":
    print(f"R_brg = {R_brg/1e3:.0f} kN   M at flange = {R_brg*lev_flange/1e6:.1f} kNm   P_ch = {P_ch/1e3:.1f} kN")
    for g, it, c, m, s, a, fos, u in rows:
        a_s = "" if a is None else f"{a:7.0f}"
        f_s = "" if fos is None else f"{fos:6.2f}"
        print(f"{g:11s} | {it:46s} | {c:12s} | {m:40s} | {s:8.1f} | {a_s} | {f_s}")
