# Roadmap

Each phase adds exactly one new class of assembly operation. Each machine built is
used by the cell afterwards. Exits are judged by sensor verifiers, bought instruments,
and the `closure-auditor` — never by Claude's own assessment.

Dates are proposals and are meant to be hard. Change them, but do not soften them.

Hardware: SO-101 (ordered 2026-10-15, in transit). No printer or cameras yet — see
`SHOPPING.md`. Recommended printer: open-frame with flexible PEI sheet, network API
and G-code pause (e.g. Prusa MK4S).

## Now — before the arm arrives

- [x] Arm control server with safety limits, on the simulated SO-101 (sim backend).
- [x] Independent safety hook on every arm command.
- [x] Real-arm backend written against LeRobot (untested until arrival).
- [x] Clearance-matrix coupon CAD (`cad/coupon.py`).
- [x] Error-budget study (`src/swayam/studies/error_budget.py`). Findings:
      same-direction approach should improve repeatability about 7x (3.7 -> 0.5 mm);
      kinematic calibration should improve camera-guided placement about 4x
      (14 -> 3.5 mm); shoulder and elbow dominate the error.
- [x] Same-direction approach in the arm server (on by default).
- [x] Repeatability prediction pre-registered:
      `predictions/2026-10-15-arm-repeatability.md`.
- [x] CI: tests run on every push to GitHub.
- [x] Real-arm backend checked line by line against LeRobot 0.6.1 source (import path,
      degree convention, raw registers, no interactive calibration inside MCP).
- [x] Repeatability protocol scripted (`swayam.experiments.repeatability`), rehearsed in sim.
- [x] First-72-hours runbook: `docs/DAY_ONE.md`.
- [x] Task scene in sim (cube on bed, kit-tray slot with funnel), scene poses as
      numbers, verifier, IK `move_gripper_to`, labelled weld grasp
      (`sim/so101/scene_task.xml`, `src/swayam/ik.py`).
- [x] Zero-shot pick-and-place baseline in sim, 10 attempts, pre-registered in
      `predictions/2026-10-15-sim-pick-place-zero-shot.md`; results in
      `studies/out/sim_pick_place_zero_shot.md`: 10/10 (Wilson 95% 72-100%),
      median 16 tool calls, 75 s, $0.61 median ($0.76 mean) per attempt. Prediction (7/10) missed on
      the high side; by its own rule the sim task is too easy. Next: harder sim
      (no weld forgiveness / smaller funnel) with a new prediction, then hardware.
- [x] Backlash evidence recorded: `predictions/2026-10-15-arm-repeatability-addendum.md`.
- [x] Harder sim, task v2 (`SWAYAM_TASK_VERSION=2`: geometric grasp rule, 4 mm funnel, optional
      2 mm RMS placement noise), pre-registered in
      `predictions/2026-10-15-sim-pick-place-zero-shot-v2.md`; results in
      `studies/out/sim_pick_place_zero_shot_v2.md`: v2 8/10 and v2-noise 8/10 (Wilson 95%
      49-94% each), median 19.5 / 20 calls, $11.61 / $11.06, audited. v2 prediction (7/10)
      held; the noise prediction (5/10) missed high (difference 0, 95% interval about
      +-34 points: no evidence of a noise effect at n = 10). All 4 failures: the subject
      released with the cube underside at or below the pocket top, the weld let it tilt, and
      the tilt rule refused every re-grasp. Proposed, not pre-registered (needs a decision):
      v2-noise is the sim reference for the hardware rerun and the sim is not hardened further
      before the arm arrives.
- [ ] Buy the day-one items in `SHOPPING.md`; order the printer and cameras.
- [ ] Day the arm arrives: **film the build** (`baseline/BUILD_FILMING.md`). This is
      Phase 0 step 5 and cannot be redone later.
- [ ] Day 1 (17th): build and film. Day 2: calibrate, bring up, sign/zero check.
      Day 3: run the repeatability protocol. All in `docs/DAY_ONE.md`.

## Phase 0 — Instrument; build what needs no assembly (target: 2026-11-15)

New operations: harvest, inspect, mount a part on itself.

1. MCP arm server: telemetry (position, load, current, temperature, voltage), limited
   joint/pose moves, grip, AprilTag poses, on-demand image, e-stop. Claude Code hook
   rejecting any out-of-limit command.
2. Hand-eye calibration (ChArUco). Gauge R&R on the measurement first, then
   ARM ERROR: run the pre-registered protocol in
   `predictions/2026-10-15-arm-repeatability.md` exactly as written, and record
   whether the prediction held. Then kinematic calibration (identify each joint's
   zero offset from ChArUco views) and re-measure placement error.
3. Clearance-matrix coupon as a designed experiment. Factors: clearance (0.0–0.6 mm),
   orientation on the bed, material. Response: slide / press / snap, with force from
   motor current. Output: a fit table that becomes the CadQuery parameters for every
   later part.
4. Zero-shot baseline (AA-Robotics style): Claude drives the arm live on "remove part
   from bed, place in tray slot", 10 attempts. Report score, time, time to first
   action, cost, grasp success, irrecoverable mistakes.
5. Human baselines: time a person on the same task, and on a full SO-101 build broken
   into a step graph (duration, tolerance, force per step). The step graph is the
   closure denominator.
6. Build: snap-on fingertip pads that the arm fits to itself by pressing its jaws into
   a docking fixture.

**Exit:** arm-made pads beat the stock jaws on grasp success over a fixed 10-object
set, at least 30 grasps each, Wilson 95% intervals not overlapping; pads fitted with
zero human touches (auditor-confirmed).

## Phase 1 — Put parts into parts (target: 2027-01-15)

New operations: place, peg-in-hole, snap/press, pause-and-embed. No electricity, no
screws.

Build: a herringbone planetary gearbox for the STS3215 output. At most 10 printed
parts and 2 vitamin types, vitamins embedded mid-print. The printer -> kit loop feeds
the parts.

- Before the first hardware attempt: tolerance stack-up and FMEA.
- Test stand: a servo drives the input; ratio and backlash from the encoders,
  torque at slip from motor current. Gauge R&R on the stand.
- Claude proposes the spec from Phase 0 numbers; I approve it before building.

**Exit:** 30 gearboxes built unattended; Cpk >= 1.33 on backlash and torque at slip;
5 checked with bought instruments; zero LLM-minutes per cycle; cost per gearbox
reported against a human at $37.81/h.

## Phase 2 — Add electricity (target: 2027-03-31)

New operations: handle a powered vitamin, blind-mate a connector, write the servo ID
over the bus, run a powered test.

Build: joint module = STS3215 + Phase 1 gearbox + housing that mates the servo's
connector as the servo seats (fallback: pogo-pin adapter PCB, counted as a vitamin),
with bayonet interfaces on both ends.

**Exit:** 10 modules built unattended; each enumerates on the bus, gets its ID written
by the cell, and passes the sweep / backlash / torque spec; cycle time under
[X] minutes.

## North star (target: 2027-06-30)

Phase 3: stack joint modules into a child arm in one unattended night. The child
passes the parent's acceptance test and the Phase 0 grasp benchmark.

Later: the cell's other half — the printers.
