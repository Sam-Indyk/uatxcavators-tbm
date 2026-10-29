"""Rev I load basis: one place for every design load, derived from the hydraulic hardware.

Jack force  F = n_cyl · p · A_bore          (4 × Chief WT 5 × 24, bore 127.0 → A = 12,668 mm²)
Jam moment  M = F · e + M_g                 (e = 105 mm: resultant of an off-centre jam, R_head / 3; M_g = machine weight
                                              hung off ring 1 at the seat, horizontal, from calc_support.py)
Torque      T_design = 20 kNm ≥ T_motor,max = 44.71 Nm/bar × 400 bar = 17.9 kNm ≥ 2 × T_interlock

| Case | Pressure | F | Meaning |
| LC1 | thrust model | 303 kN, T 6 kNm | normal boring, factored lubricated demand at 5 m (Thrust_Model, Scenarios) |
| LC2 | 121 bar | 613 kN | jam at the thrust cap (reducing valve), the credible worst case |
| LC3 | 158 bar | 800 kN | jam at the jack-pressure interlock: reducing valve failed, interlock working (structural design case) |
| LC4 | 178 bar (2,580 psi) | 901 kN | jam at the pump relief: reducing valve and interlock both failed (hardware limit) |

Units: N, mm, N·mm, MPa.
"""
import math

pi = math.pi

# hydraulics (Thrust_Model Inputs J1-J4, Capacity tab; thrust-ring.md)
N_CYL = 4
D_BORE = 127.0                       # 5.00 in
A_BORE = pi / 4 * D_BORE ** 2        # 12,668 mm²
BAR = 0.1                            # MPa per bar
P_CAP_BAR = 121.0                    # thrust-circuit reducing valve: 613 kN
P_INTERLOCK_BAR = 158.0              # jack-pressure interlock: 800 kN
P_PUMP_RELIEF_BAR = 2580 / 14.5038   # pump relief 2,580 psi = 177.9 bar

# geometry of the load
R_HEAD = 315.0                       # cutting radius (gauge)
E_JAM = 105.0                        # = R_HEAD / 3; PDB jam screen 590 kN with 62 kNm
M_G_SEAT = 3.05e6                    # weight moment at the ring 1 seat (x = 30), module + head + drive, horizontal (massprops_revI.py)
P_CHAMBER = 0.1                      # MPa: 1.0 bar, top of the 0.2-1.0 bar chamber-pressure window
D_BULKHEAD = 584.2                   # shell ID: area the chamber pressure acts on

# torque
NM_PER_BAR = 44.71                   # Poclain MS18 2,812 cc/rev, theoretical
P_MOTOR_MAX_BAR = 400.0
T_INTERLOCK = 10e6
T_DESIGN = 20e6
T_OPERATING = 6e6
ETA_MECH = 0.95                      # motor mechanical efficiency (catalogue order of magnitude)
P_MOTOR_OP_BAR = T_INTERLOCK / 1e3 / (NM_PER_BAR * ETA_MECH)     # 235.4 bar: operating pressure at the 10 kNm interlock
P_MOTOR_RELIEF_BAR = P_MOTOR_OP_BAR + max(0.10 * P_MOTOR_OP_BAR, 20.0)   # rules 4.c.3.2: +10 % or +20 bar, whichever is higher: 259 bar

CASES = {
    "LC1": {"F": 303e3, "T": T_OPERATING, "what": "normal boring, factored lubricated demand at 5 m (Thrust_Model)"},
    "LC2": {"F": N_CYL * P_CAP_BAR * BAR * A_BORE, "T": T_DESIGN, "what": "jam at the 121 bar thrust cap"},
    "LC3": {"F": N_CYL * P_INTERLOCK_BAR * BAR * A_BORE, "T": T_DESIGN, "what": "jam at the 158 bar jack-pressure interlock (reducing valve failed)"},
    "LC4": {"F": N_CYL * P_PUMP_RELIEF_BAR * BAR * A_BORE, "T": T_DESIGN, "what": "jam at the 2,580 psi pump relief (valve and interlock failed)"},
}


def jack_force(p_bar):
    return N_CYL * p_bar * BAR * A_BORE


def axial_and_moment(case):
    """(F, M) at the spindle for a load case; LC1 uses an operating eccentricity of e/2 with no jam"""
    F = CASES[case]["F"]
    e = E_JAM if case != "LC1" else E_JAM / 2
    return F, F * e + M_G_SEAT


def chamber_force():
    return P_CHAMBER * pi / 4 * D_BULKHEAD ** 2


# Side force from an uneven torque reaction on the face (added in Rev I).
# Cutting resistance spread over only part of the face leaves a net tangential force on the head.
#   half-face contact (jam):  F_s = 3·T / (π·R)          (axial resultant then sits at 4R/3π, beyond e = R/3)
#   linear pressure p0(1 + k·r·cosθ/R), friction-like tangential traction: F_s = 2·T·e / R²   (LC1, e = E_JAM/2)
# F_s acts at the cutting face (X_FACE) at 90° to the eccentricity, so its moment adds to F·e as a vector.
X_FACE = -215.0                      # mid-height of the drag-bit cutting edges (bit tips at -225.8, holders at -203.8)


def side_force(case):
    if case == "LC1":
        return 2 * T_OPERATING * (E_JAM / 2) / R_HEAD ** 2
    return 3 * T_MOTOR_RELIEF / (pi * R_HEAD)        # torque in a jam is capped by the motor relief (255 bar)


def moment_at(case, x):
    """resultant bending moment (N·mm) at axial station x ≥ X_FACE: (F·e + M_g) and F_s·(x − X_FACE) at 90°"""
    F, M = axial_and_moment(case)
    Ms = side_force(case) * (x - X_FACE)
    return math.hypot(M, Ms)


T_MOTOR_MAX = NM_PER_BAR * P_MOTOR_MAX_BAR * 1e3          # N·mm
T_MOTOR_RELIEF = NM_PER_BAR * P_MOTOR_RELIEF_BAR * 1e3

if __name__ == "__main__":
    import paths  # noqa: F401
    print(f"A_bore = {A_BORE:.0f} mm²; pump relief = {P_PUMP_RELIEF_BAR:.1f} bar")
    for k, c in CASES.items():
        F, M = axial_and_moment(k)
        print(f"{k}: F = {F/1e3:.1f} kN, M = {M/1e6:.2f} kNm, T = {c['T']/1e6:.0f} kNm — {c['what']}")
    print(f"chamber force {chamber_force()/1e3:.1f} kN; motor torque at 400 bar {T_MOTOR_MAX/1e6:.2f} kNm, at {P_MOTOR_RELIEF_BAR:.0f} bar relief {T_MOTOR_RELIEF/1e6:.2f} kNm")
    for k in CASES:
        print(f"{k}: side force {side_force(k)/1e3:.1f} kN; resultant moment at the seat (x = 30) {moment_at(k, 30)/1e6:.2f} kNm "
              f"vs F·e + M_g {axial_and_moment(k)[1]/1e6:.2f}")
