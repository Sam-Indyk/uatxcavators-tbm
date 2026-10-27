"""DN600 spindle mount design options (Oct 26, 2026). Axis +X rearward, X = 0 at cartridge front face. Units mm.

  S  Spherical, dry cartridge   : 23228 + 29328N + 23228; flange at the cartridge FRONT on ring 1 front face; body behind ring 1
  T  Tapered pair, dry cartridge: 2 x 32228 back-to-back (O); one-piece front block (flange + cup shoulder); body behind ring 1
  E  Rev E (reference)          : spherical set; flange in the middle, front half of the cartridge in the slurry chamber
Visualisation models; Fusion 360 is the model of record.
"""
import json, math, sys
import cadquery as cq
from paths import STEP, MESH

r = lambda d: d / 2.0
SH_OD, SH_ID = 609.6, 584.2
SH_X0, SH_X1 = -175.0, 1110.0
R_pipe = 245.0
T_R1 = 70.0
D_drive, L_drive = 400.0, 478.3


def revolve(pts):
    return cq.Workplane("XY").polyline(pts).close().revolve(360, (0, 0, 0), (1, 0, 0))


def ring(x0, x1, ri, ro):
    return revolve([(x0, ri), (x1, ri), (x1, ro), (x0, ro)])


def cyl_x(x0, length, rr, ang, dia):
    a = math.radians(ang)
    return (cq.Workplane("YZ").workplane(offset=x0)
            .center(rr * math.cos(a), rr * math.sin(a)).circle(dia / 2).extrude(length))


def cyl_r(x, ang, r0, r1, dia):
    a = math.radians(ang)
    d = cq.Vector(0, math.cos(a), math.sin(a))
    return cq.Workplane(cq.Plane(origin=(x, r0 * d.y, r0 * d.z), xDir=(1, 0, 0), normal=d.toTuple())).circle(dia / 2).extrude(r1 - r0)


def holes(s, x0, length, bc, dia, n, phase=0.0):
    for i in range(n):
        s = s.cut(cyl_x(x0, length, bc / 2, phase + 360.0 * i / n, dia))
    return s


def screws(x_face, length, bc, d, n, head_d, head_h, phase=0.0, head_rear=False):
    out = None
    for i in range(n):
        a = math.radians(phase + 360.0 * i / n)
        y, z = bc / 2 * math.cos(a), bc / 2 * math.sin(a)
        if not head_rear:
            sh = cq.Workplane("YZ").workplane(offset=x_face).center(y, z).circle(d / 2).extrude(length)
            hd = cq.Workplane("YZ").workplane(offset=x_face - head_h).center(y, z).circle(head_d / 2).extrude(head_h)
        else:
            sh = cq.Workplane("YZ").workplane(offset=x_face - length).center(y, z).circle(d / 2).extrude(length)
            hd = cq.Workplane("YZ").workplane(offset=x_face).center(y, z).circle(head_d / 2).extrude(head_h)
        b = sh.union(hd)
        out = b if out is None else out.union(b)
    return out


def dowels(x0, length, bc, angs, dia=16):
    out = None
    for a in angs:
        c = cyl_x(x0, length, bc / 2, a, dia)
        out = c if out is None else out.union(c)
    return out


# ---------------- common: shell weldment ----------------
def shell_weldment(x_r1):
    shell = ring(SH_X0, SH_X1, r(SH_ID), r(SH_OD))
    r1 = ring(x_r1, x_r1 + T_R1, 170.0, r(SH_ID) - 0.5)
    r1 = holes(r1, x_r1 - 1, 26, 370, 10.2, 16, phase=11.25)
    for a in (0, 180):
        r1 = r1.cut(cyl_x(x_r1 - 1, T_R1 + 2, R_pipe, a, 77))
    for a in (90, 270):
        r1 = r1.cut(cyl_x(x_r1 - 1, T_R1 + 2, 225, a, 12))
        r1 = r1.cut(cyl_x(x_r1 - 1, 21, 185, a, 16))                       # dowel holes (match-reamed)
    r1 = r1.cut(cyl_x(x_r1 - 1, T_R1 + 2, 178, 0, 6))
    weld = revolve([(x_r1, r(SH_ID)), (x_r1 - 14, r(SH_ID)), (x_r1, r(SH_ID) - 14)])
    pipes = None
    for a in (0, 180):
        p = cyl_x(x_r1 - 100, SH_X1 - x_r1 + 100, R_pipe, a, 76.1).cut(cyl_x(x_r1 - 101, SH_X1 - x_r1 + 102, R_pipe, a, 65))
        pipes = p if pipes is None else pipes.union(p)
    sad = None
    for sgn in (1, -1):
        b = cq.Workplane("YZ").workplane(offset=760).center(268 * sgn, 0).rect(26, 90).extrude(20)
        b = b.cut(cyl_x(759, 22, R_pipe, 0 if sgn > 0 else 180, 76.2))
        sad = b if sad is None else sad.union(b)
    taps = None
    for a in (90, 270):
        t = cyl_x(x_r1 + T_R1, 120, 225, a, 12).cut(cyl_x(x_r1 + T_R1 - 1, 122, 225, a, 8))
        taps = t if taps is None else taps.union(t)
    purge = cyl_x(x_r1 + T_R1, 120, 178, 0, 10).cut(cyl_x(x_r1 + T_R1 - 1, 122, 178, 0, 6))
    return [
        ("Shield shell (1285)", shell, "#8a8f94", 0, "Shell weldment"),
        ("Ring 1, 70 thk A572-50, pre-machined", r1, "#5f86a8", 0, "Shell weldment"),
        ("Ring 1 weld, 14 mm front fillet", weld, "#c99a3c", 0, "Shell weldment"),
        ("Slurry pipes, R245, 12 + 6", pipes, "#e0e4e8", 0, "Shell weldment"),
        ("Pipe saddles", sad, "#5f86a8", 0, "Shell weldment"),
        ("Pressure tap tubes", taps, "#e0e4e8", 0, "Shell weldment"),
        ("Seal-purge grease tube", purge, "#d9c24a", 0, "Shell weldment"),
    ], r1, pipes


# ---------------- common: front end (cover, seals, adapter) ----------------
def front_end(with_shim=True):
    wear = ring(-120, 15, 70, 85)
    end_plate = holes(ring(-200, -185, 0, 80), -201, 17, 90, 17, 4, phase=45)
    adapter = ring(-185, -150, 65, 150).union(ring(-150, -120, 65, 85))
    adapter = holes(adapter, -186, 37, 250, 21, 16)
    adapter = adapter.union(ring(-150, -136, 99, 103)).union(ring(-150, -136, 113, 117))
    cover = revolve([(-140, 85.6), (-140, 125), (-40, 125), (-40, 155), (-0.6, 155),
                     (-0.6, 124.8), (15, 124.8), (15, 115), (-0.6, 115), (-0.6, 85.6)])
    cover = cover.cut(ring(-112, -40, 85.6, 100))
    cover = cover.cut(ring(-141, -130, 97, 105)).cut(ring(-141, -130, 111, 119))
    cover = holes(cover, -41, 42, 280, 11, 12, phase=15)
    cover = cover.cut(cyl_x(-41, 42, 140, 0, 6))
    seals = ring(-112, -97, 85.1, 100).union(ring(-89, -74, 85.1, 100)).union(ring(-66, -51, 85.1, 100))
    lant = ring(-97, -89, 86, 100).union(ring(-74, -66, 86, 100))
    parts = [
        ("Wear sleeve Ø170", wear, "#d0a060", -1300, "Bearing module"),
        ("Front cover", cover, "#9c5530", -1600, "Bearing module"),
        ("Lip seals ×3", seals, "#2b2f33", -1600, "Bearing module"),
        ("Grease lantern rings ×2", lant, "#d9c24a", -1600, "Bearing module"),
        ("Cover screws", screws(-40, 55, 280, 10, 12, 16, 10, phase=15), "#3c3f44", -1600, "Bearing module"),
        ("Front adapter + labyrinth", adapter, "#aab0b6", -1950, "Bearing module"),
        ("End plate + screws", end_plate.union(screws(-200, 40, 90, 16, 4, 24, 10, phase=45)), "#7d8288", -2100, "Bearing module"),
    ]
    if with_shim:
        parts.append(("Cover shims", ring(-0.6, 0, 126, 154), "#d9c24a", -1530, "Bearing module"))
    return parts, cover, adapter


def drive_parts(x_face, dx=650):
    drv = ring(x_face + 0.5, x_face + L_drive, 0, r(D_drive))
    drv = drv.union(ring(x_face - 15, x_face + 0.5, 70, 124.8))
    drv = drv.cut(ring(x_face - 16, x_face + 92, 0, 66))
    drv = holes(drv, x_face, 45, 280, 26, 12)
    for a in (15, 135, 255):
        drv = drv.cut(cyl_x(x_face, 21, 140, a, 16))
    return [
        ("Drive envelope Ø400 (motor TBD)", drv, "#2f6f9f", dx, "Drive"),
        ("Drive screws 12 × M16", screws(x_face + 28, 53, 280, 16, 12, 24, 10, head_rear=True), "#3c3f44", dx, "Drive"),
        ("Dowels 3 × Ø16, drive to cartridge", dowels(x_face - 20, 40, 280, (15, 135, 255)), "#e0a030", dx, "Drive"),
    ], drv


def sph23(x0):
    return (ring(x0, x0 + 88, 115, 125).union(ring(x0, x0 + 88, 70, 81))
            .union(ring(x0 + 8, x0 + 80, 83, 113)))


def cart_common_holes(cart, x_fl_rear, x_rear, flange_front=0.0):
    """flange bolts, counterbores, cover holes, O-ring, purge, dowels, drive holes"""
    cart = holes(cart, flange_front - 1, x_fl_rear - flange_front + 2, 370, 13.5, 16, phase=11.25)
    for i in range(16):
        cart = cart.cut(cyl_x(flange_front - 1, 14, 185, 11.25 + 22.5 * i, 20))
    cart = holes(cart, flange_front - 1, 21, 280, 8.5, 12, phase=15)
    cart = cart.cut(ring(x_fl_rear - 3, x_fl_rear + 0.1, 194, 198))
    cart = cart.cut(cyl_x(x_fl_rear - 25, 26, 178, 0, 6))
    cart = cart.cut(cyl_r(x_fl_rear - 22, 0, 137, 201, 6))
    cart = cart.cut(cyl_x(flange_front - 1, x_fl_rear - flange_front - 21, 140, 0, 6))
    cart = cart.cut(cyl_x(x_fl_rear - 2, 2.2, 178, 0, 14).cut(cyl_x(x_fl_rear - 3, 4, 178, 0, 9)))
    for a in (90, 270):
        cart = cart.cut(cyl_x(flange_front - 1, x_fl_rear - flange_front + 2, 185, a, 16))
    cart = holes(cart, x_rear - 25, 26, 280, 14.0, 12)
    for a in (15, 135, 255):
        cart = cart.cut(cyl_x(x_rear - 21, 22, 140, a, 16))
    return cart


# ======================= option S: spherical, dry =======================
def option_S():
    x_r1 = 40.0
    parts, r1, pipes = shell_weldment(x_r1)
    x_rear = 560.0
    cart = revolve([
        (0, 125), (0, 200), (40, 200), (40, 169.95), (55, 169.95), (55, 155), (x_rear, 155), (x_rear, 125),
        (208, 125), (208, 100), (178, 100), (178, 120.5), (118, 120.5), (118, 126), (103, 126), (103, 125),
    ])
    cart = cart_common_holes(cart, 40.0, x_rear)
    for a in (90, 270):
        cart = cart.cut(cyl_x(177, 32, 104, a, 12))
    cart = cart.cut(cyl_r(470, 90, 120, 160, 8))
    cweld = revolve([(55, 155), (67, 155), (55, 167)])                 # CJP + reinforcement, flange to tube (machined after)
    hw = ring(162, 178, 90, 119.8)
    sw = ring(118, 140, 70, 112).union(revolve([(140, 82), (140, 110), (162, 118), (162, 90)]))
    shaft = revolve([(-185, 0), (-185, 65), (-120, 65), (-120, 70), (103, 70), (103, 82.5), (118, 82.5), (118, 70),
                     (528, 70), (528, 65), (652, 65), (652, 0)])
    fe, cover, adapter = front_end(True)
    dparts, drv = drive_parts(x_rear)
    parts += [
        ("Cartridge: flange + tube (CJP), machined after welding", cart, "#b8673a", -900, "Bearing module"),
        ("Flange-to-tube weld (CJP)", cweld, "#c99a3c", -900, "Bearing module"),
        ("Cartridge screws 16 × M12, recessed", screws(13, 27 + 25, 370, 12, 16, 18, 12, phase=11.25), "#3c3f44", -900, "Bearing module"),
        ("Dowels 2 × Ø16, cartridge to ring 1", dowels(5, 55, 370, (90, 270)), "#e0a030", -900, "Bearing module"),
        ("29328N housing washer", hw, "#4f8a8b", -1000, "Bearing module"),
        ("Spindle Ø140", shaft, "#c7ccd1", -1300, "Bearing module"),
        ("Front 23228", sph23(15), "#6aa368", -1300, "Bearing module"),
        ("29328N shaft washer + rollers", sw, "#4f8a8b", -1300, "Bearing module"),
        ("Spacer sleeve", ring(140, 415, 70, 82.5), "#9aa0a6", -1300, "Bearing module"),
        ("Rear 23228", sph23(415), "#6aa368", -1300, "Bearing module"),
        ("Rear KM28 nut", ring(503, 528, 70, 95), "#7d8288", -1300, "Bearing module"),
    ] + fe + dparts
    checks = dict(x_r1=x_r1, x_rear=x_rear, drive_rear=x_rear + L_drive, cart=cart, shaft=shaft, r1=r1, pipes=pipes,
                  drv=drv, cover=cover, adapter=adapter)
    return parts, checks


# ======================= option T: 32228 pair, dry =======================
def cup_A(x_back):            # cup back face (thick end) at the REAR, x_back = rear face
    return revolve([(x_back - 58, 125), (x_back, 125), (x_back, 96), (x_back - 58, 112)])


def cone_A(x_front):          # cone back face (large end, rib) at the FRONT
    return revolve([(x_front, 70), (x_front + 68, 70), (x_front + 68, 84), (x_front + 15, 98), (x_front + 7, 102), (x_front, 102)])


def roll_A(x_front):
    return revolve([(x_front + 16, 98.5), (x_front + 67, 85.3), (x_front + 67, 96.4), (x_front + 16, 110.6)])


def cup_B(x_back):            # mirrored: back face at the FRONT
    return revolve([(x_back, 125), (x_back + 58, 125), (x_back + 58, 112), (x_back, 96)])


def cone_B(x_rear):           # cone back face at the REAR
    return revolve([(x_rear - 68, 84), (x_rear - 68, 70), (x_rear, 70), (x_rear, 102), (x_rear - 7, 102), (x_rear - 15, 98)])


def roll_B(x_rear):
    x0 = x_rear - 71.75
    return revolve([(x0 + 56, 98.5), (x0 + 5, 85.3), (x0 + 5, 96.4), (x0 + 56, 110.6)])


def option_T():
    x_r1 = 40.0
    parts, r1, pipes = shell_weldment(x_r1)
    xA0 = 15.0                                   # bearing A spans 15..86.75
    xA1 = xA0 + 71.75
    xB1 = 323.0                                  # bearing B spans 251.25..323
    xB0 = xB1 - 71.75
    x_rear = 380.0
    # front block (one piece): flange 0..40 Ø400, hub 40..110 Ø340 in ring bore, cup A seat Ø250, shoulder Ø220
    block = revolve([(0, 125), (0, 200), (40, 200), (40, 169.95), (110, 169.95), (110, 110), (xA1, 110), (xA1, 125)])
    tube = revolve([(110, 155), (x_rear, 155), (x_rear, 125), (xB0, 125), (xB0, 110), (xB0 - 23, 110), (xB0 - 23, 115), (110, 115)])
    cart = block.union(tube)
    cart = cart_common_holes(cart, 40.0, x_rear)
    cart = cart.cut(cyl_r(200, 90, 110, 160, 8))
    tweld = revolve([(110, 155), (122, 155), (110, 167)])
    shaft = revolve([(-185, 0), (-185, 65), (-120, 65), (-120, 70), (83, 70), (83, 82.5), (98, 82.5), (98, 70),
                     (348, 70), (348, 65), (472, 65), (472, 0)])
    fe, cover, adapter = front_end(False)
    dparts, drv = drive_parts(x_rear)
    parts += [
        ("Cartridge: one-piece front block + tube", cart, "#b8673a", -900, "Bearing module"),
        ("Block-to-tube weld (CJP, not in thrust path)", tweld, "#c99a3c", -900, "Bearing module"),
        ("Cartridge screws 16 × M12, recessed", screws(13, 27 + 25, 370, 12, 16, 18, 12, phase=11.25), "#3c3f44", -900, "Bearing module"),
        ("Dowels 2 × Ø16, cartridge to ring 1", dowels(5, 55, 370, (90, 270)), "#e0a030", -900, "Bearing module"),
        ("32228 cup A (front)", cup_A(xA1), "#6a8fb3", -1000, "Bearing module"),
        ("32228 cup B (rear)", cup_B(xB0), "#6a8fb3", -800, "Bearing module"),
        ("Spindle Ø140", shaft, "#c7ccd1", -1300, "Bearing module"),
        ("32228 cone + rollers A", cone_A(xA0).union(roll_A(xA0)), "#3f7fbf", -1300, "Bearing module"),
        ("32228 cone + rollers B", cone_B(xB1).union(roll_B(xB1)), "#3f7fbf", -1300, "Bearing module"),
        ("Rear KM28 nut (sets end play)", ring(xB1, xB1 + 25, 70, 95), "#7d8288", -1300, "Bearing module"),
    ] + fe + dparts
    checks = dict(x_r1=x_r1, x_rear=x_rear, drive_rear=x_rear + L_drive, cart=cart, shaft=shaft, r1=r1, pipes=pipes,
                  drv=drv, cover=cover, adapter=adapter)
    return parts, checks


def vol(a, b):
    try:
        return round(a.intersect(b).val().Volume() / 1000.0, 2)
    except Exception:
        return 0.0


def export(tag, parts, checks):
    c = checks
    clash = {
        "pipes_vs_drive": vol(c["pipes"], c["drv"]), "pipes_vs_cart": vol(c["pipes"], c["cart"]),
        "shaft_vs_cart": vol(c["shaft"], c["cart"]), "cart_vs_ring1": vol(c["cart"], c["r1"]),
        "shaft_vs_ring1": vol(c["shaft"], c["r1"]), "drive_vs_shaft": vol(c["drv"], c["shaft"]),
        "cover_vs_adapter": vol(c["cover"], c["adapter"]),
    }
    info = {"ring1_depth_from_shield_front": c["x_r1"] - SH_X0, "cartridge_length": c["x_rear"],
            "drive_rear_x": c["drive_rear"], "leg_length": SH_X1 - (c["x_r1"] + T_R1)}
    print(tag, json.dumps(clash), json.dumps(info))
    out, assy = [], cq.Assembly(name=f"spindle_mount_{tag}")
    masses = {}
    for name, wp, col, dx, grp in parts:
        pos, idx = [], []
        for f in wp.val().Faces():
            vs, tris = f.tessellate(0.2, 0.3)
            base = len(pos) // 3
            for v in vs:
                pos += [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
            for t in tris:
                idx += [t[0] + base, t[1] + base, t[2] + base]
        kg = round(wp.val().Volume() * 7.85e-6, 1)
        if name.startswith("Drive envelope"):
            kg = 0.0
        if "seals" in name.lower():
            kg = round(kg * 0.2, 1)
        masses[grp] = masses.get(grp, 0) + kg
        out.append({"name": name, "color": col, "dx": dx, "group": grp, "pos": pos, "idx": idx, "kg": kg})
        safe = "".join(ch if ch.isalnum() else "_" for ch in name)
        assy.add(wp, name=safe, color=cq.Color(*[int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
    assy.export(str(STEP / f"spindle_mount_{tag}.step"))
    cart_kg = next(o["kg"] for o in out if o["name"].startswith("Cartridge:"))
    print(tag, {k: round(v, 1) for k, v in masses.items()}, "cartridge", cart_kg)
    json.dump({"parts": out, "clash": clash, "info": info, "masses": masses, "cart_kg": cart_kg},
              open(MESH / f"mesh_{tag}.json", "w"), separators=(",", ":"))


if __name__ == "__main__":
    which = sys.argv[1:] or ["S", "T"]
    if "S" in which:
        export("optS", *option_S())
    if "T" in which:
        export("optT", *option_T())
