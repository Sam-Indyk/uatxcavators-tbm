"""DN600 spindle mount, rev E: single mounting ring.
Axis +X rearward, X = 0 at cartridge front face. Units mm. Visualisation model; Fusion 360 is the model of record.

One welded ring (ring 1, machined before welding). One cartridge carries all three bearings and the drive.
  cartridge = front sleeve + disc + rear sleeve, welded then machined on the bench
  thrust: 29328N housing washer -> disc front face -> disc rear face -> ring 1 (no weld in the thrust path)
  rear 23228 and drive pilot share one Ø250 bore in the rear sleeve
"""
import json, math
import cadquery as cq

r = lambda d: d / 2.0
SH_OD, SH_ID = 609.6, 584.2
SH_X0, SH_X1 = -175.0, 1110.0                   # shield front / rear ends (1285)

# bearings
B23, D23 = 88.0, 250.0
H29, D29 = 60.0, 240.0
x23f = 15.0
x_col = x23f + B23                              # 103
x29 = x_col + 15.0                              # 118
L = 400.0
c23f = x23f + B23 / 2                           # 59
x23r = c23f + L - B23 / 2                       # 415

# cartridge
D_sl = 310.0
x_d0 = x29 + H29                                # 178  disc front face = thrust shoulder
x_d1 = x_d0 + 40.0                              # 218  disc rear face = seat on ring 1
D_disc, D_disc_bore = 400.0, 200.0
D_spig, l_spig = 340.0, 15.0                    # register spigot on disc rear face
x_rear = 560.0                                  # cartridge rear face (drive face)
BC_cart = 370.0                                 # 16 x M12 cartridge to ring 1
BC_cov = 280.0                                  # 12 x M10 front cover
BC_drv = 280.0                                  # 12 x M16 drive to cartridge rear face

# ring 1
x_r1 = x_d1                                     # 218
t_r1 = 70.0
D_r1_bore = D_spig                              # Ø340 H7 register
R_pipe = 245.0
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
    """radial drilled hole at axial station x, angle ang, from radius r0 to r1"""
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


# ================= shell weldment =================
shell = ring(SH_X0, SH_X1, r(SH_ID), r(SH_OD))

ring1 = ring(x_r1, x_r1 + t_r1, r(D_r1_bore), r(SH_ID) - 0.5)
ring1 = holes(ring1, x_r1 - 1, 26, BC_cart, 10.2, 16, phase=11.25)      # M12 tapped 25 deep from the front
for ang in (0, 180):
    ring1 = ring1.cut(cyl_x(x_r1 - 1, t_r1 + 2, R_pipe, ang, 77))        # slurry pipes
for ang in (90, 270):
    ring1 = ring1.cut(cyl_x(x_r1 - 1, t_r1 + 2, 225, ang, 12))           # chamber pressure taps
ring1 = ring1.cut(cyl_x(x_r1 - 1, t_r1 + 2, 178, 0, 6))                  # seal-purge grease passage

weld1 = revolve([(x_r1, r(SH_ID)), (x_r1 - 14, r(SH_ID)), (x_r1, r(SH_ID) - 14)])   # 14 mm front fillet only

pipes = None
for ang in (0, 180):
    p = cyl_x(120, SH_X1 - 120, R_pipe, ang, 76.1).cut(cyl_x(119, SH_X1 - 118, R_pipe, ang, 65))
    pipes = p if pipes is None else pipes.union(p)
saddles = None                                                            # rear pipe supports welded to shell
for ang in (0, 180):
    a = math.radians(ang)
    blk = (cq.Workplane("YZ").workplane(offset=760).center(268 * math.cos(a), 268 * math.sin(a))
           .rect(26, 90).extrude(20))
    if ang == 0:
        blk = (cq.Workplane("YZ").workplane(offset=760).center(268, 0).rect(26, 90).extrude(20))
    else:
        blk = (cq.Workplane("YZ").workplane(offset=760).center(-268, 0).rect(26, 90).extrude(20))
    blk = blk.cut(cyl_x(759, 22, R_pipe, ang, 76.2))
    saddles = blk if saddles is None else saddles.union(blk)
taps = None
for ang in (90, 270):
    t = cyl_x(x_r1 + t_r1, 120, 225, ang, 12).cut(cyl_x(x_r1 + t_r1 - 1, 122, 225, ang, 8))
    taps = t if taps is None else taps.union(t)
purge = cyl_x(x_r1 + t_r1, 120, 178, 0, 10).cut(cyl_x(x_r1 + t_r1 - 1, 122, 178, 0, 6))

# ================= cartridge weldment (machined after welding) =================
cart = revolve([
    (0, r(D23)), (0, r(D_sl)), (x_d0, r(D_sl)), (x_d0, r(D_disc)), (x_d1, r(D_disc)),
    (x_d1, r(D_spig) - 0.05), (x_d1 + l_spig, r(D_spig) - 0.05), (x_d1 + l_spig, r(D_sl)),
    (x_rear, r(D_sl)), (x_rear, r(D23)), (x_d1, r(D23)), (x_d1, r(D_disc_bore)), (x_d0, r(D_disc_bore)),
    (x_d0, r(D29) + 0.5), (x29, r(D29) + 0.5), (x29, r(D23) + 1), (x_col, r(D23) + 1), (x_col, r(D23)),
])
cart = holes(cart, x_d0 - 1, 42, BC_cart, 13.5, 16, phase=11.25)
for i in range(16):
    cart = cart.cut(cyl_x(x_d0 - 1, 14, BC_cart / 2, 11.25 + 22.5 * i, 20))   # counterbores, heads recessed
cart = holes(cart, -1, 21, BC_cov, 8.5, 12, phase=15)                    # front cover M10
cart = holes(cart, x_rear - 25, 26, BC_drv, 14.0, 12)                    # drive M16 tapped
cart = cart.cut(ring(x_d1 - 3, x_d1 + 0.1, 194, 198))                    # O-ring, disc to ring 1
# seal-purge passage: ring port (R178, 0 deg) -> disc -> radial -> sleeve (R140) -> front face
cart = cart.cut(cyl_x(x_d1 - 25, 26, 178, 0, 6))
cart = cart.cut(cyl_r(x_d1 - 22, 0, 137, 201, 6))                        # radial cross-drill, plugged at disc OD
cart = cart.cut(cyl_x(-1, x_d1 - 21, 140, 0, 6))
cart = cart.cut(cyl_x(x_d1 - 2, 2.2, 178, 0, 14).cut(cyl_x(x_d1 - 3, 4, 178, 0, 9)))   # port O-ring
for ang in (90, 270):                                                    # housing-washer knock-out holes
    cart = cart.cut(cyl_x(x_d0 - 1, 42, 104, ang, 12))
cart = cart.cut(cyl_r(470, 90, 120, 160, 8))                             # rear bearing grease port (dry side)
cart_welds = (revolve([(x_d0, r(D_sl)), (x_d0 - 12, r(D_sl)), (x_d0, r(D_sl) + 12)])          # front sleeve to disc
              .union(revolve([(x_d1 + l_spig, r(D_sl)), (x_d1 + l_spig + 12, r(D_sl)),
                              (x_d1 + l_spig, r(D_sl) + 12)])))                                # rear sleeve to disc

hw29 = ring(x29 + 44, x29 + H29, 90, r(D29) - 0.2)
sw29 = (ring(x29, x29 + 22, 70, 112)
        .union(revolve([(x29 + 22, 82), (x29 + 22, 110), (x29 + 44, 118), (x29 + 44, 90)])))


def brg23(x0):
    return (ring(x0, x0 + B23, 115, r(D23)).union(ring(x0, x0 + B23, 70, 81))
            .union(ring(x0 + 8, x0 + B23 - 8, 83, 113)))


b23f, b23r = brg23(x23f), brg23(x23r)

shaft = revolve([
    (-185, 0), (-185, 65), (-120, 65), (-120, 70), (x_col, 70), (x_col, 82.5), (x29, 82.5), (x29, 70),
    (x23r + B23 + 25, 70), (x23r + B23 + 25, 65), (650, 65), (650, 0),
])
spacer = ring(x29 + 22, x23r, 70, 82.5)
nut_r = ring(x23r + B23, x23r + B23 + 25, 70, 95)
wear = ring(-120, x23f, 70, 85)
end_plate = holes(ring(-200, -185, 0, 80), -201, 17, 90, 17, 4, phase=45)
adapter = ring(-185, -150, 65, 150).union(ring(-150, -120, 65, 85))
adapter = holes(adapter, -186, 37, 250, 21, 16)
adapter = adapter.union(ring(-150, -136, 99, 103)).union(ring(-150, -136, 113, 117))

cover = revolve([(-140, 85.6), (-140, 125), (-40, 125), (-40, r(D_sl)), (-0.6, r(D_sl)),
                 (-0.6, r(D23) - 0.2), (15, r(D23) - 0.2), (15, 115), (-0.6, 115), (-0.6, 85.6)])
cover = cover.cut(ring(-112, -40, 85.6, 100))
cover = cover.cut(ring(-141, -130, 97, 105)).cut(ring(-141, -130, 111, 119))
cover = holes(cover, -41, 42, BC_cov, 11, 12, phase=15)
cover = cover.cut(cyl_x(-41, 42, 140, 0, 6))
seals = ring(-112, -97, 85.1, 100).union(ring(-89, -74, 85.1, 100)).union(ring(-66, -51, 85.1, 100))
lanterns = ring(-97, -89, 86, 100).union(ring(-74, -66, 86, 100))
shim = ring(-0.6, 0, 126, 154)


# dowels (torque backup + relocation): 2 x Ø16 disc-to-ring 1 at R185, 3 x Ø16 drive-to-cartridge at R140
dw1 = None
for ang in (90, 270):
    c = cyl_x(x_d0 + 5, 55, BC_cart / 2, ang, 16)
    dw1 = c if dw1 is None else dw1.union(c)
dw2 = None
for ang in (15, 135, 255):
    c = cyl_x(x_rear - 20, 40, BC_drv / 2, ang, 16)
    dw2 = c if dw2 is None else dw2.union(c)
for ang in (90, 270):
    cart = cart.cut(cyl_x(x_d0 - 1, 42, BC_cart / 2, ang, 16))
    ring1 = ring1.cut(cyl_x(x_r1 - 1, 21, BC_cart / 2, ang, 16))
for ang in (15, 135, 255):
    cart = cart.cut(cyl_x(x_rear - 21, 22, BC_drv / 2, ang, 16))

drive = ring(x_rear + 0.5, x_rear + L_drive, 0, r(D_drive))
drive = drive.union(ring(x_rear - 15, x_rear + 0.5, 70, r(D23) - 0.2))   # pilot Ø250 f7 with O-ring
drive = drive.cut(ring(x_rear - 16, 652, 0, 66))                         # female spline bore
drive = holes(drive, x_rear, 45, BC_drv, 26, 12)                         # screw clearance in the envelope
for ang in (15, 135, 255):
    drive = drive.cut(cyl_x(x_rear, 21, BC_drv / 2, ang, 16))

cart_screws = screws(x_d0 + 13, 27 + 24, BC_cart, 12, 16, 18, 12, phase=11.25)
cover_screws = screws(-40, 55, BC_cov, 10, 12, 16, 10, phase=15)
adapter_screws = screws(-200, 40, 90, 16, 4, 24, 10, phase=45)
drive_screws = screws(x_rear + 28, 53, BC_drv, 16, 12, 24, 10, head_rear=True)

# depth-setting fixture (assembly aid, shown only exploded): 3 legs from the table under the rear end
legs = None
for ang in (30, 150, 270):
    lg = cyl_x(x_r1 + t_r1, SH_X1 - (x_r1 + t_r1), 255, ang, 30)
    legs = lg if legs is None else legs.union(lg)

parts = [
    ("Shield shell (1285)", shell, "#8a8f94", 0, "Shell weldment"),
    ("Ring 1, 70 thk A572-50, pre-machined", ring1, "#5f86a8", 0, "Shell weldment"),
    ("Ring 1 weld, 14 mm front fillet", weld1, "#c99a3c", 0, "Shell weldment"),
    ("Slurry pipes, R245, 12 + 6", pipes, "#e0e4e8", 0, "Shell weldment"),
    ("Pipe saddles", saddles, "#5f86a8", 0, "Shell weldment"),
    ("Pressure tap tubes", taps, "#e0e4e8", 0, "Shell weldment"),
    ("Seal-purge grease tube", purge, "#d9c24a", 0, "Shell weldment"),
    ("Depth gauge legs (fixture, removed)", legs, "#e07a3a", 1400, "Fixture"),
    ("Cartridge weldment", cart, "#b8673a", -900, "Bearing module"),
    ("Cartridge welds", cart_welds, "#c99a3c", -900, "Bearing module"),
    ("Cartridge screws 16 × M12, recessed", cart_screws, "#3c3f44", -900, "Bearing module"),
    ("Dowels 2 × Ø16, cartridge to ring 1", dw1, "#e0a030", -900, "Bearing module"),
    ("29328N housing washer", hw29, "#4f8a8b", -1000, "Bearing module"),
    ("Spindle Ø140", shaft, "#c7ccd1", -1300, "Bearing module"),
    ("Front 23228", b23f, "#6aa368", -1300, "Bearing module"),
    ("29328N shaft washer + rollers", sw29, "#4f8a8b", -1300, "Bearing module"),
    ("Spacer sleeve", spacer, "#9aa0a6", -1300, "Bearing module"),
    ("Rear 23228", b23r, "#6aa368", -1300, "Bearing module"),
    ("Rear KM28 nut", nut_r, "#7d8288", -1300, "Bearing module"),
    ("Wear sleeve Ø170", wear, "#d0a060", -1300, "Bearing module"),
    ("Front cover", cover, "#9c5530", -1600, "Bearing module"),
    ("Lip seals ×3", seals, "#2b2f33", -1600, "Bearing module"),
    ("Grease lantern rings ×2", lanterns, "#d9c24a", -1600, "Bearing module"),
    ("Cover shims", shim, "#d9c24a", -1530, "Bearing module"),
    ("Cover screws", cover_screws, "#3c3f44", -1600, "Bearing module"),
    ("Front adapter + labyrinth", adapter, "#aab0b6", -1950, "Bearing module"),
    ("End plate + screws", end_plate.union(adapter_screws), "#7d8288", -2100, "Bearing module"),
    ("Drive envelope Ø400 (motor TBD)", drive, "#2f6f9f", 650, "Drive"),
    ("Drive screws 12 × M16", drive_screws, "#3c3f44", 650, "Drive"),
    ("Dowels 3 × Ø16, drive to cartridge", dw2, "#e0a030", 650, "Drive"),
]


def vol(a, b):
    try:
        return a.intersect(b).val().Volume() / 1000.0
    except Exception:
        return 0.0


checks = {
    "pipes_vs_drive": vol(pipes, drive), "pipes_vs_cart": vol(pipes, cart), "pipes_vs_ring1": vol(pipes, ring1),
    "shaft_vs_cart": vol(shaft, cart), "shaft_vs_ring1": vol(shaft, ring1), "cart_vs_ring1": vol(cart, ring1),
    "rear23228_vs_cart": vol(b23r, cart), "spacer_vs_cart": vol(spacer, cart), "drive_vs_shaft": vol(drive, shaft),
    "drive_vs_ring1": vol(drive, ring1), "cover_vs_adapter": vol(cover, adapter), "saddles_vs_drive": vol(saddles, drive),
    "ring1_front_depth_from_shield_front": x_r1 - SH_X0,
    "leg_length_from_rear_end": SH_X1 - (x_r1 + t_r1),
    "drive_rear_x": x_rear + L_drive,
}
print(json.dumps({k: round(v, 2) for k, v in checks.items()}, indent=1))

out = []
assy = cq.Assembly(name="spindle_mount_revE")
for name, wp, col, dx, grp in parts:
    pos, idx = [], []
    for f in wp.val().Faces():
        vs, tris = f.tessellate(0.15, 0.25)
        base = len(pos) // 3
        for v in vs:
            pos += [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
        for t in tris:
            idx += [t[0] + base, t[1] + base, t[2] + base]
    kg = round(wp.val().Volume() * 7.85e-6, 1)
    if name.startswith("Drive envelope") or grp == "Fixture":
        kg = 0.0
    if "seals" in name.lower():
        kg = round(kg * 0.2, 1)
    out.append({"name": name, "color": col, "dx": dx, "group": grp, "pos": pos, "idx": idx, "kg": kg})
    if grp != "Fixture":
        safe = "".join(ch if ch.isalnum() else "_" for ch in name)
        assy.add(wp, name=safe, color=cq.Color(*[int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
    print(f"{grp:16s} {name:40s} {kg:7.1f}")
assy.export("/home/claude/cad/spindle_mount_revE.step")
json.dump({"parts": out, "checks": checks}, open("/home/claude/cad/mesh5.json", "w"), separators=(",", ":"))
