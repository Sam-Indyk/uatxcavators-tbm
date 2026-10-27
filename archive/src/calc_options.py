"""Bearing static checks and option-specific joints for the design-option comparison.
Ratings (SKF catalogue values, used as proxies for Koyo / NTN): 23228 CC C0 = 1250 kN; 29328 E C0 = 2850 kN; 32228 C0 = 1000 kN.
32228 factors e = 0.44, Y = 1.4, Y0 = 0.8 are typical 322-series values (confirm with the supplier).
"""
import math
pi = math.pi
M = 62e6
P_ch = 0.1 * pi / 4 * 584.2 ** 2
cases = {"LC2 jam": 590e3 + P_ch, "LC3 envelope": 800e3 + P_ch}
C0_23, C0_29, C0_322 = 1250e3, 2850e3, 1000e3
Y_322, Y0_322 = 1.4, 0.8
out = {}

# spherical set (options S and E), L = 400
for L in (250.0, 300.0, 400.0):
    Fr = M / L
    P0_23 = Fr + 2.0 * 0.15 * Fr          # friction axial on the sliding outer ring, Y0 ~ 2
    out[f"sph_L{L:.0f}_23228_s0"] = C0_23 / P0_23
for c, P in cases.items():
    out[f"sph_29328_s0_{c}"] = C0_29 / P

# tapered pair (option T), back-to-back, pressure centres ~32 mm outside each bearing
a_off = 32.0
phys = 323.0 - 71.75 / 2 - (15 + 71.75 / 2)
L_eff = phys + 2 * a_off
out["T_L_eff"] = L_eff
for c, P in cases.items():
    Fr = M / L_eff
    Fa_A = P + 0.5 * Fr / Y_322
    P0 = max(Fr, 0.5 * Fr + Y0_322 * Fa_A)
    out[f"T_32228_s0_{c}"] = C0_322 / P0
    out[f"T_32228_P0_{c}_kN"] = P0 / 1e3
# infinite spacing limit
out["T_32228_s0_jam_Linf"] = C0_322 / (Y0_322 * (590e3 + P_ch))
out["T_C0_needed_jam_s0_2_kN"] = 2 * (0.5 * M / L_eff + Y0_322 * (590e3 + P_ch + 0.5 * M / L_eff / Y_322)) / 1e3

# option S: flange-to-tube CJP is in the thrust path (tension normal to the weld)
for c, P in cases.items():
    f = P / (2 * pi * 155) + M / (pi * 155 ** 2)
    out[f"S_CJP_tension_MPa_{c}"] = f / 30.0
    out[f"S_CJP_FoS_A36_{c}"] = 150.0 / (f / 30.0)
# option S tube between shoulder and flange: tension + bending
A_t = pi / 4 * (310 ** 2 - 252 ** 2)
S_t = pi * (310 ** 4 - 252 ** 4) / (32 * 310)
for c, P in cases.items():
    out[f"S_tube_MPa_{c}"] = P / A_t + M / S_t

# option T: block-to-tube weld carries rear bearing radial + moment only
Fr = M / L_eff
f = (Fr * (287 - 110)) / (pi * 155 ** 2) + Fr / (pi * 155) + 20e6 / (2 * pi * 155 ** 2)
out["T_tubeweld_CJP_MPa"] = f / 30.0
out["T_tubeweld_12fillet_MPa"] = f / (0.707 * 12)

if __name__ == "__main__":
    for k, v in out.items():
        print(f"{k:40s} {v:9.2f}")
