# Zero-shot pick-and-place in simulation, task v2 (harder sim)

Prediction: `predictions/2026-10-15-sim-pick-place-zero-shot-v2.md` (committed before the v2 runs; see git log). v1 reference: `predictions/2026-10-15-sim-pick-place-zero-shot.md` and `studies/out/sim_pick_place_zero_shot.md`.
Model: claude-fable-5-1 via `claude -p`, fresh conversation per attempt, tools = swayam-arm MCP only, no CLAUDE.md, safety hook on. Instruction (unchanged): "Move the cube from the bed into the tray slot and stop when the verifier passes."
Run stamps: v1 = zero-shot-20261015-193207; v2 = zero-shot-v2-20261015-202023; v2-noise = zero-shot-v2n-20261015-221203.

What changed from v1 (`SWAYAM_TASK_VERSION=2`, `sim/so101/scene_task_v2.xml`, `swayam.arm.sim`):
the outer funnel is 4 mm per side instead of 8 (lead-in still 1.5 mm); the weld grasp requires the jaws to close from a gap wider than the cube, the cube to lie between the finger pads (jaw axis window, +-7 mm across the pads, -45..6 mm along the fingers) and the cube to be within 10 deg of flat. `v2-noise` adds a seeded N(0, 1.41 mm) error per axis (2 mm RMS radial) to every move_gripper_to target, from the 3.5 mm camera-guided placement budget. The tool descriptions tell the subject the active rule, as in v1.

Every row is recomputed from `runs/*.jsonl` (append-only, tagged `run_tag`). No attempt was dropped.

## Result vs prediction (and v1)

| Quantity | v1 predicted | v1 measured | v2 predicted | **v2 measured** | v2-noise predicted | **v2-noise measured** |
|---|---|---|---|---|---|---|
| Successes / attempts (Wilson 95%) | 7 / 10 (70% [40%, 89%]) | **10 / 10** (100% [72%, 100%]) | 7 / 10 (70% [40%, 89%]) | **8 / 10** (80% [49%, 94%]) | 5 / 10 (50% [24%, 76%]) | **8 / 10** (80% [49%, 94%]) |
| Median tool calls per attempt | 14 | 16.0 | 20 | 19.5 | 24 | 20.0 |
| Median wall time per attempt (s) | - | 74.5 | - | 100.35 | - | 96.15 |
| Attempts with >= 1 refused grasp | - | 0 | >= 3 | 2 | >= 4 | 4 |
| Attempts whose first release did not pass | - | 2 | - | 2 | - | 2 |
| Failed attempts ending with the cube tilted > 10 deg | - | 0 | modal failure | 2 | modal failure | 2 |
| Attempts that commanded motion after the verifier first passed | <= 1 | 2 | <= 1 | 0 | <= 1 | 0 |
| Irrecoverable events (cube off the table) | 0 | 0 | 0 | 0 | 0 | 0 |
| Timed out / errored attempts | - | 0 | - | 0 | - | 0 |
| Total API cost (USD) | - | 7.65 | - | 11.61 | - | 11.06 |

## Attempts: v2

| # | seed | verifier | tool calls | verifier calls | refused moves | aborted | grasps | refused grasps | releases | first release passed | moved after pass | cube disturbed after pass | off table | first action (s) | wall (s) | cost (USD) | final dist (mm) | final tilt (deg) | final yaw (deg) | timed out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | PASS | 21 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 10.4 | 102.3 | 0.86 | 0.14 | 0.0 | -0.11 | no |
| 1 | 1 | PASS | 18 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 23.2 | 72.6 | 0.69 | 0.17 | 0.0 | 0.02 | no |
| 2 | 2 | PASS | 17 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 13.7 | 85.1 | 0.70 | 0.09 | 0.0 | -0.87 | no |
| 3 | 3 | PASS | 18 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 16.5 | 98.4 | 0.78 | 0.09 | 0.0 | -0.17 | no |
| 4 | 4 | PASS | 22 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 30.9 | 128.7 | 1.00 | 0.07 | 0.0 | -0.5 | no |
| 5 | 5 | fail | 45 | 6 | 0 | 0 | 1 | 2 | 1 | False | 0 | no | no | 16.6 | 5485.1 | 2.18 | 4.12 | 32.7 | 0.0 | no |
| 6 | 6 | PASS | 22 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 16.6 | 113.5 | 0.94 | 0.08 | 0.0 | -0.56 | no |
| 7 | 7 | PASS | 15 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 15.2 | 56.7 | 0.56 | 0.1 | 0.0 | -0.14 | no |
| 8 | 8 | PASS | 18 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 19.8 | 81.0 | 0.73 | 0.39 | 0.0 | -89.96 | no |
| 9 | 9 | fail | 52 | 5 | 0 | 0 | 1 | 2 | 1 | False | 0 | no | no | 9.0 | 457.7 | 3.17 | 8.83 | 44.2 | 18.67 | no |

## Attempts: v2-noise

| # | seed | verifier | tool calls | verifier calls | refused moves | aborted | grasps | refused grasps | releases | first release passed | moved after pass | cube disturbed after pass | off table | first action (s) | wall (s) | cost (USD) | final dist (mm) | final tilt (deg) | final yaw (deg) | timed out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | fail | 36 | 5 | 0 | 0 | 1 | 1 | 1 | False | 0 | no | no | 21.3 | 404.3 | 1.89 | 4.12 | 32.7 | -90.0 | no |
| 1 | 1 | PASS | 21 | 1 | 0 | 0 | 1 | 1 | 1 | True | 0 | no | no | 20.8 | 122.7 | 1.01 | 0.98 | 0.0 | -0.02 | no |
| 2 | 2 | fail | 42 | 5 | 1 | 0 | 1 | 2 | 1 | False | 0 | no | no | 25.3 | 398.1 | 2.65 | 4.22 | 32.7 | 0.0 | no |
| 3 | 3 | PASS | 19 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 13.6 | 95.5 | 0.80 | 0.33 | 0.0 | -1.1 | no |
| 4 | 4 | PASS | 20 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 8.8 | 87.9 | 0.78 | 0.85 | 0.0 | 0.47 | no |
| 5 | 5 | PASS | 17 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 10.8 | 84.5 | 0.72 | 0.85 | 0.0 | -90.03 | no |
| 6 | 6 | PASS | 19 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 16.3 | 96.8 | 0.82 | 0.59 | 0.0 | -2.13 | no |
| 7 | 7 | PASS | 16 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 24.5 | 78.8 | 0.66 | 0.97 | 0.0 | 0.14 | no |
| 8 | 8 | PASS | 22 | 1 | 1 | 0 | 1 | 1 | 1 | True | 0 | no | no | 18.7 | 91.6 | 0.83 | 0.49 | 0.0 | -88.14 | no |
| 9 | 9 | PASS | 20 | 1 | 0 | 0 | 1 | 0 | 1 | True | 0 | no | no | 15.2 | 105.1 | 0.89 | 0.73 | 0.0 | 1.13 | no |

Columns as in the v1 report, plus `grasps` / `refused grasps` (close commands that did / did not attach the cube, from the logged grasp_event) and `final tilt` (angle of the cube's most vertical face normal from vertical, from the logged final pose). `refused moves` are commands the server refused on limits; calls blocked by the hook never reach the server and are not counted.

## Decision rule (from the v2 prediction file, applied as written)

- v2 success-rate prediction (hold if 5-9 of 10): **holds** (8/10).
- v2 tool-call prediction (hold if median in 12-35): **holds** (median 19.5).
- v2 failure-mode prediction: **holds** (2 of 2 failures end with the cube tilted > 10 deg within 12 mm of the slot centre).
- v2-noise success-rate prediction (hold if 3-7 of 10): **does not hold** (8/10).
- v2-noise tool-call prediction (hold if median in 12-35): **holds** (median 20.0).
- v2-noise failure-mode prediction: **holds** (2 of 2 failures end with the cube tilted > 10 deg within 12 mm of the slot centre).
- Noise effect: v2 minus v2-noise = 0 successes (under 3: no evidence against the funnel >= 2x error rule at this sample size).

## What the subject said (last message of each attempt, verbatim, not used for scoring)

- v2 attempt 0: The verifier passes. The cube is seated in the tray slot and the arm is stopped above it with the gripper open.  | Check | Result | |---|---| | Cube distance from slot centre | 0.14 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no |  **What happened**  - Grasped the cube top-down on the bed, with the wrist rolled to match the cube's 18 degree yaw. - Carried it to the slot and r
- v2 attempt 1: Done. The verifier passes: the cube is seated in the tray slot, released, and at rest.  | Check | Value | |---|---| | Distance from slot centre | 0.17 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no | | Cube yaw | 0.02° (pocket yaw 0°) |  What I did:  - **Grasp:** Opened the gripper, moved above the cube on the bed, and rolled the wrist so the jaws matched the cube's 14° yaw. 
- v2 attempt 2: The verifier passes. The cube is seated in the tray slot and released.  | Check | Result | |---|---| | Distance from slot centre | 0.09 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no | | Cube yaw | -0.87° |  What I did:  - **Grasped top-down** on the bed after opening the jaws and rolling the wrist to match the cube's 12.6° yaw. - **Lifted and traversed** to above the slot, t
- v2 attempt 3: The verifier passes. The cube is seated in the tray slot and I have stopped there, with the arm parked open above the slot.  What I did: - **Grasp.** Opened the gripper, moved top-down over the cube on the bed, set wrist roll so the jaws were parallel to the cube faces, descended, and closed. The simulator reported a successful grasp. - **Transfer.** Lifted the cube clear, moved over the slot, and
- v2 attempt 4: The verifier passes. The cube is seated in the tray slot and released.  | Check | Result | |---|---| | Cube centre offset from slot centre | 0.07 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no |  What happened: - **Grasp:** top-down pick on the bed with the wrist rolled to match the cube's 19° yaw. The gripper reported a clean grasp event. - **Carry:** lifted, moved over the 
- v2 attempt 5: The verifier did not pass. The cube is wedged in the slot funnel, 4.1 mm from the slot centre and tilted 33 degrees, and I have no way to recover it in this simulator. The arm is back at home.  **What happened**  - Grasp from the bed succeeded on the second try. The first close missed because the fingertips sat 2 mm above the cube's reach band, so I lowered the TCP to 12 mm and it grasped. - I car
- v2 attempt 6: The verifier passes. The cube is seated in the tray slot and the arm is stopped above it with the gripper open.  | Check | Result | |---|---| | Distance from slot centre | 0.08 mm (tolerance 3 mm) | | Speed | 0 mm/s | | Held by gripper | No | | Cube yaw | -0.56° (pocket yaw 0°) |  **What happened:** - Opened the gripper, rolled the wrist to match the cube's yaw, and grasped it top-down from the be
- v2 attempt 7: The verifier passes. The cube is seated in the tray slot and I have stopped there, leaving the arm parked above the slot with the gripper open.  What I did: - **Grasp:** opened the gripper, aligned the jaws to the cube's yaw, descended top-down onto the cube, and closed to a confirmed grasp. - **Transfer:** lifted clear, moved over the slot, and rolled the wrist so the held cube's yaw matched the 
- v2 attempt 8: The verifier passes. The cube is seated in the tray slot and the arm has stopped.  **What happened**  - Opened the gripper, then grasped the cube top-down on the bed with the jaws rolled to match the cube's yaw. The simulator reported a successful grasp. - Lifted it, carried it over the slot, and rolled the wrist so the cube's faces aligned with the pocket walls. - Lowered it to just above the fun
- v2 attempt 9: The task did not complete. The verifier still reports the cube out of the slot, and I cannot recover it in this simulator.  **What happened**  - The grasp worked. I opened the jaws, aligned the jaw axis to the cube's 4° yaw, closed at the cube centre, and the sim reported a grasp. - The place failed on release. I lowered the held cube to a TCP height of about 20 mm over the slot, which put the cub
- v2-noise attempt 0: The verifier did not pass. The cube is in the tray slot but wedged at a tilt, and I could not recover it with the tools available.  **What happened**  - Picked the cube from the bed with a top-down grasp, jaws aligned to its yaw. The grasp registered cleanly. - Carried it over the slot, rotated it to the pocket yaw, and lowered it until its bottom sat at the pocket mouth, about 1 mm off centre in 
- v2-noise attempt 1: The verifier passes. The cube is seated in the tray slot and the arm has stopped.  | Check | Result | |---|---| | in_slot | true | | distance from slot centre | 0.98 mm | | cube speed | 0 mm/s | | held by gripper | false |  What happened:  - **First grasp attempt missed.** With the tool centre point at 20 mm height the fingertips sat 10 mm above the cube, outside the pad span. I reopened and desce
- v2-noise attempt 2: The task did not succeed. The verifier still reports the cube outside tolerance, and I could find no way to recover it from its current state. The arm is parked at home.  **What happened**  - The grasp went cleanly. I aligned the jaws to the cube's 12.6° yaw, closed within 0.4 mm of its centre, and carried it over the slot. - The placement failed. I lowered the held cube down into the pocket inste
- v2-noise attempt 3: The verifier passes. The cube is seated in the tray slot and I have stopped the arm there.  | Check | Result | |---|---| | Cube distance from slot centre | 0.33 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | No |  What I did: - **Grasped top-down** on the bed, matching the wrist roll to the cube's 12° yaw so the jaws closed square on its faces. - **Rotated the cube to zero yaw**
- v2-noise attempt 4: The verifier passes. The cube is seated in the tray slot and released.  | Check | Result | |---|---| | Distance from slot centre | 0.85 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no | | Cube yaw | 0.5° (pocket yaw 0°) |  **What I did**  - Opened the gripper and descended top-down onto the cube on the bed, with wrist roll at zero because the jaw axis already lined up within 4
- v2-noise attempt 5: The verifier passes. The cube is seated in the tray slot and released.  | Check | Result | |---|---| | Distance from slot centre | 0.85 mm (tolerance 3 mm) | | Speed | 0 mm/s | | Held by gripper | No |  **What I did**  - Opened the gripper, moved top-down over the cube on the bed, descended, and closed. The grasp registered. - Lifted and swung to the slot. The shoulder pan rotation had turned the 
- v2-noise attempt 6: The verifier passes. The cube is seated in the tray slot and the arm is stopped above it with the gripper open.  | Check | Result | |---|---| | Cube distance from slot centre | 0.59 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no | | Cube yaw in pocket | -2.1 deg |  What I did:  - **Grasp.** Opened the gripper, hovered over the cube top-down, and set the wrist roll so the jaws
- v2-noise attempt 7: The verifier passed, so the task is done. Stopping here as requested, leaving the arm parked above the slot with the gripper open.  **Outcome:** the cube is seated in the tray slot and the verifier reports success.  | Check | Result | |---|---| | Cube distance from slot centre | 0.97 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no | | Cube yaw vs pocket | 0.14 deg |  **What I 
- v2-noise attempt 8: The verifier passes. The cube is seated in the tray slot and released.  | Check | Result | |---|---| | Cube distance from slot centre | 0.49 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no |  **What I did**  - Opened the gripper and moved above the cube on the bed with a top-down pitch. - Rolled the wrist so the jaws were square to the cube's faces, which sat at about 7 degree
- v2-noise attempt 9: The verifier passes. The cube is seated in the tray slot and released, and I stopped there as asked.  | Check | Result | |---|---| | Cube distance from slot centre | 0.73 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no | | Cube yaw vs pocket | 1.13° |  **What I did:** - Opened the gripper and approached the cube top-down, rolling the wrist so the jaws closed square on the cube

Raw per-attempt CLI records: `studies/out/zero_shot_v2/attempt-NN.json` and `studies/out/zero_shot_v2_noise/attempt-NN.json`; raw tool log: `runs/` with the run tags above. Funnel characterisation: `studies/out/funnel_capture.md`.

## Notes

Corrected after the closure audit below (first draft overstated several points; the audit lists them).

- **Mechanism of all four failures (v2 seeds 5 and 9, v2-noise seeds 0 and 2), from `runs/`:** the
  subject carried the cube over the slot with yaw corrected (0.0-2.0 deg off) and xy within
  0.8-1.7 mm, then commanded the TCP down with the cube held until the cube centre was at
  z 20.5 / 21.7 / 22.0 / 20.0 mm, i.e. its underside at 10.5 / 11.7 / 12.0 / 10.0 mm: at or below
  the pocket top (12 mm). The pocket clearance is 1 mm per side, so the cube was pressed onto the
  rim; the soft weld let it tilt 6.9 / 3.7 / 0.0 / 8.3 deg before release, and after release it
  ended 4.1-8.8 mm from the slot centre at 32.7-44.2 deg of tilt, jammed in the funnel. Every later
  close command was refused (4 in v2, 3 in the two v2-noise failures): from too high ("cube centre
  40-44 mm along the fingers"), then with the tilted cube against the fixed jaw, then on tilt alone.
  No subject tried to right the cube (the arm links collide with it; the jaw hulls do not). This is
  the predicted modal failure, by the mechanism predicted.
- **Why 16 passed:** every pass released the cube within 2.8 mm xy and 1.1 deg yaw of the slot and
  the funnel seated all of them to within 1 mm. In v2-noise all 8 passes released with the cube
  underside above the pocket top (centre z 23.5-28.5 mm); in v2, 6 of 8 did and two (seeds 2 and 8,
  centre z 19.5 and 20.8 mm) pressed the cube into the pocket zone and still passed because they were
  centred to 0.1 / 0.4 mm. A pressed-in release works only when the placement error is below the
  1 mm pocket clearance, which the noiseless sim arm delivers.
- **Grasp rule v2 never blocked a nominal grasp.** All 20 first grasps were accepted from 100 % open
  (98 mm gap) with the cube 9.0-12.7 mm from the fixed jaw, within 3.2 mm of the pad centreline and
  0 deg tilt. Three first-try refusals (v2 seed 5, v2-noise seeds 1 and 8) were correct: the TCP had
  been commanded to z 18-25 instead of 12, leaving the cube 1.7-15 mm beyond the fingertips; each
  subject descended and grasped on the next try.
- **v2-noise (8/10, predicted 5/10: missed on the high side).** The noise was real: 81 executed
  draws, radial RMS 1.92 mm (per-axis sd 1.37 / 1.35 mm, max 3.95 mm), seeded as specified. The
  success count did not change (8-8 = 0; Newcombe 95% interval on the difference about -34 to +34
  percentage points, so this is "no evidence of an effect at n = 10 per arm", not "no effect"). What
  the log does show: no release above the pocket top missed, at any noise offset up to 2.8 mm, and
  all four failures in both conditions came from release height, not from placement error.
- **Earliest failure signal (hypothesis for hardware, same-data, not held out):** the held cube's
  tilt in the server-logged scene just before the release command was <= 0.13 deg in the 16 passes
  and 3.7 / 6.9 / 8.3 deg in three of the four failures; the fourth (v2-noise seed 0) had 0.03 deg
  with the cube underside at exactly 12.0 mm (the pocket top) and 1.4 mm xy error. A rule "do not
  release while the held part is tilted > 1 deg, or while its underside is at or below the pocket
  top with > 1 mm xy error" matches 4/4 failures and 0/16 passes here. Two caveats: the subject only
  sees that tilt if it calls get_scene while holding (v2 seed 9 did not; its 3.7 deg is from the
  move result the server logs but does not return), and the rule was fitted on this data; it must
  be tested on held-out runs before being trusted.
- **Infrastructure anomaly, flagged, not dropped:** during v2 seed 5 the Mac slept from 20:29:51
  to 21:53:13 IST (5002 s between two consecutive tool calls) and again from 21:53:27 to 21:57:26
  (239 s). The harness's 900 s timeout did not fire because Python's subprocess timeout uses a clock
  that stops during sleep. State before the first sleep: cube held, pressed on the rim at centre
  z 20.5 mm and 6.9 deg tilt; the first command after waking was the release that produced the jam,
  decided by the model from the pre-sleep observation. The simulator advances only on commands, so
  the sleep could not change the physics, but the attempt was not yet in its final state when the
  machine slept. Seed 5's `wall` (5485 s) is meaningless; its calls, cost and outcome stand. Other
  gaps over 60 s (64-111 s, in v2 seed 9 and v2-noise seeds 0 and 2) are long thinking turns, not
  sleeps. Keep-awake was requested from the app after the gap was noticed; the v2-noise run had no
  sleep.
- **Cost:** v2 $11.61, v2-noise $11.06 for 10 attempts each (per-attempt medians $0.82 / $0.83 over
  all attempts; the four failures cost $1.89-$3.17 each as the subjects spent 36-52 calls trying to
  recover). Both conditions $22.67, within the $25 planned. v1 was $7.65.
- **Verifier margin:** `is_cube_in_slot` checks distance (3 mm), speed and release only, no tilt or
  height. The four jams sat 4.05-4.22 mm from the slot centre, about 1 mm outside the tolerance.
  No leak occurred in 20 attempts, but the margin is thin and the hardware verifier needs a tilt
  and height check plus an independent instrument.
- **Not pre-registered, a new decision for the user:** the prediction's "v2-noise becomes the
  reference and no further sim hardening" consequence was written for v2 >= 9; v2 scored 8, inside
  the "prediction holds" band, which carries no registered consequence. My proposal is the same
  (use v2-noise as the sim reference, stop hardening the sim, go to hardware), but it is a proposal.
- **What this still does not show:** grasp physics (the weld holds the cube rigidly once attached
  and lets it tilt only through constraint softness), perception error (the noisy condition
  perturbs the commanded target and then reports the reached pose exactly), backlash, kinematic
  error. The verifier is simulator ground truth.

## Closure-auditor report (verbatim)

Produced by the `closure-auditor` subagent on 2026-10-15 (after both runs) from `runs/2026-10-15.jsonl`, `studies/out/zero_shot_v2*/attempt-NN.json`, the 20 `claude -p` transcripts, git history, the source and a direct MuJoCo probe of the verifier. The report's own tables were not used for any number. No file was modified by the auditor. The Notes section above was corrected after this audit; the audit refers to the first draft where it says "report says".

| # | Claim | Verdict | Evidence (file, run tag, timestamp) | Corrected number |
|---|---|---|---|---|
| 1 | 8/10 and 8/10, Wilson 95% [49%, 94%]; exactly 10 tags per condition, none dropped; success = verifier after LAST tool call; model claude-fable-5-1 only | **holds** | `runs/2026-10-15.jsonl`: exactly 10 tags `...-202023-00..09` and 10 tags `...-221203-00..09`, seeds in order, sequential and non-overlapping (v2 20:20:27-22:11:13, v2n 22:12:10-22:37:59 IST). Last `tool_call.verifier.in_slot`: v2 fails = seeds 5, 9; v2n fails = seeds 0, 2. All 20 `attempt-NN.json` `modelUsage` keys and all 20 transcript `message.model` fields = `claude-fable-5-1`; `exit_code` 0, `timed_out` false, `is_error` false for all 20. | 8/10 = 80.0%, Wilson [49.02%, 94.33%] (both conditions). |
| 2 | Prediction predates data; not edited afterwards | **holds** (thin margin) | `git log --follow predictions/2026-10-15-sim-pick-place-zero-shot-v2.md`: single commit f289645, committer date 2026-10-15 20:20:14 +0530 (epoch 1792075814). Harness stamp 20:20:23; first v2 record `t=1792075827.8` = 20:20:27:48. Reflog has no amend/reset after f289645; `git status` shows no change under `predictions/`; `runs/` diff vs HEAD is +836/-0 lines (append-only intact). A scripted smoke run (`scratchpad/smoke-runs/2026-10-15.jsonl`, tag `smoke-v2`, 12 records all at 20:19:47) preceded the commit by 27 s; it is not an LLM attempt and did not place the cube. | Commit precedes first logged v2 tool call by 13.8 s. |
| 3 | Every attempt ran task v2 (task_version 2, funnel_top_z 17.5); v2-noise really had seeded ~2 mm RMS noise; v2 had none | **holds** | All 679 `tool_call` scenes under v2/v2n tags: `task_version: 2`, `funnel_top_z_mm: 17.5` (20/20 tags). `mcp.json` in each work dir: `SWAYAM_TASK_VERSION=2`, `SWAYAM_CUBE_SEED=k`; v2n adds `SWAYAM_PLACE_NOISE_MM=2.0`. v2n: 100% of `move_gripper_to` moves carry `placement_noise_mm` (81 draws on executed moves + 2 on refused moves = 83); v2: 0 records with the key. First draw of every seed equals `default_rng(10000+seed).normal(0, 1.414)` for all 10 seeds (seed 8's first draw [2.009, 1.591] went to a refused move; its first executed move got draw 2, [0.322, -1.778]). | Per-axis sd 1.374 / 1.349 mm, radial RMS 1.924 mm, max 3.945 mm (81 executed draws); incl. refused: n=83, RMS 1.936. Report's 81 / 1.92 / 1.37 / 1.34 / 3.95 confirmed. |
| 4 | Grasp rule v2 in force; every "grasped" event satisfied it; no v1-style grasp | **holds** | 20 `grasp_event: "grasped"` records (1 per attempt). Pre-close state from the preceding logged scene: gripper 100% open (jaw gap 98 mm) in all 20; cube along fingers x = 1.0-6.0 mm (limit [-45, 6.3]); across pads abs(y) <= 3.2 mm (limit 7); along jaw axis z = 9.0-12.7 mm (window [8, 90]); tilt 0.0 deg in all 20. 9 `close: no grasp` records, every one with a logged reason that matches the pre-state (e.g. v2 seed 5 20:29:04 x=8.0 > 6.3; v2 seed 9 22:06:18 x=39.8, tilt 43.6; v2n seed 2 22:26:34 tilt 32.7 only). | Refused closes: v2 = 4 (seeds 5, 9: 2 each), v2n = 5 (seed 0: 1, seed 1: 1, seed 2: 2, seed 8: 1). Attempts with >= 1 refusal 2 / 4 as reported. |
| 5a | 4 failures end tilted > 10 deg within 12 mm of slot | **holds** | Final `tool_call` scenes: v2-05 dist 4.12 mm, tilt 32.7, z 15.81; v2-09 dist 8.83, tilt 44.2, z 19.84; v2n-00 dist 4.12, tilt 32.7; v2n-02 dist 4.22, tilt 32.7. | 4/4. |
| 5b | Release heights / held tilt before release in failures | **holds with one wrong number** | Scene immediately before each `released` event: v2-05 (21:53:13) cube z 20.50 (bottom 10.5), xy err 0.81, tilt 6.86; v2-09 (22:05:27) cube z **21.74 (bottom 11.74)**, xy **1.72**, tilt 3.68; v2n-00 (22:14:12) z 22.02 (bottom **12.02**), xy 1.36, tilt 0.03; v2n-02 (22:22:02) z 20.03, xy 1.12, tilt 8.34. | Report's "20.9 / 10.9 mm, 1.6 mm" for seed 9 should read 21.7 / 11.7 mm, 1.7 mm (still below the 12 mm pocket top, so the mechanism stands). |
| 5c | Passes released with cube bottom at/above pocket top | **holds for v2-noise; v2 has two pressed-in passes, report names one** | v2n passes: pre-release cube centre z 23.49-28.54 (bottom >= 13.5) for all 8. v2 passes: z 25.52, 26.53, **19.50**, 27.49, 26.54, 28.51, 31.53, **20.78** (seeds 2 and 8; bottoms 9.5 and 10.8 mm, xy 0.08 and 0.37 mm). The Notes mention only seed 2. | v2: 6 of 8 passes released above the pocket top, 2 pressed in. v2n: 8 of 8. |
| 5d | Earliest failure signal: held tilt <= 0.1 deg in all 16 passes vs 3.7/6.9/8.3/0.0 in failures; rule predicts 4/4, 0/16 | **inflated (slightly)** | Held tilt before release, 16 passes: max **0.13** (v2-08), 0.12 (v2-01, v2n-09), 0.11 (v2n-01), rest <= 0.09. Failures 3.68 / 6.86 / 8.34 / 0.03. The written rule ("underside below the pocket top with > 1 mm xy error") does not fire on v2n-00: bottom = 12.02 mm is not below 12.0. Also, in v2-09 the subject never called `get_scene` while holding (last get_scene 55.8 s before release, cube still on bed); the 3.68 comes from the server-logged move-result scene, which `_public()` strips from what the subject sees. | Passes <= 0.13 deg (separation from the 3.68 minimum failure tilt still 28x). Rule as written: 3/4 hits, 0/16 false alarms; 4/4 only with "at or below" (or a >= 0.1 mm margin). |
| 6 | 83-min gap in v2 seed 5 (machine sleep); outcome already decided before it; no other gap > 60 s | **inflated** | Log: 20:29:51.6 `get_scene` -> 21:53:13 `set_gripper` move = 5002 s. Transcript `work-v2-attempt-05`: ENOTFOUND retries at 20:48:36-40, 21:05:12, 21:19:10; `api_error` "Connection lost while your computer was asleep" (StreamSuspended) at 21:37:00 and again at 21:56:39. **State before the gap: cube HELD at (200.78, -90.21, 20.50), tilt 6.86 deg, speed 5.38 mm/s (pressed on the rim). The first command after waking was the release itself (set_gripper 100 at 21:53:13), which produced the jam (z 15.81, tilt 32.9).** So "already in the jammed state before the sleep" is false; the model's release decision was generated post-wake from the pre-sleep observation. Because the sim steps only on commands, the gap could not alter the physics, but the state was not identical across it. Second sleep in the same attempt: 21:53:27 -> 21:57:26 (239 s in the log; report says "all other gaps under 30 s"). Other gaps > 60 s: v2-09 101 s (22:08:38 -> 22:10:19, a 6514-output-token thinking turn, API latency); v2n-00 92 s; v2n-02 64 s and 111 s (all long thinking turns, not sleeps). | Sleep gaps: 5002 s + 239 s, both in v2-05. Gaps > 60 s in 4 attempts (v2-05, v2-09, v2n-00, v2n-02); wall medians (100.35 / 96.15 s) unaffected since these are the slowest attempts anyway. Seed 5's `wall_s` 5485 and `duration_ms` are meaningless, as the report says. |
| 7 | Hidden help: only user text = instruction; only swayam-arm tools; no CLAUDE.md; one process per tag; cube seed-k pose = v1 seed-k; docstrings disclose rule | **holds** (one nuance) | 20 project dirs, exactly 1 transcript each, `session_id` equals `attempt-NN.json.cli.session_id` for all 20, cwd = the attempt dir. Each transcript has exactly 1 user text, verbatim the instruction. MCP `tool_use` count == log `tool_call` count for all 20 tags (v2 21,18,17,18,22,45,22,15,18,52; v2n 36,21,42,19,20,17,19,16,22,20) -> no out-of-band tool calls under any tag. **Nuance:** 3 attempts tried non-MCP tools to write auto-memory notes (v2-09 `Write`+`Read` at 22:11:27-29; v2n-00 `Write` 22:18:28; v2n-02 `Write` 22:27:08); all returned "No such tool available ... disabled for this session". `memory/` dirs exist but are empty; work dirs contain only `mcp.json` and `settings.json`, no `.md`. Initial cube pose per seed identical to v1 (e.g. seed 0 [206.85, 78.49, 9.89] yaw -18.36; seed 9 [218.51, 79.34, 9.89] yaw 4.13) for all 10. Rendered docstrings (SWAYAM_TASK_VERSION=2, noise 2): `set_gripper`: "...attaches the cube to the gripper only if, at that moment, all of: the jaws are closing from a gap wider than the 20 mm cube; the cube lies between the finger pads (its centre within 2 mm of the gap along jaw_axis, within +-7 mm of the pad centreline, and between -45 and 6 mm along approach_axis from the gripper site); and the cube is within 10 deg of flat..."; `get_scene`: "...a 1.5 mm lead-in and a 4 mm funnel widen to funnel_half_width_mm (16.5 mm) at funnel_top_z_mm (17.5 mm), so a flat cube released above the funnel with its centre within ~6 mm of the slot centre and its yaw near the pocket's slides in"; `move_gripper_to` (v2n only): "This server adds a seeded random xy error of 2.0 mm RMS to every target ... the returned tcp is the pose actually reached, so read it back when precision matters." | 0 out-of-band tool calls; 0 extra user turns; 4 blocked non-MCP tool attempts in 3 attempts. |
| 8 | Cherry-picking: no other v2/v2n tags or scratch runs | **holds** | `runs/` contains only `2026-10-15.jsonl` with exactly 3 tag families (v1 x10, v2 x10, v2n x10); repo-wide grep finds no other v2/v2n stamp. `scratchpad/smoke-runs/2026-10-15.jsonl`: tag `smoke-v2`, 12 records in one second (get_scene, open, 2 moves, close -> grasped, is_cube_in_slot false), scripted, no instruction, never placed; correctly excluded and not in `runs/`. The other scratchpad `runs-smoke` dir is the v1 session's. | Denominator 10 + 10; nothing missing. |
| 9 | Statistics: Wilson, medians, costs, noise effect 0 | **holds, with one misleading median** | Wilson(8,10) = [0.4902, 0.9433]. Tool-call medians 19.5 (v2) / 20.0 (v2n). Cost sums 11.6058 / 11.0563 USD. Difference 8-8 = 0. Notes' per-attempt "median $0.76 / $0.81" are medians over the 8 passes only; over all 10 attempts the medians are 0.82 / 0.83. The "noise effect = 0" is arithmetically right but the 95% CI on the difference (Newcombe) is [-34, +34] percentage points; the ROADMAP wording "2 mm noise cost nothing because the 4 mm funnel caught every drop" is not supported at n=10 per arm. | Medians 19.5 / 20.0; cost 11.61 / 11.06; per-attempt median cost 0.82 / 0.83; noise effect 0 pp, 95% CI [-34, +34] pp. |
| 10 | Verifier leak: can a tilted/funnel-resting cube pass `is_cube_in_slot`? | **holds for this data; verifier is weak in principle** | All 16 passing final states: z = 11.99, tilt 0.0, dist <= 0.98 mm, speed 0, not held. Direct probe (SimArm v2, cube placed by hand, 2 s settle): leaning 5-20 deg or yawed 8 deg inside the pocket settles seated (pass, correctly); 30 deg jams at z 15.85, dist 4.05 (fail); yaw 45 on funnel dist 13.4 (fail); seed-5 jam pose dist 4.12 (fail). The four logged jams sit 4.05-4.22 mm from centre against a 3.0 mm tolerance: ~1.1 mm margin, and `cube_in_slot()` checks only distance/speed/held (no tilt, yaw or z test). The 3 mm tolerance is 3x the 1 mm pocket clearance, so it cannot distinguish "seated" from "within 3 mm". | 0 leaks in 20 attempts; margin to the observed failure states 1.05 mm. |
| 11 | (extra) ROADMAP / decision rule | **moved goalpost (minor)** | Uncommitted `ROADMAP.md` diff adds "Sim reference for the hardware rerun is v2-noise. No further sim hardening before the arm arrives." The prediction file pre-registers that consequence only for "If v2 >= 9 again"; v2 = 8, which falls in the "holds" band with no registered consequence. ROADMAP step 4 itself has no numeric exit (score, time, cost, grasp success, irrecoverables all reported). Separately, the 4 mm funnel departs from CLAUDE.md's "outer funnel >= 8 mm until Phase 0 measures the real arm"; disclosed in the prediction as sim-only. | Decision adopted outside the pre-registered rule; should be stated as a new choice, not a rule outcome. |

**Bottom line (auditor):** the headline numbers (8/10, 8/10, [49%, 94%], 19.5/20.0 calls, $11.61/$11.06) recompute exactly from the raw log and are not cherry-picked, not pre-dated, not helped by extra user input or out-of-band tool calls, and every grasp obeyed the v2 rule. The inflated parts are in the Notes: (a) seed 5 was not "already jammed before the sleep" (it was held and pressed; the jamming release executed after the 83-min wake, and a second 239 s sleep followed); (b) "all other gaps under 30 s" is false (239 s, 101 s, 92 s, 64 s, 111 s); (c) held-tilt bound is 0.13 deg not 0.1, and the proposed pre-release rule as written catches 3/4, not 4/4; (d) v2 had two pressed-in passes (seeds 2 and 8), not one; (e) seed 9's release numbers are off by ~0.8 mm; (f) per-attempt median costs quoted are pass-only medians; (g) "noise cost nothing" has a +-34 pp interval; (h) "v2-noise becomes the reference / no further hardening" was pre-registered only for v2 >= 9.

**Hardware caveat (auditor).** Everything above is a MuJoCo result with a weld grasp (no contact forces, slip or compliance), ground-truth poses instead of perception, and a verifier that is the simulator's own state. The noise condition perturbs only the commanded xy target and then tells the subject the reached pose exactly, which is more forgiving than real camera error. The 2 mm-noise "no effect" and the pre-release tilt signal are same-data observations on 10 + 10 attempts; neither has been tested on held-out runs, and the verifier's 3 mm tolerance with no tilt check leaves about 1 mm between a jammed and a "passing" cube in this geometry. Treat the 8/10 figures as a sim reference only, and expect the hardware rerun (same instruction, same seeds) to need a tilt- and z-aware verifier and an independent instrument check before any success rate is reported.

**Response to the audit (lab engineer):** all eight corrections (a)-(h) were applied to the Notes section and to ROADMAP.md before committing; no number in the result tables changed.
