"""Rev H assembly sequence (shop orientation) + mesh/STEP export for the viewer.
World frame of the viewer: +Y up, floor at y = 0. Machine axis +X rearward.
Group pose = rotation about world Z (th, degrees) + translation t of the machine origin.
  th = -90: front up (machine +X points down);  th = +90: rear up;  th = 0: horizontal.
"""
import json, math
import cadquery as cq
import build_revH_detail as M
from paths import STEP, VIEWER_DATA

FU, RU, H = -90.0, 90.0, 0.0


def pose(th, x, y, z=0.0):
    return {"th": th, "t": [x, y, z]}


UP = [0, 900, 0]
SHELL0 = pose(FU, 0, 1157)
groups = {
    # one common pivot, so groups that move together stay together mid-motion
    "shell": {"pivot": 300, "init": SHELL0},
    "tube": {"pivot": 300, "init": pose(FU, 1700, 765)},
    "rotor": {"pivot": 300, "init": pose(RU, 1050, 193)},
    "head": {"pivot": 300, "init": pose(RU, -1150, 184)},
    "cap": {"pivot": 300, "init": pose(FU, -1800, -154)},
}
MOD_IN = [pose(FU, 1700, 765 + 1600), pose(FU, 0, 1157 + 1600), SHELL0]
steps = []


def st(phase, title, text, add=None, remove=None, moves=None, focus=None, dur=1.6):
    steps.append({"phase": phase, "title": title, "text": text, "add": add or [], "remove": remove or [],
                  "moves": moves or {}, "focus": focus or [], "dur": dur})


P1, P2, P3, P4, P5, P6, P7 = ("1 · Shell weldment", "2 · Cutterhead weldment", "3 · Bearing module (bench)",
                              "4 · Module into the shell", "5 · Cutterhead onto the spindle", "6 · Drive", "7 · Thrust ring (launch)")
st(P1, "Shell on the table",
   "Shield shell Ø609.6 × 12.7 × 1,285. Both ends faced on the lathe first and the rear end counterbored Ø590.6 × 12 (casing seat); the front end face is the depth datum. "
   "Stands on its rear end on a flat table.",
   add=[(["shell"], [0, 0, 0])], focus=["shell"])
st(P1, "Gauge legs",
   "Three legs, 1,047 long (tube with ground ends), stand on the table inside the shell at R255, 120° apart. Their tops set ring 1's seat 128.0 from the front end.",
   add=[(["legs"], UP)], focus=["shell"])
st(P1, "Ring 1 onto the legs",
   "Ring 1 is finished before welding: waterjet blank from 4.5 in A572-50, Blanchard-ground to 110, lathe for the Ø400 × 35 counterbore and Ø318.5 bore, 16 × M12 tapped. "
   "Lowered onto the legs; 3 shims in the 0.5 mm OD gap centre it.",
   add=[(["ring1"], UP)], focus=["ring1"])
st(P1, "Slurry pipes",
   "Before ring 1 is welded: Ø76.1 pipes at 12 and 6 o'clock pushed through ring 1's holes from the front, flush with the plate face, and tacked. "
   "They carry no structural load.",
   add=[(["pipes"], UP)], focus=["ring1"])
st(P1, "Weld ring 1 and seal-weld the pipes",
   "Depth 128.0 ± 0.5 at 4 points. Tack 8 places, then the 14 mm fillet from the front in 4 opposed quadrants. Preheat 66 °C, interpass ≤ 250 °C. "
   "Pipes seal-welded at the front face into a 6 × 45° bevel; at 12 and 6 the ring fillet runs into the pipe weld (8.6 mm apart). "
   "After cooling: seat flatness ≤ 0.05, depth re-checked.",
   add=[(["weld"], [0, 0, 0]), (["pipewelds"], [0, 0, 0])], focus=["ring1"])
st(P1, "Legs out",
   "Shell lifted off the table; legs removed through the rear end.",
   remove=[("legs", [0, -1400, 0])], focus=["shell"])
st(P1, "Pipe saddles",
   "Shell on blocks. Saddles welded in under the pipes from the open rear end (x = 950, 207 mm in from the rear).",
   add=[(["saddles"], [0, -700, 0])], focus=["shell"])
st(P1, "Pressure taps",
   "Two Ø12 tap tubes at 3 and 9 o'clock, welded flush with the plate.",
   add=[(["taps"], UP)], focus=["ring1"])
st(P1, "Anti-roll fins",
   "Four fins, 20 × 70 × 990 plate, at 1, 3, 9 and 11 o'clock (clear of the launch rails at 5 and 7 and the lubrication ports at 10, 12 and 2). "
   "30° lead ramp with a knife edge, 45° tail ramp, 2 × 8 mm fillets. They resist 21.7 kNm of roll in cu 50 kPa clay: FoS 2.17 on the 10 kNm interlock.",
   add=[(["fin30"], [500 * 0.866, 0, 500 * 0.5]), (["fin90"], [0, 0, 500]), (["fin270"], [0, 0, -500]), (["fin330"], [500 * 0.866, 0, -500 * 0.5]),
        (["finwelds"], [0, 0, 0])], focus=["shell"])

st(P2, "Spider plate",
   "One waterjet piece from 2 in A572-50: 8 arms, centre, tab slots, cap pocket (milled 30 deep). Face down on the welding table.",
   add=[(["spider"], UP)], focus=["spider"])
st(P2, "Hub ring",
   "Locking-assembly hub ring Ø340 × Ø190 × 50.8 (A572-50; Ø320 minimum for 165 MPa hub pressure), centred on a fixture pin through the spider centre. "
   "It goes on before the gussets: the gussets' inner edges step in to R125 above it, so it cannot be dropped in afterwards.",
   add=[(["hubring"], UP)], focus=["spider"])
st(P2, "Gussets into the slots",
   "Eight 25 mm gussets. Two tabs on each drop through the spider's slots, which sets position and squareness without a jig; the inner edges bear on the hub ring.",
   add=[(["gussets"], UP)], focus=["spider"])
st(P2, "Journal sleeve",
   "Journal sleeve drops into the R125 opening between the gusset edges and stands on the hub ring. Head thrust passes from the hub ring into the sleeve by contact, not through the weld.",
   add=[(["sleeve"], UP)], focus=["spider"])
st(P2, "Weld and machine the head",
   "Gusset-to-spider 2 × 12 mm fillets, gusset-to-hub and gusset-to-sleeve 8 mm, tab plug welds. Then one lathe setup: Ø190 bore for the locking assembly, "
   "Ø140 bore, Ø170 seal journal, rear face, labyrinth rings.",
   add=[(["headwelds"], [0, 0, 0])], focus=["spider"])
st(P2, "Turn the head over",
   "Head turned face-up.",
   moves={"head": [pose(RU, -1150, 184 + 700), pose(FU, -1150, 100 + 700), pose(FU, -1150, 100)]}, focus=["spider"])
st(P2, "Bit holders and carbide",
   "17 holders welded to the arms; trapezoid carbide bits brazed in. 3 bits share the gauge track at R308.65.",
   add=[(["holders", "carbide"], UP)], focus=["spider"])
st(P2, "Centre cap",
   "Centre cap, 30 mm plate, cut to clear the arm-0 and arm-3 holders. Carries the 7 inner bits (R ≤ 118) and the centre cone with 3 carbide blades.",
   add=[(["cap", "capholders", "capcarbide", "blades"], UP)], focus=["cap"])

st(P3, "Spindle on its nose",
   "Spindle (Ø140, 4140 QT) stands on its nose on a stand.",
   add=[(["shaft"], UP)], focus=["shaft"])
st(P3, "Backing ring",
   "Backing ring Ø190 dropped over the rear end onto the collar (supports the 29328 shaft washer out to Ø190; SKF da min 185).",
   add=[(["backing"], UP)], focus=["shaft"])
st(P3, "29328N shaft washer + rollers",
   "Shaft washer with its roller set heated to 110 °C on the induction heater, dropped onto the backing ring, held down until cool.",
   add=[(["sw", "t_rol"], UP)], focus=["shaft"])
st(P3, "Turn the spindle over",
   "Spindle turned nose-up; it now stands on its drive end.",
   moves={"rotor": [pose(RU, 1050, 193 + 600), pose(FU, 1050, 775 + 300), pose(FU, 1050, 775)]}, focus=["shaft"])
st(P3, "Front 23228",
   "Front 23228 heated to 110 °C and dropped over the nose onto the collar.",
   add=[(["f_ir", "f_or", "f_rol", "f_cage"], UP)], focus=["shaft"])
st(P3, "Cartridge tube",
   "Cartridge tube (seamless 323.9 × 60, turned to Ø318, no welds) front end up on a stand.",
   add=[(["tube"], UP)], focus=["tube"])
st(P3, "Housing washer",
   "29328N housing washer dropped in from the front onto the shoulder 233 mm down (Ø204 left as rolled; SKF Da max 208).",
   add=[(["hw"], UP)], focus=["tube"])
st(P3, "Eye bolt",
   "M30 eye bolt into the spindle nose. The same thread later pulls the head on and pushes it off.",
   add=[(["eye"], [0, 400, 0])], focus=["shaft"])
st(P3, "Spindle into the tube",
   "Spindle lowered rear end first into the tube. The rollers seat on the housing washer; the front 23228 outer ring slides into its Ø250 seat.",
   moves={"rotor": [pose(FU, 1050, 775 + 1100), pose(FU, 1700, 765 + 1100), pose(FU, 1700, 765)]}, focus=["tube"], dur=2.4)
st(P3, "Turn the module over",
   "Eye bolt out. Module turned front-down and stood on the nose; the weight goes tube → housing washer → rollers → collar → nose.",
   remove=[("eye", [0, 500, 0])],
   moves={g: [pose(FU, 1700, 765 + 900), pose(RU, 1700, 193 + 900), pose(RU, 1700, 193)] for g in ("rotor", "tube")},
   focus=["tube"], dur=2.4)
st(P3, "Spacer sleeve",
   "Spacer sleeve slid over the rear end down to the shaft washer.",
   add=[(["spacer"], UP)], focus=["tube"])
st(P3, "Rear 23228",
   "Rear 23228 heated to 110 °C, slid onto the shaft and into the rear seat together, pushing on the inner ring. This bearing floats axially in its seat.",
   add=[(["r_ir", "r_or", "r_rol", "r_cage"], UP)], focus=["tube"])
st(P3, "MB28 + KM28",
   "Lock washer, then the KM28 nut tightened with a hook spanner; one washer tab bent into a nut slot.",
   add=[(["mb", "nut"], UP)], focus=["tube"])
st(P3, "Turn front-up",
   "Module turned front-up again.",
   moves={g: [pose(RU, 1700, 193 + 900), pose(FU, 1700, 765 + 900), pose(FU, 1700, 765)] for g in ("rotor", "tube")},
   focus=["tube"], dur=2.2)
st(P3, "Seal carrier",
   "Carrier with 3 lip seals 170 × 200 × 15 and 2 lantern rings slid over the nose on an assembly cone. Push and pull the shaft with a dial indicator on the nose; "
   "shim to 0.10–0.20 end play. 12 × M6 countersunk, flush.",
   add=[(["carrier", "sealcase", "seallip", "sealspring", "lantern", "shim", "carscrews"], UP)], focus=["tube"])
st(P3, "O-ring and seal-purge line",
   "Static O-ring rolled over the tube end into its groove (seals the ring 1 bore). The seal-purge line (Ø8) lies in a 14 × 9 groove milled along the tube OD from the port at x = 125 to x = 600, "
   "so nothing stands above Ø318 when the module passes through ring 1. Bearings are packed with grease here; no relube lines (12 rpm, ≈ 1,200 head revolutions per 5 m).",
   add=[(["oring"], [0, 0, 0]), (["purge", "purgefit"], [600 * 0.866, 0, 600 * 0.5])], focus=["tube"])
st(P3, "Split flange",
   "Flange halves into the groove from both sides.",
   add=[(["halfA"], [700, 0, 0]), (["halfB"], [-700, 0, 0])], focus=["tube"])
st(P3, "Split screws and pins",
   "2 × M10 across each split. First build: ream 4 radial Ø16 holes through the flange into the tube land and drive the pins in from outside.",
   add=[(["splitscrews"], [200, 0, 0]), (["pin45"], [106.1, 0, 106.1]), (["pin135"], [-106.1, 0, 106.1]), (["pin225"], [-106.1, 0, -106.1]),
        (["pin315"], [106.1, 0, -106.1])], focus=["tube"])

st(P4, "Module into ring 1",
   "Eye bolt back in. Module (≈ 330 kg) lifted and lowered rear end first through ring 1's Ø318.5 bore until the split flange sits in the counterbore. "
   "Flange flush with the plate face.",
   add=[(["eye"], [0, 400, 0])],
   moves={g: MOD_IN for g in ("rotor", "tube")}, focus=["shell"], dur=3.2)
st(P4, "Bolt and dowel",
   "16 × M12 10.9 into ring 1 at 70 % proof. First assembly: ream 2 × Ø16 dowels through the flange into ring 1 at 12 and 6. Eye bolt out.",
   add=[(["flscrews", "fldowels"], [0, 300, 0])], remove=[("eye", [0, 500, 0])], focus=["ring1"])

st(P5, "Head onto the nose",
   "Head lowered onto the nose. The Ø170 journal passes the lip seals on a thin assembly sleeve and stops on the front 23228 inner ring.",
   moves={"head": [pose(FU, -1150, 100 + 1600), pose(FU, 0, 1157 + 1600), SHELL0]}, focus=["shell"], dur=3.0)
st(P5, "Locking assembly",
   "Locking assembly (140 × 190 × 50) slid into the gap between shaft and hub ring. Screws tightened in rounds to 123 Nm (B-LOC B400 catalogue).",
   add=[(["la", "lascrews"], [0, 500, 0])], focus=["spider"])
st(P5, "Centre cap",
   "Cap with the inner bits into its pocket; 8 × M8 countersunk. Two M12 holes in the cap pull it out later.",
   moves={"cap": [pose(FU, -1800, -154 + 1900), pose(FU, 0, 1157 + 1500), SHELL0]}, focus=["spider"], dur=2.6)
st(P5, "Cap screws", "8 × M8 countersunk.", add=[(["capscrews"], [0, 300, 0])], focus=["spider"])

ALL = ("shell", "tube", "rotor", "head", "cap")
st(P6, "Turn the machine rear-up",
   "Machine turned rear end up and stood on a ring under the head.",
   moves={g: [pose(FU, 0, 1157 + 600), pose(RU, 0, 426 + 600), pose(RU, 0, 426)] for g in ALL}, focus=["shell"], dur=3.0)
st(P6, "Seal-purge supply",
   "Supply line connected to the end of the groove line at x = 600 (560 mm down from the open rear end) and run back to the surface.",
   add=[(["gsupply"], [0, 600, 0])], focus=["shell"])
st(P6, "Adapter dowels",
   "3 × Ø16 dowels pressed into the cartridge rear face (holes reamed with the adapter on the bench, first build).",
   add=[(["addowels"], [0, 150, 0])], focus=["tube"])
st(P6, "Drive adapter",
   "Adapter weldment (flanges + 14 in XS pipe, machined after welding) lowered over the shaft end onto the dowels; Ø250 pilot into the cartridge bore.",
   add=[(["adapter", "adwelds"], UP)], focus=["adapter"])
st(P6, "Adapter screws",
   "12 × M16 10.9 put in through the two side windows and the open rear, tightened to 248 Nm.",
   add=[(["adscrews"], [0, 150, 0])], focus=["adapter"])
st(P6, "Spindle-side coupling hub",
   "Hub lowered through the adapter's Ø282 bore onto the Ø130 shaft end. Its 130 × 180 locking assembly is tightened from above through the middle of the jaw ring.",
   add=[(["hub1", "hub1la", "hub1scr"], UP)], focus=["adapter"])
st(P6, "Coupling spider",
   "Polyurethane spider dropped into the jaws.",
   add=[(["elast"], [0, 500, 0])], focus=["adapter"])
st(P6, "Hydraulic motor",
   "Motor (Poclain MS18, 2,812 cc, ≈ 152 kg) with the motor-side hub on its spline lowered onto the adapter. The jaws engage the spider; "
   "the Ø282 spigot enters the adapter bore.",
   add=[(["motor", "mbolts_r", "mshaft", "hub2"], [0, 1100, 0])], focus=["adapter"], dur=2.4)
st(P6, "Motor screws", "8 × M20 10.9 put in behind the motor flange, tightened to 484 Nm.", add=[(["mbolts"], [0, 60, 0])], focus=["adapter"])
st(P6, "Hoses", "Hoses A and B (3/4 in) and the case drain run back through the casing string to the HPU.",
   add=[(["hoses"], [0, 600, 0])], focus=["adapter"])
st(P6, "Back to horizontal",
   "Machine laid horizontal on the launch cradle.",
   moves={g: [pose(RU, 0, 426 + 700), pose(H, -500, 310 + 700), pose(H, -500, 310)] for g in ALL}, focus=["shell"], dur=3.0)

st(P7, "Slurry hoses",
   "Feed (12 o'clock) and discharge (6 o'clock) hoses, Ø80 placeholder, coupled to the slurry pipe ends 5 mm inside the shield rear face. "
   "The pipes stop short of the face so the thrust ring never bears on them.",
   add=[(["shoses"], [600, 0, 0])], focus=["shell"])
st(P7, "Thrust ring onto the shield rear",
   "Thrust ring Rev A (A572-50, 76.2 thk, Ø609.6 × Ø400) with 4 saddles welded to its rear face at R260, 2, 4, 8 and 10 o'clock. "
   "Slid on from the rear, the slurry hoses passing through its notches at 12 and 6, until its Ø589.5 spigot enters the shield's Ø590.6 counterbore "
   "and its front face bears on the 9.5 wide shield end (x = 1,157). No jacking pipes yet; not bolted.",
   add=[(["tring", "tsaddles", "tears", "tsadwelds"], [900, 0, 0])], focus=["tring"], dur=2.4)
st(P7, "Jacking cylinders",
   "4 × Chief WT 5 × 24 (bore 127, rod 63.5, stroke 609.6), retracted 889 pin to pin. Each rod-end cross tube (Ø63.5 × 101.6) goes between the ears "
   "into its Ø65 seat. Thrust path: rod → cross tube → seat → block → ring → shield. Barrel and gland lengths are approximate.",
   add=[(["jcyl"], [700, 0, 0])], focus=["tring"], dur=2.4)
st(P7, "Saddle pins",
   "Ø38.1 × 160 4140 pins through the ears and cross tubes, 2 clips each. The ear holes are slotted 3 toward the ring, "
   "so the pins carry load only in retract (50 bar, 47.5 kN per cylinder).",
   add=[([f"tpin{int(a)}"], [0, -250 * math.sin(math.radians(a)), 250 * math.cos(math.radians(a))]) for a in M.TR_ANGS], focus=["tring"])

ag = {k: p[6] for k, p in M.parts.items()}
for s in steps:
    for keys, _ in s["add"]:
        for k in keys:
            assert k in ag, k
    for k, _ in s["remove"]:
        assert k in ag, k
added = [k for s in steps for keys, _ in s["add"] for k in keys]
missing = [k for k in M.parts if k not in added]
assert not missing, missing
asm = {"groups": groups, "partGroup": ag, "steps": steps}

if __name__ == "__main__":
    out, assy, masses = [], cq.Assembly(name="spindle_mount_revH_detail"), {}
    tassy = cq.Assembly(name="thrust_ring_revA")            # thrust ring + cylinders alone, same machine coordinates
    KG = {"motor": 152.0, "jcyl": 4 * 52.6}
    for key, name, wp, col, dx, grp, a in M.P:
        pos, idx = [], []
        for v in wp.vals():
            for f in v.Faces():
                vs, tris = f.tessellate(0.25, 0.35)
                base = len(pos) // 3
                for q in vs:
                    pos += [round(q.x, 1), round(q.y, 1), round(q.z, 1)]
                for t in tris:
                    idx += [t[0] + base, t[1] + base, t[2] + base]
        kg = KG.get(key, round(sum(v.Volume() for v in wp.vals()) * 7.85e-6, 1))
        if key in ("seallip", "shoses"):
            kg = round(kg * 0.16, 2)
        if key == "elast":
            kg = round(kg * 0.15, 2)
        if grp != "Fixture":
            masses[grp] = masses.get(grp, 0) + kg
        out.append({"key": key, "name": name, "color": col, "dx": dx, "group": grp, "pos": pos, "idx": idx, "kg": kg})
        # ASCII only: Fusion shows other characters in STEP product names garbled (Ø came through as Ã)
        safe = "".join(ch if ch.isascii() and ch.isalnum() else "_" for ch in name.replace("Ø", "D").replace("×", "x"))
        if grp != "Fixture":
            assy.add(wp, name=safe, color=cq.Color(*[int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
        if grp in (M.TR, M.JK):
            tassy.add(wp, name=safe, color=cq.Color(*[int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]))
    assy.export(str(STEP / "spindle_mount_revH_detail.step"))
    tassy.export(str(STEP / "thrust_ring_revA.step"))
    json.dump({"parts": out, "asm": asm, "masses": masses}, open(VIEWER_DATA / "H.json", "w"), separators=(",", ":"))
    print({k: round(v, 1) for k, v in masses.items()}, "steps", len(steps), "tris", sum(len(o["idx"]) // 3 for o in out))
