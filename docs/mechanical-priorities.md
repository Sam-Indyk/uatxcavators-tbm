# Mechanical Lead — Urgent Items (updated Oct 26, 2026)

Sources: Gantt (edited Oct 18), Internal Presentations Oct 18 slide, Gmail, Calendar. No Slack activity found since Oct 11.

## Overdue / due this week
1. Polaris Build Week 7 logs (TBC + UATXcavators) — due Sun Oct 18; no "received" confirmation in inbox → OVERDUE.
2. Select cutterhead motor (Sam + Eitan) — Gantt due 10/18, Not started → OVERDUE. Purchase due 10/25. Drive basis still unsettled: $30k plan = owned SEW RF127R77 gearmotor; PDB = hydraulic motor; Gantt still runs hydraulic cylinders/HPU, with "Hydraulic vs electric considerations" (Eitan) due 10/25. Mayr Corp offered a SlipHub torque limiter (Oct 22) for the electric option. Rev H drive interface: envelope ≤ Ø400 × 478, Ø250 f7 pilot, plain Ø130 shaft end (hollow output + shrink disc), 12 × M16 on Ø280 + 3 × Ø16 dowels. HMB100 (Ø502) does not fit.
3. Bearing housing (Sam) — due 11/1. Rev H design in `claude/spindle-mount.md`. Koyo (Matt Roberts): C0, C, Y0 and misalignment limits for 29328N + 23228; 23228 quantity (3 needed: front, rear, spare); OK to use the 23228 inner ring as a thrust spacer. Confirm the Koyo in-kind order shipped (Simrin sent address Oct 16). SKF $2,000: seals, KM28/MB28, hook spanner, grease, fitting tool kit.
4. Reply to Dean Staley on Billy Brooke's equipment comments (asked Oct 14: helpful / already considered / not useful) + add incidentals line items (UATXcavators vs Bastrop center). Mechanically relevant: GML-3280 swing-over-cross-slide may not fit 24 in shell-end facing; no 24 in / 600 mm metrology budgeted. Rev E ring 1 is pre-machined (waterjet + Blanchard + lathe bore); skim only if the seat is out of flatness after welding (reach 393 from the front end).
5. Spec pumps for conditioning + lube (Sam + Jack) — due 10/25.

## Next 2–4 weeks (Sam owns/co-owns)
- Design pipes (machining) + jack-locking (w/ Edward) — due 11/1, Not started.
- Thrust ring / jacking frame design (w/ Edward) — due 11/8, Not started; depends on hydraulic-vs-electric thrust decision.
- Design mucking/lubing tubes + holders (w/ Jack, Halyn) — due 11/15. Slurry pipes at 12 (feed) and 6 (discharge), R245, welded through ring 1 (rev E), saddles at x = 760.
- Structures BOM; Lube+Cond+Muck BOM; Pitting & Jacking BOM — due 11/15.
- Winter-break build plans: structures, cutterhead (w/ Daniel), lube/cond/muck, pitting/jacking — due 11/15.
- FDP starts 11/1, due 12/13.

## Decided since Oct 12
- Rev H (Oct 26): rev G made shop-friendly — locking assembly instead of splines, seamless-tube cartridge with a split flange (no cartridge weld), waterjet spider + tab-and-slot gussets. Corrections to rev G: ring 1 FoS 1.45 (not 1.73), head moment path, 29328 backing ring Ø190.
- Rev G (Oct 26): everything behind the bulkhead — flange flush in a counterbore (ring 1 110 thk), seals in a carrier inside the cartridge, head splined straight onto the shaft, pipes flush. L = 400.
- Rev F (Oct 26): spherical dry cartridge (housing behind ring 1, L = 280) + pyramid-frame cutterhead with trapezoid drag bits on Daniel's layout. 32228 tapered pair dropped (s₀ 1.53 at jam).
- Spindle mount rev E (Oct 26): one welded ring (machined before welding), one cartridge carrying Koyo 23228 + 29328N + 23228 and the drive; cartridge bolted + dowelled to ring 1. Supersedes rev D (second ring + rear plate) and rev C.
- Bolted cartridge housing. Pipes collected from Westbrook (Done). Purchase Bearings marked Done.
- CAD moved to Fusion 360.

## Carried / open technical
- Ring 1 FEA (governing; rev H web FoS 1.55 at the envelope case, stepped-plate model).
- Ring 1 depth (393 from shield front) to confirm from the cutterhead + adapter stack.
- Anti-roll restraint for launch rails (still open).
- Bentonite vs ACP-214 compatibility bench test.
- Reaction wall capacity resolution (Edward) — was due 10/18.
