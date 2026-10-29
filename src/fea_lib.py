"""Small linear-elastic 3D FEA helper: CadQuery solid -> gmsh tetrahedral mesh -> scikit-fem quadratic (P2) solve.

Units: mm, N, MPa. Steel E = 200 GPa, nu = 0.3.
Boundary conditions are picked with geometric predicates on facet midpoints, so a model script only describes
where loads and supports act, not mesh entity numbers.

  m, basis = mesh_shape(shape, h=10, refine=[(points, h_local, dist)])
  K = stiffness(basis)
  f = pressure_load(basis, select, pressure_fn)       # pressure_fn(x, y, z) -> MPa, positive pushes INTO the surface
  u = solve(K, f, basis, fixed_dofs)
  vm = von_mises_nodal(basis, u)

Needs: gmsh, scikit-fem, pyamg, numpy, scipy (pip install gmsh scikit-fem pyamg). On Linux gmsh also needs libGLU.
"""
import math
import os
import tempfile

import numpy as np

E_ST, NU_ST = 200e3, 0.3


def _lame(E=E_ST, nu=NU_ST):
    return E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))


def mesh_shape(shape, h=10.0, refine=(), h_min=None, verbose=False):
    """shape: cadquery Shape/Solid. refine: list of (points Nx3, h_local, radius) -> finer mesh within radius of the points.
    Returns (skfem MeshTet, Basis with ElementVector(ElementTetP2))."""
    import gmsh
    from skfem import MeshTet, Basis, ElementVector, ElementTetP2
    tmp = tempfile.mkdtemp()
    brep = os.path.join(tmp, "part.brep")
    shape.exportBrep(brep)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1 if verbose else 0)
    gmsh.model.add("part")
    gmsh.model.occ.importShapes(brep)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", h)
    gmsh.option.setNumber("Mesh.MeshSizeMin", h_min or min([h] + [r[1] for r in refine]))
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)          # HXT
    fields = []
    for pts, hl, rad in refine:
        pts = np.asarray(pts, float)
        tags = [gmsh.model.occ.addPoint(*p) for p in pts]
        gmsh.model.occ.synchronize()
        fd = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(fd, "PointsList", tags)
        ft = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(ft, "InField", fd)
        gmsh.model.mesh.field.setNumber(ft, "SizeMin", hl)
        gmsh.model.mesh.field.setNumber(ft, "SizeMax", h)
        gmsh.model.mesh.field.setNumber(ft, "DistMin", rad)
        gmsh.model.mesh.field.setNumber(ft, "DistMax", rad * 3)
        fields.append(ft)
    if fields:
        fm = gmsh.model.mesh.field.add("Min")
        gmsh.model.mesh.field.setNumbers(fm, "FieldsList", fields)
        gmsh.model.mesh.field.setAsBackgroundMesh(fm)
        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.model.mesh.generate(3)
    ntags, coords, _ = gmsh.model.mesh.getNodes()
    etypes, etags, enodes = gmsh.model.mesh.getElements(3)
    gmsh.finalize()
    coords = coords.reshape(-1, 3)
    idx = {t: i for i, t in enumerate(ntags)}
    tets = None
    for et, en in zip(etypes, enodes):
        if et == 4:                                          # 4-node tetrahedron
            tets = np.array([idx[t] for t in en]).reshape(-1, 4)
    used = np.unique(tets)
    remap = -np.ones(len(coords), int)
    remap[used] = np.arange(len(used))
    m = MeshTet(coords[used].T.copy(), remap[tets].T.copy())
    return m, Basis(m, ElementVector(ElementTetP2()))


def stiffness(basis, E=E_ST, nu=NU_ST, chunk=12000):
    """assembled in element chunks so the per-element matrices of a large P2 mesh do not exhaust memory"""
    from skfem import Basis, asm
    from skfem.models.elasticity import linear_elasticity
    lam, mu = _lame(E, nu)
    form = linear_elasticity(lam, mu)
    nel = basis.mesh.t.shape[1]
    K = None
    for i0 in range(0, nel, chunk):
        sub = Basis(basis.mesh, basis.elem, elements=np.arange(i0, min(nel, i0 + chunk)))
        Ki = asm(form, sub).tocsr()
        K = Ki if K is None else K + Ki
    return K


def facets_where(mesh, pred):
    """boundary facets whose midpoint satisfies pred(x, y, z)"""
    bf = mesh.boundary_facets()
    mid = mesh.p[:, mesh.facets[:, bf]].mean(axis=1)
    return bf[pred(*mid)]


def pressure_load(basis, facets, pfun):
    """traction = -p n on the given boundary facets (p > 0 presses into the body). pfun(x, y, z) -> MPa"""
    from skfem import FacetBasis, LinearForm
    from skfem.helpers import dot
    fb = FacetBasis(basis.mesh, basis.elem, facets=facets)

    @LinearForm
    def load(v, w):
        x, y, z = w.x
        return -pfun(x, y, z) * dot(w.n, v)
    return load.assemble(fb)


def traction_load(basis, facets, tfun):
    """traction vector tfun(x, y, z) -> (tx, ty, tz) in MPa on the given facets"""
    from skfem import FacetBasis, LinearForm
    fb = FacetBasis(basis.mesh, basis.elem, facets=facets)

    @LinearForm
    def load(v, w):
        tx, ty, tz = tfun(*w.x)
        return tx * v[0] + ty * v[1] + tz * v[2]
    return load.assemble(fb)


def spring_matrix(basis, facets, k, direction=0):
    """Winkler foundation k (N/mm per mm²) on the facets, acting on the displacement component `direction`"""
    from skfem import FacetBasis, BilinearForm
    fb = FacetBasis(basis.mesh, basis.elem, facets=facets)

    @BilinearForm
    def spr(u, v, w):
        kk = k(*w.x) if callable(k) else k
        return kk * u[direction] * v[direction]
    return spr.assemble(fb)


def dofs_on(basis, facets, comps):
    """global DOF numbers of the nodes on `facets` for displacement components comps (subset of 'u^1','u^2','u^3')"""
    d = basis.get_dofs(facets)
    out = []
    for c in comps:
        out.append(d.nodal[c])
        if c in d.facet:
            out.append(d.facet[c])
        if hasattr(d, "edge") and c in getattr(d, "edge", {}):
            out.append(d.edge[c])
    return np.unique(np.concatenate([np.asarray(o).ravel() for o in out]))


def solve(K, f, fixed, tol=1e-8, verbose=False, rbm=None):
    """CG with smoothed-aggregation AMG on the reduced system; falls back to a direct solve for small models"""
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    n = K.shape[0]
    free = np.setdiff1d(np.arange(n), fixed)
    Kf = K[free][:, free].tocsr()
    ff = f[free]
    if len(free) < 60000:
        x = spla.spsolve(Kf.tocsc(), ff)
    else:
        import pyamg
        B = None if rbm is None else rbm[free]
        ml = pyamg.smoothed_aggregation_solver(Kf, B=B, symmetry="symmetric", max_coarse=500, coarse_solver="splu")
        res = []
        x = ml.solve(ff, tol=tol, accel="cg", maxiter=2000, residuals=res)
        if verbose:
            print(f"  AMG-CG: {len(res)} iterations, relative residual {res[-1] / res[0]:.1e}")
    u = np.zeros(n)
    u[free] = x
    return u


def rigid_body_modes(basis):
    """6 rigid-body modes (3 translations, 3 rotations) at every DOF, for the AMG near-null space"""
    N = basis.N
    comp = np.zeros(N, int)
    for name in ("nodal_dofs", "edge_dofs", "facet_dofs", "interior_dofs"):
        d = getattr(basis, name, None)
        if d is not None and d.size:
            for i in range(3):
                comp[d[i]] = i
    x, y, z = basis.doflocs
    B = np.zeros((N, 6))
    for i in range(3):
        B[comp == i, i] = 1.0
    rot = {0: (np.zeros(N), -z, y), 1: (z, np.zeros(N), -x), 2: (-y, x, np.zeros(N))}
    for j, (a, b, c) in rot.items():
        B[:, 3 + j] = np.where(comp == 0, a, np.where(comp == 1, b, c))
    return B


def stress_at_points(basis, u, E=E_ST, nu=NU_ST):
    """Cauchy stress components at the quadrature points: returns (xyz [3, nel, nq], s [3, 3, nel, nq])"""
    from skfem.helpers import sym_grad
    lam, mu = _lame(E, nu)
    uh = basis.interpolate(u)
    eps = sym_grad(uh)
    tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
    s = 2 * mu * eps
    for i in range(3):
        s[i, i] = s[i, i] + lam * tr
    return basis.global_coordinates().value, s


def von_mises(s):
    return np.sqrt(0.5 * ((s[0, 0] - s[1, 1]) ** 2 + (s[1, 1] - s[2, 2]) ** 2 + (s[2, 2] - s[0, 0]) ** 2)
                   + 3 * (s[0, 1] ** 2 + s[1, 2] ** 2 + s[0, 2] ** 2))


def cyl_stress(xyz, s):
    """rotate stresses into cylindrical components about the x axis: returns dict sxx, srr, stt, sxr, sxt, srt"""
    y, z = xyz[1], xyz[2]
    th = np.arctan2(z, y)
    c, sn = np.cos(th), np.sin(th)
    srr = c * c * s[1, 1] + sn * sn * s[2, 2] + 2 * c * sn * s[1, 2]
    stt = sn * sn * s[1, 1] + c * c * s[2, 2] - 2 * c * sn * s[1, 2]
    sxr = c * s[0, 1] + sn * s[0, 2]
    sxt = -sn * s[0, 1] + c * s[0, 2]
    return {"sxx": s[0, 0], "srr": srr, "stt": stt, "sxr": sxr, "sxt": sxt}

def stress_at(basis, u, pts, E=E_ST, nu=NU_ST, delta=0.02):
    """Cauchy stress (3 x 3 x n) at arbitrary points pts (3 x n) inside the mesh: the P2 displacement is probed at
    p ± delta along each axis and differentiated (central differences, exact for a quadratic field in one element)"""
    pts = np.asarray(pts, float)
    n = pts.shape[1]
    grad = np.zeros((3, 3, n))                                   # grad[i, j] = du_i / dx_j
    for j in range(3):
        e = np.zeros((3, 1)); e[j] = delta
        up = (basis.probes(pts + e) @ u).reshape(3, n)
        um = (basis.probes(pts - e) @ u).reshape(3, n)
        grad[:, j, :] = (up - um) / (2 * delta)
    eps = 0.5 * (grad + grad.transpose(1, 0, 2))
    lam, mu = _lame(E, nu)
    tr = eps[0, 0] + eps[1, 1] + eps[2, 2]
    s = 2 * mu * eps
    for i in range(3):
        s[i, i] += lam * tr
    return s


def linearize(basis, u, p0, p1, n=41, inset=0.05):
    """Stress linearization along a stress classification line p0 -> p1 (ASME VIII-2 5.A style):
    membrane = mean of each component; bending = linear part; returned as von Mises of the membrane, of membrane +
    bending at both ends, and of the total (peak) along the line"""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = np.linalg.norm(p1 - p0)
    d = (p1 - p0) / L
    t = np.linspace(inset, L - inset, n)
    pts = (p0[:, None] + d[:, None] * t[None, :])
    s = stress_at(basis, u, pts)
    tt = (t - t[0]) / (t[-1] - t[0])
    w = np.ones(n); w[0] = w[-1] = 0.5; w /= w.sum()               # trapezoid weights
    sm = (s * w).sum(axis=2)                                       # membrane tensor
    sb = 6.0 * (s * w * (0.5 - tt)).sum(axis=2)                     # bending tensor at the p0 end (sign: + at p0)
    vm = lambda a: float(np.sqrt(0.5 * ((a[0, 0] - a[1, 1]) ** 2 + (a[1, 1] - a[2, 2]) ** 2 + (a[2, 2] - a[0, 0]) ** 2)
                                 + 3 * (a[0, 1] ** 2 + a[1, 2] ** 2 + a[0, 2] ** 2)))
    peak = max(vm(s[:, :, i]) for i in range(n))
    return {"length_mm": float(L), "Pm_vm": vm(sm), "PmPb_vm_p0": vm(sm + sb), "PmPb_vm_p1": vm(sm - sb), "peak_vm_on_line": peak}
