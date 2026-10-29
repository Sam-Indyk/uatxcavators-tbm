"""Rev I hand calculations for every part, with the equation behind each number.

Each check is a row: part, item, load case, equation (symbols then numbers), value, allowable, basis, FoS on the
allowable, FoS on yield, requirement. Rows are printed as tables and written to out/calc/calc_revI.json, which
tools/make_manual.py turns into the design manual (docs/manual-*.md).

Inputs: src/loads.py (load cases), out/calc/massprops_revI.json (masses and CGs from the detailed model; run
massprops_revI.py first), out/fea/*.json (FEA results, read where a check uses them).

Units: N, mm, MPa, N·mm (kN, kNm in the tables). ASD (allowable stress design, AISC 360 / AWS D1.1):
bending and axial 0.6 Fy, shear 0.4 Fy, bearing on machined faces 0.9 Fy, fillet weld throat 0.3 × 482 = 145 MPa.
"""
import json
import math
from pathlib import Path

import paths
import loads as LD

pi = math.pi
CALC, FEA = paths.CALC, paths.OUT / "fea"
MP = json.loads((CALC / "massprops_revI.json").read_text(encoding="utf-8"))
G = 9.81
E = 200e3
NU = 0.3

# ---------------- materials (Fy, Fu in MPa) ----------------
MAT = {
    "A572-42": (290.0, 415.0, "ASTM A572 Gr 42 plate over 4 in (ring 1 from 4.5 in plate; Gr 50 stops at 4 in)"),
    "A572-50": (345.0, 450.0, "ASTM A572 Gr 50 plate ≤ 4 in"),
    "shell": (241.0, 414.0, "24 in × 0.500 in pipe, API 5L Gr B / ASTM A53 Gr B assumed (grade to confirm)"),
    "E355": (335.0, 490.0, "EN 10297-1 E355 seamless tube, wall 40-65 mm band"),
    "4140QT": (655.0, 860.0, "AISI 4140 quenched and tempered bar (28-32 HRC)"),
    "A1085": (345.0, 450.0, "ASTM A1085 round HSS 3.000 × 0.250 in"),
    "A106B": (241.0, 414.0, "ASTM A106 Gr B / A53 Gr B pipe (14 in XS adapter tube)"),
    "42CrMo4": (450.0, 750.0, "EN 10083-3 42CrMo4+QT, section 160-250 mm (coupling hub)"),
    "E70": (400.0, 482.0, "E70 weld metal (E7018 / ER70S-6)"),
    "10.9": (830.0, 1040.0, "ISO 898-1 property class 10.9 bolt (proof / tensile)"),
}
A_S = {6: 20.1, 8: 36.6, 10: 58.0, 12: 84.3, 16: 157.0, 20: 245.0, 24: 353.0}      # bolt stress areas mm²
W_FILLET = 0.3 * 482.0                                                         # 145 MPa
PRELOAD = lambda d: 0.7 * A_S[d] * 830.0                                       # 70 % of proof load
TIGHTEN = lambda d: 0.17 * PRELOAD(d) * d / 1e3                                # Nm, K = 0.17

rows = []
CASES = ("LC1", "LC2", "LC3", "LC4")
R_CB, CB, LAND = 192.0, 30.0, 15.0                 # Rev I: Ø384 x 30 counterbore, tube land 15 (build_revI_detail.py)


def f(x, n=1):
    """number format for equation strings"""
    if abs(x) >= 1e5:
        return f"{x:,.0f}"
    return f"{x:,.{n}f}"


def chk(cid, part, item, case, eq, val, unit, allow, basis, fy=None, shear=False, kind="stress", req=1.0, note=""):
    """kind: 'stress' (FoS = allow / val), 'capacity' (val is a capacity ratio already, e.g. s0; FoS = val / allow),
    'rating' (catalogue rating: FoS = allow / val, no yield FoS)"""
    if kind == "capacity":
        fos = val / allow if allow else float("inf")
    else:
        fos = allow / val if val else float("inf")
    fos_y = None
    if fy and kind == "stress" and val:
        fos_y = (0.577 * fy if shear else fy) / val
    rows.append({"id": cid, "part": part, "item": item, "case": case, "eq": eq, "value": val, "unit": unit, "allow": allow,
                 "basis": basis, "fos": fos, "fos_yield": fos_y, "req": req, "ok": True if req is None else fos >= req - 1e-9, "note": note})
    return fos


def FM(case):
    F, M = LD.axial_and_moment(case)
    return F, M


# =====================================================================================================
# 0. LOAD BASIS
# =====================================================================================================
LOADROWS = []
for c in CASES:
    F, M = FM(c)
    LOADROWS.append({"case": c, "p_bar": {"LC1": None, "LC2": LD.P_CAP_BAR, "LC3": LD.P_INTERLOCK_BAR, "LC4": round(LD.P_PUMP_RELIEF_BAR, 1)}[c],
                     "F_kN": F / 1e3, "e_mm": LD.E_JAM if c != "LC1" else LD.E_JAM / 2, "M_kNm": M / 1e6,
                     "Fs_kN": LD.side_force(c) / 1e3, "M_seat_kNm": LD.moment_at(c, CB) / 1e6, "T_kNm": LD.CASES[c]["T"] / 1e6,
                     "what": LD.CASES[c]["what"]})
P_CH = LD.chamber_force()
T_D = LD.T_DESIGN

# =====================================================================================================
# 1. SHELL WELDMENT
# =====================================================================================================
Fy_r1, Fu_r1 = MAT["A572-42"][:2]
Fy_sh, Fu_sh = MAT["shell"][:2]
D_SH, T_SH = 609.6, 12.7
R_SHM = (D_SH - T_SH) / 2
A_SH = pi / 4 * (D_SH ** 2 - (D_SH - 2 * T_SH) ** 2)
S_SH = pi * (D_SH ** 4 - (D_SH - 2 * T_SH) ** 4) / (32 * D_SH)
for c in ("LC3", "LC4"):
    F, _ = FM(c)
    M = LD.moment_at(c, CB)
    s = F / A_SH + M / S_SH
    chk("SH-1", "Shield shell", "axial compression + bending behind ring 1", c,
        f"σ = F/A + M/S = {f(F/1e3)} kN / {f(A_SH,0)} mm² + {f(M/1e6,2)} kNm / {f(S_SH/1e3,0)}e3 mm³", s, "MPa", 0.6 * Fy_sh, "0.6 Fy", Fy_sh, req=1.0)
chk("SH-2", "Shield shell", "local buckling, D/t vs AISC compact limit 0.11 E/Fy", "geometry",
    f"D/t = {D_SH}/{T_SH} = {D_SH/T_SH:.1f};  0.11 E/Fy = 0.11 × 200,000/{Fy_sh:.0f} = {0.11*E/Fy_sh:.1f}", D_SH / T_SH, "–",
    0.11 * E / Fy_sh, "compact limit", kind="stress")
p_cr = 2 * E / (1 - NU ** 2) * (T_SH / D_SH) ** 3
chk("SH-3", "Shield shell", "external pressure: long-tube buckling vs 0.10 MPa ground + slurry pressure", "geometry",
    f"p_cr = 2E/(1−ν²)·(t/D)³ = 2 × 200,000/0.91 × ({T_SH}/{D_SH})³ = {p_cr:.2f} MPa", 0.10, "MPa", p_cr, "p_cr", kind="stress")
tau_sh = T_D / (2 * pi * R_SHM ** 2 * T_SH)
chk("SH-4", "Shield shell", "torsion at 20 kNm", "torque", f"τ = T/(2π r² t) = 20e6/(2π × {R_SHM:.1f}² × {T_SH})", tau_sh, "MPa",
    0.4 * Fy_sh, "0.4 Fy", Fy_sh, shear=True)
for c in ("LC3", "LC4"):
    F, _ = FM(c)
    s = F / A_SH
    chk("SH-5", "Shield shell", "rear end bearing on the thrust ring / casing face", c, f"σ = F/A = {f(F/1e3)} kN / {f(A_SH,0)} mm²",
        s, "MPa", 0.9 * Fy_sh, "0.9 Fy", Fy_sh)

# ---- ring 1 FEA (Rev I as built: pipes face-welded, counterbore from the build) ----
CB_TAG = f"cb{int(2 * R_CB)}x{int(CB)}"


def fea_ring1(case, mode="facewelded"):
    p = FEA / f"ring1_{case}_{mode}_R245_{CB_TAG}_p76.2x63.5.json"
    return json.loads(p.read_text()) if p.exists() else None


FEA_R1 = {c: fea_ring1(c) for c in ("LC2", "LC3", "LC4")}
for c, d in FEA_R1.items():
    if not d:
        continue
    lin = {k: v for k, v in d["linearized"].items() if isinstance(v, dict)}
    lig = {k: v for k, v in lin.items() if k.startswith("ligament")}
    kmax = max(lig, key=lambda k: max(lig[k]["PmPb_vm_p0"], lig[k]["PmPb_vm_p1"]))
    pm = max(v["Pm_vm"] for v in lig.values())
    pmpb = max(lig[kmax]["PmPb_vm_p0"], lig[kmax]["PmPb_vm_p1"])
    req_ = 1.5 if c in ("LC2", "LC3") else 1.0
    chk("R1-1", "Ring 1", "FEA: 12 o'clock pipe ligament, membrane Pm (linearized)", c,
        f"Pm = mean σ along the counterbore-wall → pipe-hole line, max over depth x = 1-30; von Mises", pm, "MPa", Fy_r1 / 1.5,
        "Fy/1.5", Fy_r1, req=1.0)
    chk("R1-2", "Ring 1", f"FEA: pipe ligament, membrane + bending Pm+Pb ({kmax.replace('ligament_x', 'x = ')})", c,
        "Pm + Pb at the ligament surface (linear part of σ along the line)", pmpb, "MPa", Fy_r1, "Fy", Fy_r1, req=req_)
    pk = max(v["peak_vm_on_line"] for v in lig.values())
    req_pk = None if c == "LC4" else 1.0                               # peaks at LC4 are reported only (chapter 01, 1.8)
    chk("R1-3", "Ring 1", "FEA: peak on the ligament lines (hole edge behind the weld, local)", c, "max von Mises along the lines", pk,
        "MPa", Fy_r1, "Fy", Fy_r1, req=req_pk, note=f"zone maximum {d['vm_peak']['pipe_ligaments']:.0f} MPa sits at the root of the 0.4 mm pipe-to-hole gap "
        "behind the front weld (crack-like corner, singular in a linear model)")
    web = max((v for k, v in lin.items() if k.startswith("web_R1")), key=lambda v: max(v["PmPb_vm_p0"], v["PmPb_vm_p1"]))
    chk("R1-4", "Ring 1", f"FEA: web behind the counterbore ({110 - CB:.0f} thk), Pm+Pb", c, "linearized through the thickness at R164, 12 and 3 o'clock",
        max(web["PmPb_vm_p0"], web["PmPb_vm_p1"]), "MPa", Fy_r1, "Fy", Fy_r1, req=req_)
    chk("R1-5", "Ring 1", "FEA: tapped holes M12 (peak)", c, "max von Mises within 16 mm of the hole bottoms", d["vm_peak"]["tapped_holes"],
        "MPa", Fy_r1, "Fy", Fy_r1, req=req_pk, note="peak stress")
    chk("R1-6", "Ring 1", "FEA: rest of the ring (peak)", c, "max von Mises outside the zones above", d["vm_ring_elsewhere"], "MPa", Fy_r1, "Fy",
        Fy_r1, req=req_pk)
    chk("SH-6", "Shield shell", "FEA: shell behind the ring (x > 120), peak", c, "max von Mises in the shell", d["vm_shell_x_gt_120"], "MPa", Fy_sh,
        "Fy", Fy_sh, req=1.5 if c != "LC4" else 1.0)


# ---- ring 1 hand model: stepped annular plate (validation of the FEA) ----
def stepped_plate(P, a, b, Rs, t1, t2, n=300):
    """axisymmetric plate: line load P at b (guided, slope 0), thickness t1 for b..Rs and t2 for Rs..a, pinned at a"""
    import numpy as np
    k = P / (2 * pi)
    D1, D2 = E * t1 ** 3 / (12 * (1 - NU ** 2)), E * t2 ** 3 / (12 * (1 - NU ** 2))
    fr = lambda r_: r_ / 2 * math.log(r_) - r_ / 4
    kM = lambda r_: k * (0.5 * math.log(r_) + 0.25) + NU * k * (0.5 * math.log(r_) - 0.25)
    gM = lambda r_: ((1 + NU) / 2, (NU - 1) / r_ ** 2)
    A = np.zeros((4, 4)); B = np.zeros(4)
    A[0, :2] = (b / 2, 1 / b); B[0] = -k * fr(b)
    A[1] = (Rs / 2 / D1, 1 / Rs / D1, -Rs / 2 / D2, -1 / Rs / D2); B[1] = -k * fr(Rs) / D1 + k * fr(Rs) / D2
    g_ = gM(Rs); A[2] = (g_[0], g_[1], -g_[0], -g_[1])
    g_ = gM(a); A[3, 2:] = g_; B[3] = -kM(a)
    c = np.linalg.solve(A, B)
    out = []
    for i in range(n + 1):
        r_ = b + (a - b) * i / n
        c1, c2, t = (c[0], c[1], t1) if r_ <= Rs else (c[2], c[3], t2)
        thD = k * fr(r_) + c1 * r_ / 2 + c2 / r_
        dthD = k * (0.5 * math.log(r_) + 0.25) + c1 / 2 - c2 / r_ ** 2
        Mr, Mt = dthD + NU * thD / r_, thD / r_ + NU * dthD
        out.append((r_, 6 * Mr / t ** 2, 6 * Mt / t ** 2, t))
    return out


R_LOAD = (161.25 + R_CB) / 2
for c in ("LC3",):
    F, _ = FM(c)
    M = LD.moment_at(c, CB)
    Peq = F + P_CH + 2 * M / R_LOAD
    res = stepped_plate(Peq, 292.1, R_LOAD, R_CB, 110.0 - CB, 110.0)
    s1 = max(max(abs(a1), abs(a2)) for rr, a1, a2, tt in res)
    chk("R1-7", "Ring 1", f"hand model: stepped annular plate {110 - CB:.0f} / 110, peak line load (P + 2M/r) at the seat centroid", c,
        f"P_eq = F + P_ch + 2M/r = {f(F/1e3)} + {f(P_CH/1e3)} + 2 × {f(M/1e6,2)}e6/{R_LOAD:.0f} = {f(Peq/1e3)} kN; σ = 6M_r/t²",
        s1, "MPa", Fy_r1, "Fy", Fy_r1, req=1.5, note="upper-bound plate model; compare R1-4 (FEA web)")

# ---- ring 1 weld (14 mm fillet from the front, the only connection to the shell) ----
R_W, LEG_W = 292.1, 14.0
L_W = 2 * pi * R_W
for c in ("LC2", "LC3", "LC4"):
    F, _ = FM(c)
    M = LD.moment_at(c, 0.0)
    q_ax = (F + P_CH) / L_W + M / (pi * R_W ** 2)
    q_t = T_D / (2 * pi * R_W ** 2)
    q = math.hypot(q_ax, q_t)
    s = q / (0.707 * LEG_W)
    chk("R1-8", "Ring 1 weld", "14 mm fillet, throat (line method)", c,
        f"q = (F + P_ch)/(2πr) + M/(πr²) = {f((F+P_CH)/1e3)}e3/{f(L_W,0)} + {f(M/1e6,2)}e6/(π × {R_W}²) = {q_ax:.0f} N/mm (+ torque {q_t:.0f} N/mm); "
        f"σ = q/(0.707 × {LEG_W:.0f})", s, "MPa", W_FILLET, "0.3 × 482", MAT["E70"][0], shear=True, req=1.0)
    chk("R1-9", "Ring 1 weld", "shell base metal at the weld toe (shear on the 14 mm leg)", c, f"τ = q/leg = {q:.0f}/{LEG_W:.0f}",
        q / LEG_W, "MPa", 0.4 * Fy_sh, "0.4 Fy (shell)", Fy_sh, shear=True)

# ---- ring 1 tapped holes: thread strip vs bolt ----
Le = 24.0
A_strip = 0.5 * pi * 12 * Le
chk("R1-10", "Ring 1", "M12 tapped holes (24 engaged): thread strip at bolt proof load", "assembly",
    f"τ = F_proof/(0.5 π d L_e) = {f(A_S[12]*830/1e3)} kN / (0.5π × 12 × {Le:.0f})", A_S[12] * 830 / A_strip, "MPa", 0.6 * Fu_r1, "0.6 Fu",
    kind="stress", note="strip strength above the bolt's proof load: the bolt fails first")

# ---- slurry pipes ----
Fy_p = MAT["A1085"][0]
p_sl = 0.5
chk("PI-1", "Slurry pipes", "hoop stress at 5 bar slurry pressure", "operating", f"σ = pD/(2t) = 0.5 × 76.2/(2 × 6.35)", p_sl * 76.2 / (2 * 6.35),
    "MPa", 0.6 * Fy_p, "0.6 Fy", Fy_p)
w_p = (pi / 4 * (76.2 ** 2 - 63.5 ** 2) * 7.85e-6 + pi / 4 * 63.5 ** 2 * 1.3e-6) * G * 3        # pipe + slurry SG 1.3, 3 g
L_p = 950.0 - 110.0
S_p = pi * (76.2 ** 4 - 63.5 ** 4) / (32 * 76.2)
chk("PI-2", "Slurry pipes", "span ring 1 → saddle (840) under 3 g (pipe full of SG 1.3 slurry)", "transport",
    f"σ = wL²/(8S) = {w_p:.3f} × 840²/(8 × {S_p:.0f})", w_p * L_p ** 2 / (8 * S_p), "MPa", 0.6 * Fy_p, "0.6 Fy", Fy_p)

# ---- anti-roll fins (from calc_fins.py method) ----
R_sh, overcut, h_f, t_f, L_f = 304.8, 315.0 - 304.8, 70.0, 20.0, 990.0
ramp_f, ramp_r = h_f / math.tan(math.radians(30)), h_f / math.tan(math.radians(45))
N_ = 4000
A1 = Ar = 0.0
for i in range(N_):
    s_ = (i + 0.5) * L_f / N_
    hh = min(h_f, s_ * h_f / ramp_f, (L_f - s_) * h_f / ramp_r)
    he = max(0.0, hh - overcut)
    A1 += he * L_f / N_
    Ar += he * L_f / N_ * (R_sh + overcut + he / 2)
Rc_f = Ar / A1
for cu, Nc in ((25, 6), (50, 6)):
    q_u = Nc * cu
    T_res = q_u * 4 * A1 / 1e6 * Rc_f / 1000.0
    chk("FN-1", "Anti-roll fins", f"roll resistance in clay c_u {cu} kPa (N_c {Nc}) vs 10 kNm interlock", "soil",
        f"T = N_c c_u × A_eff × R_c = {Nc} × {cu} kPa × {4*A1/1e6:.3f} m² × {Rc_f/1000:.3f} m = {T_res:.1f} kNm", 10.0, "kNm", T_res, "T_resist",
        req=2.0 if cu == 50 else 1.0, note="geotechnical: c_u from the site report is open")
F_fin = 20e6 / (4 * Rc_f)
w_fin = F_fin / (A1 / (h_f - overcut))
arm_f = overcut + (h_f - overcut) / 2
M_root = w_fin * arm_f
chk("FN-2", "Anti-roll fins", "fin plate root bending at 20 kNm", "torque", f"F = T/(4 R_c) = {F_fin/1e3:.1f} kN per fin; m = w·a = {w_fin:.1f} × {arm_f:.1f}; σ = 6m/t²",
    6 * M_root / t_f ** 2, "MPa", 0.6 * 345, "0.6 Fy", 345)
chk("FN-3", "Anti-roll fins", "2 × 8 mm fillets at 20 kNm", "torque", "σ = m/(t·0.707·8) + w/(2·0.707·8)",
    M_root / t_f / (0.707 * 8) + w_fin / (2 * 0.707 * 8), "MPa", W_FILLET, "0.3 × 482", MAT["E70"][0], shear=True)
chk("FN-4", "Anti-roll fins", "shell wall local bending under the fin at 20 kNm", "torque", f"σ = 6m/t_shell² = 6 × {M_root:.0f}/12.7²",
    6 * M_root / 12.7 ** 2, "MPa", 0.6 * Fy_sh, "0.6 Fy (shell)", Fy_sh)

# =====================================================================================================
# 2. LIFTING (rules: lifting FoS > 5; lifting points marked with the allowable force)
# =====================================================================================================
m_mach = MP["machine"]["kg"]
lift = MP["lifting"]
kg_pt = max(lift["kg_per_front_point"], lift["kg_per_rear_point"])
ang_sling = 60.0
P_pt = kg_pt * G / math.sin(math.radians(ang_sling))                  # N, sling leg tension
WLL_HR = 2150.0                                                       # Crosby HR-125M M20 x 2.5 x 65, WLL at 5:1
chk("LF-1", "Lifting bosses", "hoist ring load per point, 4-leg sling at 60° (machine horizontal)", "lift",
    f"P = m_pt g / sin 60° = {kg_pt:.0f} kg × 9.81/0.866 = {P_pt/1e3:.2f} kN = {P_pt/G:.0f} kg-f; WLL {WLL_HR:.0f} kg (5:1)", P_pt / G, "kg",
    WLL_HR, "hoist-ring WLL", kind="rating", req=1.0, note=f"FoS on breaking load = 5 × {WLL_HR/(P_pt/G):.1f}")
P_up = m_mach * G / 2
chk("LF-2", "Lifting bosses", "upending: whole machine on the two rear points (worst share)", "lift",
    f"P = m g/2 = {m_mach:.0f} × 9.81/2 = {P_up/1e3:.2f} kN = {P_up/G:.0f} kg-f", P_up / G, "kg", WLL_HR, "hoist-ring WLL", kind="rating")
KG_MARK = 700.0                                                        # marked allowable per boss ("LIFT 700 kg")
P_mark = KG_MARK * G
chk("LF-2b", "Lifting bosses", "marked allowable per boss vs the worst lift (upending)", "lift", f"{KG_MARK:.0f} kg marked vs {P_up / G:.0f} kg",
    P_up / G, "kg", KG_MARK, "marked allowable", kind="rating")
d_m20, Le_b = 20.0, 31.9
A_th = 0.5 * pi * d_m20 * Le_b
chk("LF-3", "Lifting bosses", "M20 thread in the A572-50 boss (31.9 engaged): strip at the marked allowable", "lift",
    f"τ = P/(0.5 π d L_e) = {P_mark:.0f}/(0.5π × 20 × {Le_b})", P_mark / A_th, "MPa", 0.6 * 450, "0.6 Fu", 345, shear=True, req=5.0)
A_gw = pi * 60.0 * T_SH
chk("LF-4", "Lifting bosses", "boss to shell, full-penetration groove weld (Ø60 × 12.7), marked allowable in shear", "lift",
    f"τ = P/(π D t) = {P_mark:.0f}/(π × 60 × 12.7)", P_mark / A_gw, "MPa", 0.4 * Fy_sh, "0.4 Fy (shell)", Fy_sh, shear=True, req=5.0)
# shell local bending under a radial pad load (Roark/Young table 31 style: σ ≈ β P / t² with β ≈ 1.5 for a Ø60 pad on R298 × 12.7)
beta_ = 1.5
s_lb = beta_ * P_mark / T_SH ** 2
chk("LF-5", "Lifting bosses", "shell local bending around the boss, radial pull at the marked allowable (β ≈ 1.5)", "lift",
    f"σ ≈ β P/t² = 1.5 × {P_mark:.0f}/12.7²; FoS on ultimate = {Fu_sh:.0f}/{s_lb:.0f} = {Fu_sh / s_lb:.1f}", s_lb, "MPa", Fy_sh, "Fy (shell)", Fy_sh, req=3.0,
    note="FoS on yield ≥ 3 and on ultimate ≥ 5 for the welded lifting attachment")
# eye bolt for the bearing module (vertical lift)
m_mod = MP["groups"]["Bearing module"]["kg"]
chk("LF-6", "Fixtures", "M30 eye bolt (DIN 580) in the spindle nose: bearing module, vertical", "lift",
    f"m = {m_mod:.0f} kg; DIN 580 M30 WLL 3,200 kg (axial)", m_mod, "kg", 3200.0, "WLL", kind="rating")

# =====================================================================================================
# 3. BEARING MODULE
# =====================================================================================================
Fy_t, Fu_t = MAT["E355"][:2]
Fy_s = MAT["4140QT"][0]
Fy_50 = MAT["A572-50"][0]
R_FL = R_CB - 0.1                                                     # flange OD radius
R_BC = R_CB - 15.0
for c in ("LC3", "LC4"):
    F, _ = FM(c)
    M = LD.moment_at(c, LAND)
    A_lip = pi * (159.0 ** 2 - 148.2 ** 2)
    S_lip = pi * (159.0 ** 4 - 148.2 ** 4) / (4 * 159.0)
    chk("FL-1", "Split flange", "tube land on the flange lip: bearing P/A + M/S", c,
        f"σ = F/A + M/S, A = π(159² − 148.2²) = {A_lip:.0f}, S = {S_lip:.0f}", F / A_lip + M / S_lip, "MPa", 0.9 * Fy_50, "0.9 Fy", Fy_50)
    chk("FL-2", "Cartridge tube", f"land shear at R148 over {LAND:.0f}", c, f"τ = F/(2π × 148 × {LAND:.0f})", F / (2 * pi * 148 * LAND), "MPa", 0.4 * Fy_t, "0.4 Fy",
        Fy_t, shear=True)
    chk("FL-3", "Split flange", "lip root shear at R159.2 over 15", c, f"τ = F/(2π × 159.2 × 15)", F / (2 * pi * 159.2 * 15), "MPa", 0.4 * Fy_50,
        "0.4 Fy", Fy_50, shear=True)
    # flange 'Z' bending: load at the lip (R153.6) to the floor contact centroid; strip model, conservative (ignores hoop)
    r_c = (161.25 + R_FL - 4) / 2
    q = F / (2 * pi * r_c)
    m_ = q * (r_c - 153.6)
    chk("FL-4", "Split flange", "flange body bending, lip → seat (strip model, hoop stiffness ignored)", c,
        f"m = q·Δr = F/(2π r_c) × (r_c − 153.6) = {q:.0f} × {r_c - 153.6:.1f}; σ = 6m/{CB:.0f}²", 6 * m_ / CB ** 2, "MPa", 0.6 * Fy_50, "0.6 Fy", Fy_50)
    A_seat = pi * ((R_FL - 4) ** 2 - 161.25 ** 2) - 16 * pi / 4 * 13.5 ** 2
    chk("FL-5", "Split flange", "flange rear face on the ring 1 seat (net of 16 holes), P/A", c, f"σ = (F + P_ch)/A = {f((F+P_CH)/1e3)} kN / {A_seat:.0f} mm²",
        (F + P_CH) / A_seat, "MPa", 0.9 * Fy_r1, "0.9 Fy (ring 1)", Fy_r1)
    A_s_ = pi * (R_CB ** 2 - 161.25 ** 2)                         # seat annulus
    S_s_ = pi * (R_CB ** 4 - 161.25 ** 4) / (4 * R_CB)
    need = M * A_s_ / S_s_ - F
    cap = 16 * PRELOAD(12)
    chk("FL-6", "Flange screws", "16 × M12 10.9: clamp needed to keep the seat closed vs preload (70 % proof)", c,
        f"N = M·A/S − F = {f(M/1e6,2)}e6 × {A_s_:.0f}/{S_s_:.0f} − {f(F/1e3)}e3 = {need/1e3:.0f} kN; clamp 16 × {PRELOAD(12)/1e3:.1f} kN",
        max(need, 1.0) / 1e3, "kN", cap / 1e3, "16 × preload", kind="stress", req=1.5,
        note="negative N: thrust alone keeps the seat closed" if need < 0 else "")
T_fr = 16 * PRELOAD(12) * R_BC
for mu in (0.30, 0.15):
    chk("FL-7", "Flange screws", f"torque by clamp friction, μ {mu:.2f}", "torque", f"T = n F_p μ r = 16 × {PRELOAD(12)/1e3:.1f} kN × {mu} × {R_BC:.0f}",
        T_D / 1e6, "kNm", T_fr * mu / 1e6, "friction capacity", kind="rating")
tau_dw = T_D / (2 * R_BC) / (pi / 4 * 16 ** 2)
chk("FL-8", "Flange dowels", "2 × Ø16 hardened dowels alone carry 20 kNm (after slip)", "torque", f"τ = T/(2r)/A = 20e6/(2 × {R_BC:.0f})/201",
    tau_dw, "MPa", 400.0, "0.4 × ~1,000 (hardened)", kind="stress")
Fp = T_D / (4 * 159.0)
D_PIN = 12.0
chk("FL-9", "Anti-rotation pins", f"4 × Ø{D_PIN:.0f} radial pins (hardened), tube → flange, shear", "torque",
    f"τ = T/(4 r)/A = 20e6/(4 × 159)/{pi / 4 * D_PIN ** 2:.0f}", Fp / (pi / 4 * D_PIN ** 2), "MPa", 400.0, "0.4 × ~1,000 (hardened)")
chk("FL-10", "Anti-rotation pins", "pin bearing on the tube land (13 engaged)", "torque", f"σ = F/(d L) = {Fp:.0f}/({D_PIN:.0f} × 13)", Fp / (D_PIN * 13), "MPa",
    0.9 * Fy_t, "0.9 Fy (tube)", Fy_t)

# ---- cartridge tube ----
for c in ("LC3", "LC4"):
    F, _ = FM(c)
    M = LD.moment_at(c, (LAND + CB) / 2)
    A_g = pi * (148.0 ** 2 - 125.0 ** 2)
    S_g = pi * (148.0 ** 4 - 125.0 ** 4) / (4 * 148.0)
    chk("CT-1", "Cartridge tube", "groove root Ø296 × Ø250: tension + bending", c, f"σ = F/A + M/S = {f(F/1e3)}e3/{A_g:.0f} + {f(M/1e6,2)}e6/{S_g:.0f}",
        F / A_g + M / S_g, "MPa", 0.6 * Fy_t, "0.6 Fy", Fy_t)
    M2 = LD.moment_at(c, 114.0)
    A_t = pi / 4 * (318 ** 2 - 250 ** 2)
    S_t = pi * (318 ** 4 - 250 ** 4) / (32 * 318)
    chk("CT-2", "Cartridge tube", "body Ø318 × Ø250 at the front seat: tension + bending", c, f"σ = F/A + M/S = {f(F/1e3)}e3/{A_t:.0f} + {f(M2/1e6,2)}e6/{S_t:.0f}",
        F / A_t + M2 / S_t, "MPa", 0.6 * Fy_t, "0.6 Fy", Fy_t)
    chk("CT-3", "Cartridge tube", "29328N housing washer on the as-rolled shoulder (Ø204-240)", c, f"σ = F/[π(120² − 102²)]",
        F / (pi * (120 ** 2 - 102 ** 2)), "MPa", 0.9 * Fy_t, "0.9 Fy", Fy_t)
    chk("CT-4", "Cartridge tube", "shoulder root shear, Ø241 × 30", c, "τ = F/(π × 241 × 30)", F / (pi * 241 * 30), "MPa", 0.4 * Fy_t, "0.4 Fy",
        Fy_t, shear=True)
J_t = pi / 32 * (318 ** 4 - 250 ** 4)
chk("CT-5", "Cartridge tube", "torsion at 20 kNm (drive reaction to ring 1)", "torque", f"τ = T r/J = 20e6 × 159/{J_t:.3g}", T_D * 159 / J_t, "MPa",
    0.4 * Fy_t, "0.4 Fy", Fy_t, shear=True)

# ---- spindle ----
L_BRG = 400.0
X_FB, X_RB = 114.0, 514.0
I140 = pi / 64 * 140 ** 4
for c in ("LC1", "LC3", "LC4"):
    F, M0 = FM(c)
    Fs = LD.side_force(c)
    T = LD.CASES[c]["T"]
    Mfb = LD.moment_at(c, X_FB)
    sb = 32 * Mfb / (pi * 140 ** 3)
    tau = 16 * T / (pi * 140 ** 3)
    vm = math.sqrt(sb ** 2 + 3 * tau ** 2)
    chk("SP-1", "Spindle", "Ø140 at the front 23228: bending + torsion (von Mises)", c,
        f"σ = 32M/(πd³) = {sb:.0f}, τ = 16T/(πd³) = {tau:.1f} with M = {Mfb/1e6:.2f} kNm, T = {T/1e6:.0f} kNm; σ_vm = √(σ² + 3τ²)", vm, "MPa",
        0.6 * Fy_s, "0.6 Fy", Fy_s, req=1.0)
    Kt = 1.6
    chk("SP-2", "Spindle", "collar fillet (Ø165 → Ø140, r 2), Kt 1.6", c, f"σ_peak = Kt σ_vm = 1.6 × {vm:.0f}", Kt * vm, "MPa", Fy_s, "Fy", Fy_s,
        req=1.0, note="peak stress at a fillet: local; static strength of a ductile shaft is set by SP-1, Kt enters fatigue (SP-4)")
tau_d = 16 * T_D / (pi * 130 ** 3)
chk("SP-3", "Spindle", "Ø130 drive end (B-LOC 130 zone), torsion at 20 kNm", "torque", f"τ = 16T/(πd³) = 16 × 20e6/(π × 130³)", tau_d, "MPa",
    0.4 * Fy_s, "0.4 Fy", Fy_s, shear=True)
# fatigue (rotating bending, fully reversed each revolution), LC1 normal boring
F1, _ = FM("LC1")
M1 = LD.moment_at("LC1", X_FB)
sa = 32 * M1 / (pi * 140 ** 3) * 1.6
Se = 0.5 * 860 * 0.80 * 0.75 * 0.81                       # Marin: surface (machined), size (Ø140), reliability 99 %
chk("SP-4", "Spindle", "fatigue at the collar fillet, LC1 rotating bending (≈ 3,600 rev per drive, design for infinite life)", "LC1",
    f"σ_a = Kt 32M/(πd³) = 1.6 × 32 × {M1/1e6:.2f}e6/(π × 140³); S_e = 0.5 Fu k_a k_b k_c = 0.5 × 860 × 0.80 × 0.75 × 0.81 = {Se:.0f}", sa, "MPa", Se,
    "S_e (endurance)", kind="stress", req=1.5)
# head moment into the shaft (Rev H couple model): LA zone ↔ journal sleeve rear bore fit, lever 139
lever = 139.0
p_hub140, D_LA140 = 165.0, 190.0
for c in ("LC3", "LC4"):
    M = LD.moment_at(c, -108.0)
    Fc = M / lever
    chk("SP-5", "Spindle", "head moment into the shaft: edge bearing of the couple on 140 × 40", c, f"F_c = M/{lever:.0f} = {Fc/1e3:.0f} kN; σ = F_c/(140 × 40)",
        Fc / (140 * 40), "MPa", 0.9 * Fy_s, "0.9 Fy", Fy_s)
    chk("SP-6", "Spindle", "couple pressure under the head LA vs its grip pressure on the shaft (no lift-off)", c,
        f"p = F_c/(140 × 50) vs p_shaft = p_hub × 190/140 = {p_hub140 * D_LA140 / 140:.0f}", Fc / (140 * 50), "MPa", p_hub140 * D_LA140 / 140,
        "LA shaft pressure", kind="stress")

# ---- bearings ----
C0_23, C_23, C0_29, C_29 = 1250e3, 915e3, 2850e3, 980e3
for c in ("LC1", "LC2", "LC3", "LC4"):
    F, M = FM(c)
    Fs = LD.side_force(c)
    a_ = X_FB - LD.X_FACE
    Rm = M / L_BRG
    Rs = Fs * (L_BRG + a_) / L_BRG
    Fr = math.hypot(Rm, Rs)
    s0 = C0_23 / Fr
    if c != "LC1":
        chk("BR-1", "Front 23228", "static safety s0 = C0/P0 (P0 = Fr; thrust taken by the 29328N)", c,
            f"Fr = √[(M/L)² + (F_s(L + a)/L)²] = √[{Rm/1e3:.0f}² + {Rs/1e3:.0f}²] = {Fr/1e3:.0f} kN; s0 = {C0_23/1e3:.0f}/{Fr/1e3:.0f}", s0, "–", 2.0,
            "s0 ≥ 2 (shock)", kind="capacity", req=1.0)
        s0t = C0_29 / F
        chk("BR-2", "29328N", "static safety s0 = C0/Fa", c, f"s0 = {C0_29/1e3:.0f}/{F/1e3:.0f}", s0t, "–", 2.0, "s0 ≥ 2 (shock)", kind="capacity",
            req=1.0 if c != "LC4" else 0.75)
    else:
        L10 = (C_29 / F) ** (10 / 3)
        chk("BR-3", "29328N", "basic rating life at LC1 (normal boring), millions of revolutions", c,
            f"L10 = (C/P)^(10/3) = ({C_29/1e3:.0f}/{F/1e3:.0f})^(10/3)", L10, "Mrev", 0.0036, "3,600 rev per 5 m drive", kind="capacity")
        L10r = (C_23 / Fr) ** (10 / 3)
        chk("BR-4", "Front 23228", "basic rating life at LC1, millions of revolutions", c, f"L10 = ({C_23/1e3:.0f}/{Fr/1e3:.1f})^(10/3)", L10r, "Mrev",
            0.0036, "3,600 rev per 5 m drive", kind="capacity")
th = LD.moment_at("LC3", X_FB) * L_BRG / (6 * E * I140)
chk("BR-5", "23228 pair", "spindle slope at the rear bearing at LC3 vs spherical-bearing misalignment (≥ 1.5°)", "LC3",
    f"θ = M L/(6 E I) = {LD.moment_at('LC3', X_FB)/1e6:.1f}e6 × 400/(6 × 200,000 × {I140:.3g})", math.degrees(th), "°", 1.5, "SKF 23228 permissible",
    kind="stress")
for c in ("LC3", "LC4"):
    F, _ = FM(c)
    A_col = pi * (82.5 ** 2 - 73.0 ** 2)
    chk("BR-6", "Spindle collar", "front 23228 inner ring on the Ø165 collar (thrust path), contact R73-82.5", c, f"σ = F/[π(82.5² − 73²)]",
        F / A_col, "MPa", 0.9 * Fy_s, "0.9 Fy", Fy_s)
    A_bk = pi * (95.0 ** 2 - 72.0 ** 2)
    chk("BR-7", "Backing ring", "backing ring on the 29328N shaft washer (to Ø190)", c, f"σ = F/[π(95² − 72²)]", F / A_bk, "MPa", 0.9 * Fy_s,
        "0.9 Fy (4140)", Fy_s)

# =====================================================================================================
# 4. CUTTERHEAD
# =====================================================================================================
T_LA140 = 28.161e6
chk("CH-1", "Head locking assembly", "B-LOC B400 140 × 190: 20 kNm vs rating", "torque", "rating 28.16 kNm (catalogue)", T_D / 1e6, "kNm",
    T_LA140 / 1e6, "catalogue Mt", kind="rating")
DN = D_LA140 * math.sqrt((Fy_50 + p_hub140) / (Fy_50 - p_hub140))
chk("CH-2", "Head hub ring", "hub ring OD for the LA hub pressure (Fenner, C = 1)", "geometry",
    f"D_N = D √[(Fy + p C)/(Fy − p C)] = 190 √[(345 + 165)/(345 − 165)] = {DN:.0f}; fitted 340", DN, "mm", 340.0, "fitted OD", kind="stress")
n_arm, Rc_arm = 8, 238.0
A1_, y1_, I1_ = 76 * 50.8, 25.4, 76 * 50.8 ** 3 / 12
A2_, y2_, I2_ = 25 * 125, 50.8 + 62.5, 25 * 125 ** 3 / 12
yn = (A1_ * y1_ + A2_ * y2_) / (A1_ + A2_)
I_tb = I1_ + A1_ * (yn - y1_) ** 2 + I2_ + A2_ * (y2_ - yn) ** 2
for c in ("LC3", "LC4"):
    F, M = FM(c)
    F_arm = F / n_arm + 2 * M / (n_arm * Rc_arm)
    Mr = F_arm * (Rc_arm - 165)
    chk("CH-3", "Cutterhead arm", "arm + gusset T-section at R165, thrust bending", c,
        f"F_arm = F/8 + 2M/(8 R_c) = {F_arm/1e3:.0f} kN; M = F_arm (238 − 165); σ = M c/I, I = {I_tb:.3g}", Mr * max(yn, 175.8 - yn) / I_tb, "MPa",
        0.6 * Fy_50, "0.6 Fy", Fy_50)
    Q = A1_ * (yn - y1_)
    qf = F_arm * Q / I_tb
    chk("CH-4", "Cutterhead arm", "gusset-to-arm fillets 2 × 12, shear flow", c, f"q = V Q/I = {F_arm:.0f} × {Q:.0f}/{I_tb:.3g}; τ = q/(2 × 0.707 × 12)",
        qf / (2 * 0.707 * 12), "MPa", W_FILLET, "0.3 × 482", MAT["E70"][0], shear=True)
F_t = T_D / 8 / 238.0
S_weak = 50.8 * 76 ** 2 / 6 + 125 * 25 ** 2 / 6
chk("CH-5", "Cutterhead arm", "arm + gusset at R165, torque bending (weak axis)", "torque", f"σ = F_t (238 − 165)/S, F_t = T/(8 × 238)",
    F_t * (238 - 165) / S_weak, "MPa", 0.6 * Fy_50, "0.6 Fy", Fy_50)
P_cap = 7 * FM("LC3")[0] / 24
chk("CH-6", "Centre cap", "30 thk cap, 7 bits on a Ø200 opening (simply supported)", "LC3", f"σ = 3(3 + ν)P/(8π t²), P = 7/24 F",
    3 * 3.3 * P_cap / (8 * pi * 30 ** 2), "MPa", 0.6 * Fy_50, "0.6 Fy", Fy_50)
# bit holder weld: one bit takes the whole jam torque (stall at the relief). Holder 30 radial × 24 tangential × 20 high;
# the cutting force F_t is tangential (along the 24 side) at 31 above the arm face. Weld group as a line (AWS):
#   A_w = 2(b + d)·a,  S_w = (b d + d²/3)·a  with d = 24 (in the force direction), b = 30 (or the part over the arm)
T_j = LD.T_MOTOR_RELIEF
for name, b_h, leg_h, R_b in (("holder at R296 (outermost non-gauge track), 14 mm fillet all round", 30.0, 14.0, 295.95),
                              ("gauge holder (16.35 of 30 over the arm end R310), 14 mm fillet", 16.35, 14.0, 308.65)):
    d_h = 24.0
    a_h = 0.707 * leg_h
    Ft = T_j / R_b
    Mh = Ft * 31.0
    Aw = 2 * (b_h + d_h) * a_h
    Sw = (b_h * d_h + d_h ** 2 / 3) * a_h
    s_h = math.hypot(Ft / Aw, Mh / Sw)
    chk("CH-7", "Bit holders", f"{name}: one bit takes the stall torque {T_j/1e6:.2f} kNm", "jam",
        f"F_t = T/R = {T_j/1e6:.2f}e6/{R_b} = {Ft/1e3:.1f} kN; M = 31 F_t; f = √[(F_t/A_w)² + (M/S_w)²], A_w = {Aw:.0f}, S_w = {Sw:.0f}", s_h, "MPa",
        W_FILLET, "0.3 × 482", MAT["E70"][0], shear=True,
        note="a bit nearer the centre sees F_t = T/R: an obstruction there is limited by what the obstruction can carry" if b_h == 30.0 else "gauge holder overhangs the arm: open item (cutterhead layout)")
for c in ("LC3", "LC4"):
    F, _ = FM(c)
    A_js = pi * (82.5 ** 2 - 73.0 ** 2)
    chk("CH-8", "Journal sleeve", "sleeve rear face on the front 23228 inner ring (head thrust by contact)", c, f"σ = F/[π(82.5² − 73²)]",
        F / A_js, "MPa", 0.9 * Fy_50, "0.9 Fy", Fy_50)

# =====================================================================================================
# 5. DRIVE
# =====================================================================================================
Fy_ad = MAT["A106B"][0]
Rm_ad, t_ad = (355.6 - 12.7) / 2, 12.7
tau_ad = T_D / (2 * pi * Rm_ad ** 2 * t_ad)
chk("DR-1", "Adapter tube", "14 in XS (A106 Gr B) torsion at 20 kNm, windows (net 76 %, Kt 3)", "torque",
    f"τ = T/(2π r² t) / 0.76 × 3 = {tau_ad:.1f}/0.76 × 3", tau_ad / 0.76 * 3, "MPa", 0.4 * Fy_ad, "0.4 Fy", Fy_ad, shear=True)
for mu in (0.30, 0.15):
    cap = 12 * PRELOAD(16) * mu * 140.0
    chk("DR-2", "Adapter screws", f"12 × M16 10.9 on Ø280, slip μ {mu:.2f}", "torque", f"T = 12 × {PRELOAD(16)/1e3:.1f} kN × {mu} × 140", T_D / 1e6, "kNm",
        cap / 1e6, "friction capacity", kind="rating")
cap_dw = 3 * 0.4 * 1100 * pi / 4 * 16 ** 2 * 140.0
chk("DR-3", "Adapter dowels", "3 × Ø16 dowels alone (after slip)", "torque", "T = 3 × 0.4 × 1,100 × 201 × 140", T_D / 1e6, "kNm", cap_dw / 1e6,
    "dowel shear capacity", kind="rating")
for mu in (0.30, 0.15):
    cap = 8 * PRELOAD(20) * mu * 167.5
    chk("DR-4", "Motor screws", f"8 × M20 10.9 on Ø335, slip μ {mu:.2f} (each of the two faces of the pilot plate)", "torque",
        f"T = 8 × {PRELOAD(20)/1e3:.1f} kN × {mu} × 167.5", T_D / 1e6, "kNm", cap / 1e6, "friction capacity", kind="rating")
# coupling ROTEX 160, 64 ShD spider (KTR catalogue: TKN 24,000 Nm, TKmax 48,000 Nm; radial 0.46 mm, angular 1.1°)
St = 1.4
chk("DR-5", "Coupling ROTEX 160", f"nominal torque: motor stall at the {LD.P_MOTOR_RELIEF_BAR:.0f} bar relief × temperature factor S_t 1.4 (≤ 60 °C)", "torque",
    f"T_N S_t = {LD.T_MOTOR_RELIEF/1e6:.2f} × 1.4 = {LD.T_MOTOR_RELIEF*St/1e6:.2f} kNm vs T_KN 24.0", LD.T_MOTOR_RELIEF * St / 1e6, "kNm", 24.0, "T_KN",
    kind="rating")
chk("DR-6", "Coupling ROTEX 160", "maximum torque: 20 kNm design × S_t 1.4", "torque", f"T_max S_t = 20 × 1.4 = 28 kNm vs T_Kmax 48", 28.0, "kNm", 48.0,
    "T_Kmax", kind="rating")
x_cpl = 757.5
for c in ("LC1", "LC3"):
    Mfb = LD.moment_at(c, X_FB)
    th_ = Mfb * L_BRG / (6 * E * I140)
    off = th_ * (x_cpl - X_RB)
    chk("DR-7", "Coupling ROTEX 160", "radial offset at the coupling from spindle bending vs 0.46 mm (64 ShD)", c,
        f"δ = θ (x_c − x_rb) = M L/(6EI) × ({x_cpl} − {X_RB:.0f}) = {th_:.2e} × {x_cpl - X_RB:.1f}", off, "mm", 0.46, "KTR ΔKr", kind="stress")
T_LA130 = 23.771e6
chk("DR-8", "Drive locking assembly", "B-LOC B400 130 × 180 on the spindle end: 20 kNm vs rating", "torque", "rating 23.77 kNm (catalogue)",
    T_D / 1e6, "kNm", T_LA130 / 1e6, "catalogue Mt", kind="rating")
chk("DR-9", "Drive locking assembly", f"same, at the motor stall torque ({LD.P_MOTOR_RELIEF_BAR:.0f} bar relief)", "torque", "", LD.T_MOTOR_RELIEF / 1e6, "kNm", T_LA130 / 1e6,
    "catalogue Mt", kind="rating")
p_hub130 = 160.0
Fy_hub = MAT["42CrMo4"][0]
DN1 = 180.0 * math.sqrt((Fy_hub + p_hub130) / (Fy_hub - p_hub130))
chk("DR-10", "Coupling hub 1", "hub OD for the B400 130 × 180 hub pressure (42CrMo4+QT, C = 1)", "geometry",
    f"D_N = 180 √[(450 + 160)/(450 − 160)] = {DN1:.0f}; hub Ø290", DN1, "mm", 290.0, "hub OD", kind="stress", note="p_hub 160 MPa scaled from the 140 row: confirm")
z, m_, dm, hw, Ls, kphi = 28, 3.0, 87.0, 2.7, 72.0, 0.75
p_sp = 2 * T_D / (dm * hw * Ls * z * kphi)
chk("DR-11", "Motor spline W90 × 3 × 28", "flank pressure in the motor hub at 20 kNm", "torque",
    f"p = 2T/(d_m h L z k_φ) = 2 × 20e6/({dm} × {hw} × {Ls:.0f} × {z} × {kphi})", p_sp, "MPa", 0.9 * Fy_hub, "0.9 Fy (hub)", Fy_hub)
m_mot = 152.0
M_mot = m_mot * G * (1050.0 - 857.0) * 3
chk("DR-12", "Motor screws", "motor overhang at 3 g: M20 tension added vs preload", "transport", f"ΔF = 4M/(n D) = 4 × {M_mot/1e6:.2f}e6/(8 × 335)",
    4 * M_mot / (8 * 335) / 1e3, "kN", PRELOAD(20) / 1e3, "preload", kind="stress")
p_op = LD.P_MOTOR_OP_BAR
chk("DR-13", "Motor circuit", "pump relief vs rules 4.c.3.2 (operating + 10 % or + 20 bar, whichever is higher)", "hydraulic",
    f"p_op = T/(V_g η) = 10,000/(44.71 × 0.95) = {p_op:.1f} bar; relief = p_op + max(0.1 p_op, 20) = {LD.P_MOTOR_RELIEF_BAR:.1f} bar; "
    f"stall torque at relief {LD.T_MOTOR_RELIEF/1e6:.2f} kNm", LD.P_MOTOR_RELIEF_BAR, "bar", 400.0, "motor max pressure (MS18)", kind="stress",
    note="the relief also caps the jam torque used in LC2-LC4 side force and the coupling / LA checks")

# =====================================================================================================
# 6. THRUST RING REV B
# =====================================================================================================
Fc_seat = lambda c: FM(c)[0] / 4


TR_VAR = "reg"                       # FEA variant of Rev B: notches + register spigot (src/fea_thrust_ring.py)


def fea_tr(case, var=TR_VAR, sup="casing"):
    p = FEA / f"tring_{case}_{var}_{sup}.json"
    return json.loads(p.read_text()) if p.exists() else None


for c in ("LC2", "LC3", "LC4"):
    for sup in ("shield", "casing"):
        d = fea_tr(c, TR_VAR, sup)
        if not d:
            continue
        req_ = 1.5 if c in ("LC2", "LC3") else 1.0
        chk("TR-1", "Thrust ring", f"FEA: ring away from the saddles, notches and spigot root, on the {sup}", c, "max von Mises", d["vm_ring_away_from_block_and_pass"],
            "MPa", Fy_50, "Fy", Fy_50, req=req_)
        chk("TR-2", "Thrust ring", f"FEA: notch zone (12 and 6 o'clock), on the {sup}", c, "max von Mises", d["vm_pass_zone"], "MPa", Fy_50, "Fy", Fy_50,
            req=req_)
        if "block_lin" in d:
            bl = d["block_lin"]
            chk("TR-3", "Saddle block", f"FEA: block under the seat, Pm+Pb (linearized), on the {sup}", c, "seat floor → ring rear face",
                max(bl["PmPb_vm_p0"], bl["PmPb_vm_p1"]), "MPa", Fy_50, "Fy", Fy_50, req=req_)
        chk("TR-4", "Thrust ring", f"FEA: contact with the {sup} (fraction of the annulus in compression)", c, "compression-only foundation iteration",
            d["contact_fraction"], "–", 1.0, "full contact", kind="capacity")
        if d.get("vm_spigot_zone") is not None:
            chk("TR-12", "Thrust ring", f"FEA: register spigot and its root corner, on the {sup}", c,
                "max von Mises (sharp re-entrant corner in the mesh; the part has a 1.5 × 0.5 relief groove there)", d["vm_spigot_zone"], "MPa", Fy_50,
                "Fy", Fy_50, req=None, note="peak at a modelled sharp corner, reported only")
A_END = pi / 4 * (609.6 ** 2 - 590.6 ** 2)            # shield rear end wall / casing wall under the bearing face, R295.3-304.8
for c in ("LC3", "LC4"):
    F = FM(c)[0]
    chk("TR-13", "Shield rear end", "bearing face on the end wall Ø609.6 × Ø590.6 (counterbored for the register)", c,
        f"σ = F/A = {F/1e3:.1f} kN / {A_END:,.0f} mm²", F / A_END, "MPa", 0.9 * Fy_sh, "0.9 Fy (bearing, machined faces)", Fy_sh)
    chk("TR-14", "Shield rear end", "axial compression in the 9.5 end wall over the 12 deep counterbore", c,
        f"σ = F/A = {F/1e3:.1f} kN / {A_END:,.0f} mm²", F / A_END, "MPa", 0.6 * Fy_sh, "0.6 Fy", Fy_sh)
for c in ("LC3", "LC4"):
    Fc = Fc_seat(c)
    chk("TR-5", "Saddle block", "seat bearing on the projected area 63.5 × 101.6", c, f"σ = F_cyl/(d L) = {Fc/1e3:.1f} kN/(63.5 × 101.6)",
        Fc / (63.5 * 101.6), "MPa", 0.9 * Fy_50, "0.9 Fy", Fy_50)
    q = Fc / 101.6
    R1_, R2_ = 63.5 / 2, 65.0 / 2
    Reff = 1 / (1 / R1_ - 1 / R2_)
    Es = E / (2 * (1 - NU ** 2))
    b_ = math.sqrt(4 * q * Reff / (pi * Es))
    pmax = 2 * q / (pi * b_)
    chk("TR-6", "Saddle block", "Hertz line contact, cross tube Ø63.5 in the Ø65 seat", c,
        f"b = √(4qR/πE*) = {b_:.1f} mm, p_max = 2q/(πb), q = {q:.0f} N/mm, R = 1/(1/31.75 − 1/32.5) = {Reff:.0f}", pmax, "MPa", 1.67 * 300.0,
        "first sub-surface yield 1.67 Fy (Fy 300 cross tube)", kind="stress", req=1.5,
        note="line contact: τ_max = 0.30 p_max at depth 0.79 b; Tresca first yield at τ_max = Fy/2 → p_max = 1.67 Fy; cross-tube steel taken as Fy 300")
    s_blk = Fc / (144 * 100)
    chk("TR-7", "Saddle block", "block compression under the seat, 144 × 100", c, f"σ = F_cyl/(144 × 100)", s_blk, "MPa", 0.6 * Fy_50, "0.6 Fy", Fy_50)
# retract (50 bar) pin / ear / weld (thrust-ring.md Rev A, unchanged in Rev B)
F_rt = 47.5e3
M_pin = F_rt / 2 * (104 / 2 + 20 / 2) - F_rt / 2 * 104 / 4
s_pin = 32 * (F_rt * (104 + 20) / 8) / (pi * 38.1 ** 3)
chk("TR-8", "Saddle pins", "pin bending in retract, span 104 + 2 × 20 (simply supported, central load)", "retract",
    f"M = P L/8 with L = 124; σ = 32M/(πd³)", s_pin, "MPa", 0.6 * Fy_s, "0.6 Fy", Fy_s)
chk("TR-9", "Saddle pins", "pin double shear in retract", "retract", "τ = P/(2 × π/4 × 38.1²)", F_rt / (2 * pi / 4 * 38.1 ** 2), "MPa", 0.4 * Fy_s,
    "0.4 Fy", Fy_s, shear=True)
L_sw = 316.3
chk("TR-10", "Saddle welds", "8 mm fillet on 316 of the 488 perimeter, retract", "retract", f"σ = P/(L × 0.707 × 8) = 47.5e3/({L_sw} × 5.66)",
    F_rt / (L_sw * 0.707 * 8), "MPa", W_FILLET, "0.3 × 482", MAT["E70"][0], shear=True)
Pcr = 701e3
for c in ("LC3", "LC4"):
    Fc = Fc_seat(c)
    chk("TR-11", "Cylinders", "rod column, both ends pinned, full pin-to-pin length (Euler)", c, f"P_cr = π²EI/L² = 701 kN; P = {Fc/1e3:.0f} kN",
        Fc / 1e3, "kN", Pcr / 1e3, "P_cr", kind="rating")

# =====================================================================================================
OUT_ = {"materials": {k: {"Fy": v[0], "Fu": v[1], "spec": v[2]} for k, v in MAT.items()},
        "loads": LOADROWS, "chamber_kN": P_CH / 1e3, "rows": rows,
        "massprops": {"machine": MP["machine"], "groups": {k: {"kg": v["kg"], "cg": v["cg"]} for k, v in MP["groups"].items()},
                      "hung_off_ring1": MP["hung_off_ring1"], "lifting": MP["lifting"]}}
(CALC / "calc_revI.json").write_text(json.dumps(OUT_, indent=1, ensure_ascii=False, default=float), encoding="utf-8")

if __name__ == "__main__":
    print("Load basis")
    for r in LOADROWS:
        print(f"  {r['case']}: F {r['F_kN']:.1f} kN, e {r['e_mm']:.1f}, M {r['M_kNm']:.2f} kNm, F_s {r['Fs_kN']:.1f} kN, M_seat {r['M_seat_kNm']:.2f}, T {r['T_kNm']:.0f}")
    print(f"\n{'id':6s} {'part':24s} {'item':72s} {'case':9s} {'value':>9s} {'allow':>9s} {'FoS':>6s} {'FoS_y':>6s} req")
    low = []
    for r in rows:
        fy_ = f"{r['fos_yield']:.2f}" if r["fos_yield"] else "  –"
        flag = "" if r["ok"] else "  << below requirement"
        print(f"{r['id']:6s} {r['part'][:24]:24s} {r['item'][:72]:72s} {r['case']:9s} {r['value']:9.2f} {r['allow']:9.2f} {r['fos']:6.2f} {fy_:>6s} {r['req'] if r['req'] is not None else '–'}{flag}")
        if not r["ok"]:
            low.append(r)
    print(f"\n{len(rows)} checks, {len(low)} below requirement")
