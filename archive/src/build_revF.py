"""DN600 spindle mount + cutterhead, rev F.
Mount: spherical dry cartridge (23228 + 29328N + 23228), flange at the cartridge front on ring 1, L = 280.
Cutterhead: Daniel's layout (Ø630, 8 arms, 24 positions, 12.7 mm tracks, 3 on gauge) with trapezoid drag bits,
carried on a pyramid frame: 8 struts + centre tube converging rearward to a hub ring bolted to the spline adapter.
Axis +X rearward, X = 0 at cartridge front face. Units mm. Visualisation model; Fusion 360 is the model of record.
"""
import json, math
import cadquery as cq
import build_opts as bo

bo.SH_X0, bo.SH_X1 = -305.0, 980.0          # shield 1285, front edge just behind the arms
r = lambda d: d / 2.0
ring, revolve, cyl_x, cyl_r, holes, screws, dowels = bo.ring, bo.revolve, bo.cyl_x, bo.cyl_r, bo.holes, bo.screws, bo.dowels

L = 280.0
c23f = 59.0
x23r = c23f + L - 44.0                       # 295
x_nut = x23r + 88.0                          # 383
x_rear = x_nut + 25.0 + 32.0                 # 440

# ---------------- head geometry ----------------
X_ARM_F, X_ARM_B = -360.8, -310.0            # arms 50.8 deep
R_ARM_IN, R_ARM_OUT, W_ARM = 90.0, 310.0, 76.0
X_HUB_F, X_HUB_B = -225.0, -185.0            # hub ring, bolts to adapter flange front face (-185)
R_NODE_HUB, R_NODE_ARM = 175.0, 245.0
STRUT = 60.0
ARM_ANGS = [i * 45.0 for i in range(8)]
GAUGE_ARMS = (0, 3, 5)


def rotx(wp, ang):
    return wp.rotate((0, 0, 0), (1, 0, 0), ang)


def arm(ang):
    a = (cq.Workplane("YZ").workplane(offset=X_ARM_F).center((R_ARM_IN + R_ARM_OUT) / 2, 0)
         .rect(R_ARM_OUT - R_ARM_IN, W_ARM).extrude(X_ARM_B - X_ARM_F))
    return rotx(a, ang)


def strut(ang):
    a = math.radians(ang)
    p0 = cq.Vector(X_HUB_F + 5, R_NODE_HUB * math.cos(a), R_NODE_HUB * math.sin(a))
    p1 = cq.Vector(X_ARM_B - 5, R_NODE_ARM * math.cos(a), R_NODE_ARM * math.sin(a))
    d = p1 - p0
    t = cq.Vector(0, -math.sin(a), math.cos(a))
    pl = cq.Plane(origin=p0.toTuple(), xDir=t.toTuple(), normal=d.normalized().toTuple())
    return cq.Workplane(pl).rect(STRUT, STRUT).extrude(d.Length)


def bit(c, ang, gauge=False):
    """holder block + trapezoid carbide drag bit at track radius c on the arm at angle ang (leading side +Z before rotation)"""
    z0 = W_ARM / 2 - 12.0
    holder = (cq.Workplane("YZ").workplane(offset=X_ARM_F - 20).center(c, z0).rect(30, 24).extrude(20))
    trap = (cq.Workplane("XY").workplane(offset=z0 - 7)
            .polyline([(X_ARM_F - 20, c - 11), (X_ARM_F - 20, c + 11), (X_ARM_F - 42, c + 6.35), (X_ARM_F - 42, c - 6.35)])
            .close().extrude(14))
    return rotx(holder, ang), rotx(trap, ang)


# track layout: gauge track (3 bits) + 21 single tracks at 12.7 mm, fully staggered
tracks = []
c_g = 315.0 - 6.35
for k, arm_i in enumerate(GAUGE_ARMS):
    tracks.append((c_g, arm_i, True))
for k in range(1, 22):
    c = c_g - 12.7 * k
    arm_i = (k * 3 + 1) % 8
    tracks.append((c, arm_i, False))

arms = None
for a in ARM_ANGS:
    arms = arm(a) if arms is None else arms.union(arm(a))
hub_disc = ring(X_ARM_F, X_ARM_B, 0, 100)
centre_cone = revolve([(X_ARM_F, 0), (X_ARM_F, 40), (X_ARM_F - 34, 0)])
centre_tube = ring(X_ARM_B, X_HUB_F, 85, 100)
hub = ring(X_HUB_F, X_HUB_B, 85, 210)
hub = holes(hub, X_HUB_F - 1, 42, 250, 21, 16, phase=11.25)
struts = None
for a in ARM_ANGS:
    struts = strut(a) if struts is None else struts.union(strut(a))
frame = arms.union(hub_disc).union(centre_tube).union(hub).union(struts)

holders, carbide = None, None
for c, arm_i, g in tracks:
    h, t = bit(c, ARM_ANGS[arm_i], g)
    holders = h if holders is None else holders.union(h)
    carbide = t if carbide is None else carbide.union(t)

head_bolts = screws(X_HUB_F, 40 + 35 - 5, 250, 20, 16, 30, 12.5, phase=11.25)

# ---------------- mount (spherical dry, L = 280) ----------------
parts, r1, pipes = bo.shell_weldment(40.0)
cart = revolve([
    (0, 125), (0, 200), (40, 200), (40, 169.95), (55, 169.95), (55, 155), (x_rear, 155), (x_rear, 125),
    (208, 125), (208, 100), (178, 100), (178, 120.5), (118, 120.5), (118, 126), (103, 126), (103, 125),
])
cart = bo.cart_common_holes(cart, 40.0, x_rear)
for a in (90, 270):
    cart = cart.cut(cyl_x(177, 32, 104, a, 12))
cart = cart.cut(cyl_r(x23r + 44, 90, 120, 160, 8))
cweld = revolve([(55, 155), (67, 155), (55, 167)])
hw = ring(162, 178, 90, 119.8)
sw = ring(118, 140, 70, 112).union(revolve([(140, 82), (140, 110), (162, 118), (162, 90)]))
shaft = revolve([(-185, 0), (-185, 65), (-120, 65), (-120, 70), (103, 70), (103, 82.5), (118, 82.5), (118, 70),
                 (x_nut + 25, 70), (x_nut + 25, 65), (x_rear + 92, 65), (x_rear + 92, 0)])
fe, cover, adapter = bo.front_end(True)
dparts, drv = bo.drive_parts(x_rear)

parts += [
    ("Cartridge: flange + tube (CJP), machined after welding", cart, "#b8673a", -900, "Bearing module"),
    ("Flange-to-tube weld (CJP)", cweld, "#c99a3c", -900, "Bearing module"),
    ("Cartridge screws 16 × M12, recessed", screws(13, 27 + 25, 370, 12, 16, 18, 12, phase=11.25), "#3c3f44", -900, "Bearing module"),
    ("Dowels 2 × Ø16, cartridge to ring 1", dowels(5, 55, 370, (90, 270)), "#e0a030", -900, "Bearing module"),
    ("29328N housing washer", hw, "#4f8a8b", -1000, "Bearing module"),
    ("Spindle Ø140", shaft, "#c7ccd1", -1300, "Bearing module"),
    ("Front 23228", bo.sph23(15), "#6aa368", -1300, "Bearing module"),
    ("29328N shaft washer + rollers", sw, "#4f8a8b", -1300, "Bearing module"),
    ("Spacer sleeve", ring(140, x23r, 70, 82.5), "#9aa0a6", -1300, "Bearing module"),
    ("Rear 23228", bo.sph23(x23r), "#6aa368", -1300, "Bearing module"),
    ("Rear KM28 nut", ring(x_nut, x_nut + 25, 70, 95), "#7d8288", -1300, "Bearing module"),
] + fe + dparts + [
    ("Cutterhead frame: 8 arms, hub disc, centre tube, 8 struts, hub ring", frame, "#8c6bb1", -2600, "Cutterhead"),
    ("Bit holders ×24", holders, "#5a4a7a", -2600, "Cutterhead"),
    ("Trapezoid carbide drag bits ×24", carbide, "#e8d36a", -2600, "Cutterhead"),
    ("Centre cone (placeholder)", centre_cone, "#8c6bb1", -2600, "Cutterhead"),
    ("Head-to-adapter bolts 16 × M20", head_bolts, "#3c3f44", -2600, "Cutterhead"),
]


def vol(a, b):
    return bo.vol(a, b)


shell = parts[0][1]
checks = {
    "head_vs_shell": vol(frame.union(holders).union(carbide), shell),
    "head_vs_cover": vol(frame, cover), "head_vs_adapter": vol(frame, adapter),
    "struts_vs_pipes": vol(frame, pipes), "pipes_vs_drive": vol(pipes, drv),
    "shaft_vs_cart": vol(shaft, cart), "cart_vs_ring1": vol(cart, r1), "drive_vs_shaft": vol(drv, shaft),
    "bolts_vs_struts": vol(head_bolts, struts),
    "head_front_x": X_ARM_F - 42, "shield_front_x": bo.SH_X0, "shield_rear_x": bo.SH_X1,
    "drive_rear_x": x_rear + bo.L_drive, "overall_length": x_rear + bo.L_drive - (X_ARM_F - 42),
    "ring1_depth": 40 - bo.SH_X0, "legs": bo.SH_X1 - 110, "cartridge_length": x_rear,
    "track_radii": [round(t[0], 2) for t in tracks],
}
print(json.dumps(checks))
bo.export("revF", parts, dict(x_r1=40.0, x_rear=x_rear, drive_rear=x_rear + bo.L_drive, cart=cart, shaft=shaft, r1=r1,
                              pipes=pipes, drv=drv, cover=cover, adapter=adapter))
