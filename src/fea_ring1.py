"""Ring 1 (bulkhead) 3D FEA: ring 1 + front fillet weld + shield shell, half model (z >= 0, symmetric about x-y).

Geometry: ring 1 110 thk, Ø400 x 35 counterbore at the front, Ø318.5 bore, 16 x M12 tapped holes on Ø370 (tap drill
Ø10.2 x 26), 2 x Ø16 dowel holes at 12 and 6, slurry-pipe holes Ø77 at R_pipe (12 and 6), Ø12 pressure taps at R225
(3 and 9), 14 mm front fillet to the shell (ring OD 0.5 radial clear of the shell ID, so the fillet is the only
connection), shell Ø609.6 x 12.7 from x = -128 to 500.

Pipe modes: "open"  = holes empty (pipes seal-welded at the front only: Rev H)
            "welded" = pipe fused to the hole over the full ring thickness (upper bound on the support the pipe gives);
                       pipe OD x ID from env PIPE_OD, PIPE_ID (Rev I 76.2 x 63.5; the Oct 28 option runs used 76.1 x 65.0)
            "facewelded" = Rev I as built: Ø77 hole, pipe inside with a 0.4 mm radial gap, joined only by the 6 x 45° front
                       bevel weld (x = 0-6) and the 6 mm rear fillet (x = 110-116)
Counterbore radius from env R1_RCB (Rev H 200, Rev I 196); bolt circle = counterbore - 30.

Stress linearization (ASME VIII-2 Annex 5.A style) along stress classification lines (SCL) through the governing
ligament between the counterbore wall and the 12 o'clock pipe bore, and through the ring web; Pm = membrane,
Pm + Pb = membrane + bending (von Mises).

Loads: seat pressure on the counterbore floor (flange contact) p = a + b·y, scaled so the resultant is exactly
P_seat = F + 0.1 MPa x π·200² and the moment about z is exactly M (12 o'clock = +y most compressed: the jam is placed
over the pipe holes, the worst orientation); 0.1 MPa chamber pressure on the ring's exposed front face.
Supports: shell end x = 500 fixed axially, u_z = 0 on z = 0, one node fixed in y (rigid body).

Results (out/fea/ring1_<tag>.json + .png): peak von Mises by zone. The weld root is a crack-like notch (singular in a
linear model), so the weld is assessed by the line method in calc_revI.py, not by its FE peak.
Run: python src/fea_ring1.py LC3 welded 245 [h]
"""
import json
import math
import sys
import time

import numpy as np
import cadquery as cq

import paths
import fea_lib as fl
import loads

V3 = cq.Vector
SH_ID, SH_OD = 584.2, 609.6
SH_X0, SH_X1 = -128.0, 500.0          # shell modelled to x = 500 (shell bending decays within ~4·sqrt(R·t) = 250)
T_R1 = 110.0
CB = float(__import__("os").environ.get("R1_CB", 35.0))            # counterbore depth (seat plane x = CB)
R_CB = float(__import__("os").environ.get("R1_RCB", 200.0))   # counterbore radius
R_BC = R_CB - 15.0                    # bolt circle radius (Ø370 with the Ø400 counterbore)
R_BORE = 159.25
PIPE_OD = float(__import__("os").environ.get("PIPE_OD", 76.2))
PIPE_ID = float(__import__("os").environ.get("PIPE_ID", 63.5))


def _cyl_x(x0, L, R, ang, d):
    a = math.radians(ang)
    return cq.Workplane("XY").newObject([cq.Solid.makeCylinder(d / 2, L, V3(x0, R * math.cos(a), R * math.sin(a)), V3(1, 0, 0))])


def ring1_shell(r_pipe=245.0, pipe_mode="open", rear_weld=0.0):
    def revolve(pts):
        return cq.Workplane("XY").polyline(pts).close().revolve(360, (0, 0, 0), (1, 0, 0))
    r1 = revolve([(0, R_CB + 2), (0, SH_ID / 2 - 0.5), (T_R1, SH_ID / 2 - 0.5), (T_R1, R_BORE + 2), (T_R1 - 2, R_BORE),
                  (CB + 2, R_BORE), (CB, R_BORE + 2), (CB, R_CB - 3), (CB - 3, R_CB), (2, R_CB)])
    shell = revolve([(SH_X0, SH_ID / 2), (SH_X1, SH_ID / 2), (SH_X1, SH_OD / 2), (SH_X0, SH_OD / 2)])
    weld = revolve([(0, SH_ID / 2), (-14, SH_ID / 2), (0, SH_ID / 2 - 14)])
    body = shell.union(r1).union(weld)
    if rear_weld > 0:                                                  # second fillet at the ring rear face
        body = body.union(revolve([(T_R1, SH_ID / 2), (T_R1 + rear_weld, SH_ID / 2), (T_R1, SH_ID / 2 - rear_weld)]))
    for i in range(16):
        body = body.cut(_cyl_x(CB - 0.01, 26, R_BC, 11.25 + 22.5 * i, 10.2))
    for a in (0, 180):
        body = body.cut(_cyl_x(CB - 0.01, 27, R_BC, a, 16))
        if pipe_mode == "welded":
            # fused: the pipe fills the hole (welded at both faces); pipe stubs 6 ahead and 30 behind the ring
            body = body.union(_cyl_x(-6, T_R1 + 36, r_pipe, a, PIPE_OD)).cut(_cyl_x(-20, T_R1 + 60, r_pipe, a, PIPE_ID))
        elif pipe_mode == "facewelded":
            c0 = cq.Vector(0, r_pipe * math.cos(math.radians(a)), r_pipe * math.sin(math.radians(a)))
            body = body.cut(_cyl_x(-20, T_R1 + 40, r_pipe, a, 77))
            body = body.cut(cq.Workplane("XY").newObject([cq.Solid.makeCone(44.5 + 0.06, 38.5, 6.0 + 0.06, c0 - cq.Vector(0.06, 0, 0), V3(1, 0, 0))]))
            bore = _cyl_x(-20, T_R1 + 60, r_pipe, a, PIPE_ID)
            pipe = _cyl_x(0, T_R1 + 36, r_pipe, a, PIPE_OD)
            wf = cq.Workplane("XY").newObject([cq.Solid.makeCone(44.5, 38.5, 6.0, c0, V3(1, 0, 0))])
            wr = cq.Workplane("XY").newObject([cq.Solid.makeCone(PIPE_OD / 2 + 6.0, PIPE_OD / 2, 6.0, c0 + cq.Vector(T_R1, 0, 0), V3(1, 0, 0))])
            body = body.union(pipe.union(wf).union(wr).cut(bore))
        else:
            body = body.cut(_cyl_x(-20, T_R1 + 40, r_pipe, a, 77))
    for a in (90, 270):
        body = body.cut(_cyl_x(-20, T_R1 + 40, 225, a, 12))
    half = body.intersect(cq.Workplane("XY").box(2000, 1000, 500).translate((500, 0, 250)))
    return half.val()


def run(case="LC3", pipe_mode="open", r_pipe=245.0, h=14.0, plot=True, rear_weld=0.0):
    tag = f"{case}_{pipe_mode}_R{int(r_pipe)}_cb{int(2 * R_CB)}" + (f"x{int(CB)}" if CB != 35.0 else "") + (f"_rw{int(rear_weld)}" if rear_weld else "") \
        + (f"_p{PIPE_OD:g}x{PIPE_ID:g}" if pipe_mode in ("welded", "facewelded") else "")
    F, _ = loads.axial_and_moment(case)
    M = loads.moment_at(case, CB)                                      # resultant incl. the side-force moment, put in the worst plane
    P_seat = F + loads.P_CHAMBER * math.pi * R_CB ** 2
    t0 = time.time()
    shape = ring1_shell(r_pipe, pipe_mode, rear_weld)
    bolt_angs = [11.25 + 22.5 * i for i in range(16)] + [0, 180]
    hole_pts = [(CB + 13, R_BC * math.cos(math.radians(a)), R_BC * math.sin(math.radians(a))) for a in bolt_angs if math.sin(math.radians(a)) > -0.01]
    pipe_pts = [(x, r_pipe * s, 0) for x in (0, 37, 73, 110) for s in (1, -1)]
    corner_pts = [(CB, R_CB * math.cos(t), R_CB * math.sin(t)) for t in np.linspace(0, math.pi, 13)]
    m, basis = fl.mesh_shape(shape, h=h, refine=[(hole_pts, 3.5, 12.0), (pipe_pts, 3.5, 48.0), (corner_pts, 4.0, 10.0)])
    t1 = time.time()
    K = fl.stiffness(basis)
    rr = lambda y, z: np.sqrt(y ** 2 + z ** 2)
    seat = fl.facets_where(m, lambda x, y, z: (abs(x - CB) < 0.05) & (rr(y, z) > R_BORE) & (rr(y, z) < R_CB))
    front = fl.facets_where(m, lambda x, y, z: (abs(x) < 0.05) & (rr(y, z) > R_CB + 0.5) & (rr(y, z) < SH_ID / 2))
    f1 = fl.pressure_load(basis, seat, lambda x, y, z: 1.0 + 0 * x)
    f2 = fl.pressure_load(basis, seat, lambda x, y, z: y / 100.0)
    xd = basis.doflocs[1]
    comp_x = np.zeros(basis.N, bool)
    for nm in ("nodal_dofs", "edge_dofs", "facet_dofs"):
        d = getattr(basis, nm, None)
        if d is not None and d.size:
            comp_x[d[0]] = True
    Fx = lambda f: f[comp_x].sum()
    Mz = lambda f: (f[comp_x] * xd[comp_x]).sum()
    A = np.array([[Fx(f1), Fx(f2)], [Mz(f1), Mz(f2)]])
    a, b = np.linalg.solve(A, [P_seat / 2, M / 2])                    # half model carries half of F and M
    f = a * f1 + b * f2 + fl.pressure_load(basis, front, lambda x, y, z: loads.P_CHAMBER + 0 * x)
    rear = fl.facets_where(m, lambda x, y, z: abs(x - SH_X1) < 0.05)
    sym = fl.facets_where(m, lambda x, y, z: abs(z) < 0.05)
    fixed = np.concatenate([fl.dofs_on(basis, rear, ["u^1"]), fl.dofs_on(basis, sym, ["u^3"])])
    nodes = basis.doflocs[:, basis.nodal_dofs[1]]
    k = np.argmin((nodes[0] - SH_X1) ** 2 + nodes[1] ** 2 + (nodes[2] - SH_OD / 2) ** 2)
    fixed = np.unique(np.concatenate([fixed, [basis.nodal_dofs[1][k]]]))
    u = fl.solve(K, f, fixed, rbm=fl.rigid_body_modes(basis))
    t2 = time.time()
    xyz, s = fl.stress_at_points(basis, u)
    vm = fl.von_mises(s)
    X, Y, Z = xyz
    R = np.sqrt(Y ** 2 + Z ** 2)
    ring = (X > 0.0) & (X < T_R1) & (R < SH_ID / 2 - 0.5)
    zones = {}
    zones["weld_root"] = (X < 10) & (R > SH_ID / 2 - 12)                # ring 1 fillet root + pipe bevel weld edge: crack-like, singular
    zones["pipe_ligaments"] = np.zeros_like(ring)
    for sgn in (1, -1):
        zones["pipe_ligaments"] |= ((Y - sgn * r_pipe) ** 2 + Z ** 2 < 46 ** 2) & ~zones["weld_root"]
    zones["tapped_holes"] = np.zeros_like(ring)
    for (hx, hy, hz) in hole_pts:
        zones["tapped_holes"] |= ((X - hx) ** 2 + (Y - hy) ** 2 + (Z - hz) ** 2 < 16 ** 2)
    zones["tap_holes"] = (np.abs(R - 225) < 12) & (np.abs(Y) < 12)
    zones["counterbore_corner"] = (np.abs(R - R_CB) < 6) & (np.abs(X - CB) < 6) & ~zones["pipe_ligaments"]
    other = ring.copy()
    for z_ in zones.values():
        other &= ~z_
    res = {"case": case, "pipe_mode": pipe_mode, "r_pipe": r_pipe, "rear_weld": rear_weld, "F_kN": F / 1e3, "M_kNm": M / 1e6,
           "seat_pressure": {"mean_MPa": a, "gradient_MPa_per_100mm": b},
           "nodes": int(m.p.shape[1]), "tets": int(m.t.shape[1]), "dofs": int(basis.N),
           "mesh_s": round(t1 - t0, 1), "solve_s": round(t2 - t1, 1),
           "vm_peak": {k_: float(vm[ring & z_].max()) if (ring & z_).any() else None for k_, z_ in zones.items() if k_ != "weld_root"},
           "vm_weld_root_singular": float(vm[zones["weld_root"]].max()),
           "vm_ring_elsewhere": float(vm[other].max()),
           "vm_shell_x_gt_120": float(vm[(R > SH_ID / 2) & (X > 120)].max())}
    # where is the governing peak
    pl = ring & zones["pipe_ligaments"]
    i = np.argmax(np.where(pl, vm, -1))
    res["pipe_peak_location"] = {"x": float(X.flat[i]), "r": float(R.flat[i]), "theta_deg": float(np.degrees(np.arctan2(Z.flat[i], Y.flat[i])))}
    io = np.argmax(np.where(other, vm, -1))
    res["elsewhere_peak_location"] = {"x": float(X.flat[io]), "r": float(R.flat[io]), "theta_deg": float(np.degrees(np.arctan2(Z.flat[io], Y.flat[io])))}
    # linearization: radial SCLs across the 12 o'clock ligament (counterbore wall -> pipe bore) at several depths,
    # and axial SCLs through the ring web behind the counterbore (R180) and beside the pipe (R245 at 30°)
    r_in = r_pipe - (PIPE_ID / 2 if pipe_mode == "welded" else 38.5)
    if pipe_mode == "facewelded":
        r_in = r_pipe - 38.5                                           # ligament ends at the hole wall (gap behind the weld)
    scl = {}
    for xs in (1.0, 4.0, 10.0, 20.0, 30.0):
        r0 = R_CB + max(0.0, 2.0 - xs) + 0.05                         # front chamfer 2 x 45° on the counterbore edge
        scl[f"ligament_x{xs:g}"] = ((xs, r0, 0.05), (xs, r_in, 0.05))
    r_web = R_BORE + (R_BC - 8 - R_BORE) / 2                          # web between the bore and the dowel / bolt holes
    for ang in (0.0, 90.0):
        c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        scl[f"web_R{r_web:.0f}_{ang:g}deg"] = ((CB + 0.05, r_web * c, r_web * s_ + 0.05), (T_R1 - 0.05, r_web * c, r_web * s_ + 0.05))
    c, s_ = math.cos(math.radians(30)), math.sin(math.radians(30))
    scl["web_R245_30deg"] = ((0.0, 245 * c, 245 * s_), (T_R1, 245 * c, 245 * s_))
    lin = {}
    for k_, (q0, q1) in scl.items():
        try:
            lin[k_] = fl.linearize(basis, u, q0, q1)
        except Exception as e:                                         # a point outside the mesh
            lin[k_] = f"ERR {type(e).__name__}"
    res["linearized"] = lin
    seatn = np.abs(nodes[0] - CB) < 0.05
    res["seat_axial_disp_mm"] = {"max": float(u[basis.nodal_dofs[0]][seatn].max()), "min": float(u[basis.nodal_dofs[0]][seatn].min())}
    out = paths.ROOT / "out" / "fea"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"ring1_{tag}.json").write_text(json.dumps(res, indent=1))
    (out / "cache").mkdir(exist_ok=True)
    np.savez_compressed(out / "cache" / f"ring1_{tag}.npz", p=m.p, t=m.t, u=u)
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        vmax = 345.0
        fig, ax = plt.subplots(1, 2, figsize=(12.5, 5.6))
        sel = ring & (np.abs(X - 2.0) < 2.0)
        sc = ax[0].scatter(Z[sel], Y[sel], c=vm[sel], s=1.5, cmap="turbo", vmin=0, vmax=vmax)
        ax[0].set_aspect("equal"); ax[0].set_xlabel("z (mm)"); ax[0].set_ylabel("y (mm), 12 o'clock up")
        ax[0].set_title(f"Ring 1 front face (x ≈ 2), von Mises MPa\n{case}, pipes {pipe_mode}, R{r_pipe:.0f}")
        plt.colorbar(sc, ax=ax[0], shrink=0.85)
        sel2 = ring & (np.abs(X - (T_R1 - 2)) < 2.0)
        sc2 = ax[1].scatter(Z[sel2], Y[sel2], c=vm[sel2], s=1.5, cmap="turbo", vmin=0, vmax=vmax)
        ax[1].set_aspect("equal"); ax[1].set_xlabel("z (mm)")
        ax[1].set_title("Ring 1 rear face (x ≈ 108)")
        plt.colorbar(sc2, ax=ax[1], shrink=0.85)
        fig.tight_layout()
        fig.savefig(out / f"ring1_{tag}.png", dpi=105)
        plt.close(fig)
    return res


if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "LC3"
    mode = sys.argv[2] if len(sys.argv) > 2 else "open"
    rp = float(sys.argv[3]) if len(sys.argv) > 3 else 245.0
    h = float(sys.argv[4]) if len(sys.argv) > 4 else 14.0
    rw = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    print(json.dumps(run(case, mode, rp, h, rear_weld=rw), indent=1))
