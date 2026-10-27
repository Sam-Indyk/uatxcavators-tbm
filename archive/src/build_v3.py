"""DN600 spindle mount, rev C: three bearings, welded rings + bolted plates.
Axis = +X rearward, X = 0 at cartridge front face. Units mm. Visualisation model only;
Fusion 360 remains the model of record.

Bearings (front -> rear):
  23228   140x250x88  radial, locates shaft forward (reverse load)
  29328N  140x240x60  thrust only, housing washer has radial clearance
  22318 E  90x190x64  radial, floats axially in its seat
"""
import json, math
import cadquery as cq

# ---------------- parameters ----------------
SH_OD, SH_ID = 609.6, 584.2
SH_X0, SH_X1 = -175.0, 1110.0          # 1285 shield

# cartridge
pocket = 15.0                           # cover spigot depth
B23, D23 = 88.0, 250.0
x23 = pocket                            # 23228 front face
collar_w = 15.0
x29 = x23 + B23 + collar_w              # 29328 front face (shaft washer)  = 118
H29, D29_seat = 60.0, 241.0             # housing washer seat, 0.5 mm radial clearance
t_sh, D_sh = 30.0, 196.0                # housing-washer shoulder (ID passes the 22318)
L = 300.0                               # 23228 centre -> 22318 centre
B18, D18 = 64.0, 190.0
x18 = x23 + B23 / 2 + L - B18 / 2       # 22318 front face
float_gap = 5.0
x_seat18 = x18 - float_gap
x_rear = x18 + B18 + float_gap
D_front, D_rear = 310.0, 250.0          # cartridge body ODs
D_fl, t_fl, BC_fl = 420.0, 30.0, 380.0
x_step = x29 + H29 + t_sh               # front/rear body change at shoulder

# bulkhead plate + ring 1
t_bp = 40.0
x_bp0, x_bp1 = t_fl, t_fl + 40.0        # 30 .. 70
t_ring = 40.0
x_r1 = x_bp1                            # ring 1: 70 .. 110
D_ring_id = 500.0
BC_ring = 542.0
D_plate = 576.0

# pipes / ports  (angle 0 = top, 180 = bottom)
R_pipe, D_pipe_hole = 218.0, 78.0

# motor side
x_cap1 = x_rear + 30.0                  # rear end cap
x_mp0 = 560.0                           # motor plate front face (sits on ring 2 rear face)
t_mp = 25.0
x_r2 = x_mp0 - t_ring                   # ring 2: 520 .. 560
x_mot = x_mp0 + t_mp                    # motor flange face 585


def revolve(pts):
    return cq.Workplane("XY").polyline(pts).close().revolve(360, (0, 0, 0), (1, 0, 0))


def ring(x0, x1, ri, ro):
    return revolve([(x0, ri), (x1, ri), (x1, ro), (x0, ro)])


def cyl_x(x0, length, rr, ang, dia):
    a = math.radians(ang)
    return (cq.Workplane("YZ").workplane(offset=x0)
            .center(rr * math.cos(a), rr * math.sin(a)).circle(dia / 2).extrude(length))


def holes_x(s, x0, length, bc, dia, n, phase=0.0, skip=()):
    for i in range(n):
        ang = phase + 360.0 * i / n
        if any(abs(((ang - k + 180) % 360) - 180) < 1 for k in skip):
            continue
        s = s.cut(cyl_x(x0, length, bc / 2, ang, dia))
    return s


def bolts(x_head, length, bc, dia, n, head_d, head_h, phase=0.0, forward_head=True):
    out = None
    for i in range(n):
        ang = math.radians(phase + 360.0 * i / n)
        y, z = bc / 2 * math.cos(ang), bc / 2 * math.sin(ang)
        if forward_head:
            sh = cq.Workplane("YZ").workplane(offset=x_head).center(y, z).circle(dia / 2).extrude(length)
            hd = cq.Workplane("YZ").workplane(offset=x_head - head_h).center(y, z).polygon(6, head_d).extrude(head_h)
        else:
            sh = cq.Workplane("YZ").workplane(offset=x_head - length).center(y, z).circle(dia / 2).extrude(length)
            hd = cq.Workplane("YZ").workplane(offset=x_head).center(y, z).polygon(6, head_d).extrude(head_h)
        b = sh.union(hd)
        out = b if out is None else out.union(b)
    return out


r = lambda d: d / 2.0

# ---------------- shell, rings, welds ----------------
shell = ring(SH_X0, SH_X1, r(SH_ID), r(SH_OD))


def weld_ring(x0, x1, leg):
    a = revolve([(x0, r(SH_ID)), (x0 - leg, r(SH_ID)), (x0, r(SH_ID) - leg)])
    b = revolve([(x1, r(SH_ID)), (x1 + leg, r(SH_ID)), (x1, r(SH_ID) - leg)])
    return a.union(b)


def make_ring(x0):
    rg = ring(x0, x0 + t_ring, r(D_ring_id), r(SH_ID))
    for ang in (0, 180):                                      # notches for the slurry pipes
        rg = rg.cut(cyl_x(x0 - 1, t_ring + 2, R_pipe, ang, 86))
    rg = holes_x(rg, x0 - 1, 31, BC_ring, 10.2, 16, phase=11.25)  # M12 tapped 30 deep
    return rg


ring1, ring2 = make_ring(x_r1), make_ring(x_r2)
welds1, welds2 = weld_ring(x_r1, x_r1 + t_ring, 10), weld_ring(x_r2, x_r2 + t_ring, 8)

# ---------------- bulkhead plate ----------------
plate = revolve([(x_bp0, r(D_front)), (x_bp0, r(D_plate)), (x_bp1 - 12, r(D_plate)),
                 (x_bp1, r(D_plate) - 12), (x_bp1, r(D_front))])
plate = holes_x(plate, x_bp0 - 1, t_bp + 2, BC_fl, 17.5, 12, phase=15)   # cartridge bolts, nuts on dry side
plate = holes_x(plate, x_bp0 - 1, t_bp + 2, BC_ring, 13.5, 16, phase=11.25)
for ang in (0, 180):
    plate = plate.cut(cyl_x(x_bp0 - 1, t_bp + 2, R_pipe, ang, D_pipe_hole))
for ang in (90, 270):
    plate = plate.cut(cyl_x(x_bp0 - 1, t_bp + 2, 235, ang, 20))         # pressure sensor ports
gasket = ring(x_bp1, x_bp1 + 1.5, 262, 280)                               # fibre gasket (shown 1.5 thk)

# ---------------- cartridge ----------------
cart = revolve([
    (0, r(D23)), (0, r(D_fl)), (t_fl, r(D_fl)), (t_fl, r(D_front)), (x_step, r(D_front)),
    (x_step, r(D_rear)), (x_rear, r(D_rear)), (x_rear, r(D18)), (x_seat18, r(D18)),
    (x_seat18, r(D_sh)), (x29 + H29, r(D_sh)), (x29 + H29, r(D29_seat)), (x29, r(D29_seat)),
    (x29, r(D23) + 1), (x23 + B23, r(D23) + 1), (x23 + B23, r(D23)),
])
cart = holes_x(cart, -1, t_fl + 2, BC_fl, 17.5, 12, phase=15)
cart = holes_x(cart, -1, 21, 290, 8.5, 12)                                 # cover M10
cart = holes_x(cart, x_rear - 20, 21, 222, 6.8, 8, phase=22.5)            # end cap M8
for ang in (0, 180):
    cart = cart.cut(cyl_x(-1, t_fl + 2, R_pipe, ang, 86))                 # flange scallops for pipes
cart = cart.cut(ring(t_fl - 3, t_fl + 1, 163, 169))                       # O-ring groove, flange to plate
for ang in (0, 180):                                                       # knock-out notches in shoulder
    cart = cart.cut(cyl_x(x29 + H29 - 1, t_sh + 2, 103, ang, 14))

# ---------------- covers ----------------
cover = revolve([(-40, 70.5), (-40, 165), (0, 165), (0, r(D23) - 0.2), (pocket - 1, r(D23) - 0.2),
                 (pocket - 1, 95), (-25, 95), (-25, 85), (-40, 85)])
cover = holes_x(cover, -41, 42, 290, 11, 12)
shims = ring(-0.0, 0.0 + 0.8, 140, 165)                                    # shim pack under cover (shown 0.8)
end_cap = revolve([(x_rear, 46), (x_rear, r(D_rear)), (x_rear + 15, r(D_rear)), (x_rear + 15, 60),
                   (x_cap1, 60), (x_cap1, 40.5), (x_rear + 15, 40.5)])
end_cap = holes_x(end_cap, x_rear - 1, 17, 222, 9, 8, phase=22.5)

# ---------------- bearings (simplified) ----------------
brg23 = (ring(x23, x23 + B23, 115, r(D23))
         .union(ring(x23, x23 + B23, 70, 81))
         .union(ring(x23 + 8, x23 + B23 - 8, 83, 113)))
brg29_shaft = (ring(x29, x29 + 22, 70, 112)
               .union(revolve([(x29 + 22, 82), (x29 + 22, 110), (x29 + 44, 118), (x29 + 44, 90)])))
brg29_house = ring(x29 + 44, x29 + H29, 90, r(D29_seat) - 0.5)
brg18 = (ring(x18, x18 + B18, 85, r(D18))
         .union(ring(x18, x18 + B18, 45, 55))
         .union(ring(x18 + 6, x18 + B18 - 6, 57, 83)))

# ---------------- spindle ----------------
x_sh1 = x18 - 12                     # end of Ø140 / start of Ø105 shoulder
shaft = revolve([
    (-200, 0), (-200, 65), (-45, 65), (-45, 70), (x23 + B23, 70), (x23 + B23, 82.5),
    (x29, 82.5), (x29, 70), (x_sh1, 70), (x_sh1, 52.5), (x18, 52.5), (x18, 45),
    (x_rear + 2, 45), (x_rear + 2, 40), (x_cap1 + 70, 40), (x_cap1 + 70, 0),
])                                    # Ø130 spline at the front, adapter separate
adapter = ring(-185, -150, 65, 150).union(ring(-150, -60, 65, 95))
adapter = holes_x(adapter, -186, 37, 250, 21, 16)
nut_front = ring(-25, x23, 70, 92)          # KM28
clip29 = ring(x29 + 22, x29 + 26, 70, 78)   # shaft retaining ring
nut18 = ring(x18 + B18, x18 + B18 + 18, 45, 60)  # KM18

# ---------------- coupling + motor ----------------
hub_s = ring(x_cap1 + 5, x_cap1 + 70, 40, 75)
sleeve = ring(x_cap1 + 15, x_cap1 + 150, 76, 115)
hub_m = ring(x_cap1 + 90, x_cap1 + 160, 50, 75)
motor_plate = ring(x_mp0, x_mp0 + t_mp, 100, r(D_plate))
motor_plate = holes_x(motor_plate, x_mp0 - 1, t_mp + 2, BC_ring, 13.5, 16, phase=11.25)
motor_plate = holes_x(motor_plate, x_mp0 - 1, t_mp + 2, 380, 22, 12)
for ang in (0, 180):
    motor_plate = motor_plate.cut(cyl_x(x_mp0 - 1, t_mp + 2, R_pipe, ang, 82))
for ang in (90, 270):                                                   # access / hose windows
    motor_plate = motor_plate.cut(cyl_x(x_mp0 - 1, t_mp + 2, 245, ang, 60))
motor = (ring(x_mot, x_mot + 25, 0, 220).union(ring(x_mot + 25, x_mot + 70, 0, 130))
         .union(ring(x_mot + 70, x_mot + 340, 0, 251)).union(ring(x_mot + 340, x_mot + 478.3, 0, 160)))
motor = holes_x(motor, x_mot - 1, 27, 380, 22, 12)
motor_shaft = ring(x_cap1 + 90, x_mot, 0, 50)

pipes = None
for ang in (0, 180):
    p = cyl_x(x_bp1, SH_X1 - x_bp1, R_pipe, ang, 76.1).cut(cyl_x(x_bp1 - 1, SH_X1 - x_bp1 + 2, R_pipe, ang, 65))
    pipes = p if pipes is None else pipes.union(p)

# ---------------- fasteners ----------------
b_cart = bolts(0, t_fl + t_bp + 20, BC_fl, 16, 12, 24, 10, phase=15)           # heads wet side, nuts dry
n_cart = bolts(x_bp1, 14, BC_fl, 16, 12, 24, 0.01, phase=15, forward_head=False)
b_plate = bolts(x_bp0, t_bp + 30, BC_ring, 12, 16, 18, 8, phase=11.25)
b_cover = bolts(-40, 58, 290, 10, 12, 16, 7)
b_motor = bolts(x_mp0 + t_mp + 35, 35 + t_mp + 30, BC_ring, 12, 16, 18, 8, phase=11.25, forward_head=False)
b_mot2 = bolts(x_mot + 25, 25 + t_mp + 5, 380, 20, 12, 30, 12, forward_head=False)

# ---------------- parts table ----------------
# (name, solid, colour, explode dx, group)
FWD = -1;  RWD = 1
parts = [
    ("Shield shell (1285)", shell, "#8a8f94", 0, "Shell weldment"),
    ("Ring 1, welded", ring1, "#5f86a8", 0, "Shell weldment"),
    ("Ring 2, welded", ring2, "#5f86a8", 0, "Shell weldment"),
    ("Ring welds", welds1.union(welds2), "#c99a3c", 0, "Shell weldment"),
    ("Bulkhead plate, 40", plate, "#3f6f99", -650, "Bulkhead module"),
    ("Fibre gasket", gasket, "#2b2f33", -560, "Bulkhead module"),
    ("Cartridge", cart, "#b8673a", -1050, "Bulkhead module"),
    ("Cartridge bolts + nuts", b_cart.union(n_cart), "#3c3f44", -1050, "Bulkhead module"),
    ("Plate-to-ring bolts", b_plate, "#3c3f44", -650, "Bulkhead module"),
    ("29328N housing washer", brg29_house, "#4f8a8b", -1350, "Bearings"),
    ("23228 radial", brg23, "#6aa368", -1750, "Bearings"),
    ("29328N shaft washer + rollers", brg29_shaft, "#4f8a8b", -1750, "Bearings"),
    ("22318 E radial (owned)", brg18, "#8ab35a", -1750, "Bearings"),
    ("Spindle", shaft, "#c7ccd1", -1750, "Spindle"),
    ("KM28 nut, circlip, KM18 nut", nut_front.union(clip29).union(nut18), "#7d8288", -1750, "Spindle"),
    ("Front adapter (on spline)", adapter, "#aab0b6", -2600, "Spindle"),
    ("Front cover + lip seal", cover, "#9c5530", -2150, "Bulkhead module"),
    ("Shim pack", shims, "#d9c24a", -2080, "Bulkhead module"),
    ("Cover bolts", b_cover, "#3c3f44", -2150, "Bulkhead module"),
    ("Rear end cap + seal", end_cap, "#9c5530", -1050 + 250, "Bulkhead module"),
    ("Coupling hub, spindle", hub_s, "#a8a24f", -1750, "Coupling"),
    ("Coupling sleeve", sleeve, "#bdb65a", 250, "Coupling"),
    ("Motor plate, 25 (windowed)", motor_plate, "#7a6aa8", 500, "Motor module"),
    ("Plate-to-ring 2 bolts", b_motor, "#3c3f44", 500, "Motor module"),
    ("Motor (HMB100 envelope)", motor, "#2f6f9f", 700, "Motor module"),
    ("Motor shaft + hub", motor_shaft.union(hub_m), "#c7ccd1", 700, "Motor module"),
    ("Motor bolts", b_mot2, "#3c3f44", 700, "Motor module"),
    ("Slurry pipes (straight, 12 + 6)", pipes, "#e0e4e8", 0, "Services"),
]

SUPPLIER = {"Motor (HMB100 envelope)": 144.0}


def clash(a, b):
    try:
        return a.intersect(b).val().Volume() / 1000.0
    except Exception:
        return 0.0


report = {
    "cartridge_length": x_rear, "L": L, "x18": x18, "x_rear": x_rear,
    "motor_front": x_mot, "motor_rear": round(x_mot + 478.3, 1),
    "pipe_motor_clash_cm3": round(clash(pipes, motor), 1),
    "pipe_cart_clash_cm3": round(clash(pipes, cart), 1),
    "pipe_ring_clash_cm3": round(clash(pipes, ring1.union(ring2)), 1),
    "shaft_cart_clash_cm3": round(clash(shaft, cart), 2),
    "brg18_vs_cart_cm3": round(clash(brg18, cart), 2),
}
print(json.dumps(report, indent=1))

out = []
assy = cq.Assembly(name="spindle_mount_revC")
for name, wp, col, dx, grp in parts:
    pos, idx = [], []
    for f in wp.val().Faces():
        vs, tris = f.tessellate(0.15, 0.25)
        base = len(pos) // 3
        for v in vs:
            pos += [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
        for t in tris:
            idx += [t[0] + base, t[1] + base, t[2] + base]
    kg = SUPPLIER.get(name, round(wp.val().Volume() * 7.85e-6, 1))
    if name == "Fibre gasket":
        kg = 0.2
    out.append({"name": name, "color": col, "dx": dx, "group": grp, "pos": pos, "idx": idx, "kg": kg})
    safe = "".join(ch if ch.isalnum() else "_" for ch in name)
    assy.add(wp, name=safe, color=cq.Color(*[int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
    print(f"{grp:16s} {name:34s} {kg:7.1f} kg")
assy.export("/home/claude/cad/spindle_mount_revC.step")
json.dump({"parts": out, "report": report}, open("/home/claude/cad/mesh3.json", "w"), separators=(",", ":"))
