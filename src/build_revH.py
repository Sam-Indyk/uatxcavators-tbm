"""DN600 spindle mount + cutterhead, rev H: rev G layout, simplified for manufacture.
  1. Keyless: head on a 140 x 190 locking assembly (no splines); drive end plain Ø130 for a vendor shrink disc.
  2. Cartridge = one seamless tube (323.9 x 60 stock, ID 204 = 29328 housing shoulder as rolled) + split flange
     (2 half rings in a groove). Thrust passes tube land -> flange lip -> ring 1 seat by contact. No weld on the cartridge.
  3. Cutterhead: one waterjet spider plate (arms + centre in one piece) + 8 flat gussets (tab-and-slot) + LA hub ring
     + journal sleeve. Removable centre cap over the locking-assembly screws.
  Grease points all on the tube OD behind ring 1; ring 1 has no drillings except bolts, dowels, pipes and taps.
Axis +X rearward, X = 0 at ring 1 front face. Units mm. Visualisation model; Fusion 360 is the model of record.
"""
import paths  # noqa: F401  (UTF-8 stdout, output folders)
import json, math
import cadquery as cq
import build_opts as bo

r = lambda d: d / 2.0
ring, revolve, cyl_x, cyl_r, holes, screws, dowels = bo.ring, bo.revolve, bo.cyl_x, bo.cyl_r, bo.holes, bo.screws, bo.dowels
SH_ID, SH_OD = bo.SH_ID, bo.SH_OD

# ---------------- positions (bearing stack as rev G, + Ø190 washer backing ring) ----------------
T_R1, CB = 110.0, 35.0                      # counterbore = flange thickness; ring web 75 under the seat
L = 400.0
x23f = 70.0; c23f = x23f + 44
x_col = x23f + 88                          # collar 158..173
x_bk = x_col + 15                          # backing ring 173..188 (29328 da min 185)
x29 = x_bk + 15                            # 29328N 188..248
x_sh = x29 + 60                            # housing shoulder 248..278 (stock ID 204, Da max 208)
x23r = c23f + L - 44                       # 470
x_nut = x23r + 88                          # 558
x_rear = x_nut + 25 + 32                   # 615
R_TUBE, R_GRV, LAND = 159.0, 148.0, 20.0   # tube OD 318, groove root Ø296, land x0..20, groove x20..40
R_REC = 137.0                               # carrier recess / flange OD Ø274
X_ARM_B = -133.0; X_ARM_F = X_ARM_B - 50.8 # spider plate
X_LA0, X_LA1 = -133.0, -83.0               # locking assembly / hub ring
X_SL1 = 70.0                               # journal sleeve rear face = front 23228 inner ring
SH_X0 = X_ARM_B + 5.0; SH_X1 = SH_X0 + 1285.0
bo.SH_X0, bo.SH_X1, bo.T_R1 = SH_X0, SH_X1, 110.0
R_PIPE = 245.0
ARM_ANGS = [i * 45.0 for i in range(8)]


def rotx(wp, ang):
    return wp.rotate((0, 0, 0), (1, 0, 0), ang)


def sector(x0, x1, r0, r1, a_mid, half):
    """annular sector between r0 and r1, centred on angle a_mid (deg), +-half deg"""
    pts = [(0, 0)] + [(1.6 * r1 * math.cos(math.radians(a_mid - half + 2 * half * i / 16)),
                       1.6 * r1 * math.sin(math.radians(a_mid - half + 2 * half * i / 16))) for i in range(17)]
    w = cq.Workplane("YZ").workplane(offset=x0).polyline(pts).close().extrude(x1 - x0)
    return w.intersect(ring(x0, x1, r0, r1))


# ---------------- shell weldment ----------------
shell = ring(SH_X0, SH_X1, r(SH_ID), r(SH_OD))
r1 = revolve([(0, 200), (0, r(SH_ID) - 0.5), (T_R1, r(SH_ID) - 0.5), (T_R1, 159.25), (CB, 159.25), (CB, 200)])
r1 = holes(r1, CB - 1, 26, 370, 10.2, 16, phase=11.25)                       # M12 tapped into the seat
for a in (0, 180):
    r1 = r1.cut(cyl_x(CB - 1, 27, 185, a, 16))                              # dowels
    r1 = r1.cut(cyl_x(-1, T_R1 + 2, R_PIPE, a, 77))                         # slurry pipes, flush
for a in (90, 270):
    r1 = r1.cut(cyl_x(-1, T_R1 + 2, 225, a, 12))                            # pressure taps, flush
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

# ---------------- cartridge tube (seamless 323.9 x 60, no weld) ----------------
cart = revolve([
    (0, R_REC), (0, R_TUBE), (LAND, R_TUBE), (LAND, R_GRV), (CB, R_GRV), (CB, R_TUBE), (x_rear, R_TUBE), (x_rear, 125),
    (465, 125), (465, 126), (x_sh + 30, 126), (x_sh + 30, 102), (x_sh, 102), (x_sh, 120.5), (x29, 120.5), (x29, 126),
    (x_col, 126), (x_col, 125), (10, 125), (10, R_REC),
])
cart = holes(cart, 10, 16, 262, 5.0, 12, phase=15)                         # seal carrier M6 tapped
for a in (90, 270):
    cart = cart.cut(cyl_x(x_sh - 1, 32, 111, a, 12))                        # housing-washer knock-outs
cart = holes(cart, x_rear - 25, 26, 280, 14.0, 12)                         # drive M16 tapped
for a in (15, 135, 255):
    cart = cart.cut(cyl_x(x_rear - 21, 22, 140, a, 16))                     # drive dowels
for a in (45, 135, 225, 315):
    cart = cart.cut(cyl_r(10, a, 146, 161, 16))                             # anti-rotation pins
cart = cart.cut(ring(70, 76, 154, 159.5))                                  # O-ring groove, static seal in ring 1 bore
# grease: seal purge (axial in the wall, plugged at the front), front 23228, 29328N, rear 23228 - all fed from behind ring 1
cart = cart.cut(cyl_x(6, 120, 142.5, 30, 5)).cut(cyl_r(125, 30, 140, 161, 5)).cut(cyl_r(27, 30, 124, 145, 5))
cart = cart.cut(cyl_r(118, 90, 120, 161, 6)).cut(cyl_r(221, 90, 118, 161, 6)).cut(cyl_r(c23f + L, 90, 120, 161, 8))
oring = ring(70.5, 75.5, 154.5, 159.2)
fittings = None
for x, a in ((125, 30), (118, 90), (221, 90), (c23f + L, 90)):
    f = cyl_r(x, a, R_TUBE, 176, 12).cut(cyl_r(x, a, R_TUBE - 1, 177, 5))
    fittings = f if fittings is None else fittings.union(f)

# ---------------- split flange (2 halves in the groove) ----------------
sfl = revolve([(0, 159.2), (0, 199.9), (CB, 199.9), (CB, R_GRV + 0.2), (LAND, R_GRV + 0.2), (LAND, 159.2)])
sfl = holes(sfl, -1, CB + 2, 370, 13.5, 16, phase=11.25)
for i in range(16):
    sfl = sfl.cut(cyl_x(-1, 14, 185, 11.25 + 22.5 * i, 20))               # recessed heads
for a in (0, 180):
    sfl = sfl.cut(cyl_x(-1, CB + 2, 185, a, 16))                           # dowel holes
for a in (45, 135, 225, 315):
    sfl = sfl.cut(cyl_r(10, a, 146, 201, 16))                               # pin holes
tang = None
for z in (172, -172):
    s = cq.Workplane("XZ").workplane(offset=-20).center(15, z).circle(5).extrude(40)       # M10 across the kerf, along Y
    s = s.union(cq.Workplane("XZ").workplane(offset=-28).center(15, z).circle(8).extrude(8))
    tang = s if tang is None else tang.union(s)
sfl = sfl.cut(tang)
kerf = cq.Workplane("XY").box(CB + 4, 3.0, 420).translate((CB / 2, 0, 0))
sfl = sfl.cut(kerf)
pins = None
for a in (45, 135, 225, 315):
    p = cyl_r(10, a, 146, 199.5, 16)
    pins = p if pins is None else pins.union(p)

# ---------------- seal carrier (flush) ----------------
carrier = revolve([(0, 86), (0, R_REC - 0.5), (9.4, R_REC - 0.5), (9.4, 124.8), (70, 124.8), (70, 112), (69, 112), (69, 100), (8, 100), (8, 86)])
carrier = carrier.cut(ring(-1, 8, 101, 109)).cut(ring(-1, 8, 115, 123))
carrier = holes(carrier, -1, 12, 262, 6.6, 12, phase=15)
carrier = holes(carrier, -1, 3.4, 262, 12, 12, phase=15)                    # countersunk heads, flush
carrier = carrier.cut(cyl_r(27, 30, 99, 126, 6))
seals = ring(8, 23, 85.1, 100).union(ring(31, 46, 85.1, 100)).union(ring(54, 69, 85.1, 100))
lant = ring(23, 31, 86, 100).union(ring(46, 54, 86, 100))
shim = ring(9.4, 10, 126, R_REC - 1)
carrier_screws = screws(3.3, 20, 262, 6, 12, 12, 3.3, phase=15)

# ---------------- spindle + bearings ----------------
shaft = revolve([(X_LA0, 0), (X_LA0, 70), (x_col, 70), (x_col, 82.5), (x_bk, 82.5), (x_bk, 70),
                 (x_nut + 25, 70), (x_nut + 25, 65), (x_rear + 92, 65), (x_rear + 92, 0)])
shaft = shaft.cut(cyl_x(X_LA0 - 1, 61, 0, 0, 26))                          # M30 pull / push-off thread
backing = ring(x_bk, x29, 70, 95)
hw = ring(x29 + 44, x29 + 60, 90, 119.8)
sw = ring(x29, x29 + 22, 70, 112).union(revolve([(x29 + 22, 82), (x29 + 22, 110), (x29 + 44, 118), (x29 + 44, 90)]))
spacer = ring(x29 + 22, x23r, 70, 80)
nut = ring(x_nut, x_nut + 25, 70, 95)

# ---------------- cutterhead ----------------
R_ARM_IN, R_ARM_OUT, W_ARM = 150.0, 310.0, 76.0
TABS = ((190.0, 220.0), (245.0, 275.0))


def arm(ang):
    return rotx(cq.Workplane("YZ").workplane(offset=X_ARM_F).center((R_ARM_IN + R_ARM_OUT) / 2, 0)
                .rect(R_ARM_OUT - R_ARM_IN, W_ARM).extrude(X_ARM_B - X_ARM_F), ang)


def gusset(ang, t=25.0, with_tabs=True):
    g = (cq.Workplane("XY").polyline([(X_ARM_B, 170), (X_ARM_B, 290), (-8, 175), (-8, 125), (X_LA1, 125), (X_LA1, 170)])
         .close().extrude(t).translate((0, 0, -t / 2)))
    if with_tabs:
        for a, b in TABS:
            g = g.union(cq.Workplane("XY").center((X_ARM_F + X_ARM_B) / 2, (a + b) / 2)
                        .rect(X_ARM_B - X_ARM_F, b - a).extrude(t).translate((0, 0, -t / 2)))
    return rotx(g, ang)


def slots(ang):
    s = None
    for a, b in TABS:
        w = (cq.Workplane("XY").center((X_ARM_F + X_ARM_B) / 2, (a + b) / 2)
             .rect(X_ARM_B - X_ARM_F + 2, b - a + 0.4).extrude(25.4).translate((0, 0, -12.7)))
        s = w if s is None else s.union(w)
    return rotx(s, ang)


def bit(c, ang):
    z0 = W_ARM / 2 - 12.0
    holder = cq.Workplane("YZ").workplane(offset=X_ARM_F - 20).center(c, z0).rect(30, 24).extrude(20)
    trap = (cq.Workplane("XY").workplane(offset=z0 - 7)
            .polyline([(X_ARM_F - 20, c - 11), (X_ARM_F - 20, c + 11), (X_ARM_F - 42, c + 6.35), (X_ARM_F - 42, c - 6.35)])
            .close().extrude(14))
    return rotx(holder, ang), rotx(trap, ang)


tracks = [(315.0 - 6.35, a, True) for a in (0, 3, 5)]
tracks += [(315.0 - 6.35 - 12.7 * k, (k * 3 + 1) % 8, False) for k in range(1, 22)]

# centre cap outline: R135, cut back to R118 at arm 0 and R112 at arm 3 so no holder straddles the cap edge
X_CAP1 = X_ARM_F + 30.0
cap_outline = ring(X_ARM_F, X_CAP1, 0, 135).cut(sector(X_ARM_F - 1, X_CAP1 + 1, 118, 140, 0, 22.5)).cut(
    sector(X_ARM_F - 1, X_CAP1 + 1, 112, 140, 135, 22.5))

spider = ring(X_ARM_F, X_ARM_B, 100, 170)
for a in ARM_ANGS:
    spider = spider.union(arm(a))
spider = spider.cut(cap_outline)                                           # 30 deep pocket
spider = holes(spider, X_CAP1, 16, 216, 6.8, 8, phase=22.5)               # cap screws M8
for a in ARM_ANGS:
    spider = spider.cut(slots(a))
gussets = None
for a in ARM_ANGS:
    gussets = gusset(a) if gussets is None else gussets.union(gusset(a))
hubring = ring(X_LA0, X_LA1, 95, 170)
sleeve = revolve([(X_LA1, 70), (X_LA1, 125), (-8, 125), (-8, 85), (X_SL1, 85), (X_SL1, 70)])
sleeve = sleeve.union(ring(-8, 6, 103, 107)).union(ring(-8, 6, 117, 121))   # labyrinth rings
la = ring(X_LA0, X_LA1, 70, 95).union(screws(X_LA0, 35, 165, 12, 12, 18, 10))

cap = holes(holes(cap_outline, X_ARM_F - 1, 32, 216, 9, 8, phase=22.5), X_ARM_F - 1, 5.5, 216, 16, 8, phase=22.5)
cap = cap.union(revolve([(X_ARM_F, 0), (X_ARM_F, 24), (X_ARM_F - 25, 0)]))
cap_screws = screws(X_ARM_F + 4.5, 39.5, 216, 8, 8, 16, 4.5, phase=22.5)

holders = carbide = None
for c, ai, g in tracks:
    h, t = bit(c, ARM_ANGS[ai])
    holders = h if holders is None else holders.union(h)
    carbide = t if carbide is None else carbide.union(t)

dparts, drv = bo.drive_parts(x_rear)

parts = [
    ("Shield shell (1285)", shell, "#8a8f94", 0, "Shell weldment"),
    ("Ring 1, 110 thk, Ø400 × 35 counterbore, Ø318.5 bore", r1, "#5f86a8", 0, "Shell weldment"),
    ("Ring 1 weld, 14 mm front fillet", weld, "#c99a3c", 0, "Shell weldment"),
    ("Slurry pipes, flush at plate, R245, 12 + 6", pipes, "#e0e4e8", 0, "Shell weldment"),
    ("Pipe saddles", sad, "#5f86a8", 0, "Shell weldment"),
    ("Pressure tap tubes, flush", taps, "#e0e4e8", 0, "Shell weldment"),
    ("Cartridge: seamless tube 323.9 × 60, no weld", cart, "#b8673a", -900, "Bearing module"),
    ("Split flange, 2 halves in tube groove", sfl, "#d08a4a", -900, "Bearing module"),
    ("Split-joint screws 2 × M10", tang, "#3c3f44", -900, "Bearing module"),
    ("Anti-rotation pins 4 × Ø16, flange to tube", pins, "#e0a030", -900, "Bearing module"),
    ("Flange screws 16 × M12, recessed", screws(13, 45, 370, 12, 16, 18, 12, phase=11.25), "#3c3f44", -900, "Bearing module"),
    ("Dowels 2 × Ø16, flange to ring 1", dowels(5, 55, 370, (0, 180)), "#e0a030", -900, "Bearing module"),
    ("Static O-ring, tube in ring 1 bore", oring, "#2b2f33", -900, "Bearing module"),
    ("Grease fittings ×4 (behind ring 1)", fittings, "#d9c24a", -900, "Bearing module"),
    ("Seal carrier (flush)", carrier, "#9c5530", -1250, "Bearing module"),
    ("Lip seals ×3", seals, "#2b2f33", -1250, "Bearing module"),
    ("Grease lantern rings ×2", lant, "#d9c24a", -1250, "Bearing module"),
    ("Carrier shims", shim, "#d9c24a", -1200, "Bearing module"),
    ("Carrier screws 12 × M6 CSK", carrier_screws, "#3c3f44", -1250, "Bearing module"),
    ("29328N housing washer", hw, "#4f8a8b", -1000, "Bearing module"),
    ("Spindle Ø140, plain ends", shaft, "#c7ccd1", -1500, "Bearing module"),
    ("Front 23228", bo.sph23(x23f), "#6aa368", -1500, "Bearing module"),
    ("Backing ring Ø190 (29328 da min 185)", backing, "#9aa0a6", -1500, "Bearing module"),
    ("29328N shaft washer + rollers", sw, "#4f8a8b", -1500, "Bearing module"),
    ("Spacer sleeve", spacer, "#9aa0a6", -1500, "Bearing module"),
    ("Rear 23228", bo.sph23(x23r), "#6aa368", -1500, "Bearing module"),
    ("Rear KM28 nut", nut, "#7d8288", -1500, "Bearing module"),
    ("Spider plate 50.8, one waterjet piece", spider, "#8c6bb1", -2300, "Cutterhead"),
    ("Gussets ×8, 25 thk, tab-and-slot", gussets, "#a58ad0", -2300, "Cutterhead"),
    ("LA hub ring 50.8 (Ø340 × Ø190)", hubring, "#7a5aa1", -2300, "Cutterhead"),
    ("Journal sleeve Ø170 (seal running surface)", sleeve, "#d0a060", -2300, "Cutterhead"),
    ("Locking assembly 140 × 190 × 50", la, "#3f6f8f", -2300, "Cutterhead"),
    ("Bit holders ×24", holders, "#5a4a7a", -2300, "Cutterhead"),
    ("Trapezoid carbide drag bits ×24", carbide, "#e8d36a", -2300, "Cutterhead"),
    ("Centre cap 30 thk + cone (removable)", cap, "#6a4a91", -2650, "Cutterhead"),
    ("Cap screws 8 × M8 CSK", cap_screws, "#3c3f44", -2650, "Cutterhead"),
] + dparts

V = bo.vol
head = spider.union(gussets).union(hubring).union(sleeve)
checks = {
    "head_vs_shell": V(head.union(holders).union(carbide), shell), "head_vs_ring1": V(head, r1),
    "head_vs_cart": V(head, cart), "head_vs_flange": V(head, sfl), "head_vs_carrier": V(head, carrier),
    "head_vs_carrier_screws": V(head, carrier_screws), "gussets_vs_spider": V(gussets, spider),
    "gussets_vs_hub": V(gussets, hubring.union(sleeve)), "spider_vs_cap": V(spider, cap), "bits_vs_cap": V(holders.union(carbide), cap),
    "bits_vs_spider": V(holders.union(carbide), spider), "la_vs_hub": V(la, hubring), "la_vs_shaft": V(la, shaft),
    "la_vs_cap": V(la, cap), "pipes_vs_head": V(pipes, head), "pipes_vs_drive": V(pipes, drv), "pipes_vs_cart": V(pipes, cart),
    "cart_vs_ring1": V(cart, r1), "flange_vs_ring1": V(sfl, r1), "flange_vs_cart": V(sfl, cart), "pins_vs_cart": V(pins, cart),
    "pins_vs_flange": V(pins, sfl), "tang_vs_flange": V(tang, sfl), "carrier_vs_cart": V(carrier, cart),
    "shaft_vs_cart": V(shaft, cart), "shaft_vs_sleeve": V(shaft, sleeve), "drive_vs_shaft": V(drv, shaft),
    "fittings_vs_ring1": V(fittings, r1), "fittings_vs_pipes": V(fittings, pipes),
    "head_front_x": X_ARM_F - 42, "shield_front_x": SH_X0, "shield_rear_x": SH_X1, "drive_rear_x": x_rear + bo.L_drive,
    "overall": x_rear + bo.L_drive - (X_ARM_F - 42), "ring1_depth": -SH_X0, "legs": SH_X1 - T_R1,
    "chamber_depth": -X_ARM_B, "overhang_bearing_to_bits": c23f - (X_ARM_F - 42),
    "cap_bits": [round(c, 2) for c, ai, g in tracks if c + 15 <= 135],
}
print(json.dumps(checks))
bo.export("revH", parts, dict(x_r1=0.0, x_rear=x_rear, drive_rear=x_rear + bo.L_drive, cart=cart, shaft=shaft, r1=r1,
                              pipes=pipes, drv=drv, cover=carrier, adapter=head))
