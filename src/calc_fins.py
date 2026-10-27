"""Anti-roll fins (dirt wings) for the rev H shield. Method from the team's reference chat:
resisting torque = sum over fins of (ultimate lateral soil pressure x effective projected area x radius) >= FS x max torque.
Clay: q_ult = Nc x cu.  Only fin height beyond the 10.2 mm radial overcut bears on undisturbed soil.
Shell skin friction against roll is not counted (shown separately).
"""
import paths  # noqa: F401  (UTF-8 stdout, output folders)
import math
pi = math.pi
T_int = 10.0            # kNm, cutterhead torque interlock (inhibit rotate above 10 kNm)
T_relief = 11.2         # kNm, MS18 at 250 bar theoretical (if the HPU relief is set there)
FS_target = 2.0
R_sh = 304.8            # shield OD radius
overcut = 315.0 - R_sh  # gauge radius 315 -> 10.2 mm
n_fin, t_fin, h, L = 4, 20.0, 70.0, 990.0
ramp_f = h / math.tan(math.radians(30))      # 30 deg leading ramp
ramp_r = h / math.tan(math.radians(45))      # 45 deg trailing ramp
angles = (30, 90, 270, 330)                  # 0 = 12 o'clock; rails at 150/210, lube ports at 0/60/300


def eff_area_and_radius():
    # integrate the fin height above the overcut along its length (mm2), and its area-weighted radius
    N = 4000
    A = Ar = 0.0
    for i in range(N):
        s = (i + 0.5) * L / N
        hh = min(h, s * h / ramp_f, (L - s) * h / ramp_r)
        he = max(0.0, hh - overcut)
        A += he * L / N
        Ar += he * L / N * (R_sh + overcut + he / 2)
    return A, Ar / A


A1, Rc = eff_area_and_radius()
A_tot = n_fin * A1 / 1e6                        # m2
print(f"Fin: {n_fin} x {t_fin:.0f} thk x {h:.0f} high x {L:.0f} long, 30 deg lead ramp ({ramp_f:.0f}), 45 deg tail ramp ({ramp_r:.0f}); at {angles} deg")
print(f"Effective area beyond the overcut: {A1/1e6:.4f} m2 per fin, {A_tot:.3f} m2 total; centroid radius {Rc:.1f} mm")
print(f"Envelope over the fins: dia {2*(R_sh+h):.0f} (cut bore dia 630)")
print("\nResisting torque (kNm) and FoS on the 10 kNm interlock / 11.2 kNm at 250 bar relief")
print(f"  {'cu kPa':>6s} {'Nc':>4s} {'q_ult kPa':>9s} {'T_resist':>9s} {'FoS 10':>7s} {'FoS 11.2':>8s}")
for cu in (25, 50, 75):
    for Nc in (6, 9):
        q = Nc * cu
        T = q * A_tot * Rc / 1000.0
        print(f"  {cu:6d} {Nc:4d} {q:9.0f} {T:9.1f} {T/T_int:7.2f} {T/T_relief:8.2f}")
# required area check at the design point (cu 50, Nc 6, FS 2)
q_d = 6 * 50
A_req = FS_target * T_int / (q_d * Rc / 1000.0)
print(f"\nDesign point cu 50 kPa, Nc 6, FS 2: area needed {A_req:.3f} m2, provided {A_tot:.3f} m2")
# skin friction on the lubricated shield (not counted)
A_sh = pi * 2 * R_sh / 1000 * 1.285
for tau in (3, 8):
    print(f"  shield skin shear {tau} kPa -> roll resistance {tau*A_sh*R_sh/1000:.1f} kNm (not counted)")
# loads on each fin at FS-level torque (20 kNm)
T_d = FS_target * T_int
F_fin = T_d / (n_fin * Rc / 1000.0)
w = F_fin * 1e3 / (A1 / (h - overcut))      # N per mm of effective length
arm = overcut + (h - overcut) / 2
Mroot = w * arm
sig = 6 * Mroot / t_fin ** 2
leg = 8.0
weld = Mroot / t_fin / (0.707 * leg) + w / (2 * 0.707 * leg)
shell_b = 6 * Mroot / 12.7 ** 2
print(f"\nAt {T_d:.0f} kNm: {F_fin:.1f} kN per fin, {w:.1f} N/mm")
print(f"  fin plate root bending {sig:.1f} MPa vs 207 (FoS {207/sig:.1f})")
print(f"  2 x {leg:.0f} mm fillets {weld:.1f} MPa vs 145 (FoS {145/weld:.1f})")
print(f"  shell wall local bending {shell_b:.1f} MPa vs 207 (FoS {207/shell_b:.1f})")
tau_w = T_d * 1e6 / (2 * pi * 292.1 ** 2 * 0.707 * 14)
print(f"  ring 1 weld torsion {tau_w:.1f} MPa vs 145")
# net side force from the asymmetric pattern
fy = sum(-math.sin(math.radians(a)) for a in angles) * F_fin
fz = sum(math.cos(math.radians(a)) for a in angles) * F_fin
print(f"  net lateral force on the shield {math.hypot(fy, fz):.1f} kN (pattern not symmetric) -> {math.hypot(fy,fz)*1e3/(609.6*1285)*1000:.0f} kPa on the shield side")
# jacking drag added
cu = 50.0
plough = n_fin * (h - overcut) * t_fin * 9 * cu / 1e6 * 0.5          # 30 deg ramp, half of end bearing
adh = n_fin * 2 * A1 / 1e6 * 0.5 * cu
print(f"\nAdded jacking force at cu 50: ploughing {plough:.1f} kN + side adhesion (alpha 0.5) {adh:.1f} kN = {plough+adh:.1f} kN "
      f"({(plough+adh)/613*100:.1f} % of the 613 kN relief cap)")
print(f"Fin mass {n_fin * t_fin * h * L * 7.85e-6 * 0.93:.1f} kg total")
