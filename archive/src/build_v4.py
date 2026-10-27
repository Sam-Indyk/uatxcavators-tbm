"""DN600 spindle mount, rev D.
Axis +X rearward, X = 0 at cartridge front face. Units mm. Visualisation model; Fusion 360 is the model of record.

Changes from rev C:
  - rear radial bearing = second Koyo 23228, carried in the rear plate (no 22318, no rear cartridge)
  - cartridge = flange disc + front sleeve; thrust shoulder is the disc face (no weld in the thrust path)
  - cartridge bolts straight to a wide welded ring 1 (no bulkhead plate, no gasket); O-ring, metal-to-metal
  - everything crossing the bulkhead is in the shell weldment; the bearing module leaves forward with no access behind ring 1
  - rear plate: one straight Ø250 bore holds the rear 23228 (from the front) and the drive pilot (from the rear)
  - shaft Ø140 throughout plus one collar; Ø130 splines at both ends; no front nut
  - front seal: labyrinth + 3 lip seals on a replaceable wear sleeve, 2 grease lantern rings
  - drive drawn as an envelope (Ø400 max) that clears the slurry pipes
"""
import json, math
import cadquery as cq

r = lambda d: d / 2.0
SH_OD, SH_ID = 609.6, 584.2
SH_X0, SH_X1 = -175.0, 1110.0

# bearings
B23, D23, d23 = 88.0, 250.0, 140.0
H29, D29 = 60.0, 240.0
x23f = 15.0                         # front 23228 front face
x_col = x23f + B23                  # collar 103..118
x29 = x_col + 15.0                  # 29328N 118..178
L = 400.0
c23f = x23f + B23 / 2               # 59
c23r = c23f + L                     # 459
x23r = c23r - B23 / 2               # 415

# cartridge
D_sleeve = 310.0
x_disc0 = x29 + H29                 # 178  (thrust shoulder = disc front face)
t_disc = 40.0
x_disc1 = x_disc0 + t_disc          # 218  (bears on ring 1)
D_disc = 400.0
D_disc_bore = 200.0
D_spigot, l_spigot = 260.0, 15.0
BC_cart = 350.0

# ring 1 / ring 2 / rear plate
t_r1 = 60.0
x_r1 = x_disc1                      # 218..278
D_r1_id = 260.0
t_r2 = 40.0
x_rp0 = 520.0                       # rear plate front face = ring 2 rear face
x_r2 = x_rp0 - t_r2                 # 480..520
D_r2_id = 380.0
t_rp = 40.0
x_rp1 = x_rp0 + t_rp                # 560
x_hub0 = 400.0                      # hub front
D_hub = 310.0
D_rp = 560.0
BC_rp = 510.0

R_pipe = 245.0                      # slurry pipes, 12 and 6 o'clock
D_drive = 400.0
L_drive = 478.3


def revolve(pts):
    return cq.Workplane("XY").polyline(pts).close().revolve(360, (0, 0, 0), (1, 0, 0))


def ring(x0, x1, ri, ro):
    return revolve([(x0, ri), (x1, ri), (x1, ro), (x0, ro)])


def cyl_x(x0, length, rr, ang, dia):
    a = math.radians(ang)
    return (cq.Workplane("YZ").workplane(offset=x0)
            .center(rr * math.cos(a), rr * math.sin(a)).circle(dia / 2).extrude(length))


def holes(s, x0, length, bc, dia, n, phase=0.0):
    for i in range(n):
        s = s.cut(cyl_x(x0, length, bc / 2, phase + 360.0 * i / n, dia))
    return s


def screws(x_face, length, bc, d, n, head_d, head_h, phase=0.0, head_rear=False):
    """socket/hex screws along X. head_rear=False: head ahead of x_face, shank rearward."""
    out = None
    for i in range(n):
        a = math.radians(phase + 360.0 * i / n)
        y, z = bc / 2 * math.cos(a), bc / 2 * math.sin(a)
        if not head_rear:
            sh = cq.Workplane("YZ").workplane(offset=x_face).center(y, z).circle(d / 2).extrude(length)
            hd = cq.Workplane("YZ").workplane(offset=x_face - head_h).center(y, z).circle(head_d / 2).extrude(head_h)
        else:
            sh = cq.Workplane("YZ").workplane(offset=x_face - length).center(y, z).circle(d / 2).extrude(length)
            hd = cq.Workplane("YZ").workplane(offset=x_face).center(y, z).polygon(6, head_d).extrude(head_h)
        b = sh.union(hd)
        out = b if out is None else out.union(b)
    return out


def fillet_weld(x_face, rad, leg, sign):
    """triangular fillet bead at a ring face / shell bore corner. sign -1 = on the front face."""
    return revolve([(x_face, rad), (x_face + sign * leg, rad), (x_face, rad - leg)])


# ================= shell weldment =================
shell = ring(SH_X0, SH_X1, r(SH_ID), r(SH_OD))

ring1 = ring(x_r1, x_r1 + t_r1, r(D_r1_id), r(SH_ID))
ring1 = holes(ring1, x_r1 - 1, 31, BC_cart, 14.0, 12, phase=15)              # M16 tapped 30 deep, blind from the front
for ang in (0, 180):
    ring1 = ring1.cut(cyl_x(x_r1 - 1, t_r1 + 2, R_pipe, ang, 77))            # pipes welded through
for ang in (90, 270):
    ring1 = ring1.cut(cyl_x(x_r1 - 1, t_r1 + 2, 225, ang, 12))               # chamber pressure taps
ring1 = ring1.cut(cyl_x(x_r1 - 1, t_r1 + 2, 140, 105, 6))                    # seal-purge grease passage

ring2 = ring(x_r2, x_r2 + t_r2, r(D_r2_id), r(SH_ID))
ring2 = holes(ring2, x_r2 + t_r2 - 30, 31, BC_rp, 17.5, 12, phase=15)        # M20 tapped from the rear
for ang in (0, 180):
    ring2 = ring2.cut(cyl_x(x_r2 - 1, t_r2 + 2, R_pipe, ang, 82))
for ang in (90, 270):
    ring2 = ring2.cut(cyl_x(x_r2 - 1, t_r2 + 2, R_pipe, ang, 50))

welds = (fillet_weld(x_r1, r(SH_ID), 12, -1)             # ring 1: front fillet only
         .union(fillet_weld(x_r2 + t_r2, r(SH_ID), 10, +1)))  # ring 2: rear fillet only

pipes = None
for ang in (0, 180):
    p = cyl_x(120, SH_X1 - 120, R_pipe, ang, 76.1).cut(cyl_x(119, SH_X1 - 118, R_pipe, ang, 65))
    pipes = p if pipes is None else pipes.union(p)
taps = None
for ang in (90, 270):
    t = cyl_x(x_r1 + t_r1, 120, 225, ang, 12).cut(cyl_x(x_r1 + t_r1 - 1, 122, 225, ang, 8))
    taps = t if taps is None else taps.union(t)
purge = cyl_x(x_r1 + t_r1, 120, 140, 105, 10).cut(cyl_x(x_r1 + t_r1 - 1, 122, 140, 105, 6))

# ================= bearing module =================
# cartridge: front sleeve + flange disc, welded, then machined
cart = revolve([
    (0, r(D23)), (0, r(D_sleeve)), (x_disc0, r(D_sleeve)), (x_disc0, r(D_disc)),
    (x_disc1, r(D_disc)), (x_disc1, r(D_spigot) - 0.05), (x_disc1 + l_spigot, r(D_spigot) - 0.05),
    (x_disc1 + l_spigot, r(D_disc_bore)), (x_disc0, r(D_disc_bore)),
    (x_disc0, r(D29) + 0.5), (x29, r(D29) + 0.5), (x29, r(D23) + 1), (x_col, r(D23) + 1), (x_col, r(D23)),
])
cart = holes(cart, x_disc0 - 1, t_disc + 2, BC_cart, 17.5, 12, phase=15)
for i in range(12):                                                           # counterbores, heads below flush
    cart = cart.cut(cyl_x(x_disc0 - 1, 18, BC_cart / 2, 15 + 30 * i, 27))
cart = holes(cart, -1, 21, 280, 8.5, 12)                                      # front cover M10
cart = cart.cut(ring(x_disc1 - 3, x_disc1 + 1, 190, 194))                     # O-ring, disc to ring 1
cart = cart.cut(cyl_x(-1, x_disc1 + 2, 140, 105, 6))                          # purge passage, front face to disc rear face
cart = cart.cut(cyl_x(x_disc1 - 2, 3, 140, 105, 14).cut(cyl_x(x_disc1 - 3, 5, 140, 105, 9)))  # port O-ring
for ang in (0, 180):                                                          # housing-washer knock-out slots
    cart = cart.cut(cyl_x(x_disc0 - 1, t_disc + l_spigot + 2, 104, ang, 12))
cart_weld = revolve([(x_disc0, r(D_sleeve)), (x_disc0 - 12, r(D_sleeve)), (x_disc0, r(D_sleeve) + 12)])

hw29 = ring(x29 + 44, x29 + H29, 90, r(D29) - 0.2)                            # 29328N housing washer
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
end_plate = holes(ring(-200, -185, 0, 80), -201, 17, 90, 17, 4, phase=45)
spacer = ring(x29 + 22, x23r, 70, 82.5)                                       # retains 29328N shaft washer, locates rear 23228
nut_r = ring(x23r + B23, x23r + B23 + 25, 70, 95)                             # KM28 rear
wear = ring(-120, x23f, 70, 85)                                               # hardened wear sleeve Ø170
grease_seal = ring(x_disc1 + l_spigot - 15, x_disc1 + l_spigot, 82.6, r(D_disc_bore))

# front adapter with labyrinth rings on its rear face
adapter = ring(-185, -150, 65, 150).union(ring(-150, -120, 65, 85))
adapter = holes(adapter, -186, 37, 250, 21, 16)
adapter = adapter.union(ring(-150, -136, 99, 103)).union(ring(-150, -136, 113, 117))

# front cover: flange + nose; 3 lip seals and 2 lantern rings in the nose
cover = revolve([(-140, 85.6), (-140, 125), (-40, 125), (-40, r(D_sleeve)), (-0.6, r(D_sleeve)),
                 (-0.6, r(D23) - 0.2), (15, r(D23) - 0.2), (15, 115), (-0.6, 115), (-0.6, 85.6)])
cover = cover.cut(ring(-112, -40, 85.6, 100))                                 # seal bore Ø200
cover = cover.cut(ring(-141, -130, 97, 105)).cut(ring(-141, -130, 111, 119))  # labyrinth grooves
cover = holes(cover, -41, 42, 280, 11, 12)
cover = cover.cut(cyl_x(-41, 42, 140, 105, 6))
seals = None
for x0, w in ((-112, 15), (-89, 15), (-66, 15)):
    s = ring(x0, x0 + w, 85.1, 100)
    seals = s if seals is None else seals.union(s)
lanterns = ring(-97, -89, 86, 100).union(ring(-74, -66, 86, 100))
shim = ring(-0.6, 0, 126, 154)

# ================= rear plate + drive =================
rp = revolve([(x_hub0, r(D23)), (x_hub0, r(D_hub)), (x_rp0, r(D_hub)), (x_rp0, r(D_rp)),
              (x_rp1, r(D_rp)), (x_rp1, r(D23))])
rp = holes(rp, x_rp0 - 1, t_rp + 2, BC_rp, 22, 12, phase=15)
for ang in (0, 180):
    rp = rp.cut(cyl_x(x_rp0 - 1, t_rp + 2, R_pipe, ang, 82))
for ang in (90, 270):
    rp = rp.cut(cyl_x(x_rp0 - 1, t_rp + 2, R_pipe, ang, 50))
rp = holes(rp, x_rp1 - 25, 26, 300, 17.5, 12)                                 # drive bolts M20 tapped
rp_cap = ring(x_hub0 - 10, x_hub0, 82.6, r(D_hub))                            # grease cap + seal at hub front
dowels = None
for ang in (30, 210):
    d = cyl_x(x_r2 + 10, 70, BC_rp / 2, ang, 16)
    dowels = d if dowels is None else dowels.union(d)
rp_bolts = screws(x_rp1, t_rp + 30, BC_rp, 20, 12, 30, 13, phase=15, head_rear=True)

drive = ring(x_rp1 + 0.5, x_rp1 + L_drive, 0, r(D_drive))
drive = drive.union(ring(x_rp1 - 15, x_rp1 + 0.5, 70, r(D23) - 0.2))         # pilot in the Ø250 bore
drive = drive.cut(ring(x_rp1 - 16, 652, 0, 66))                               # female spline bore for the spindle
drive_bolts = screws(x_rp1 + 25, 50, 300, 20, 12, 30, 13, head_rear=True)

cart_screws = screws(x_disc0 + 17, t_disc - 17 + 30, BC_cart, 16, 12, 24, 16, phase=15)
cover_screws = screws(-40, 55, 280, 10, 12, 16, 10)
adapter_screws = screws(-200, 40, 90, 16, 4, 24, 10, phase=45)

parts = [
    # name, solid, colour, explode dx, group
    ("Shield shell (1285)", shell, "#8a8f94", 0, "Shell weldment"),
    ("Ring 1, 60 thk, welded front", ring1, "#5f86a8", 0, "Shell weldment"),
    ("Ring 2, 40 thk, welded rear", ring2, "#5f86a8", 0, "Shell weldment"),
    ("Ring welds (one side each)", welds, "#c99a3c", 0, "Shell weldment"),
    ("Slurry pipes, R245, 12 + 6", pipes, "#e0e4e8", 0, "Shell weldment"),
    ("Pressure tap tubes", taps, "#e0e4e8", 0, "Shell weldment"),
    ("Seal-purge grease tube", purge, "#d9c24a", 0, "Shell weldment"),
    ("Cartridge (sleeve + disc)", cart, "#b8673a", -900, "Bearing module"),
    ("Cartridge weld", cart_weld, "#c99a3c", -900, "Bearing module"),
    ("Cartridge screws 12 × M16, recessed", cart_screws, "#3c3f44", -900, "Bearing module"),
    ("29328N housing washer", hw29, "#4f8a8b", -1000, "Bearing module"),
    ("Rear grease seal", grease_seal, "#2b2f33", -900, "Bearing module"),
    ("Spindle Ø140", shaft, "#c7ccd1", -1250, "Bearing module"),
    ("Front 23228", b23f, "#6aa368", -1250, "Bearing module"),
    ("29328N shaft washer + rollers", sw29, "#4f8a8b", -1250, "Bearing module"),
    ("Spacer sleeve", spacer, "#9aa0a6", -1250, "Bearing module"),
    ("Rear 23228", b23r, "#6aa368", -1250, "Bearing module"),
    ("Rear KM28 nut", nut_r, "#7d8288", -1250, "Bearing module"),
    ("Wear sleeve Ø170", wear, "#d0a060", -1250, "Bearing module"),
    ("Front cover", cover, "#9c5530", -1550, "Bearing module"),
    ("Lip seals ×3", seals, "#2b2f33", -1550, "Bearing module"),
    ("Grease lantern rings ×2", lanterns, "#d9c24a", -1550, "Bearing module"),
    ("Cover shims", shim, "#d9c24a", -1480, "Bearing module"),
    ("Cover screws", cover_screws, "#3c3f44", -1550, "Bearing module"),
    ("Front adapter + labyrinth", adapter, "#aab0b6", -1900, "Bearing module"),
    ("End plate + screws", end_plate.union(adapter_screws), "#7d8288", -2050, "Bearing module"),
    ("Rear plate + bearing hub", rp, "#7a6aa8", 350, "Rear plate + drive"),
    ("Hub grease cap", rp_cap, "#2b2f33", 350, "Rear plate + drive"),
    ("Rear plate screws 12 × M20 + 2 dowels", rp_bolts.union(dowels), "#3c3f44", 350, "Rear plate + drive"),
    ("Drive envelope Ø400 (motor TBD)", drive, "#2f6f9f", 700, "Rear plate + drive"),
]


def vol(a, b):
    try:
        return a.intersect(b).val().Volume() / 1000.0
    except Exception:
        return 0.0


checks = {
    "pipes_vs_drive_cm3": vol(pipes, drive),
    "pipes_vs_cart_cm3": vol(pipes, cart),
    "pipes_vs_rearplate_cm3": vol(pipes, rp),
    "pipes_vs_ring2_cm3": vol(pipes, ring2),
    "shaft_vs_cart_cm3": vol(shaft, cart),
    "shaft_vs_ring1_cm3": vol(shaft, ring1),
    "rear23228_vs_rp_cm3": vol(b23r, rp),
    "spacer_vs_cart_cm3": vol(spacer, cart),
    "drive_vs_shaft_cm3": vol(drive, shaft),
    "cart_vs_ring1_cm3": vol(cart, ring1),
    "cover_vs_adapter_cm3": vol(cover, adapter),
    "x_drive_rear": x_rp1 + L_drive,
}
print(json.dumps({k: round(v, 2) for k, v in checks.items()}, indent=1))

SUPPLIER = {}
out = []
assy = cq.Assembly(name="spindle_mount_revD")
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
    if name.startswith("Drive envelope"):
        kg = 0.0
    if "seal" in name.lower() and "grease tube" not in name.lower():
        kg = round(kg * 0.2, 1)
    out.append({"name": name, "color": col, "dx": dx, "group": grp, "pos": pos, "idx": idx, "kg": kg})
    safe = "".join(ch if ch.isalnum() else "_" for ch in name)
    assy.add(wp, name=safe, color=cq.Color(*[int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
    print(f"{grp:20s} {name:40s} {kg:7.1f}")
assy.export("/home/claude/cad/spindle_mount_revD.step")
json.dump({"parts": out, "checks": checks}, open("/home/claude/cad/mesh4.json", "w"), separators=(",", ":"))
