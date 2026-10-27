"""Adds the cutterhead motor to the option-A bulkhead model in two mounting variants.
plate : motor bolted to a second welded plate, flexible coupling to the spindle
bell  : motor bolted to a bell housing on the cartridge rear face, sliding spline sleeve
Motor = HMB100 ENVELOPE placeholder (478 axial, Ø502 drum), not supplier geometry.
"""
import json, math
import cadquery as cq
from mount_geom import *  # noqa

BC_motor = 380.0


def motor_at(x0, shaft_len=75):
    m = (ring(x0, x0 + 25, 0, 220)            # mounting flange Ø440
         .union(ring(x0 + 25, x0 + 70, 0, 130))  # shaft boss
         .union(ring(x0 + 70, x0 + 340, 0, 251))  # main drum Ø502
         .union(ring(x0 + 340, x0 + 478.3, 0, 160)))  # valve housing
    m = holes_x(m, x0 - 1, 27, BC_motor, 22, 12)
    shaft = ring(x0 - shaft_len, x0, 0, 50)
    return m, shaft


def weld_pair(x0, x1, leg):
    a = revolve([(x0, r(SH_ID)), (x0 - leg, r(SH_ID)), (x0, r(SH_ID) - leg)])
    b = revolve([(x1, r(SH_ID)), (x1 + leg, r(SH_ID)), (x1, r(SH_ID) - leg)])
    return a.union(b)


# slurry feed / return, straight runs at the bulkhead port positions (rev-A routing)
pipes = None
for ang in (40, -40):
    a = math.radians(ang)
    t = (cq.Workplane("YZ").workplane(offset=x_bh1).center(252 * math.cos(a), 252 * math.sin(a))
         .circle(76.1 / 2).circle(65 / 2).extrude(SH_x1 - x_bh1))
    pipes = t if pipes is None else pipes.union(t)

# ---------- variant 1: welded motor plate + flexible coupling ----------
mp0, mp1 = 600.0, 625.0
motor_plate = ring(mp0, mp1, 140, r(SH_ID))
motor_plate = holes_x(motor_plate, mp0 - 1, 27, BC_motor, 20, 12)
for ang in (40, -40):
    a = math.radians(ang)
    motor_plate = motor_plate.cut(cq.Workplane("YZ").workplane(offset=mp0 - 1)
                                  .center(252 * math.cos(a), 252 * math.sin(a)).circle(40).extrude(27))
mp_welds = weld_pair(mp0, mp1, 8)
coupling = ring(500, 545, 70, 115).union(ring(545, 550, 80, 115)).union(ring(550, 595, 50, 115))
motor1, mshaft1 = motor_at(mp1)
v1_bolts = bolts_x(mp0 - 0.0, mp1 - mp0 + 25, BC_motor, 20, 12, 30, 12, head_at_start=True)

# ---------- variant 2: bell housing on the cartridge rear face ----------
bh_x0 = x_rear
bell = (ring(bh_x0, bh_x0 + 20, 100, 165)
        .union(ring(bh_x0 + 20, bh_x0 + 100, 130, 150))
        .union(ring(bh_x0 + 100, bh_x0 + 120, 130, 220)))
bell = holes_x(bell, bh_x0 - 1, 22, 290, 13, 12, phase=15)
bell = holes_x(bell, bh_x0 + 99, 22, BC_motor, 22, 12)
spline = ring(500, 529, 70, 95).union(ring(529, 589, 50, 95))
motor2, mshaft2 = motor_at(bh_x0 + 120, shaft_len=bh_x0 + 120 - 529)
v2_bolts = (bolts_x(bh_x0 + 20, 45, 290, 12, 12, 18, 8, phase=15, head_at_start=False)
            .union(bolts_x(bh_x0 + 100, 45, BC_motor, 20, 12, 30, 12)))

common = [
    ("Shield shell (stub)", shell, "#8a8f94"),
    ("Bulkhead, 50 mm", bulkhead, "#5f86a8"),
    ("Bulkhead welds", welds, "#c99a3c"),
    ("Bearing cartridge", cartridge, "#b8673a"),
    ("Front cover + seals", cover, "#9c5530"),
    ("Preload springs", springs, "#d9c24a"),
    ("23228 radial bearing", brg23, "#6aa368"),
    ("29328N thrust bearing", brg29, "#4f8a8b"),
    ("Spindle + adapter", shaft, "#c7ccd1"),
    ("Spacer sleeve + KM28 locknut", locknut, "#7d8288"),
    ("Flange bolts 12 x M16", flange_bolts, "#3c3f44"),
    ("Cover bolts 12 x M10", cover_bolts, "#3c3f44"),
    ("Slurry pipes, straight (rev A)", pipes, "#e0e4e8"),
]
plate = [
    ("Motor plate, 25 mm welded", motor_plate, "#7a6aa8"),
    ("Motor plate welds", mp_welds, "#c99a3c"),
    ("Flexible coupling", coupling, "#a8a24f"),
    ("Motor (HMB100 envelope)", motor1, "#2f6f9f"),
    ("Motor shaft", mshaft1, "#c7ccd1"),
    ("Motor bolts 12 x M20", v1_bolts, "#3c3f44"),
]
bellset = [
    ("Bell housing", bell, "#7a6aa8"),
    ("Spline sleeve", spline, "#a8a24f"),
    ("Motor (HMB100 envelope)", motor2, "#2f6f9f"),
    ("Motor shaft", mshaft2, "#c7ccd1"),
    ("Bell + motor bolts", v2_bolts, "#3c3f44"),
]


def clash(a, b):
    try:
        return a.intersect(b).val().Volume()
    except Exception:
        return 0.0


report = {}
for tag, mot, x0 in (("plate", motor1, mp1), ("bell", motor2, bh_x0 + 120)):
    report[tag] = {
        "motor_front_x": x0, "motor_rear_x": round(x0 + 478.3, 1),
        "pipe_clash_cm3": round(clash(pipes, mot) / 1000, 1),
    }
report["plate"]["plate_pipe_clash_cm3"] = round(clash(pipes, motor_plate) / 1000, 1)
print(json.dumps(report, indent=1))

out = []
SUPPLIER = {"Motor (HMB100 envelope)": 144.0}
for variant, plist in (("common", common), ("plate", plate), ("bell", bellset)):
    assy = cq.Assembly(name=f"spindle_mount_{variant}")
    for name, wp, col in plist:
        pos, idx = [], []
        for f in wp.val().Faces():
            vs, tris = f.tessellate(0.15, 0.25)
            base = len(pos) // 3
            for v in vs:
                pos += [round(v.x, 1), round(v.y, 1), round(v.z, 1)]
            for t in tris:
                idx += [t[0] + base, t[1] + base, t[2] + base]
        kg = SUPPLIER.get(name, round(wp.val().Volume() * 7.85e-6, 1))
        out.append({"name": name, "color": col, "variant": variant, "pos": pos, "idx": idx, "kg": kg})
        assy.add(wp, name=name.replace(" ", "_").replace(",", "").replace("+", "and").replace("(", "").replace(")", ""),
                 color=cq.Color(*[int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
        print(f"{variant:6s} {name:32s} {kg:7.1f} kg")
    if variant != "common":
        full = cq.Assembly(name=f"spindle_mount_motor_{variant}")
        for name, wp, col in common + plist:
            full.add(wp, name=name.replace(" ", "_").replace(",", "").replace("+", "and").replace("(", "").replace(")", ""),
                     color=cq.Color(*[int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
        full.export(f"/home/claude/cad/spindle_mount_motor_{variant}.step")

json.dump({"parts": out, "report": report}, open("/home/claude/cad/mesh2.json", "w"), separators=(",", ":"))
