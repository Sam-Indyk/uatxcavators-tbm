# Mechanical Lead — Urgent Items (updated Oct 28, 2026)

Sources: Gantt (edited Oct 18), Internal Presentations Oct 18 slide, Gmail, Calendar. No Slack activity found since Oct 11.

## Overdue / due this week
1. Polaris Build Week 7 logs (TBC + UATXcavators) — due Sun Oct 18; no "received" confirmation in inbox → OVERDUE.
2. Select cutterhead motor (Sam + Eitan) — Gantt due 10/18, Not started → OVERDUE. Purchase due 10/25. Drive basis decided Oct 27: hydraulic motor (not the SEW RF127R77 gearmotor). Poclain MS18 shaft motor on the Rev I drive: adapter bell housing with a Ø300 rear bore and a 20 mm motor pilot plate (8 × M20 on Ø335, placeholder); coupling selected Oct 28: KTR ROTEX 160, 64 ShD spider, steel hubs (B-LOC B400 130 × 180 in hub 1, W90 spline in hub 2); pump relief 259 bar (rules: +10 %). Needed: Poclain certified drawing, KTR confirmation of the shortened hubs, and a decision on the +111 mm over 1,340 (accept, hollow-spline motor, or offset motor). HMB100 (Ø502) does not fit. Thrust side still open: Gantt runs hydraulic cylinders/HPU, "Hydraulic vs electric considerations" (Eitan) was due 10/25.
3. Bearing housing (Sam) — due 11/1. Rev I design in `claude/spindle-mount.md`; full design manual `claude/manual-00-overview.md` … `manual-09-bom.md` (loads, every part with equations, FEA, lift plan, BOM). Koyo (Matt Roberts): C0, C, Y0 and misalignment limits for 29328N + 23228; 23228 quantity (3 needed: front, rear, spare); OK to use the 23228 inner ring as a thrust spacer. Confirm the Koyo in-kind order shipped (Simrin sent address Oct 16). SKF $2,000: seals, KM28/MB28, hook spanner, grease, fitting tool kit.
4. Reply to Dean Staley on Billy Brooke's equipment comments (asked Oct 14: helpful / already considered / not useful) + add incidentals line items (UATXcavators vs Bastrop center). Mechanically relevant: GML-3280 swing-over-cross-slide may not fit 24 in shell-end facing; no 24 in / 600 mm metrology budgeted. Rev E ring 1 is pre-machined (waterjet + Blanchard + lathe bore); skim only if the seat is out of flatness after welding (reach 393 from the front end).
5. Spec pumps for conditioning + lube (Sam + Jack) — due 10/25.

## Next 2–4 weeks (Sam owns/co-owns)
- Design pipes (machining) + jack-locking (w/ Edward) — due 11/1, Not started.
- Thrust ring / jacking frame design (w/ Edward) — due 11/8, Not started; depends on hydraulic-vs-electric thrust decision.
- Design mucking/lubing tubes + holders (w/ Jack, Halyn) — due 11/15. Slurry pipes at 12 (feed) and 6 (discharge), R245, welded through ring 1 (Rev H), saddles at x = 950.
- Structures BOM; Lube+Cond+Muck BOM; Pitting & Jacking BOM — due 11/15.
- Winter-break build plans: structures, cutterhead (w/ Daniel), lube/cond/muck, pitting/jacking — due 11/15.
- FDP starts 11/1, due 12/13.

## Decided since Oct 12
- Oct 28: Rev I after a full review with 3D FEA (manual-00 lists the 15 changes): ring 1 Ø384 × 30 counterbore in A572 Gr 42 (Gr 50 plate stops at 4 in), slurry pipes A1085 Ø76.2 × 6.35 welded at both ring faces and run through U-notches in thrust ring Rev B; ROTEX 160 coupling + Ø300 adapter bore + motor pilot plate; window guards; 4 lifting bosses with Crosby HR-125M M20 hoist rings; seal-purge supply rerouted to R185; split-flange screws M8; load cases LC1-LC4 from F = 4 p A (613 / 801 / 901 kN) plus a side force; thrust ring register (spigot Ø589.5 × 10 in a Ø590.6 × 12 shield rear counterbore, ported from the Oct 27 local work, saved on branch local-oct28-register). 174 checks; 1 below requirement (gauge bit holders overhang the arm end: cutterhead layout).
- Oct 28: Fusion link. Claude works in Fusion through the Autodesk Fusion MCP server; the UATXSync add-in (repo `fusion/`) pulls GitHub main every 2 min and imports changed scripted parts and the 109 design constants into the Fusion design "UATX scripts reference" (Shamir V1); Export to repo writes Fusion designs back.
- Oct 27: hydraulic motor for the cutterhead (Rev H drive adapter + jaw coupling); weight check on the cantilevered mount (3.23 kNm at the seat, no rear support); anti-roll fins 4 × 20 × 70 × 990 at 1, 3, 9, 11 o'clock (Thrust_Model Anti_Roll_Fins tab: +5.5 kN lubricated, governing design thrust 674 kN); 52-step assembly sequence, collision-checked; scripts and STEP in GitHub Sam-Indyk/uatxcavators-tbm.
- Rev H (Oct 26): rev G made shop-friendly — locking assembly instead of splines, seamless-tube cartridge with a split flange (no cartridge weld), waterjet spider + tab-and-slot gussets. Corrections to rev G: ring 1 FoS 1.45 (not 1.73), head moment path, 29328 backing ring Ø190.
- Rev G (Oct 26): everything behind the bulkhead — flange flush in a counterbore (ring 1 110 thk), seals in a carrier inside the cartridge, head splined straight onto the shaft, pipes flush. L = 400.
- Rev F (Oct 26): spherical dry cartridge (housing behind ring 1, L = 280) + pyramid-frame cutterhead with trapezoid drag bits on Daniel's layout. 32228 tapered pair dropped (s₀ 1.53 at jam).
- Spindle mount rev E (Oct 26): one welded ring (machined before welding), one cartridge carrying Koyo 23228 + 29328N + 23228 and the drive; cartridge bolted + dowelled to ring 1. Supersedes rev D (second ring + rear plate) and rev C.
- Bolted cartridge housing. Pipes collected from Westbrook (Done). Purchase Bearings marked Done.
- CAD moved to Fusion 360.

## Carried / open technical
- Ring 1 FEA done (Rev I): pipe-hole wall membrane + bending 187 MPa at LC3, FoS 1.55 on Fy 290; Rev H's Ø400 counterbore left a 6.5 mm wall (461 MPa peak).
- Ring 1 depth (393 from shield front) to confirm from the cutterhead + adapter stack.
- Anti-roll: fins designed (Oct 27). Still open: launch portal notches for the Ø750 fin envelope; roll restraint before the fins engage; soil c_u from the geotech report (fins need ≥ 46 kPa for FoS 2).
- Bentonite vs ACP-214 compatibility bench test.
- Reaction wall capacity resolution (Edward) — was due 10/18.
