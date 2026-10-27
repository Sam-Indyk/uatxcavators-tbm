"""Rev G: ring 1 with Ø400 x 40 counterbore (70 thick under the seat, 110 outside), splined head hub, overhang.
Ring 1 modelled as an annular plate guided at r = 200 and pinned at the weld; the 70 mm lip governs at r = 200,
the 110 mm section governs at the pipe holes (r = 245). A572-50, allowable 0.6 Fy = 207 MPa.
"""
import math, importlib.util
spec = importlib.util.spec_from_file_location("d", "/home/claude/cad/calc_revD.py")
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
pi = math.pi
P_ch = 0.1 * pi / 4 * 584.2 ** 2
M = 62e6 + 2.28e6
fa = 0.6 * 345
for c, P in (("LC2 jam", 590e3 + P_ch), ("LC3 envelope", 800e3 + P_ch)):
    Peq = P + 2 * M / 200
    res = d.annular_plate(Peq, 292.1, 200.0, 70.0, "pinned")
    s200 = max(abs(res[0][1]), abs(res[0][2]))
    r245 = min(res, key=lambda x: abs(x[0] - 245))
    s245 = 2.5 * max(abs(r245[1]), abs(r245[2])) * (70 / 110) ** 2
    q = Peq / (2 * pi * 200)
    print(f"{c:13s} lip at r=200 (70 thk): {s200:6.1f} MPa FoS {fa/s200:4.2f} | pipe holes (110 thk, Kt 2.5): {s245:5.1f} FoS {fa/s245:4.2f} | lip shear {q/70:4.1f} MPa FoS {0.4*345/(q/70):4.1f}")
# splined hub: Ø130 x 40 engagement, 20 kNm
T = 20e6
tau = T / (65 * 0.5 * pi * 130 * 40)
print(f"spline Ø130 x 40, mean tooth shear at 20 kNm: {tau:.1f} MPa (0.4 Fy 4140 QT = 262)")
for L in (400.0,):
    Fr = 62e6 / L
    print(f"23228 s0 at L={L:.0f}: {1250e3/(1.3*Fr):.2f}; side-load factor 1 + 339.8/{L:.0f} = {1+339.8/L:.2f}")
