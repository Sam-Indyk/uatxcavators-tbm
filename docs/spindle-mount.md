# Cutterhead Spindle Mount (current: Rev H, Oct 26, 2026)

Scripts, viewer and STEP files: GitHub repo Sam-Indyk/uatxcavators-tbm (src/, viewer/, out/; see its CLAUDE.md). This doc is mirrored there as docs/spindle-mount.md.

Rev H is at the end of this doc. The sections below it record rev E and the options that led to rev H.

One welded ring, one bolted cartridge carrying all three bearings and the drive. Supersedes rev D (rear bearing in a separate rear plate on a second ring).
Fusion 360 is the model of record. Visual model: `spindle_mount_revE.step` (CadQuery, envelope-level). Calc: `calc_revE.py`.
Axis: x = 0 at cartridge front face, +x rearward. Shield front end x = −175, rear end x = 1110. Units mm.

## Layout

| Item | Rev E |
|---|---|
| Bearings | Koyo 23228 (front) + Koyo 29328N (thrust) + Koyo 23228 (rear, floating), L = 400 |
| Cartridge | Weldment: front sleeve Ø310 + disc Ø400 × 40 + rear sleeve Ø310; machined after welding; 560 long |
| Thrust path | 29328N housing washer → disc front face → disc rear face → ring 1. No weld in the path |
| Cartridge to ring 1 | 16 × M12 10.9 on Ø370 (heads recessed) + 2 × Ø16 dowels at 3 and 9 o'clock; Ø340 H7/g6 spigot register; O-ring at R196 |
| Ring 1 | A572 Gr 50, 70 thk, OD = measured shell ID − 1.0, Ø340 H7 bore; front face x = 218 (393 from shield front end) |
| Ring 1 weld | 1 × 14 mm fillet, front face only, 4 passes, preheat 66 °C |
| Rear bore | One Ø250 H7 bore x = 218–560: rear 23228 floats in it; drive pilot enters from the rear |
| Drive | Envelope ≤ Ø400 × 478; pilot Ø250 f7 with O-ring; female Ø130 spline; 12 × M16 on Ø280 + 3 × Ø16 dowels into cartridge rear face |
| Shaft | Ø140, one Ø165 collar, Ø130 splines at both ends |
| Front stack | End plate → adapter → wear sleeve Ø170 → front 23228 inner ring → collar |
| Rear stack | Collar → 29328N shaft washer → spacer sleeve → rear 23228 → KM28 |
| Front seal | Labyrinth + 3 lip seals 170 × 200 × 15 on wear sleeve + 2 lantern rings, continuous grease purge |
| Purge path | Tube on ring 1 rear → ring 1 (R178, 12 o'clock) → O-ring port → disc → radial cross-drill (plugged) → sleeve (R140) → cover → lanterns |
| Grease | Cartridge interior is one cavity (front seals to drive pilot O-ring); relube port at x = 470, 3 o'clock |
| Slurry pipes | Ø76.1 at R245, 12 and 6; welded through ring 1; saddles at x = 760 |
| Pressure taps | 2 × Ø12 at R225, 3 and 9 o'clock |
| Overall | Drive rear face x = 1038; head front ≈ −240 → ≈ 1278 |

End play 0.10–0.20, set by shims under the front cover.

## Masses (steel, modelled; drive excluded)

| Group | kg |
|---|---|
| Bearing module (cartridge, 3 bearings, shaft, cover, seals, adapter, dowels) | 365 |
| Shell weldment (shell, ring 1, weld, pipes, saddles, taps) | 353 |

## Structural check

AISC 360 ASD, AWS D1.1. Welds as a line. Ring 1 as an annular plate, guided at r = 200, pinned at the weld. Bolts ISO 10.9, preload 70 % of proof.

| Case | Loads |
|---|---|
| LC2 jam | 590 kN + 26.8 kN (1 bar) + 62 kNm + drive 2.3 kNm |
| LC3 envelope | 800 kN + 26.8 kN + 62 kNm + 2.3 kNm |
| Torque | 20 kNm (10 kNm interlock × 2) |

Radial reaction per 23228: 155 kN. Moment through the cartridge joint: 64.3 kNm.

| Joint | Mode | Case | Value | Capacity | FoS |
|---|---|---|---|---|---|
| Shaft Ø140 at collar, Kt 1.5 | von Mises | LC2 | 358 | 655 | 1.83 |
| 29328N washer on disc | bearing | LC3 | 60 | 225 | 3.76 |
| Disc on ring 1 | min contact, no preload | LC2 | −2.5 | — | — |
| Disc on ring 1 | clamp needed vs preload (kN) | LC2 | 80.5 | 784 | 9.74 |
| Disc on ring 1 | max contact with preload | LC3 | 71 | 311 | 4.38 |
| Ring 1, 70 thk A572-50 | bending, max | LC3 | 119 | 207 | 1.73 |
| Ring 1, 70 thk A572-50 | bending at pipe holes, Kt 2.5 | LC3 | 128 | 207 | 1.62 |
| Ring 1 weld, 1 × 14 | throat | LC3 | 70 | 145 | 2.07 |
| Ring 1 weld, 1 × 14 | shell base metal | LC3 | 49 | 96 | 1.94 |
| Front sleeve to disc, 1 × 12 | throat | LC2 | 47 | 145 | 3.06 |
| Rear sleeve to disc, groove, 30 wall | base metal shear | LC2 | 20 | 100 | 4.98 |
| Shell at ring 1 | axial + bending | LC3 | 53 | 144 | 2.73 |

### Torque transfer (20 kNm)

Spigot and pilot registers are round and carry no torque. Torque crosses each bolted joint by clamp friction; dowels are the backup if the faces are oily.

| Joint | Mode | Per item (kN) | Capacity (kN) | FoS |
|---|---|---|---|---|
| Drive to cartridge, 12 × M16 | slip, μ 0.30 (clean, dry) | 11.9 | 27.4 | 2.30 |
| Drive to cartridge, 12 × M16 | slip, μ 0.15 (oily) | 11.9 | 13.7 | 1.15 |
| Drive to cartridge, 12 × M16 | bolt shear after slip | 11.9 | 36.7 | 3.09 |
| Drive to cartridge, 3 × Ø16 dowels | dowels alone | 47.6 | 88.5 | 1.86 |
| Cartridge to ring 1, 16 × M12 | slip, μ 0.30 | 6.8 | 14.7 | 2.17 |
| Cartridge to ring 1, 16 × M12 | slip, μ 0.15 | 6.8 | 7.3 | 1.09 |
| Cartridge to ring 1, 16 × M12 | bolt shear after slip | 6.8 | 19.7 | 2.92 |
| Cartridge to ring 1, 2 × Ø16 dowels | dowels alone | 54.1 | 88.5 | 1.64 |
| Cartridge tube Ø310/Ø250 | torsion (MPa) | 5.9 | 100 | 16.9 |
| Shell | torsion (MPa) | 2.8 | 96 | 34.1 |

Not covered: FEA of ring 1 and disc; fatigue (≈ 3,600 head revolutions per 5 m drive); spline Kt; bearing catalogue checks.

## Ring 1: machined before welding

| Step | Method | Tolerance |
|---|---|---|
| Blank | Waterjet from 3 in A572-50: OD, Ø334 rough bore, pipe holes Ø77, taps Ø12, purge Ø6, 16 × Ø10.2 tap drills | ±0.25 |
| Faces | Blanchard grind both sides to 70.0 | ±0.1, flat 0.05 |
| Bore | Lathe: Ø340 H7 | H7 |
| OD | Measured shell ID at ring position (8 angles) − 1.0; waterjet or lathe | ±0.25 |
| Threads | 16 × M12, 25 deep | — |
| Dowel holes | Not pre-drilled; match-reamed through the cartridge disc at first assembly | Ø16 H7 |

Weld distortion control: seat band r = 170–200 is 92 mm inside the weld; tack 8 places; weld in 4 opposed quadrants; interpass ≤ 250 °C. Acceptance after welding: seat flatness ≤ 0.05, depth 393.0 ± 0.5 at 4 points, bore roundness ≤ 0.05. Out of tolerance: skim seat from the front end (reach 393) or epoxy-chock the disc.

## Ring 1 depth and squareness

Requirement: front face 393 ± 2 from the shield front end (sets cutterhead protrusion; final value from the cutterhead/adapter stack); square to the shield axis within 1 mrad (0.6 across the face).

1. Face both shield ends on the lathe first; overall length 1285.0. The front end face is the datum.
2. Stand the shell rear end down on a flat table.
3. Stand 3 gauge legs on the table inside the shell at R255, 120° apart: length 822.0 (= 1285 − 393 − 70). Tube with ground ends, or threaded rod with jam nuts.
4. Lower ring 1 onto the legs. Centre radially with 3 shims in the 0.5 mm OD gap.
5. Straightedge across the front end; depth to the ring seat face at 0°, 90°, 180°, 270°: 393.0 ± 0.5, spread ≤ 0.5. Adjust legs.
6. Tack 8 places. Re-measure. Weld (flat position, from above).
7. Re-measure depth and flatness. Remove legs through the rear end.

The ring position does not need to be known more precisely than this: the cartridge locates on the ring's seat face (axial) and bore (radial), and all bearing-to-bearing and bearing-to-drive alignment is inside the cartridge.

## Cartridge: machined after welding (bench part)

1. Weld front sleeve and rear sleeve to the disc: 12 mm fillet front; single-V groove rear (root removed by the bore).
2. Setup 1 (front): turn OD datum; bore Ø250 H7, Ø252 relief, Ø241, Ø200; face disc front and rear; turn Ø400 and Ø340 g6 spigot; O-ring and port grooves.
3. Setup 2 (rear), indicate on the setup 1 OD: bore Ø250 H7 x = 218–560; face rear; 12 × M16 on Ø280.
4. Drill: 16 × Ø13.5 + counterbores, cover M10, purge passages, grease port.

## Assembly

### Bearing module (bench, shaft vertical)
1. Heat front 23228 to 110 °C; slide on from the spline end against the collar. Fit wear sleeve.
2. Heat 29328N shaft washer + rollers; slide on from the rear against the collar.
3. Cartridge front up on a stand. Drop the 29328N housing washer onto the disc face.
4. Lower the shaft rear end first until the front 23228 enters Ø250 and the rollers seat.
5. Measure cover depth; shim to 0.10–0.20 end play; fit cover with seals and lanterns (assembly cone).
6. Fit adapter and end plate.
7. Invert. Slide spacer on; heat rear 23228 and slide it onto the shaft and into the rear bore together, pushing on the inner ring. KM28 + MB28 after cooling.
8. Bench-fit the drive once: pilot in, 12 × M16, ream 3 × Ø16 dowels through the drive flange into the cartridge rear face. Remove drive.

### Installation
1. Shell front end up. Lower the bearing module (365 kg) rear end first through ring 1's Ø340 bore; spigot engages.
2. 16 × M12. Match-ream 2 × Ø16 dowels through the disc into ring 1 (first assembly only); fit dowels. Grease-pack counterbores, cap.
3. Shell horizontal. Drive in from the rear (reach 550): pilot into Ø250, spline engages (turn adapter), dowels, 12 × M16.
4. Cutterhead onto adapter, 16 × M20.

### Service
Drive out the rear → 16 × M12 → bearing module out the front. Nothing else disturbed; dowels return the module to position.

## Bearings and sourcing

| Source | Item | Qty |
|---|---|---|
| Koyo (in-kind) | 29328N | 2 (confirmed Oct 16) |
| Koyo (in-kind) | 23228 | 3: front, rear, spare (1 accepted Oct 15; confirm count) |
| SKF ($2,000) | Lip seals 170 × 200 × 15 | 6 |
| SKF | KM28 + MB28 | 2 |
| SKF | HN 28 hook spanner | 1 |
| SKF | Bearing grease EP2 | 1 pail |
| SKF | Fitting tool kit | 1 |
| Supplier | Ring 1 blank, A572-50 3 in, waterjet + Blanchard | 1 |
| Supplier | Disc blank, 2 in plate | 1 |
| Supplier | Heavy-wall tube ≈ Ø320 × 35 wall | ≈ 0.6 m |
| Supplier | Dowels Ø16 hardened | 5 + spares |

Required static ratings (s₀ = 2): 23228 C₀ ≥ 403 kN; 29328N C₀ ≥ 1,180 kN.

## Rev D → rev E

| Item | Rev D | Rev E |
|---|---|---|
| Rings | 2 (ring 1 + ring 2) | 1 |
| Precision fit-ups in the shell | Ring 1 seat + rear plate centring with mandrel | Ring 1 seat only |
| Rear bearing housing | Rear plate on ring 2 | Rear sleeve of the cartridge |
| Drive mount | Rear plate | Cartridge rear face |
| Moment at cartridge joint | 24.6 kNm | 64.3 kNm (joint stays closed by preload, margin 9.7) |
| Ring 1 | 60 thk, Ø260 bore | 70 thk, Ø340 bore |
| Mass, module + shell structure | 784 | 718 |

## Design options (Oct 26, 2026)

Option models: `spindle_mount_optS.step` (spherical, dry), `spindle_mount_optT.step` (32228 pair, dry). Calc: `calc_options.py`. Ratings used (SKF catalogue, proxies for Koyo/NTN): 23228 C₀ 1,250 kN; 29328 C₀ 2,850 kN; 32228 C₀ 1,000 kN, Y 1.4, Y₀ 0.8 (typical 322-series).

| | Spherical, dry (S) | Tapered pair, dry (T) | Rev E |
|---|---|---|---|
| Bearings | 23228 + 29328N + 23228 | 2 × 32228 back-to-back | 23228 + 29328N + 23228 |
| Thrust bearing s₀, jam / 800 kN | 4.62 / 3.45 | 1.53 / 1.21 | 4.62 / 3.45 |
| 23228 s₀ at L = 400 / 300 / 250 | 6.20 / 4.65 / 3.88 | — | 6.20 |
| Flange position | front of cartridge, on ring 1 front face | front of cartridge (one-piece block) | middle of cartridge |
| Housing ahead of ring 1 face | flange 40 + cover | flange 40 + cover | sleeve 218 + cover |
| Ring 1 face from shield front | 215 | 215 | 393 |
| Weld in thrust path | flange–tube CJP, 56 MPa, FoS 2.69 (A36) | none | none |
| Cartridge length / mass | 560 / 137 kg | 380 / 112 kg | 560 / 139 kg |
| Bearing module mass | 363 kg | 287 kg | 365 kg |
| End play | cover shims | rear nut | cover shims |
| Drive rear face | x = 1038 | x = 858 | x = 1038 |

- 32228 pair: s₀ at the jam case is 2.03 even at infinite spacing; the thrust term (Y₀ × Fa) governs. C₀ ≥ 1,311 kN needed at a 300 mm effective spread.
- Ring 1, its weld and the cartridge joint carry 64 kNm in S, T and rev E alike (FoS 1.62 ring bending, 2.07 weld).
- Viewer: tabs for rev G, rev F, spherical dry, rev E, rev D, rev C, rev B and a comparison table. The 32228 pair was dropped on Oct 26.

## Rev F (Oct 26, 2026): spherical dry cartridge + pyramid-frame cutterhead

Model: `spindle_mount_revF.step`. Calc: `calc_revF.py`. The 32228 tapered pair is dropped.

| Item | Rev F |
|---|---|
| Mount | Spherical dry cartridge: 23228 + 29328N + 23228, L = 280; flange at the cartridge front on ring 1 front face |
| Cartridge | 440 long, 113 kg; rear face x = 440 |
| Cutterhead layout | Daniel's: Ø630, 8 arms (76 × 50.8), hub disc Ø200, 24 positions |
| Cutters | Trapezoid carbide drag bits: base 22, tip 12.7, 22 tall, 14 thick, on 30 × 24 × 20 holders at the arm leading edge |
| Tracks | Gauge R 308.65 × 3 (arms at 0°, 135°, 225°); 21 single tracks at 12.7 down to R 41.95; centre cone placeholder |
| Frame | 8 struts 60 × 60 A572-50 from arm nodes (R 245, x = −315) to hub ring nodes (R 175, x = −220), 36.4° to axis, 118 long; centre tube Ø200 × 15 |
| Hub ring | Ø420 × Ø170 × 40; 16 × M20 on Ø250 to the adapter flange (PDB bolt pattern) |
| Head front (bit tips) | x = −402.8; arm front face x = −360.8 |
| Shield | Front edge x = −305 (behind the arms), rear x = 980 |
| Ring 1 face from shield front | 345 (depth legs 870) |
| Drive rear face | x = 918; overall bit tip to drive rear 1,321 (envelope 1,340) |
| Head mass (frame, bits, bolts) | 135 kg in the visual model (Daniel's flat head: 38.3 kg with bits) |

| Check | Case | Value | Allowable | FoS |
|---|---|---|---|---|
| 23228 s₀ | jam | — | — | 4.34 |
| 29328N s₀ | jam / 800 kN | — | — | 4.62 / 3.45 |
| Strut 60 × 60, axial + torque bending | LC3 | 89.8 MPa | 207 | 2.31 |
| Strut end CJP (base metal) | LC3 | 89.8 MPa | 207 | 2.31 |
| Hub ring hoop compression | LC3 | 47.3 MPa | 207 | 4.37 |
| Arm radial tension at node | LC3 | 31.2 MPa | 207 | 6.64 |
| Strut slenderness KL/r | — | 6.8 | — | no buckling |
| Side-load factor at front bearing, 1 + a/L | — | 1 + 462/280 = 2.65 | — | — |

Struts carry all thrust and moment in this check (centre tube ignored). Arm bending between the hub disc and the strut nodes is not covered; it stays with Daniel's head check. Struts sweep the slurry chamber between x = −315 and −220.

## Rev G (Oct 26, 2026): everything behind the bulkhead

Model: `spindle_mount_revG.step`. Calc: `calc_revG.py`. Ring 1 front face is x = 0 in this model. The only part ahead of ring 1 is the rotating cutterhead.

| Item | Rev G |
|---|---|
| Ring 1 | A572-50, 110 thk (from 4.5 in plate); Ø400 × 40 counterbore; Ø340 bore; seat (counterbore floor) at x = 40 |
| Cartridge | Flange Ø400 × 40 flush in the counterbore; Ø310 tube to x = 615; CJP flange-to-tube at x = 40; 145 kg |
| Cartridge to ring 1 | 16 × M12 on Ø370 into the seat (heads recessed), 2 × Ø16 dowels, O-ring at R192 on the seat |
| Seal carrier | Flush with the plate inside the cartridge bore: 3 lip seals 170 × 200 × 15 + 2 lantern rings on wear sleeve Ø170; face labyrinth (2 rings on the head hub); rear face clamps the front 23228 through shims (end play 0.10–0.20); 12 × M10 on Ø280 |
| Bearings | Front 23228 x = 70–158; 29328N x = 173–233; shoulder x = 233–263; rear 23228 x = 470–558; L = 400 |
| Head to shaft | Hub ring Ø420 × 40 splined directly onto the Ø130 shaft nose (no adapter), 8 mm off the plate; end plate on the shaft nose reached through a removable centre cap (6 × M10) |
| Cutterhead | As rev F: 8 arms, pyramid frame (8 struts 60 × 60 + centre tube), 24 trapezoid drag bits; arm back face x = −133, bit tips x = −225.8 |
| Chamber depth | 133 (arm back face to plate), swept by the struts |
| Slurry pipes, pressure taps | End flush at the plate |
| Shield | Front edge x = −128, rear x = 1157; ring 1 face 128 from shield front; depth legs 1047 |
| Drive rear face | x = 1093; overall bit tip to drive rear 1,319 |
| Masses | Shell weldment 397 kg; bearing module 317 kg; cutterhead 140 kg |

| Check | Case | Value | Allowable | FoS |
|---|---|---|---|---|
| Ring 1 lip at r = 200 (70 thk under seat) | LC3 | 119 MPa | 207 | 1.73 (corrected in rev H: 1.45) |
| Ring 1 at pipe holes (110 thk, Kt 2.5) | LC3 | 52 MPa | 207 | 4.01 |
| Ring 1 lip shear at r = 200 | LC3 | 16.7 MPa | 138 | 8.3 |
| Head spline Ø130 × 40, 20 kNm | — | 37.7 MPa | 262 | 6.9 |
| 23228 s₀ / 29328N s₀ (jam) | LC2 | — | — | 6.20 / 4.62 |
| Side-load factor at front bearing | — | 1 + 340/400 = 1.85 | — | — |
| Struts, ring 1 weld, flange CJP | — | as rev F / rev E | — | 2.31 / 2.07 / 2.69 |

Head removal: centre cap → end plate → head slides off the spline. Bearing service: head off → drive out the rear → 16 × M12 → bearing module out the front.
Counterbore inner corner is on the compression face of ring 1 under thrust; give it a 3 mm radius.

## Rev H (Oct 26, 2026): rev G simplified for manufacture

Model: `spindle_mount_revH.step`. Calc: `calc_revH.py`. Positions as rev G (ring 1 front face x = 0). Viewer: Rev H tab (default).

| Item | Rev H |
|---|---|
| Head to shaft | Keyless locking assembly 140 × 190 × 50 (Fenner B-LOC B400 140 mm: 28.2 kNm, 402 kN, hub pressure 165 MPa) in an A572-50 hub ring Ø340 × 50.8 at x = −133 to −83; screws face forward under the centre cap |
| Head thrust path | Spider → hub ring → journal sleeve (contact) → front 23228 inner ring → collar → backing ring → 29328N |
| Journal sleeve | Ø140 bore; Ø250 body x = −83 to −8; Ø170 seal journal x = −8 to 70; labyrinth rings on its rear shoulder; welded into the head, machined with it |
| Shaft | Ø140 plain from the nose (x = −133) to the collar; Ø165 collar x = 158–173; M140 × 2 for KM28; drive end Ø130 plain for a vendor shrink disc; M30 pull / push-off thread in the nose |
| 29328N shaft abutment | Backing ring Ø190 × Ø140 × 15 between collar and shaft washer (SKF da min 185) |
| Cartridge | Seamless tube 323.9 × 60 (E355 / S355J2H), turned to Ø318; ID 204 left as rolled at the housing shoulder x = 248–278 (SKF Da max 208); Ø250 H7 at the two 23228 seats, Ø241 at the 29328N, Ø252 relief between; 615 long, 148 kg; no welds |
| Cartridge to ring 1 | Groove Ø296 at x = 20–35 behind a 20 mm land; split flange (2 half rings, 35 thk, OD 399.8, 3 mm kerf at 12 and 6) in the groove and the ring 1 counterbore; thrust land → flange lip → ring 1 seat by contact; 16 × M12 10.9 on Ø370; 2 × Ø16 dowels at 3 and 9; 4 × Ø16 radial pins flange → tube land (torque); 2 × M10 across each split (handling); static O-ring on the tube in the ring 1 bore |
| Ring 1 | 110 thk; Ø400 × 35 counterbore (web 75 under the seat); Ø318.5 bore; no drilled passages |
| Seal carrier | As rev G; flange Ø273 × 9.4, 12 × M6 countersunk on Ø262 (flush; gussets pass 8 mm from the plate) |
| Grease | As first issued: 4 fittings on the tube OD behind ring 1. Superseded Oct 27 (seal-purge line in a groove on the tube OD only; see Grease under Anti-roll fins) |
| Cutterhead | Spider plate 50.8: 8 arms 76 wide + centre in one waterjet piece; 8 gussets 25 thk in the arm planes, 2 tabs each through slots in the spider; gusset-to-arm fillets 2 × 12; centre cap 30 thk in a 30 deep pocket, carries the 7 inner bits (R ≤ 118.15) and the cone, 8 × M8 countersunk; 24 trapezoid bits as rev F/G |
| Positions | Bearings, drive face x = 615, drive rear x = 1093, shield −128 to 1157, legs 1047, chamber 133: as rev G. Overall 1,319 |
| Masses | Shell weldment 405 kg; bearing module 335 kg (tube 148); cutterhead 141 kg |

| Check | Case | Value | Allowable | FoS |
|---|---|---|---|---|
| Locking assembly torque | torque | 20 kNm | 28.2 kNm | 1.41 |
| Hub ring OD for 165 MPa hub pressure | — | 320 needed | 340 fitted | — |
| Head moment into shaft, edge bearing (lever 139) | LC2 | 82.6 MPa | 310 | 3.76 |
| Shaft Ø140 at front 23228, bending | LC2 | 239 MPa | 393 | 1.65 |
| Tube land on flange lip, P/A + M/S | LC3 | 160 MPa | 310 | 1.94 |
| Land shear at R148 | LC3 | 43 MPa | 142 | 3.30 |
| Flange lip root shear | LC3 | 53 MPa | 138 | 2.58 |
| Tube at groove root, tension + bending | LC3 | 92 MPa | 213 | 2.32 |
| Tube at front seat, tension + bending | LC3 | 59 MPa | 213 | 3.59 |
| 29328N washer on as-rolled shoulder | LC3 | 64 MPa | 320 | 5.01 |
| Clamp needed on ring 1 seat vs 16 × M12 | LC2 | 197 kN | 784 kN | 3.98 |
| Ring 1 web, stepped plate 75 / 110, load at R180 | LC3 | 134 MPa | 207 | 1.55 |
| Ring 1 at pipe holes, Kt 2.5 | LC3 | 57 MPa | 207 | 3.64 |
| Arm + gusset at R165, thrust bending | LC3 | 74.5 MPa | 207 | 2.78 |
| Gusset-to-arm fillets 2 × 12, shear flow | LC3 | 82 MPa | 145 | 1.76 |
| Arm + gusset at R165, torque | torque | 12.4 MPa | 207 | 16.7 |
| Centre cap 30 thk, 7 bits | LC3 | 102 MPa | 207 | 2.03 |
| Anti-rotation pins 4 × Ø16, shear | torque | 156 MPa | 400 | 2.56 |
| Pin bearing on tube land | torque | 151 MPa | 320 | 2.11 |
| 23228 s₀ / 29328N s₀ | jam / 800 kN | — | — | 6.20 / 4.62, 3.45 |

Corrections to rev G found in this check:
- Ring 1 web: the rev G value (1.73) put the load at R200. With the load at the contact centroid (R185) and the 70 / 110 step, rev G is 1.45 at LC3.
- Rev G did not check the head moment into the shaft; a 40 mm splined hub ring has no path for 64 kNm.
- Rev G's Ø165 collar is below the 29328's shaft abutment (SKF da min 185).

Stock: Ovako hollow bar stops at OD 242.7, so the Ø340 hollow bar for a lip on the tube does not exist as stock. The lip moved to the split flange; the tube is stock seamless 323.9 × 60.

### Manufacture

| Part | Route |
|---|---|
| Ring 1 | Waterjet from 4.5 in A572-50 → Blanchard to 110 → lathe: Ø400 × 35 counterbore, Ø318.5 bore → tap 16 × M12 → weld |
| Cartridge tube | Saw 615 from 323.9 × 60 → lathe setup 1 (front): OD Ø318, land, groove, Ø250 H7 front seat, Ø252, Ø241, shoulder face → setup 2 (rear): Ø252 relief, Ø250 H7 rear seat, rear face → drill: M6 × 12, M16 × 12, grease drillings |
| Split flange | Waterjet from 1.5 in plate as 2 halves (3 mm kerf) → bolt together → lathe: OD, faces, lip → drill 16 × Ø13.5 + counterbores, M10 split screws; ream pins Ø16 through flange into the tube land with the halves fitted |
| Spider plate | Waterjet from 2 in plate with slots, LA access opening, holes → mill 30 deep cap pocket |
| Gussets, hub ring, cap | Waterjet from 1 in / 2 in / 1.25 in plate |
| Journal sleeve | Lathe from Ø255 bar |
| Head weldment | Gussets into slots, hub ring and sleeve on a fixture plate → weld → lathe, one setup: Ø190 LA bore, Ø140 bore, Ø170 journal, rear face |
| Bought | Locking assembly, shrink disc (with the drive), bearings, KM28, seals, dowels and pins |

### Assembly
1. Bench, shaft vertical: heat front 23228 onto the nose against the collar; backing ring; heat 29328N shaft washer + rollers onto the shaft.
2. Tube front up; housing washer onto the shoulder; lower the shaft; spacer; heat rear 23228; KM28.
3. Split-flange halves into the groove, 2 × M10 each side; pins in.
4. Carrier with seals and lanterns over the nose; shim to 0.10–0.20 end play; 12 × M6.
5. Shell front up: lower the module through ring 1; 16 × M12; ream and fit 2 × Ø16 dowels (first assembly).
6. Lower the head over the nose until the journal sleeve seats on the front 23228; torque the locking assembly screws; centre cap.
7. Drive from the rear onto the plain Ø130 end; shrink disc; 12 × M16 + 3 dowels.

Head removal: cap off → release the locking assembly → M30 push-off screw against the shaft nose.

### Drive (Oct 27, 2026): hydraulic motor, adapter, coupling

Model: `spindle_mount_revH_detail.step` (`build_revH_detail.py`, `asm_revH.py`). Viewer: Rev H tab (detailed) and Rev H assembly tab (52 steps).

| Item | Value |
|---|---|
| Motor | Poclain MS18 shaft motor, 2,812 cc/rev, 2A50 bearing support, W90 × 3 × 28 spline shaft (catalogue); 112–152 kg |
| Torque per bar | 44.71 Nm/bar theoretical; 6 kNm at 134 bar (141 at 95 % efficiency); 10 kNm at 224 bar (235); max 17.9 kNm |
| Flow at 12 rpm | 33.7 L/min + leakage; 7.5 kW shaft power at 6 kNm |
| Adapter | Weldment: front flange 25 thk Ø380 with Ø250 pilot into the cartridge bore; 14 in XS pipe (Ø355.6 × 12.7); rear flange 30 thk Ø400 with Ø282 bore for the motor spigot; 2 windows 130 × 140 at 3 and 9 o'clock; machined after welding; x = 600–877 |
| Adapter to cartridge | 12 × M16 10.9 on Ø280 (heads inside the bell) + 3 × Ø16 dowels (existing cartridge pattern) |
| Motor to adapter | 8 × M20 10.9 on Ø335, Ø282 spigot (placeholder pattern until the certified drawing) |
| Coupling | Jaw type, plug-in: spindle hub Ø280 on the Ø130 shaft end with an internal 130 × 180 locking assembly (screws reached through the jaw ring before the motor goes on); polyurethane spider; motor hub with W90 spline bore. Rating ≥ 10 kNm nominal, ≥ 20 kNm max; size open |
| Grease | Superseded Oct 27: bearings grease-packed at assembly, no relube lines; seal-purge line only (see Grease under Anti-roll fins) |
| Hoses | A, B (3/4 in) and case drain from the motor rear, back through the casing string |
| Overall | Bit tip x = −225.8 to motor rear x = 1225: 1,451 (+111 over 1,340); motor rear 68 past the shield rear |
| Masses | Shell 405 (446 with fins), bearing module 329, cutterhead 143, drive 281 kg (motor at catalogue 152) |

| Check (20 kNm) | Value | FoS |
|---|---|---|
| Adapter tube torsion, windows Kt 3 | 34 MPa vs 138 | 4.1 |
| Adapter to cartridge, 12 × M16 slip μ 0.30 / 0.15 | 46.0 / 23.0 kNm | 2.30 / 1.15 |
| Adapter dowels alone, 3 × Ø16 | — | 1.86 |
| Motor to adapter, 8 × M20 slip μ 0.30 / 0.15 | 57.2 / 28.6 kNm | 2.86 / 1.43 |
| Overhung motor on the adapter | 0.27 kNm | — |

Assembly sequence (52 steps, shop orientation; collision-checked by replaying every motion against the model, `audit_asm.py`): shell standing on its rear end with 3 gauge legs (1,047) → ring 1 on the legs → slurry pipes through ring 1 → ring 1 fillet + pipe seal welds → legs out → saddles from the rear → taps → anti-roll fins → head weldment face-down: spider, hub ring, gussets (tab-and-slot, inner edges on the hub ring), journal sleeve, welds, machining; turned face-up for holders → bearing module on the bench (spindle nose-down for backing ring and 29328N shaft washer; nose-up for the front 23228; tube front-up with the housing washer; spindle lowered in on an M30 eye bolt; module turned over for spacer, rear 23228, MB28 + KM28; turned back for carrier and seals, O-ring and grooved purge line, split flange, split screws and radial pins) → module lowered through ring 1 from the front → head lowered onto the nose, locking assembly, centre cap → machine turned rear-up: purge supply, adapter dowels, adapter, adapter screws, spindle hub, spider, motor with hub, motor screws, hoses → horizontal on the cradle. Final replay (Oct 27; every step sampled at up to 90 frames, flag threshold 0.3 cm³ above the finished-state overlap): 0 collisions in 52 steps. Order fixes on Oct 27: hub ring before gussets; pipes before the ring weld; saddles from the rear; no fittings standing above Ø318 while the module passes ring 1; one pivot for groups that move together.

### Weight on the cantilevered mount (Oct 27, 2026)

Calc: `calc_support.py` (masses and CGs from the detailed model; seat plane x = 35).

| Item | Value |
|---|---|
| Hung off ring 1: bearing module / head / drive | 329 kg at x = 279 / 143 kg at x = −117 / 281 kg at x = 922 (753 kg, 7.39 kN) |
| Whole machine | 1,200 kg, CG x = 422 |
| Weight moment at the seat, horizontal | 3.02 kNm head on, 3.23 kNm head off |
| Weight moment at the adapter joint (x = 615) | 0.85 kNm |

| Check | Case | Value | Limit | FoS |
|---|---|---|---|---|
| Moment at the seat vs jam design moment | 1 g | 3.23 kNm | 64.3 | 19.9 |
| Same | 3 g transport | 9.69 kNm | 64.3 | 6.6 |
| M12 tension added by weight vs preload | 1 g / 3 g | 2.2 / 6.6 kN | 49.0 | 22.4 / 7.5 |
| Weight shear vs flange friction (μ 0.30) | 3 g | 22.2 kN | 235 | 10.6 |
| Ring 1 bore bearing | 3 g | 0.93 MPa | 310 | 335 |
| Ring 1 weld from weight | 3 g | 6.1 MPa | 145 | 23.8 |
| Cartridge tube bending behind ring 1 | 3 g | 4.3 MPa | 213 | 50 |
| Adapter M16 tension added vs preload | 3 g | 3.0 kN | 91.2 | 30 |
| Ring 1 web, LC3 + weight moment | design | 137 MPa | 207 | 1.51 |
| Seat clamp needed, LC2 jam + weight | design | 237 kN | 784 | 3.3 |
| M12 stress amplitude, 10 kNm operating swing | fatigue | 8.0 MPa | 48.9 | 6.1 |
| M12 stress amplitude, full jam swing | fatigue | 51.5 MPa | 48.9 (infinite life) | 0.95 |
| Drive-end sag from tube bending | 1 g | 0.008 mm | — | — |

Bolts carry tension only while the joint stays clamped (no slip, no separation); the weight is carried by the Ø318.5 bore fit and flange friction. Tightening torque at 70 % proof (K 0.17): M12 100 Nm, M16 248 Nm, M20 484 Nm.

### Anti-roll fins (Oct 27, 2026)

Calc: `calc_fins.py`. Method: resisting torque = Σ q_ult × effective projected area × radius ≥ FS × max torque; clay q_ult = Nc × cu; only fin height beyond the 10.2 mm radial overcut counts.

| Item | Value |
|---|---|
| Fins | 4 × 20 thk × 70 high × 990 long, A572-50; x = 150–1140; 30° lead ramp (121) with knife edge, 45° tail ramp (70); 2 × 8 mm fillets |
| Positions | 1, 3, 9 and 11 o'clock (30°, 90°, 270°, 330°): clear of the launch rails at 5 and 7 and the lubrication ports at 10, 12 and 2 |
| Effective area beyond the overcut | 0.0527 m² per fin, 0.211 m² total; centroid R344 |
| Torque to resist | 10 kNm interlock (11.2 kNm at 250 bar relief) |
| Envelope over the fins | Ø750 (cut bore Ø630): launch portal or seal needs notches |
| Added jacking force | Thrust_Model, Anti_Roll_Fins tab (τ basis, c_u 75 for ploughing): 1.6 kN ploughing + fin-face friction on 0.485 m² = 5.5 kN lubricated, 12.3 kN dry, 19.8 kN dry + breakout. Governing design thrust 649.3 → 674.0 kN (thrust cap FoS 0.94 → 0.91); reach 16.6 → 16.2 m lubricated, 8.7 → 8.4 m dry. calc_fins.py basis (α 0.5 × c_u 50 adhesion): 11.6 kN |
| Mass | 40.5 kg |

| cu (kPa) | Nc | q_ult (kPa) | T_resist (kNm) | FoS on 10 kNm | FoS on 11.2 kNm |
|---|---|---|---|---|---|
| 25 | 6 | 150 | 10.9 | 1.09 | 0.97 |
| 25 | 9 | 225 | 16.3 | 1.63 | 1.46 |
| 50 | 6 | 300 | 21.7 | 2.17 | 1.94 |
| 50 | 9 | 450 | 32.6 | 3.26 | 2.91 |
| 75 | 6 | 450 | 32.6 | 3.26 | 2.91 |

Not counted: lubricated shield skin shear 3–8 kPa = 2.3–6.0 kNm of roll resistance. Fin structure at 20 kNm: 14.5 kN per fin; plate bending 9.9 MPa (FoS 20.8), fillets 7.3 MPa (19.8), shell wall local bending 24.6 MPa (8.4), ring 1 weld torsion 3.8 MPa. Net side force from the asymmetric pattern at 20 kNm: 25 kN (32 kPa on the shield side).

Grease (Oct 27): bearings grease-packed at assembly; relube drillings removed. The seal-purge line (Ø8) lies in a 14 × 9 groove along the tube OD from the port at x = 125 to x = 600, so nothing stands above Ø318 while the module passes through ring 1; the supply line is connected at x = 600 after installation.

### Thrust ring at the shield rear (Oct 27, 2026)

Thrust ring Rev A (`docs/thrust-ring.md`) added to the detailed model at launch, before the first jacking pipe: front face on the shield rear end, x = 1,157.0 to 1,233.2; 4 × Chief WT 5 × 24 at R260, 2, 4, 8 and 10 o'clock; assembly phase 7, steps 53–55 (55 steps in total). Collision replay of all 55 steps (threshold 0.3 cm³): 0 collisions. STEP of the ring alone: `out/step/thrust_ring_revA.step`. STEP part names are now ASCII (Ø → D, × → x).

| Interface | Value |
|---|---|
| Seal-purge supply line, Ø10 at R209, 30° | Passes through the ring annulus (bore R200): 5.98 cm³ overlap (`tring/gsupply`) |
| Slurry pipe bores at the shield rear, R212.5–277.5 at 12 and 6 | Covered by the ring front face (annulus R200–304.8) |
| Motor body / port bosses / hoses in the Ø400 bore | Radial clearance 60 / 94 / 103 |

## Open

- Drive: Poclain MS18 modelled (Oct 27). Need the certified drawing (flange pattern, body), coupling size selection, and a decision on the +111 mm over 1,340 (accept, direct-mount hollow-spline motor, or offset motor).
- Locking assembly: B-LOC B400 140 gives 1.41 on 20 kNm. Tollok TLK450 140 × 190 is 64.6 kNm by Rexnord part code (width to confirm).
- Tube stock: seamless 323.9 × 60 E355 is a European stock size; find a US source or equivalent (OD ≥ 320, ID ≤ 206).
- Centre cap and inner bit layout with Daniel (7 bits on the cap).
- Soil cu from the geotech report: fins give FoS 1.09 alone at cu 25 kPa.
- Launch portal / seal notches for the Ø750 fin envelope.
- Koyo: C₀, C, Y₀, misalignment limits; 23228 quantity; 23228 inner ring as a thrust spacer (≈ 128 MPa face stress).
- Ring 1 FEA (rev H web FoS 1.51 with weight added, stepped-plate model).
- Depth 393: confirm from the cutterhead + adapter stack.
- Shell pipe grade (A53 Gr B assumed).
- Ring 1 pipe holes leave 8.6 mm between pipe and shell bore at 12 and 6; ring fillet runs into the pipe weld there.
- Chamber depth 133 with 8 gussets sweeping it (rev H): confirm slurry feed/discharge flow with Jack.
- Seal-purge supply line route behind x = 1,157: at R209 it crosses the thrust ring annulus (bore R200).
- Slurry pipe ends at the shield rear (R245): covered by the thrust ring front face when there is no jacking pipe.
