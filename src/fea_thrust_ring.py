"""Thrust ring 3D FEA: ring + 4 saddle blocks (fused), quarter model (y >= 0, z >= 0; y = 12 o'clock, z = 3 o'clock).

Local x: x = 0 is the ring front face (bears on the shield rear end or a casing end), +x toward the cylinders.
Load: each cylinder pushes its saddle seat toward -x with F_cyl = F / 4, applied on the Ø65 seat groove as a Hertz-like
pressure p = p0 √(1 − (φ/φc)²) about the groove bottom (φc = 20°: the Ø63.5 cross tube in the Ø65 seat touches over a
narrow arc; a uniform pressure over the half groove puts a false peak at the groove edges), scaled so the
x-resultant is exactly F_cyl. Env SEAT_UNIFORM=1 restores the uniform half-groove pressure of the Oct 28 runs.
Linearization (Pm, Pm + Pb) along two lines under the 2 o'clock block: seat bottom → ring rear face (block), and ring
rear face → front face (ring under the block).
Support: compression-only Winkler foundation on the front-face contact annulus (the wall it bears on):
  shield rear (launch): R292.1-304.8, k = E / L_shield = 200e3 / 1285 = 156 N/mm³
  casing segment end:   R295.5-305.0, k = E / L_seg    = 200e3 / 500  = 400 N/mm³
  variant reg (register): both supports R295.3-304.8 (the shield rear is counterbored to the Ø590.6 casing bore)
Iterated: facets that lift off (u_x > 0) are removed until the contact set is stable.

Pass-through variants at 12 and 6 o'clock for the slurry lines (R245):
  none  : Rev A (plain Ø400 bore)
  hole  : Ø80 hole at R245
  notch : U-notch open to the bore, width 84, to R287 (Rev I)
  reg   : notch + register spigot Ø589.5 × 10 high × 9 wide ahead of the bearing face (Rev B); the 1.5 × 0.5 relief
          groove at the spigot root is not modelled (sub-mesh feature, compressive zone, outside the contact annulus)

Writes out/fea/tring_<tag>.json and .png.  Run: python src/fea_thrust_ring.py LC3 notch shield
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
T, R_IN, R_OUT = 76.2, 200.0, 304.8
R_CYL = 260.0
SD_U, SD_V, SD_H, SD_SEAT = 144.0, 100.0, 45.5, 65.0
X_CT = T + 57.5
R_PASS = 245.0
NOTCH_W, NOTCH_R = 84.0, 287.0
HOLE_D = 80.0
SUPPORT = {"shield": (292.1, 304.8, 200e3 / 1285.0), "casing": (295.5, 305.0, 200e3 / 500.0)}
SUPPORT_REG = {"shield": (295.3, 304.8, 200e3 / 1285.0), "casing": (295.3, 304.8, 200e3 / 500.0)}
SP_D, SP_H, SP_W = 589.5, 10.0, 9.0


def geometry(variant="none"):
    ring = (cq.Workplane("YZ").circle(R_OUT).circle(R_IN).extrude(T))
    if variant == "reg":
        ring = ring.union(cq.Workplane("YZ").workplane(offset=-SP_H).circle(SP_D / 2).circle(SP_D / 2 - SP_W).extrude(SP_H))
    blocks = []
    for ang in (60.0, 120.0, 240.0, 300.0):
        b = cq.Workplane("XY").box(SD_H, SD_V, SD_U).translate((T + SD_H / 2, R_CYL, 0))
        b = b.cut(cq.Workplane("XY").newObject([cq.Solid.makeCylinder(SD_SEAT / 2, SD_U + 2, V3(X_CT, R_CYL, -SD_U / 2 - 1), V3(0, 0, 1))]))
        b = b.rotate((0, 0, 0), (1, 0, 0), -ang)                       # +ang from +y toward +z
        blocks.append(b)
    body = ring
    for b in blocks:
        body = body.union(b)
    for s in (1, -1):
        if variant == "hole":
            body = body.cut(cq.Workplane("XY").newObject([cq.Solid.makeCylinder(HOLE_D / 2, T + 2, V3(-1, s * R_PASS, 0), V3(1, 0, 0))]))
        elif variant in ("notch", "reg"):
            r0 = R_IN - 5
            x0 = -1.0 if variant == "notch" else -SP_H - 1
            n = cq.Workplane("XY").box(T + 1 - x0, NOTCH_R - NOTCH_W / 2 - r0, NOTCH_W).translate(((T + 1 + x0) / 2, s * (r0 + (NOTCH_R - NOTCH_W / 2 - r0) / 2), 0))
            n = n.union(cq.Workplane("XY").newObject([cq.Solid.makeCylinder(NOTCH_W / 2, T + 1 - x0, V3(x0, s * (NOTCH_R - NOTCH_W / 2), 0), V3(1, 0, 0))]))
            body = body.cut(n)
    q = body.intersect(cq.Workplane("XY").box(400, 400, 400).translate((150, 200, 200)))
    return q.val()


def run(case="LC3", variant="notch", support="shield", h=9.0, plot=True):
    F, _ = loads.axial_and_moment(case)
    Fc = F / 4.0
    r0, r1, k = (SUPPORT_REG if variant == "reg" else SUPPORT)[support]
    tag = f"{case}_{variant}_{support}" + ("_uniformseat" if __import__("os").environ.get("SEAT_UNIFORM") == "1" else "")
    t0 = time.time()
    shape = geometry(variant)
    a = math.radians(60.0)
    seat_pts = [(X_CT - 30, R_CYL * math.cos(a) + dz * math.sin(a) * 0, R_CYL * math.sin(a)) for dz in (0,)]
    pass_pts = [(x, R_PASS, 0) for x in (0, 38, 76)] + [(x, NOTCH_R, 0) for x in (0, 38, 76)]
    m, basis = fl.mesh_shape(shape, h=h, refine=[(pass_pts, 3.0, 30.0), (seat_pts, 3.5, 50.0)])
    K = fl.stiffness(basis)
    rr = lambda y, z: np.sqrt(y ** 2 + z ** 2)
    # seat facets: on the Ø65 groove of the block at 60°: distance from the cross-tube axis ≈ 32.5
    ca, sa = math.cos(a), math.sin(a)

    def seat_pred(x, y, z):
        # cross-tube axis passes through (X_CT, R_CYL·ca, R_CYL·sa), direction = tangential (-sa, ca) in (y, z)
        dy, dz = y - R_CYL * ca, z - R_CYL * sa
        radial = dy * ca + dz * sa                                      # component along the ring radius
        d = np.sqrt((x - X_CT) ** 2 + radial ** 2)
        return (np.abs(d - SD_SEAT / 2) < 0.3) & (x < X_CT)
    seat = fl.facets_where(m, seat_pred)
    phic = math.radians(20.0)
    uniform = __import__("os").environ.get("SEAT_UNIFORM") == "1"

    def p_seat(x, y, z):
        if uniform:
            return 1.0 + 0 * x
        cphi = np.clip((X_CT - x) / (SD_SEAT / 2), -1, 1)               # 1 at the groove bottom (toward the ring)
        phi = np.arccos(cphi)
        return np.sqrt(np.clip(1 - (phi / phic) ** 2, 0, None))
    f1 = fl.pressure_load(basis, seat, p_seat)
    comp_x = np.zeros(basis.N, bool)
    for nm in ("nodal_dofs", "edge_dofs", "facet_dofs"):
        d = getattr(basis, nm, None)
        if d is not None and d.size:
            comp_x[d[0]] = True
    sc = -Fc / f1[comp_x].sum()                                        # pressure pushes toward -x
    f = sc * f1
    contact = fl.facets_where(m, lambda x, y, z: (np.abs(x) < 0.05) & (rr(y, z) > r0 - 0.01) & (rr(y, z) < r1 + 0.01))
    sym_z = fl.facets_where(m, lambda x, y, z: np.abs(z) < 0.05)
    sym_y = fl.facets_where(m, lambda x, y, z: np.abs(y) < 0.05)
    fixed = np.concatenate([fl.dofs_on(basis, sym_z, ["u^3"]), fl.dofs_on(basis, sym_y, ["u^2"])])
    active = contact.copy()
    rbm = fl.rigid_body_modes(basis)
    for it in range(8):
        Ks = fl.spring_matrix(basis, active, k, direction=0)
        u = fl.solve(K + Ks, f, fixed, rbm=rbm)
        mid = m.p[:, m.facets[:, active]].mean(axis=1)
        # facet u_x: average of its vertex displacements
        ux_nodes = u[basis.nodal_dofs[0]]
        ux_f = ux_nodes[m.facets[:, active]].mean(axis=0)
        keep = ux_f < 0.0                                                # compressed (moving toward -x into the support)
        if keep.all():
            break
        active = active[keep]
    t1 = time.time()
    xyz, s = fl.stress_at_points(basis, u)
    vm = fl.von_mises(s)
    X, Y, Z = xyz
    R = np.sqrt(Y ** 2 + Z ** 2)
    in_ring = X < T - 0.5
    near_block = np.zeros_like(in_ring)
    for ang in (60.0,):
        aa = math.radians(ang)
        tang = -Y * math.sin(aa) + Z * math.cos(aa)
        radl = Y * math.cos(aa) + Z * math.sin(aa)
        near_block = (np.abs(tang) < SD_U / 2 + 10) & (np.abs(radl - R_CYL) < SD_V / 2 + 10) & (X > T - 12)
    pass_zone = (np.abs(Z) < NOTCH_W / 2 + 25) & (Y > R_IN - 5)
    # register spigot and its root corner (a relief groove in the part; a sharp re-entrant corner in the mesh)
    spig_zone = (X < 3.0) & (R > SP_D / 2 - SP_W - 3) & (R < SP_D / 2 + 3) if variant == "reg" else np.zeros_like(in_ring)
    # contact pressure and line load
    ux_nodes = u[basis.nodal_dofs[0]]
    cn = m.facets[:, active]
    pc = -k * ux_nodes[cn].mean(axis=0)
    area_full = math.pi / 4 * (r1 ** 2 - r0 ** 2) / 1.0 / 4                 # quarter
    mid_all = m.p[:, m.facets[:, contact]].mean(axis=1)
    res = {"case": case, "variant": variant, "support": support, "F_kN": F / 1e3, "F_cyl_kN": Fc / 1e3, "k_N_per_mm3": k,
           "nodes": int(m.p.shape[1]), "dofs": int(basis.N), "solve_s": round(t1 - t0, 1), "contact_iterations": it + 1,
           "contact_fraction": float(len(active) / len(contact)),
           "contact_pressure_max_MPa": float(pc.max()),
           "vm_ring_max": float(vm[in_ring].max()),
           "vm_ring_away_from_block_and_pass": float(vm[in_ring & ~near_block & ~pass_zone & ~spig_zone].max()),
           "vm_spigot_zone": float(vm[spig_zone].max()) if variant == "reg" else None,
           "vm_pass_zone": float(vm[in_ring & pass_zone].max()) if variant != "none" else None,
           "vm_block_zone": float(vm[near_block].max()),
           "ux_min_mm": float(ux_nodes.min()), "ux_max_mm": float(ux_nodes.max())}
    ca_, sa_ = math.cos(math.radians(60.0)), math.sin(math.radians(60.0))
    pt_ = lambda x: (x, R_CYL * ca_, R_CYL * sa_)
    res["block_lin"] = fl.linearize(basis, u, pt_(X_CT - SD_SEAT / 2), pt_(T))
    res["ring_under_block_lin"] = fl.linearize(basis, u, pt_(T), pt_(0.0))
    i = np.argmax(np.where(in_ring & ~near_block & ~spig_zone, vm, -1))
    res["ring_peak_at"] = {"x": float(X.flat[i]), "r": float(R.flat[i]), "deg_from_12": float(np.degrees(np.arctan2(Z.flat[i], Y.flat[i])))}
    out = paths.ROOT / "out" / "fea"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"tring_{tag}.json").write_text(json.dumps(res, indent=1))
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(12, 5.5))
        for j, (xx, ttl) in enumerate(((1.5, "front face (x ≈ 1.5, bears on the casing)"), (T - 1.5, "rear face (x ≈ 74.7, saddles)"))):
            sel = np.abs(X - xx) < 1.5
            scp = ax[j].scatter(Z[sel], Y[sel], c=vm[sel], s=2, cmap="turbo", vmin=0, vmax=250)
            ax[j].set_aspect("equal"); ax[j].set_xlabel("z (mm), 3 o'clock →"); ax[j].set_ylabel("y (mm), 12 o'clock ↑")
            ax[j].set_title(f"Thrust ring {variant}, {case} ({F/1e3:.0f} kN), {support}\n{ttl}")
            plt.colorbar(scp, ax=ax[j], shrink=0.85, label="von Mises (MPa)")
        fig.tight_layout()
        fig.savefig(out / f"tring_{tag}.png", dpi=105)
        plt.close(fig)
    return res


if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "LC3"
    var = sys.argv[2] if len(sys.argv) > 2 else "notch"
    sup = sys.argv[3] if len(sys.argv) > 3 else "shield"
    h = float(sys.argv[4]) if len(sys.argv) > 4 else 9.0
    print(json.dumps(run(case, var, sup, h), indent=1))
