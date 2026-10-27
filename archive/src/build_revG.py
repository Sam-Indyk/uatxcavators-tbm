"""DN600 spindle mount + cutterhead, rev G: everything that can be is behind the bulkhead.
Ring 1 front face at x = 0. Ahead of it: only the rotating cutterhead (hub ring 10 mm off the plate, labyrinth in the gap).
  - cartridge flange recessed flush in a Ø400 x 40 counterbore; ring 1 110 thick (70 under the seat)
  - seal stack in a carrier ring inside the cartridge bore, flush with the plate; carrier also clamps the front 23228 (shims)
  - head hub ring splined directly onto the shaft (no adapter); end plate on the shaft nose, reached through the centre cap
  - slurry pipes and pressure taps end flush at the plate
  - 23228 + 29328N + 23228, L = 400
Axis +X rearward. Units mm. Visualisation model; Fusion 360 is the model of record.
"""
import json, math
import cadquery as cq
import build_opts as bo

r = lambda d: d / 2.0
ring, revolve, cyl_x, cyl_r, holes, screws, dowels = bo.ring, bo.revolve, bo.cyl_x, bo.cyl_r, bo.holes, bo.screws, bo.dowels
SH_ID, SH_OD = bo.SH_ID, bo.SH_OD

# ---------------- positions ----------------
T_R1, CB = 110.0, 40.0                     # ring 1 thickness, counterbore depth (= flange thickness)
L = 400.0
x23f = 70.0                                # front 23228 70..158
c23f = x23f + 44
x_col = x23f + 88                          # collar 158..173
x29 = x_col + 15                           # 29328N 173..233
x_sh = x29 + 60                            # shoulder 233..263
x23r = c23f + L - 44                       # 470
x_nut = x23r + 88                          # 558
x_rear = x_nut + 25 + 32                   # 615
X_HUB_F, X_HUB_B = -48.0, -8.0             # head hub ring
X_ARM_B = X_HUB_F - 85.0                   # -133
X_ARM_F = X_ARM_B - 50.8                   # -183.8
SH_X0 = X_ARM_B + 5.0                      # shield front edge just behind the arms
SH_X1 = SH_X0 + 1285.0
R_PIPE = 245.0

# ---------------- shell weldment ----------------
shell = ring(SH_X0, SH_X1, r(SH_ID), r(SH_OD))
r1 = revolve([(0, 200), (0, r(SH_ID) - 0.5), (T_R1, r(SH_ID) - 0.5), (T_R1, 170), (CB, 170), (CB, 200)])
r1 = holes(r1, CB - 1, 26, 370, 10.2, 16, phase=11.25)                       # M12 tapped into the seat
for a in (90, 270):
    r1 = r1.cut(cyl_x(CB - 1, 21, 185, a, 16))                              # dowels
    r1 = r1.cut(cyl_x(-1, T_R1 + 2, 225, a, 12))                            # pressure taps, flush
for a in (0, 180):
    r1 = r1.cut(cyl_x(-1, T_R1 + 2, R_PIPE, a, 77))                         # slurry pipes, flush
r1 = r1.cut(cyl_x(CB - 1, T_R1 - CB + 2, 178, 0, 6))                        # seal-purge passage from the seat
weld = revolve([(0, r(SH_ID)), (-14, r(SH_ID)), (0, r(SH_ID) - 14)])
pipes = None
for a in (0, 180):
    p = cyl_x(0, SH_X1, R_PIPE, a, 76.1).cut(cyl_x(-1, SH_X1 + 2, R_PIPE, a, 65))
    pipes = p if pipes is None else pipes.union(p)
sad = None
for sgn in (1, -1):
    b = cq.Workplane("YZ").workplane(offset=950).center(268 * sgn, 0).rect(26, 90).extrude(20)
    b = b.cut(cyl_x(949, 22, R_PIPE, 0 if sgn > 0 else 180, 76.2))
    sad = b if sad is None else sad.union(b)
taps = None
for a in (90, 270):
    t = cyl_x(T_R1, 120, 225, a, 12).cut(cyl_x(T_R1 - 1, 122, 225, a, 8))
    taps = t if taps is None else taps.union(t)
purge = cyl_x(T_R1, 120, 178, 0, 10).cut(cyl_x(T_R1 - 1, 122, 178, 0, 6))

# ---------------- cartridge (flange flush in the counterbore) ----------------
cart = revolve([
    (10, 150), (0, 150), (0, 199.9), (CB, 199.9), (CB, 155), (x_rear, 155), (x_rear, 125), (x_sh + 30, 125),
    (x_sh + 30, 100), (x_sh, 100), (x_sh, 120.5), (x29, 120.5), (x29, 126), (x_col, 126), (x_col, 125), (10, 125),
])
cart = holes(cart, -1, CB + 2, 370, 13.5, 16, phase=11.25)
for i in range(16):
    cart = cart.cut(cyl_x(-1, 14, 185, 11.25 + 22.5 * i, 20))              # recessed heads
cart = holes(cart, 9, 22, 280, 8.5, 12, phase=15)                          # seal carrier M10
for a in (90, 270):
    cart = cart.cut(cyl_x(-1, CB + 2, 185, a, 16))
    cart = cart.cut(cyl_x(x_sh - 1, 32, 104, a, 12))                         # housing-washer knock-outs
cart = cart.cut(ring(CB - 3, CB + 0.1, 190, 194))                          # O-ring on the seat
cart = cart.cut(cyl_x(20, CB - 19, 178, 0, 6))                             # purge: seat port -> radial -> carrier
cart = cart.cut(cyl_r(25, 0, 120, 181, 6))
cart = cart.cut(cyl_x(CB - 2, 2.2, 178, 0, 14).cut(cyl_x(CB - 3, 4, 178, 0, 9)))
cart = holes(cart, x_rear - 25, 26, 280, 14.0, 12)
for a in (15, 135, 255):
    cart = cart.cut(cyl_x(x_rear - 21, 22, 140, a, 16))
cart = cart.cut(cyl_r(c23f + L, 90, 120, 160, 8))                          # rear bearing relube
cweld = revolve([(CB, 155), (CB + 12, 155), (CB, 167)])

# ---------------- seal carrier (flush with the plate) ----------------
carrier = revolve([(0, 86), (0, 149.5), (9.4, 149.5), (9.4, 124.8), (70, 124.8), (70, 112), (69, 112), (69, 100), (8, 100), (8, 86)])
carrier = carrier.cut(ring(-1, 8, 101, 109)).cut(ring(-1, 8, 115, 123))     # labyrinth grooves
carrier = holes(carrier, -1, 12, 280, 11, 12, phase=15)
carrier = carrier.cut(cyl_r(27, 0, 99, 126, 6))
seals = ring(8, 23, 85.1, 100).union(ring(31, 46, 85.1, 100)).union(ring(54, 69, 85.1, 100))
lant = ring(23, 31, 86, 100).union(ring(46, 54, 86, 100))
shim = ring(9.4, 10, 126, 149)
carrier_screws = screws(0, 28, 280, 10, 12, 16, 8, phase=15)

# ---------------- spindle + bearings ----------------
shaft = revolve([(X_HUB_F, 0), (X_HUB_F, 65), (X_HUB_B, 65), (X_HUB_B, 70), (x_col, 70), (x_col, 82.5), (x29, 82.5),
                 (x29, 70), (x_nut + 25, 70), (x_nut + 25, 65), (x_rear + 92, 65), (x_rear + 92, 0)])
wear = ring(X_HUB_B, x23f, 70, 85)
hw = ring(x29 + 44, x29 + 60, 90, 119.8)
sw = ring(x29, x29 + 22, 70, 112).union(revolve([(x29 + 22, 82), (x29 + 22, 110), (x29 + 44, 118), (x29 + 44, 90)]))
spacer = ring(x29 + 22, x23r, 70, 82.5)
nut = ring(x_nut, x_nut + 25, 70, 95)
end_plate = holes(ring(X_HUB_F - 15, X_HUB_F, 0, 80), X_HUB_F - 16, 17, 90, 17, 4, phase=45)
end_screws = screws(X_HUB_F - 15, 40, 90, 16, 4, 24, 10, phase=45)

# ---------------- cutterhead ----------------
R_ARM_IN, R_ARM_OUT, W_ARM = 90.0, 310.0, 76.0
R_NODE_HUB, R_NODE_ARM, STRUT = 175.0, 245.0, 60.0
ARM_ANGS = [i * 45.0 for i in range(8)]


def rotx(wp, ang):
    return wp.rotate((0, 0, 0), (1, 0, 0), ang)


def arm(ang):
    return rotx(cq.Workplane("YZ").workplane(offset=X_ARM_F).center((R_ARM_IN + R_ARM_OUT) / 2, 0)
                .rect(R_ARM_OUT - R_ARM_IN, W_ARM).extrude(X_ARM_B - X_ARM_F), ang)


def strut(ang):
    a = math.radians(ang)
    p0 = cq.Vector(X_HUB_F + 5, R_NODE_HUB * math.cos(a), R_NODE_HUB * math.sin(a))
    p1 = cq.Vector(X_ARM_B - 5, R_NODE_ARM * math.cos(a), R_NODE_ARM * math.sin(a))
    d = p1 - p0
    t = cq.Vector(0, -math.sin(a), math.cos(a))
    return cq.Workplane(cq.Plane(origin=p0.toTuple(), xDir=t.toTuple(), normal=d.normalized().toTuple())).rect(STRUT, STRUT).extrude(d.Length)


def bit(c, ang):
    z0 = W_ARM / 2 - 12.0
    holder = cq.Workplane("YZ").workplane(offset=X_ARM_F - 20).center(c, z0).rect(30, 24).extrude(20)
    trap = (cq.Workplane("XY").workplane(offset=z0 - 7)
            .polyline([(X_ARM_F - 20, c - 11), (X_ARM_F - 20, c + 11), (X_ARM_F - 42, c + 6.35), (X_ARM_F - 42, c - 6.35)])
            .close().extrude(14))
    return rotx(holder, ang), rotx(trap, ang)


tracks = [(315.0 - 6.35, a, True) for a in (0, 3, 5)]
tracks += [(315.0 - 6.35 - 12.7 * k, (k * 3 + 1) % 8, False) for k in range(1, 22)]

frame = None
for a in ARM_ANGS:
    frame = arm(a) if frame is None else frame.union(arm(a))
frame = frame.union(ring(X_ARM_F, X_ARM_B, 60, 100))                         # hub disc with access hole
frame = frame.union(ring(X_ARM_B, X_HUB_F, 85, 100))                         # centre tube
hub = ring(X_HUB_F, X_HUB_B, 65, 210)                                        # splined bore Ø130
hub = hub.union(ring(X_HUB_B, X_HUB_B + 14, 103, 107)).union(ring(X_HUB_B, X_HUB_B + 14, 117, 121))   # labyrinth rings
frame = frame.union(hub)
for a in ARM_ANGS:
    frame = frame.union(strut(a))
frame = frame.cut(ring(X_ARM_F - 1, X_ARM_F + 10, 59, 70.5))                 # pocket for the centre cap rim
cap = revolve([(X_ARM_F, 0), (X_ARM_F, 70), (X_ARM_F + 10, 70), (X_ARM_F + 10, 59.5), (X_ARM_B, 59.5), (X_ARM_B, 0)])
cap = cap.union(revolve([(X_ARM_F, 0), (X_ARM_F, 24), (X_ARM_F - 25, 0)]))
cap = holes(cap, X_ARM_F - 1, 12, 120, 11, 6)
holders = carbide = None
for c, ai, g in tracks:
    h, t = bit(c, ARM_ANGS[ai])
    holders = h if holders is None else holders.union(h)
    carbide = t if carbide is None else carbide.union(t)

dparts, drv = bo.drive_parts(x_rear)

parts = [
    ("Shield shell (1285)", shell, "#8a8f94", 0, "Shell weldment"),
    ("Ring 1, 110 thk A572-50, Ø400 × 40 counterbore", r1, "#5f86a8", 0, "Shell weldment"),
    ("Ring 1 weld, 14 mm front fillet", weld, "#c99a3c", 0, "Shell weldment"),
    ("Slurry pipes, flush at plate, R245, 12 + 6", pipes, "#e0e4e8", 0, "Shell weldment"),
    ("Pipe saddles", sad, "#5f86a8", 0, "Shell weldment"),
    ("Pressure tap tubes, flush", taps, "#e0e4e8", 0, "Shell weldment"),
    ("Seal-purge grease tube", purge, "#d9c24a", 0, "Shell weldment"),
    ("Cartridge: flush flange + tube (CJP)", cart, "#b8673a", -900, "Bearing module"),
    ("Flange-to-tube weld (CJP)", cweld, "#c99a3c", -900, "Bearing module"),
    ("Cartridge screws 16 × M12, recessed", screws(13, 27 + 25, 370, 12, 16, 18, 12, phase=11.25), "#3c3f44", -900, "Bearing module"),
    ("Dowels 2 × Ø16, cartridge to ring 1", dowels(5, 55, 370, (90, 270)), "#e0a030", -900, "Bearing module"),
    ("Seal carrier (flush)", carrier, "#9c5530", -1250, "Bearing module"),
    ("Lip seals ×3", seals, "#2b2f33", -1250, "Bearing module"),
    ("Grease lantern rings ×2", lant, "#d9c24a", -1250, "Bearing module"),
    ("Carrier shims", shim, "#d9c24a", -1200, "Bearing module"),
    ("Carrier screws 12 × M10", carrier_screws, "#3c3f44", -1250, "Bearing module"),
    ("29328N housing washer", hw, "#4f8a8b", -1000, "Bearing module"),
    ("Spindle Ø140", shaft, "#c7ccd1", -1500, "Bearing module"),
    ("Wear sleeve Ø170", wear, "#d0a060", -1500, "Bearing module"),
    ("Front 23228", bo.sph23(x23f), "#6aa368", -1500, "Bearing module"),
    ("29328N shaft washer + rollers", sw, "#4f8a8b", -1500, "Bearing module"),
    ("Spacer sleeve", spacer, "#9aa0a6", -1500, "Bearing module"),
    ("Rear 23228", bo.sph23(x23r), "#6aa368", -1500, "Bearing module"),
    ("Rear KM28 nut", nut, "#7d8288", -1500, "Bearing module"),
    ("Cutterhead frame (splined hub ring, struts, arms)", frame, "#8c6bb1", -2300, "Cutterhead"),
    ("Bit holders ×24", holders, "#5a4a7a", -2300, "Cutterhead"),
    ("Trapezoid carbide drag bits ×24", carbide, "#e8d36a", -2300, "Cutterhead"),
    ("Centre cap + cone (removable)", cap, "#7a5aa1", -2600, "Cutterhead"),
    ("End plate + screws", end_plate.union(end_screws), "#7d8288", -2450, "Cutterhead"),
] + dparts

V = bo.vol
checks = {
    "head_vs_shell": V(frame.union(holders).union(carbide), shell), "head_vs_ring1": V(frame, r1),
    "head_vs_cart": V(frame, cart), "head_vs_carrier": V(frame, carrier), "frame_vs_cap": V(frame, cap), "bits_vs_cap": V(holders.union(carbide), cap),
    "pipes_vs_head": V(pipes, frame), "pipes_vs_drive": V(pipes, drv), "pipes_vs_cart": V(pipes, cart),
    "cart_vs_ring1": V(cart, r1), "carrier_vs_cart": V(carrier, cart), "shaft_vs_cart": V(shaft, cart),
    "shaft_vs_frame": V(shaft, frame), "endplate_vs_frame": V(end_plate, frame), "drive_vs_shaft": V(drv, shaft),
    "stationary_ahead_of_plate_min_x": 0.0,
    "head_front_x": X_ARM_F - 42, "shield_front_x": SH_X0, "shield_rear_x": SH_X1, "drive_rear_x": x_rear + bo.L_drive,
    "overall": x_rear + bo.L_drive - (X_ARM_F - 42), "ring1_depth": -SH_X0, "legs": SH_X1 - T_R1,
    "chamber_depth": -X_ARM_B, "overhang_bearing_to_bits": c23f - (X_ARM_F - 42),
}
print(json.dumps(checks))
bo.export("revG", parts, dict(x_r1=0.0, x_rear=x_rear, drive_rear=x_rear + bo.L_drive, cart=cart, shaft=shaft, r1=r1,
                              pipes=pipes, drv=drv, cover=carrier, adapter=frame))
