import sys
s=open(sys.argv[1]).read()
s=s.replace("# Cutterhead Spindle Mount — Rev C (Oct 23, 2026)","# Cutterhead Spindle Mount — Rev C (Oct 23, 2026; structural check Oct 25)")
s=s.replace("| Ring 1 weld, single 10 mm fillet / double | 62 / 31 MPa (allowable 144) |\n","")
s=s.replace("| Bulkhead plate, 40 thk: shear / bending at 800 kN | 15 / 45 MPa |\n","")
s=s.replace("| Plate-to-ring gasket band stress at 800 kN | 16 MPa |\n","")
s=s.replace("| Ring 1 | 40 thk, Ø584.2 OD × Ø500 ID, x = 70–110; notched at 12 and 6 for pipes |",
 "| Ring 1 | 40 thk, Ø584.2 OD × Ø500 ID, x = 70–110; notched at 12 and 6 for pipes; 12 mm continuous front fillet |")
s=s.replace("| Ring 2 | Same section as ring 1, x = 520–560 |","| Ring 2 | Same section as ring 1, x = 520–560; 8 mm continuous rear fillet |")
s=s.replace("Ring 1 single front fillet carries 800 kN at 62 MPa.\n","Ring 1 front fillet: 12 mm leg, 3 passes. Fit-up gap ≤ 1.6 mm; leg increased by the gap above that (AWS D1.1). Preheat 66 °C (ring 40 thk, AWS D1.1 Category B).\n")
check='''## Structural check (Oct 25, 2026)

Method: AISC 360 ASD, AWS D1.1. Fillet welds treated as a line: every load becomes force per mm of weld (direct axial P/2πR, bending M/πR², torsion T/2πR², transverse V/πR), combined as a vector, divided by throat (0.707 × leg). Calc: `weld_calc.py`.

Allowables (ASD, Ω included): weld throat 0.30 F_EXX = 145 MPa (E70); base metal shear at fusion face 0.40 Fy; bending/tension 0.60 Fy; bearing on finished surfaces 0.90 Fy. Fy = 250 (A36 rings, plates, cartridge), 240 (A53 Gr B shell, assumed).

| Case | Loads |
|---|---|
| LC1 structural | 800 kN thrust + 26.8 kN (1 bar on bulkhead) |
| LC2 jam | 590 kN + 26.8 kN + 62 kNm |
| LC3 envelope | 800 kN + 26.8 kN + 62 kNm |
| LC4 torque | 20 kNm (10 kNm interlock × 2) + motor module weight × 2 |

| Joint | Mode | Governing case | Stress | Allowable | FoS |
|---|---|---|---|---|---|
| 29328N washer on shoulder | compression | LC1/LC3 | 54.9 | 225 | 4.10 |
| Cartridge shoulder root Ø241 × 30 | shear | LC1/LC3 | 36.4 | 100 | 2.75 |
| Cartridge tube Ø310/Ø252 | tension | LC1/LC3 | 32.3 | 150 | 4.64 |
| Flange on bulkhead plate | compression | LC3 | 27.4 | 225 | 8.22 |
| Flange on bulkhead plate | min contact (gap if < 0) | LC2 | −0.7 | 0 | — |
| Cartridge bolts 12 × M16 10.9 | tension per bolt, kN | LC2 | 54.4 | 91 (preload) | 1.68 |
| Bulkhead plate 40 thk | shear | LC3 | 26.9 | 100 | 3.72 |
| Bulkhead plate 40 thk | bending | LC3 | 80.6 | 150 | 1.86 |
| Plate on ring 1 (gasket band) | compression | LC3 | 26.4 | 225 | 8.52 |
| Plate on ring 1 (gasket band) | min contact | LC2 | 2.5 | 0 | — |
| Ring 1 weld, 1 × 10 fillet | throat shear | LC3 | 96.4 | 145 | 1.50 |
| Ring 1 weld, 1 × 10 fillet | shell base metal | LC3 | 68.2 | 96 | 1.41 |
| **Ring 1 weld, 1 × 12 fillet** | throat shear | LC3 | 80.4 | 145 | 1.80 |
| **Ring 1 weld, 1 × 12 fillet** | shell base metal | LC3 | 56.8 | 96 | 1.69 |
| Ring 1 weld, 2 × 10 fillet | throat shear | LC3 | 48.2 | 145 | 3.00 |
| Shell wall | axial + bending | LC3 | 52.2 | 150 | 2.88 |
| Ring 2 weld, 1 × 8 fillet | throat shear | LC4 | 6.7 | 145 | 21.7 |
| Motor plate to ring 2, 16 × M12 | slip per bolt, kN | LC4 | 4.6 | 15 | 3.19 |
| Motor to plate, 12 × M20 | slip per bolt, kN | LC4 | 8.8 | 43 | 4.87 |
| Shell wall | torsion | LC4 | 2.8 | 96 | 34.1 |

Not covered: fatigue (≈ 3,600 head revolutions and 10 pushes per 5 m drive), shaft spline, coupling (vendor rating), bearing ratings (Koyo data pending), FEA of plate and ring.

'''
s=s.replace("## Geometry\n", check+"## Geometry\n",1)
s=s.replace("- Ring 1 face flatness after welding: facing vs epoxy chock.","- Ring 1 face flatness after welding: facing vs epoxy chock.\n- Shell pipe grade (A53 Gr B assumed, Fy 240) and plate grade (A36 assumed) to confirm.\n- Gasket datasheet: rated surface stress ≥ 26.4 MPa.")
open(sys.argv[2],'w').write(s)
