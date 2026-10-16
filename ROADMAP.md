# Roadmap

**Mission:** Swayam Labs builds the smallest open "design file in, machine out" cell, and
measures how much of that loop an AI engineer closes. Why this and not something else:
`docs/DIRECTION.md`.

**Two metrics.**
- **Closure %**: share of human labour-minutes to build the target machine that machines
  perform with no human touch (denominator: the filmed human build).
- **Design iterations per week with no human CAD**: how fast the engineer improves a
  machine from its own logged failures.

**Rules of the ladder.** Each toy adds exactly one capability the next toy needs. Each is
pre-registered in `predictions/`, judged by a sensor or bought instrument, audited by
`closure-auditor`, and public. Every machine built is used by the cell afterwards. Dates
are proposals and are meant to be hard: change them, do not soften them.

**Hardware:** SO-101 arriving 2026-10-17. No printer or cameras yet; see `SHOPPING.md`.
The printer is the precision machine (0.1 mm); the arm is the material handler (error
budget: ~4 mm camera-guided, ~0.5 mm same-direction return). Design accordingly.

**Adopt, don't build:** LeRobot + SmolVLA / GR00T for learned skills; LeRobot's placo
kinematics (not our own IK); MHS-shaped capability descriptions for the agent-hardware
interface; agentcad or cad-skill for CAD; the Fast-UMI gripper for demonstration data;
NIST Task Board #1 / Peg-in-Bench geometries as insertion verifiers; aftermarket
printer ejection instead of arm harvesting; sim only for kinematics checks. The full
map of what exists, and what we already duplicated, is `docs/LANDSCAPE.md`.

## Now: the first 72 hours (Oct 17–19)

- [ ] Order the day-one items in `SHOPPING.md` (dial indicator is the critical one).
- [ ] Printer decision re-opened by the landscape sweep: the cell should not use the
      arm to harvest parts; the printer ejects them. Choose between Bambu A1 + FarmLoop
      (documented unattended loop) and Prusa MK4S (open API but no "set ready" endpoint
      as of 2025 firmware) on that basis, then order this week.
- [ ] Swap `src/swayam/ik.py` for LeRobot's placo kinematics (`uv sync --extra kinematics`);
      keep our round-trip tests as the acceptance check; delete ours at parity.
- [ ] Day 1: build the arm with the camera running (`baseline/BUILD_FILMING.md`). The
      step log is the closure denominator and cannot be redone.
- [ ] Day 2: calibrate, bring up the real backend, sign/zero check (`docs/DAY_ONE.md`).
- [ ] Day 3: run `predictions/2026-10-15-arm-repeatability.md` exactly as written; write
      the result in a new file; auditor checks it.
- [ ] Apply to the Model Hardware Standard research preview; restructure the arm tools'
      descriptions as capability files (what it measures, what it adjusts, its limits).

## Toy 0 — Baseline (target: 2026-10-26)

Repeatability measured against the prediction; single-joint backlash loaded and
unloaded; human build filmed and logged. Zero-shot hardware baseline: the sim task's
instruction and seeds rerun on the real arm with the printed bed region and a bought
tray; metrics as in `studies/out/sim_pick_place_zero_shot_v2.md`.

Also: hand-eye calibration with OpenCV `calibrateHandEye` and the VLA-REPLICA AprilTag
script (no calibrator of our own); contact force at working speed measured with a scale
and recorded against ISO/TS 15066 Annex A; a BasicMOST estimate beside the filmed times.

**Exit:** prediction verdict recorded; `baseline/build_log.csv` complete; measured ARM
ERROR written into `config/limits.json` and the design rules.

## Toy 1 — Fixture autogen (target: 2026-11-30, needs the printer)

Given any part's STL, the engineer generates a locating nest with a two-stage funnel
(outer sized to placement error, inner to repeatability), prints it, and the arm places
the part in it. Before designing: read Fabrica's pickup-fixture generator (geometry
processing + bin packing, CoRL 2025) and fixturemate's rules; reuse, do not reinvent.
Verification parts: Peg-in-Bench pegs and NIST Task Board #1 sizes (4/8/12/16 mm)
first, so our numbers are comparable; then three SO-101 parts of different shapes.
Count design iterations to 10/10.

**Exit:** three parts, each 10/10 placements by AprilTag pose, 95% intervals reported;
design iterations per part logged; zero human CAD edits (auditor-confirmed).

## Toy 2 — Self-upgrade (target: 2026-12-15)

Snap-on fingertip pads, designed by the engineer from the measured grasp failures,
fitted by the arm to itself through a docking fixture.

**Exit:** arm-made pads beat the stock jaws on grasp success over a fixed 10-object set,
30 grasps each, Wilson 95% intervals not overlapping; fitted with zero human touches.

## Toy 3 — Skill from human video (target: 2027-01-31)

Print a Fast-UMI handheld gripper (its robot-side unit adapts to any arm). Record 50
human demonstrations of "tray → fixture" with a phone camera, through LeRobot's
recording stack (evaluate phosphobot as middleware first); fine-tune SmolVLA (or GR00T
N1.6 via LeRobot on a rented GPU). Compare
three ways of doing the same step: scripted with fixtures, learned policy, Claude
zero-shot. Report success, time, and LLM-minutes per cycle for each.

**Exit:** a pre-registered three-way comparison on 30 trials each; the winner becomes
the cell's default for that step and the reason is written down.

## Toy 4 — Redesign for the robot (target: 2027-02-28)

One SO-101 part (candidate: the wrist-roll housing) redesigned by the engineer as a
snap-fit, printable subassembly the arm can put together; printed; assembled by the arm;
tested against the original part's function.

**Exit:** closure % on that subassembly; design iterations logged; the redesigned part
installed on the arm and used from then on.

## Toy 5 — Design file in, mechanism out (target: 2027-04-15)

The herringbone planetary gearbox for the STS3215 output: printed in place, at most 2
vitamin types embedded mid-print by the arm (pause-and-embed), kit fed by the
printer-ejects → tray loop. Tolerance stack-up and FMEA before the first attempt; gauge
R&R on the test stand. Any insertion step is first scored on NIST Task Board #1 peg
sizes; if learning is needed for insertion, start from NVIDIA AutoMate / IndustReal in
Isaac Lab, not from scratch.

**Exit:** 30 gearboxes built unattended; Cpk >= 1.33 on backlash and torque at slip;
5 checked with bought instruments; zero LLM-minutes per cycle; cost per gearbox
against a human at $37.81/h.

## Toy 6 — The cell as an API (target: 2027-05-31)

Arm, printer and cameras exposed through MHS-style capability files and safety
interlocks, with VLA-REPLICA's cross-lab reproducibility protocol (fixed camera poses by
AprilTag, published calibration, in- and out-of-distribution test sets). An outsider
sends a design file and receives a fabricated, verified part, with the run log public.

**Exit:** one stranger, one design file, one verified part, reproduced from the repo.

## Toy 7 — Child arm (north star 1, target: 2027-08-31)

Joint modules (servo + Toy 5 gearbox + blind-mate housing) stacked into a child arm in
one unattended night. The child passes the parent's acceptance test and Toy 2's grasp
benchmark.

## Toy 8 — A product it was never shown (north star 2, target: 2027-12-31)

A small product the lab has not built before, chosen by someone outside the lab,
designed for the cell by the engineer, built with closure above the child arm's, and
reproduced by a stranger from the repo. This is what proves the method is not a recipe.

## Record (completed before the arm arrived)

- Arm control server with two independent safety layers; `travel()` for long moves;
  real-arm backend checked line by line against LeRobot 0.6.1 source.
- Error-budget study: same-direction approach ~7x better repeatability (3.7 → 0.5 mm);
  kinematic calibration ~4x better placement (14 → 3.5 mm); shoulder and elbow dominate.
  Backlash addendum: Robo9 measured 0.62–1.30° per servo vs the 0.5° assumed.
- Pre-registered repeatability prediction and scripted protocol, rehearsed in sim.
- Sim task scene, IK, verifier, labelled weld grasp. Zero-shot baselines: v1 10/10
  (too easy by its own rule); v2 8/10 with and without 2 mm noise (Wilson 49–94%);
  held-out pre-release abort signal did not generalise (hits 1/2, false alarms 0/18).
  All audited; details in `studies/out/`. Sim work frozen 2026-10-16.
- CI on every push; first-72-hours runbook; shopping list; direction brief.
