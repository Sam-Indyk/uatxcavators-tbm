"""Spindle bearing cartridge + bulkhead mount — visualisation model.
Axis = +X rearward. X = 0 is the cartridge front face. Units mm.
Option A: 50 mm bulkhead welded in the shield, machined after welding,
cartridge flange bolted to its FRONT face (thrust in compression).
"""
import json, math
import cadquery as cq

# ---- parameters (same names as the Fusion parameter table) ----
D23, B23 = 250.0, 88.0          # Koyo 23228
D29, H29 = 240.0, 60.0          # Koyo 29328N
L, pocket = 350.0, 15.0
D_relief, D_lip, t_lip = 252.0, 200.0, 30.0
D_body, D_flange, t_flange = 330.0, 420.0, 30.0
BC_flange, BC_cover = 380.0, 290.0
x_relief = pocket + B23
x_seat29 = pocket + B23 / 2 + L - H29 / 2
x_lip = x_seat29 + H29
x_rear = x_lip + t_lip

# bulkhead / shield
SH_OD, SH_ID = 609.6, 584.2
t_bh = 50.0
x_bh0 = t_flange                 # bulkhead front face = flange rear face
x_bh1 = x_bh0 + t_bh
D_bh_bore = D_body + 2.0         # register bore for the cartridge body
SH_x0, SH_x1 = -260.0, 1150.0     # shell stub shown (not full 1285 length)
D_shaft = 140.0

AX = cq.Vector(1, 0, 0)


def revolve(pts):
    """pts are (x, r) pairs of a closed half-section; revolve about X."""
    wp = cq.Workplane("XY").polyline(pts).close()
    return wp.revolve(360, (0, 0, 0), (1, 0, 0))


def ring(x0, x1, ri, ro):
    return revolve([(x0, ri), (x1, ri), (x1, ro), (x0, ro)])


def holes_x(solid, x0, length, bc, dia, n, phase=0.0):
    """cut n axial holes (along X) on a bolt circle."""
    for i in range(n):
        a = math.radians(phase + 360.0 * i / n)
        y, z = bc / 2 * math.cos(a), bc / 2 * math.sin(a)
        cyl = cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(dia / 2).extrude(length)
        solid = solid.cut(cyl)
    return solid


def bolts_x(x0, length, bc, dia, n, head_d, head_h, phase=0.0, head_at_start=True):
    out = None
    for i in range(n):
        a = math.radians(phase + 360.0 * i / n)
        y, z = bc / 2 * math.cos(a), bc / 2 * math.sin(a)
        shank = cq.Workplane("YZ").workplane(offset=x0).center(y, z).circle(dia / 2).extrude(length)
        hx = x0 - head_h if head_at_start else x0 + length
        head = cq.Workplane("YZ").workplane(offset=hx).center(y, z).polygon(6, head_d).extrude(head_h)
        b = shank.union(head)
        out = b if out is None else out.union(b)
    return out


# ---------------- cartridge ----------------
r = lambda d: d / 2
cart_pts = [
    (0, r(D23)), (0, r(D_flange)), (t_flange, r(D_flange)), (t_flange, r(D_body)),
    (x_rear, r(D_body)), (x_rear, r(D_lip)), (x_lip, r(D_lip)), (x_lip, r(D29)),
    (x_seat29, r(D29)), (x_seat29, r(D_relief)), (x_relief, r(D_relief)), (x_relief, r(D23)),
]
cartridge = revolve(cart_pts)
cartridge = holes_x(cartridge, -1, t_flange + 2, BC_flange, 17.5, 12, phase=15)
cartridge = holes_x(cartridge, -1, 21, BC_cover, 8.5, 12, phase=0)
# O-ring groove on flange rear face (face seal to bulkhead)
cartridge = cartridge.cut(ring(t_flange - 4, t_flange + 1, r(D_body) + 8, r(D_body) + 14))

# ---------------- bulkhead (option A) ----------------
bulkhead = ring(x_bh0, x_bh1, r(D_bh_bore), r(SH_ID))
bulkhead = holes_x(bulkhead, x_bh0 - 1, 33, BC_flange, 14.0, 12, phase=15)   # tapped M16, 32 deep (blind)
# slurry feed / return Ø78 at r=252, ±40° from top; sensor port Ø20 at bottom
for ang, d in [(40, 78.0), (-40, 78.0), (180, 20.0), (160, 20.0)]:
    a = math.radians(ang)
    rr = 252.0 if d > 30 else 245.0
    cyl = cq.Workplane("YZ").workplane(offset=x_bh0 - 1).center(rr * math.cos(a), rr * math.sin(a)).circle(d / 2).extrude(t_bh + 2)
    bulkhead = bulkhead.cut(cyl)

# fillet welds bulkhead->shell, both faces (10 mm leg, triangular ring)
def weld_ring(xface, sign):
    return revolve([(xface, r(SH_ID)), (xface + sign * 10, r(SH_ID)), (xface, r(SH_ID) - 10)])
welds = weld_ring(x_bh0, -1).union(weld_ring(x_bh1, +1))

# ---------------- shield shell stub ----------------
shell = ring(SH_x0, SH_x1, r(SH_ID), r(SH_OD))

# ---------------- front cover ----------------
cover = revolve([
    (-25, r(142)), (-25, r(330)), (0, r(330)), (0, r(250) - 0.1),
    (5, r(250) - 0.1), (5, r(170)), (-10, r(170)),  # seal housing bore
    (-10, r(142)),
])
cover = holes_x(cover, -26, 27, BC_cover, 11, 12)

springs = None
for i in range(8):
    a = math.radians(22.5 + 45 * i)
    s = (cq.Workplane("YZ").workplane(offset=5).center(118 * math.cos(a), 118 * math.sin(a))
         .circle(8).circle(4).extrude(10))
    springs = s if springs is None else springs.union(s)

# ---------------- bearings (simplified envelopes) ----------------
b23_x0 = pocket
brg23 = (ring(b23_x0, b23_x0 + B23, r(230), r(D23))                   # outer ring
         .union(ring(b23_x0, b23_x0 + B23, r(D_shaft), r(162)))       # inner ring
         .union(ring(b23_x0 + 8, b23_x0 + B23 - 8, r(164), r(228))))  # roller band
x29 = x_seat29
brg29 = (ring(x29, x29 + 22, r(D_shaft), 112)                        # shaft washer (front)
         .union(revolve([(x29 + 22, 82), (x29 + 22, 110), (x29 + 44, 118), (x29 + 44, 90)]))  # rollers
         .union(ring(x29 + 44, x29 + H29, 86, r(D29))))               # housing washer (rear, on lip)

# ---------------- spindle ----------------
shaft = (ring(-150, x_rear + 60, 0, r(D_shaft))
         .union(ring(b23_x0 + B23, x29, 0, r(155)))                   # collar between bearings
         .union(ring(-185, -150, 0, r(300))))                         # front adapter flange (16 x M20 to head)
shaft = holes_x(shaft, -186, 37, 250, 21, 16)
locknut = ring(x29 + 22, x29 + 60, r(D_shaft), 80).union(ring(x29 + 60, x29 + 80, r(D_shaft), 95))  # spacer sleeve + nut

# ---------------- fasteners ----------------
flange_bolts = bolts_x(0, t_flange + 30, BC_flange, 16, 12, 24, 10, phase=15)
cover_bolts = bolts_x(-25, 45, BC_cover, 10, 12, 16, 7)

parts = [
    ("Shield shell (stub)", shell, "#8a8f94"),
    ("Bulkhead, 50 mm", bulkhead, "#5f86a8"),
    ("Bulkhead welds", welds, "#c99a3c"),
    ("Bearing cartridge", cartridge, "#b8673a"),
    ("Front cover + seals", cover, "#9c5530"),
    ("Preload springs", springs, "#d9c24a"),
    ("23228 radial bearing", brg23, "#6aa368"),
    ("29328N thrust bearing", brg29, "#4f8a8b"),
    ("Spindle + adapter", shaft, "#c7ccd1"),
    ("KM28 locknut", locknut, "#7d8288"),
    ("Flange bolts 12 x M16", flange_bolts, "#3c3f44"),
    ("Cover bolts 12 x M10", cover_bolts, "#3c3f44"),
]

