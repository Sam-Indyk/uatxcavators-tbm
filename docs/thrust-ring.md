# Thrust Ring (Rev B, Oct 28, 2026; Rev A Oct 27)

Interface between 4 × Chief WT 5 × 24 cylinders and the rear end of the last casing segment. Units mm unless noted. Ring front face (casing side) is z = 0, +z rearward toward the cylinders.

## Cylinder (Chief WT, Bailey SKU 216207, SAE 12 ports)

| Item | Value |
|---|---|
| Bore / rod | 5.00 in (127.0) / 2.50 in (63.5) |
| Stroke | 24.00 in (609.6) |
| Retracted / extended, pin to pin | 35 in (889) / 59 in (1,498.6) |
| Barrel OD | 5.75 in (146.1) |
| Cross tube OD × length | 2.50 in (63.5) × 4.00 in (101.6), both ends |
| Pin bore / pin | 1.515 in (38.5) / 1.50 in (38.1) |
| Rated pressure / test | 3,000 psi (206.8 bar) / 4,500 psi |
| Rod material | Chromed steel, 75 ksi (517 MPa) min yield |
| Mass | 116 lb (52.6 kg) |
| Catalogue "column load" 58,900 lb | = 3,000 psi × bore area (262 kN); not a buckling rating |
| Bore area / annulus area | 12,668 mm² / 9,501 mm² |

## Force vs pressure, 4 cylinders

| Pressure (bar) | Per cylinder (kN) | Total (kN) | Basis |
|---|---|---|---|
| 121 (1,755 psi) | 153.3 | 613 | Relief cap (reaction wall FoS 2.3) |
| 158 (2,290 psi) | 200.0 | 800 | Structural design case |
| 195 | 247.0 | 988 | PDB relief setting |
| 200 | 253.4 | 1,013 | PDB jack-pressure interlock |
| 207 (3,000 psi) | 262.0 | 1,048 | Cylinder rating |
| 50 (retract) | 47.5 | 190 | Retract relief |

## Layout

| Item | Rev A |
|---|---|
| Ring | A572 Gr 50, 76.2 thk (3 in plate); OD Ø609.6 (= shield OD, rides the launch rails at casing height); ID Ø400 |
| Cylinder positions | R260 at 2, 4, 8 and 10 o'clock (±30° from horizontal); 12 and 6 o'clock open |
| Cylinder envelope | Barrel outer edge at x = ±298; 80 radial clearance from barrel to the launch-rail contact line (rails at 30° from bottom) |
| Cylinder spacing | 260 chord between 2 and 4 o'clock; 114 between barrels |
| Cross tube axis | Tangential (cylinder pivots radially in the saddle) |
| Front face | Same register and face as a casing segment's front end, machined from the casing joint drawing; no bolts to the casing |
| Through opening | Ø400: slurry feed + return (Ø76.1), motor A / B / case drain, lube hose (19), cables |

## Saddle (4 per ring, same design on the reaction-wall spreader and both ends of each spacer column)

| Item | Value |
|---|---|
| Block | A572-50, 144 (tangential) × 100 (radial) × 45.5 high, welded to ring rear face |
| Seat | Ø65 half-bore (1.5 diametral clearance on Ø63.5 tube), floor 25 above ring face, tube centre z = 57.5; seat edges 12 below tube centre; wrap 136° |
| Bearing width / projected area | 101.6 / 6,028 mm² |
| Ears | 2 × 20 thk × 80 wide, R40 ends, 104 gap between ears, overall height 97.5 above ring face |
| Ear holes | Ø39.5 slotted 3 long in z, toward the ring: tube seats on the saddle under thrust, pin bears only in retract |
| Pin | Ø38.1 × 160, 4140 HT, 2 × retaining clips |
| Saddle to ring weld | 8 mm fillet all round (488 perimeter); not in the thrust path |
| Thrust path | Rod → rod-end cross tube OD → saddle seat → block → ring → casing face. No pin, no weld |

## Masses

| Item | kg |
|---|---|
| Ring | 99.4 |
| Saddles + ears, 4 | ≈ 28 |
| Pins, 4 | ≈ 7 |
| Thrust ring assembly | ≈ 134 |
| Cylinders, 4 | 210 |

## Structural check

Allowables as spindle-mount Rev H: 0.6 Fy bending = 207 MPa (A572-50), 0.9 Fy bearing = 310 MPa, E70 fillet throat 145 MPa.

Ring model: 720-element curved grid (out-of-plane bending + torsion), loads at R260, compression-only support at the casing wall (R299.6), foundation k = E t / L = 3,800 N/mm per mm (9.5 wall, 500 segment). Captures out-of-plane bending between cylinders and eversion from the 39.6 radial offset between load and support.

| Check | 613 kN | 800 kN | 1,048 kN |
|---|---|---|---|
| Ring max moment (kNm) | 8.63 | 11.26 | 14.75 |
| Ring max torque (kNm) | 0.96 | 1.25 | 1.64 |
| Ring von Mises (MPa) | 86.4 | 112.7 | 147.7 |
| Ring FoS on 207 | 2.40 | 1.84 | 1.40 |
| Ring contact on casing | 100 % | 100 % | 100 % |
| Peak line load on casing wall (N/mm) | 582 | 760 | 995 |
| Peak casing wall bearing, 9.3 wall (MPa) | 62.6 | 81.7 | 107.0 |
| Saddle seat bearing (MPa) / FoS on 310 | 25.4 / 12.2 | 33.2 / 9.3 | 43.5 / 7.1 |
| Saddle block compression (MPa) | 10.6 | 13.9 | 18.2 |

Pattern comparison at 800 kN (same ring):

| Pattern | VM (MPa) | FoS | Barrel to rail contact line |
|---|---|---|---|
| 45 / 135 / 225 / 315° | 114.2 | 1.81 | ≈ 7 |
| 2 / 4 / 8 / 10 o'clock (Rev A) | 112.7 | 1.84 | 80 |

Foundation sensitivity, 800 kN: k = 500 → 141.1 MPa (1.47); 3,800 → 112.7 (1.84); 40,000 → 98.8 (2.10).

Thickness study, 800 kN, 2 / 4 / 8 / 10 o'clock:

| Thickness | VM (MPa) | FoS | Ring mass (kg) |
|---|---|---|---|
| 50.8 (2 in) | 234.5 | 0.88 | 66.3 |
| 63.5 (2.5 in) | 156.7 | 1.32 | 82.8 |
| 76.2 (3 in) | 112.7 | 1.84 | 99.4 |
| 88.9 (3.5 in) | 85.4 | 2.42 | 116.0 |
| 101.6 (4 in) | 68.1 | 3.04 | 132.6 |

### Retract (50 bar, 47.5 kN per cylinder)

| Check | Value | Allowable | FoS |
|---|---|---|---|
| Pin bending, span 104 + 2 × 20 | 157 MPa | 393 (0.6 × 655) | 2.50 |
| Pin double shear | 20.8 MPa | 262 | 12.6 |
| Ear net section | 29.3 MPa | 207 | 7.1 |
| Ear tear-out | 29.3 MPa | 138 | 4.7 |
| Saddle fillet, 8 mm all round | 17.2 MPa | 145 | 8.4 |

Pin as a thrust path (rejected): 545 MPa at 613 kN, 712 MPa at 800 kN (1.5 in pin bending in the 104 + 2 × 20 clevis).

### Cylinder column (rod only over full pin-to-pin length, both ends pinned, 10 mm eccentricity with P-δ amplification, rod yield 517 MPa)

| Per cylinder (kN) | Euler FoS (Pcr 701 kN) | Combined stress (MPa) | Combined FoS |
|---|---|---|---|
| 153.3 (613 total) | 4.58 | 126.4 | 4.09 |
| 200.0 (800 total) | 3.51 | 174.4 | 2.96 |
| 247.0 (195 bar) | 2.84 | 229.7 | 2.25 |
| 325.0 (PDB screen) | 2.16 | 343.5 | 1.51 |

## Conflicts with the PDB record

| Item | PDB | With 4 × WT 5 × 24 |
|---|---|---|
| Relief for 613 kN | 195 bar | 121 bar (195 bar = 988 kN) |
| Jack-pressure interlock | > 200 bar (1,013 kN) | 158 bar = 800 kN structural case |
| Reaction wall at relief | FoS 2.3 on 613 kN | FoS 1.45 at 195 bar / 1.42 at 200 bar |
| Extension interlock | > 740 | Stroke is 609.6 |
| Insertion clearance (stroke − segment) | 150–250 required | 609.6 − 500 = 109.6 |
| Rod | 3.5 in selected (325 kN screen) | 2.5 in; combined FoS 4.09 at 613 kN, 2.96 at 800 kN |

## Manufacture

| Part | Route |
|---|---|
| Ring | Waterjet or plasma from 3 in A572-50 (OD + 2, ID − 2) → weld saddles → 32 in lathe: OD Ø609.6, ID Ø400, front face and register from the casing joint drawing; flat 0.1 |
| Saddle blocks | Saw from 2 in bar or plate → mill Ø65 seat → weld to ring, 4 opposed |
| Ears | Waterjet from 0.75 in plate → Ø39.5 × 3 slot after welding (line-bored with the seat) |
| Bought | 4 × Chief WT 5 × 24 (SKU 216207, $958.63 ea), 4 × 4140 HT pins Ø38.1, clips |

Saddle seat heights (z = 57.5 to tube centre) within 0.25 of each other across the four positions.

## Model (Oct 27, 2026): at the shield rear, no jacking pipes

Model: `src/build_revH_detail.py`, parts `tring`, `tsaddles`, `tears`, `tsadwelds`, `tpin60` / `tpin120` / `tpin240` / `tpin300` and `jcyl`; constants `TR_*`, `SD_*`, `EAR_*`, `X_CT`, `CYL_L`. Assembly steps 53–55 (phase 7) in `src/asm_revH.py`. STEP: `out/step/thrust_ring_revA.step` (ring, saddles, pins, cylinders) and inside `out/step/spindle_mount_revH_detail.step`; both in machine coordinates (x = 0 at the ring 1 front face, +x rearward). Viewer: Rev H tab, groups "Thrust ring" and "Jacking cylinders"; Rev H assembly tab, steps 53–55.

| Item | Value |
|---|---|
| Position | Launch before the first jacking pipe: ring front face on the shield rear end; x = 1,157.0 to 1,233.2 (z = 0 at x = 1,157) |
| Front face | Flat. The register (the machined step that locates the ring on the casing end) is not modelled: casing joint drawing open (Rev B adds it, below) |
| Cross-tube and pin axis | x = 1,290.7 (z = 133.7: rear face + 57.5); tube concentric with the Ø65 seat |
| Cap-end pin, retracted | x = 2,179.7 |
| Ears, as modelled | Lug (plate with a pin hole) on each block end: R40 end rearward; foot shaped to the Ø65 seat so the eye is closed; Ø39.5 hole slotted 3 toward the ring |
| Cylinders | Envelope (outer shape only): cross tubes, rod and barrel diameters from the catalogue; gland and barrel lengths approximate; 52.6 kg each (catalogue) |
| Modelled masses | Ring 99.4; saddle blocks 16.5; ears 3.8; welds 0.3; pins 5.7 (no clips); weldment + pins 125.6 kg |

Interference (`build_revH_detail.py --check`, cm³): every thrust-ring pair is 0 except `tring/gsupply` 5.98. Collision replay of the 55-step assembly (`audit_asm.py`, threshold 0.3 cm³): 0 collisions; ring slid on axially over the hoses, cylinders slid into the seats, pins inserted along their axes.

### Interface with the shield rear

| Item | Value |
|---|---|
| Seal-purge supply line | Ø10 at R209 (R204–214), 30°, x = 600 to 1,500: passes through the ring annulus (bore R200), 5.98 cm³ overlap |
| Slurry pipes | Ø76.1 at R245, 12 and 6 o'clock, end at x = 1,157; bores R212.5–277.5 lie inside the ring annulus R200–304.8: both fully covered by the ring front face |
| Motor and hoses in the Ø400 bore | Motor body R140 (radial clearance 60), port bosses R106 (94), hoses R97 (103) |
| Saddle block vs ring OD | Block outer face R310 vs ring OD R304.8: 5.2 overhang at mid-width, 13.5 at the corners |
| Saddle fillet on the ring face | 316.3 of the 488 perimeter: inner side 144, ends 2 × 86.2, outer side none |

| Check (retract, 47.5 kN per cylinder) | Value | Allowable | FoS |
|---|---|---|---|
| Saddle fillet, 8 mm, 316.3 on the ring face | 26.5 MPa | 145 | 5.46 |

## Rev B (Oct 28, 2026): notches for the slurry pipes, register, 3D FEA

Model: `src/build_revI_detail.py` (part `tring`, constants `NOTCH_W`, `NOTCH_R`), assembly phase 7 in `src/asm_revI.py`, STEP `out/step/thrust_ring_revB.step`. FEA: `src/fea_thrust_ring.py`. Design manual chapter: `docs/manual-06-thrust-ring.md`.

| Item | Rev B |
|---|---|
| Notches | U-notch at 12 and 6 o'clock, 84 wide, open to the bore, round end at R287, through the ring and the spigot |
| Register | Spigot Ø589.5 × 10 high × 9 wide (R285.75-294.75) ahead of the bearing face, 1 × 45° lead-in; radial gap 0.55 in the Ø590.6 casing bore; relief groove 1.5 into the spigot × 0.5 below the bearing face at its root. Ported from the Oct 27 local Rev H work (branch `local-oct28-register`); placeholder sizes until the casing joint drawing |
| Shield rear end | Counterbored Ø590.6 × 12 (casing bore, 24 in × 0.375 wall assumed) to take the spigot like a casing end; end wall 9.5; spigot tip 2.0 short of the floor. Bearing annulus R295.3-304.8 = 17,910 mm²: 44.7 MPa at LC3, 50.3 MPa at LC4 |
| Ring stock | Bearing face to rear face 76.2; 86.2 overall with the spigot, from 3.5 in plate (88.9) |
| Slurry pipes | Ø76.2 at R245 run through the notches to x = 1,255: 3.9 clear each side and at the end. The ring slides on axially over the pipe ends and hoses |
| Seal-purge supply | Now at R185 in the bore (jog behind the motor at x = 1,095-1,150): 10 clear of the bore |
| Everything else | As Rev A |

FEA (quadratic tetrahedra, quarter model, ring + spigot + saddle blocks; compression-only springs on the bearing annulus R295.3-304.8: shield end k = 156, casing end k = 400 N/mm³; seat load Hertz-like over ±20° about the seat bottom). The relief groove is not modelled, so the spigot root is a sharp corner in the mesh; its peak is listed separately. Von Mises, MPa:

| Case | Support | F (kN) | Ring away from saddles, notches and spigot | Notch zone | Spigot zone peak | Block Pm + Pb | Ring under block Pm + Pb | Contact | Max contact p (MPa) |
|---|---|---|---|---|---|---|---|---|---|
| LC2 | shield | 613.1 | 68 | 31 | 71 | 37 | 33 | 100 % | 47.5 |
| LC2 | casing | 613.1 | 66 | 34 | 70 | 36 | 31 | 100 % | 50.1 |
| LC3 | shield | 800.6 | 89 | 40 | 92 | 48 | 43 | 100 % | 62.1 |
| LC3 | casing | 800.6 | 87 | 44 | 92 | 47 | 41 | 100 % | 65.4 |
| LC4 | shield | 901.4 | 100 | 45 | 104 | 54 | 49 | 100 % | 69.9 |
| LC4 | casing | 901.4 | 98 | 50 | 103 | 53 | 46 | 100 % | 73.6 |

Seat-load model, Rev A ring at LC3 on the casing: uniform pressure over the half groove gives 293 MPa at the seat edges and 98 MPa in the ring away from the saddles; the Hertz-like pressure gives 237 and 98. The edge peak of the uniform model is an artefact of the load model.

The notch zone sits midway between cylinders, where the ring is lightly loaded. Load cases: LC2 121 bar (613.1 kN), LC3 158 bar (800.6 kN), LC4 2,580 psi pump relief (901.4 kN); required FoS on yield 1.5 at LC2-LC3 and 1.0 at LC4 (A572 Gr 50, Fy 345).

| Check | LC3 | LC4 |
|---|---|---|
| Seat bearing on 63.5 × 101.6 (MPa) / FoS on 0.9 Fy | 31.0 / 10.0 | 34.9 / 8.9 |
| Hertz p_max, Ø63.5 in Ø65 (MPa) / FoS on first sub-surface yield 1.67 Fy (Fy 300 cross tube) | 224 / 2.24 | 237 / 2.11 |
| Cylinder rod Euler FoS (P_cr 701 kN) | 3.50 | 3.11 |
| Shield rear end wall, bearing on 17,910 mm² (MPa) / FoS on 0.9 Fy (Fy 241) | 44.7 / 4.85 | 50.3 / 4.31 |
| Shield rear end wall, axial compression (MPa) / FoS on 0.6 Fy | 44.7 / 3.23 | 50.3 / 2.87 |

## Open

- Casing joint drawing: confirm the register placeholders (spigot Ø589.5 × 10 × 9 wide, shield rear counterbore Ø590.6 × 12) and the casing wall (24 in × 0.375 assumed).
- Spacer column geometry (length set, saddle at each end).
- Reaction-wall spreader saddles (barrel-end cross tubes).
- Hydraulic circuit: common supply vs per-cylinder control; reducing valve 121 bar; interlock 158 bar; pump relief 2,580 psi (LC4); retract relief 50 bar.
- Saddle block radial position or size: outer face 5.2 past the ring OD; fillet on 316 of the 488 perimeter.
- Cylinder certified drawing: gland and barrel lengths (modelled as an envelope); cross-tube steel grade (Fy 300 assumed in the Hertz check).
- Slurry hose connection behind the ring (pipe ends at x = 1,255): fitting OD ≤ 95 at R245 to pass inside the jacking pipes later.
