"""Detailed catalogue-style parts for the rev H visual model (CadQuery). Axis +X, units mm.
Geometry is representative (bearing internals, seal profiles, fastener heads); catalogue envelopes are exact where stated.
"""
import paths  # noqa: F401  (UTF-8 stdout, output folders)
import math
import cadquery as cq

V3 = cq.Vector


def revolve(pts):
    return cq.Workplane("XY").polyline(pts).close().revolve(360, (0, 0, 0), (1, 0, 0))


def ring(x0, x1, ri, ro):
    return revolve([(x0, ri), (x1, ri), (x1, ro), (x0, ro)])


def comp(shapes):
    """one Workplane holding a compound of solids (no boolean union)"""
    solids = []
    for s in shapes:
        if isinstance(s, cq.Workplane):
            for o in s.vals():
                solids.extend(o.Solids() if hasattr(o, "Solids") else [o])
        else:
            solids.extend(s.Solids())
    return cq.Workplane("XY").newObject([cq.Compound.makeCompound(solids)])


def rotx(wp, ang):
    return wp.rotate((0, 0, 0), (1, 0, 0), ang)


def radial(ang):
    a = math.radians(ang)
    return V3(0, math.cos(a), math.sin(a))


def pt(x, r, ang):
    a = math.radians(ang)
    return V3(x, r * math.cos(a), r * math.sin(a))


def dirv(ax, ar, ang):
    a = math.radians(ang)
    return V3(ax, ar * math.cos(a), ar * math.sin(a))


def cyl(p, d, dia, length):
    return cq.Solid.makeCylinder(dia / 2, length, p, d)


def prism(pts3, vec):
    w = cq.Wire.makePolygon([V3(*p) for p in pts3], close=True)
    return cq.Solid.extrudeLinear(w, [], V3(*vec))


# ---------------- fasteners ----------------
ISO4762 = {5: (8.5, 5, 4), 6: (10, 6, 5), 8: (13, 8, 6), 10: (16, 10, 8), 12: (18, 12, 10), 14: (21, 14, 12),
           16: (24, 16, 14), 20: (30, 20, 17), 24: (36, 24, 19)}


def shcs(base, axis, d, length, head_out=True):
    """socket head cap screw; base = point on the bearing face under the head, axis = shank direction (unit)"""
    dk, k, s = ISO4762[d]
    ax = V3(*axis).normalized() if not isinstance(axis, V3) else axis.normalized()
    shank = cyl(base, ax, d, length)
    head = cyl(base - ax * k, ax, dk, k)
    # hex socket
    perp = ax.cross(V3(1, 0, 0)) if abs(ax.x) < 0.9 else ax.cross(V3(0, 1, 0))
    perp = perp.normalized()
    perp2 = ax.cross(perp).normalized()
    rr = s / math.sqrt(3)
    hexpts = [base - ax * k - ax * 0.01 + perp * (rr * math.cos(math.radians(60 * i))) + perp2 * (rr * math.sin(math.radians(60 * i)))
              for i in range(6)]
    w = cq.Wire.makePolygon(hexpts, close=True)
    sock = cq.Solid.extrudeLinear(w, [], ax * (0.6 * k))
    return shank.fuse(head).cut(sock)


def csk(base, axis, d, length):
    """countersunk screw, head flush; base = point on the top face, axis into the part"""
    ax = V3(*axis).normalized()
    dk = 2 * d
    head = cq.Solid.makeCone(dk / 2, d / 2, d * 0.55, base, ax)
    shank = cyl(base + ax * (d * 0.55), ax, d, length - d * 0.55)
    s = {6: 4, 8: 5, 10: 6, 12: 8}[d]
    perp = ax.cross(V3(1, 0, 0)) if abs(ax.x) < 0.9 else ax.cross(V3(0, 1, 0))
    perp = perp.normalized(); perp2 = ax.cross(perp).normalized()
    rr = s / math.sqrt(3)
    hexpts = [base - ax * 0.01 + perp * (rr * math.cos(math.radians(60 * i))) + perp2 * (rr * math.sin(math.radians(60 * i))) for i in range(6)]
    sock = cq.Solid.extrudeLinear(cq.Wire.makePolygon(hexpts, close=True), [], ax * (0.5 * d))
    return head.fuse(shank).cut(sock)


def axial_screws(x_face, bc, d, n, length, phase=0.0, toward=+1, kind="shcs", angles=None):
    """screws on a bolt circle; x_face = bearing face of the head; toward = +1 shank goes +x"""
    out = []
    angs = angles if angles is not None else [phase + 360.0 * i / n for i in range(n)]
    for a in angs:
        base = pt(x_face, bc / 2, a)
        if kind == "shcs":
            out.append(shcs(base, V3(toward, 0, 0), d, length))
        else:
            out.append(csk(base, V3(toward, 0, 0), d, length))
    return comp(out)


# ---------------- spherical roller bearing 23228 CC (d140 D250 B88) ----------------
def sph_roller_bearing(x0, d=140.0, D=250.0, B=88.0, Rr=97.5, e=21.0, rd=25.0, rl=28.0, n=19):
    xc = x0 + B / 2
    v = math.hypot(e, Rr)
    Rs = v + rd / 2 + 1.0
    OR = ring(x0, x0 + B, 95, D / 2).cut(cq.Workplane("XY").newObject([cq.Solid.makeSphere(Rs, V3(xc, 0, 0), V3(0, 0, 1), -90, 90, 360)]))
    OR = OR.cut(ring(xc - 6, xc + 6, D / 2 - 2.5, D / 2 + 1))                      # W33 lubrication groove
    for a in (0, 120, 240):
        OR = OR.cut(cq.Workplane("XY").newObject([cyl(pt(xc, 100, a), radial(a), 6, 30)]))
    # inner ring raceways follow the roller inner generatrix
    pts = [(x0, d / 2), (x0, 81.0)]
    rows = []
    for sign in (-1, +1):
        C = V3(xc + sign * e, Rr, 0)
        ax_ = V3(Rr / v, -sign * e / v, 0) if sign > 0 else V3(Rr / v, e / v, 0)
        # inward normal (towards the bearing axis), perpendicular to ax_ in the (x, r) plane
        nrm = V3(-ax_.y, ax_.x, 0)
        if nrm.y > 0:
            nrm = -nrm
        rows.append((C, ax_, nrm))
    (C1, a1, n1), (C2, a2, n2) = rows
    off = rd / 2 + 0.3
    P1s, P1e = C1 - a1 * (rl / 2) + n1 * off, C1 + a1 * (rl / 2) + n1 * off
    P2s, P2e = C2 - a2 * (rl / 2) + n2 * off, C2 + a2 * (rl / 2) + n2 * off
    pts += [(P1s.x - 2, 81.0), (P1s.x, P1s.y), (P1e.x, P1e.y), (P2s.x, P2s.y), (P2e.x, P2e.y), (P2e.x + 2, 81.0),
            (x0 + B, 81.0), (x0 + B, d / 2)]
    IR = revolve(pts)
    guide = ring(xc - 3.5, xc + 3.5, max(P1e.y, P2s.y) + 0.4, 96.5)
    rollers, cages = [], []
    for C, ax_, nrm in rows:
        for i in range(n):
            ang = 360.0 * i / n + (180.0 / n if C.x > xc else 0)
            base = pt(C.x - ax_.x * rl / 2, C.y - ax_.y * rl / 2, ang)
            dd = dirv(ax_.x, ax_.y, ang)
            r_ = cq.Workplane("XY").newObject([cyl(base, dd, rd, rl)]).edges().chamfer(1.6)
            rollers.append(r_.val())
        # cage side ring at the outer roller ends
        xe = C.x - ax_.x * rl / 2 * (1 if C.x < xc else -1)
        xr = (x0 + 1.5, x0 + 4.5) if C.x < xc else (x0 + B - 4.5, x0 + B - 1.5)
        cages.append(ring(xr[0], xr[1], 88.0, 100.5))
    return {"or": OR, "ir": IR, "rollers": comp(rollers), "cage": comp(cages + [guide])}


# ---------------- spherical roller thrust bearing 29328 E (d140 D240 H60) ----------------
def sph_thrust_bearing(x0, n=24):
    a = V3(24, -26, 0).normalized()            # roller axis in (x, r): rearward-inward
    nrm = V3(26, 24, 0).normalized()           # from shaft-washer raceway towards housing washer
    M = V3(x0 + 24, 95, 0)
    C = M + nrm * 9.3
    rl, d0, d1 = 26.0, 18.0, 15.0
    b0, b1 = C - a * (rl / 2), C + a * (rl / 2)
    h0, h1 = b0 + nrm * 9.4, b1 + nrm * 9.4
    SW = revolve([(x0, 70), (x0, 108), (x0 + 12, 108), (x0 + 36, 82), (x0 + 38.5, 82), (x0 + 38.5, 70)])
    HW = revolve([(x0 + 60, 89), (x0 + 60, 119.8), (h0.x - 0.6, 119.8), (h0.x, h0.y + 0.3), (h1.x + 0.4, h1.y - 0.4),
                  (x0 + 52, 92), (x0 + 52, 89)])
    rollers = []
    for i in range(n):
        ang = 360.0 * i / n
        base = pt(b0.x, b0.y, ang)
        dd = dirv(a.x, a.y, ang)
        cone = cq.Solid.makeCone(d0 / 2, d1 / 2, rl, base, dd)
        rollers.append(cq.Workplane("XY").newObject([cone]).edges().chamfer(1.2).val())
    return {"sw": SW, "hw": HW, "rollers": comp(rollers)}


# ---------------- lip seal (metal case + rubber lip + garter spring), lip facing -x ----------------
def lip_seal(xs, ri=85.1, ro=100.0, w=15.0):
    case = revolve([(xs, ro), (xs + w, ro), (xs + w, ro - 3.2), (xs + 1.6, ro - 3.2), (xs + 1.6, ri + 4.5), (xs, ri + 4.5)])
    lip = revolve([(xs + 1.6, ro - 3.4), (xs + 1.6, ri + 4.4), (xs + 2.0, ri + 0.05), (xs + 4.5, ri + 0.05), (xs + 9.0, ri + 3.2),
                   (xs + 13.5, ri + 6.5), (xs + 13.5, ro - 3.4)])
    spring = cq.Workplane("XY").newObject([cq.Solid.makeTorus(ri + 4.0, 1.3, V3(xs + 6.0, 0, 0), V3(1, 0, 0))])
    return case, lip.cut(spring), spring


def lantern(x0, x1, ri, ro, nholes=6):
    l = ring(x0, x1, ri, ro).cut(ring(x0 + 2, x1 - 2, ro - 2, ro + 1)).cut(ring(x0 + 2, x1 - 2, ri - 1, ri + 2))
    for i in range(nholes):
        a = 360.0 * i / nholes
        l = l.cut(cq.Workplane("XY").newObject([cyl(pt((x0 + x1) / 2, ri - 2, a), radial(a), 3.5, ro - ri + 4)]))
    return l


# ---------------- KM locknut + MB lock washer ----------------
def km_nut(x0, w, ri, ro, slots=4, slot_w=16.0, slot_d=7.0):
    nut = ring(x0, x0 + w, ri, ro)
    for i in range(slots):
        a = 360.0 * i / slots
        b = cq.Workplane("XY").box(w + 2, 2 * slot_d, slot_w).translate((x0 + w / 2, ro, 0))
        nut = nut.cut(rotx(b, a - 90 + 90))
    return nut


def mb_washer(x0, t, ri, ro, tab_w=10.0):
    wsh = ring(x0, x0 + t, ri, ro - 6)
    tab_in = cq.Workplane("XY").box(t, 6, tab_w).translate((x0 + t / 2, ri - 2.5, 0))
    tabs = []
    for i in range(16):
        a = 360.0 * i / 16
        tb = cq.Workplane("XY").box(t, 6, 8).translate((x0 + t / 2, ro - 3, 0))
        tabs.append(rotx(tb, a))
    out = wsh.union(tab_in)
    for tb in tabs:
        out = out.union(tb)
    return out


# ---------------- welds ----------------
def ring_fillet(x_face, r_corner, leg, toward_x, toward_r):
    """axisymmetric fillet weld at an (x, r) corner; toward_x/toward_r = +1/-1 directions of the two legs"""
    return revolve([(x_face, r_corner), (x_face + toward_x * leg, r_corner), (x_face, r_corner + toward_r * leg)])


def line_fillet(p0, p1, leg_dir_a, leg_dir_b, leg):
    """straight fillet along p0->p1 with legs along unit vectors a and b"""
    P0, P1 = V3(*p0), V3(*p1)
    A, Bv = V3(*leg_dir_a).normalized() * leg, V3(*leg_dir_b).normalized() * leg
    return prism([P0.toTuple(), (P0 + A).toTuple(), (P0 + Bv).toTuple()], (P1 - P0).toTuple())
