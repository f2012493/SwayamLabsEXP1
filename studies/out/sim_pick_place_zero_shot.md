# Zero-shot pick-and-place in simulation (Phase 0 step 4 baseline)

Run `20261015-193207`. Prediction: `predictions/2026-10-15-sim-pick-place-zero-shot.md` (committed before this run; see git log).
Model: claude-fable-5-1 via `claude -p`, fresh conversation per attempt, tools = swayam-arm MCP only, no CLAUDE.md, safety hook on. Instruction: "Move the cube from the bed into the tray slot and stop when the verifier passes."

Every row is recomputed from `runs/*.jsonl` (append-only, tagged `run_tag`). No attempt was dropped.

## Result vs prediction

| Quantity | Predicted | Measured |
|---|---|---|
| Successes / attempts | 7 / 10 | **10 / 10** |
| Success rate, Wilson 95% | 70% [40%, 89%] | **100% [72%, 100%]** |
| Median tool calls per attempt | 14 | 16.0 |
| Median wall time per attempt (s) | - | 74.5 |
| Attempts that commanded motion after the verifier first passed | <= 1 attempt | 2 (cube disturbed in 0) |
| Attempts whose first release did not pass (predicted modal failure, then recovered) | - | 2 |
| Irrecoverable events (cube off the table) | 0 | 0 |
| Total API cost (USD) | - | 7.65 |
| Most likely failure mode | cube released with yaw outside the funnel's +-20 deg capture | see table |

## Attempts

| # | seed | verifier | tool calls | verifier calls | refused | aborted | releases | first release passed | moved after pass | cube disturbed after pass | off table | first action (s) | wall (s) | cost (USD) | final dist (mm) | final cube yaw (deg) | timed out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | PASS | 15 | 1 | 0 | 0 | 1 | True | 0 | no | no | 140.4 | 201.7 | 0.66 | 0.14 | -0.84 | no |
| 1 | 1 | PASS | 29 | 3 | 0 | 0 | 2 | False | 0 | no | no | 10.4 | 116.8 | 1.06 | 0.06 | -90.49 | no |
| 2 | 2 | PASS | 42 | 3 | 0 | 0 | 3 | False | 0 | no | no | 10.6 | 213.8 | 1.79 | 0.11 | -0.05 | no |
| 3 | 3 | PASS | 17 | 2 | 0 | 0 | 1 | True | 1 | no | no | 9.9 | 81.8 | 0.68 | 0.09 | -89.61 | no |
| 4 | 4 | PASS | 15 | 1 | 0 | 0 | 1 | True | 0 | no | no | 12.8 | 60.0 | 0.55 | 0.07 | -0.01 | no |
| 5 | 5 | PASS | 15 | 1 | 0 | 0 | 1 | True | 0 | no | no | 12.1 | 59.0 | 0.57 | 0.12 | -0.89 | no |
| 6 | 6 | PASS | 16 | 1 | 0 | 0 | 1 | True | 0 | no | no | 17.9 | 88.6 | 0.56 | 0.08 | -1.07 | no |
| 7 | 7 | PASS | 16 | 1 | 0 | 0 | 1 | True | 0 | no | no | 11.1 | 67.2 | 0.57 | 0.1 | -0.36 | no |
| 8 | 8 | PASS | 18 | 2 | 0 | 0 | 1 | True | 1 | no | no | 10.7 | 62.1 | 0.62 | 0.03 | -89.73 | no |
| 9 | 9 | PASS | 16 | 1 | 0 | 0 | 1 | True | 0 | no | no | 12.9 | 63.2 | 0.59 | 0.14 | -0.76 | no |

Columns: `verifier` is the last logged verifier state of the attempt (`is_cube_in_slot`); `first release passed` is the verifier state right after the first gripper-open following a grasp; `moved after pass` counts arm commands logged after the first call whose post-call verifier was true (the AA-Robotics 'refine past success' failure) and `cube disturbed after pass` whether the cube centre moved more than 0.5 mm after that; `off table` is the cube falling below the table top. Tool calls are counted from the server log, so a call blocked by the safety hook before reaching the server is not counted.

## Decision rule (from the prediction file, applied as written)

- Success-rate prediction (hold if 5-9 of 10): **does not hold** (10/10).
- Tool-call prediction (hold if median in 8-25): **holds** (median 16.0).
- Failure-mode prediction: no attempt failed, so it holds vacuously. The predicted mode (release with the cube yaw outside the funnel's capture) appeared as a first-placement failure in 2 attempts.
- The pre-registered consequence of >= 9 successes applies: the simulated task is too easy to be a useful baseline. The next version removes the weld's 15 mm forgiveness and/or shrinks the funnel, with a new prediction file; the same instruction and seeds are rerun on hardware in Phase 0 step 4.

## What the subject said (last message of each attempt, verbatim, not used for scoring)

- attempt 0: The verifier passes. The cube is seated in the tray slot and I have stopped as requested.  What I did: - **Opened the gripper** from its initial 9 percent and moved above the cube on the bed. - **Matched the cube's yaw** by reading the reported jaw axis and setting the wrist roll, then descended and closed to grasp. - **Lifted and carried** the cube over the slot with the roll adjusted so its yaw 
- attempt 1: The verifier passes. The cube is seated in the tray slot and released, so the task is done.  | Check | Result | |---|---| | in_slot | true | | distance from slot centre | 0.06 mm | | speed | 0 mm/s | | held by gripper | false |  **What happened.** The first placement attempt jammed the cube on the pocket rim because its yaw drifted about 3 degrees during the carry and it landed a couple of millime
- attempt 2: The verifier passes. The cube is seated in the tray slot, level and square to the pocket.  | | Value | |---|---| | Cube centre offset from slot centre | 0.11 mm | | Cube speed | 0 mm/s | | Held by gripper | no |  **What happened**  - **First attempt jammed.** I grasped the cube on the bed and carried it over the slot, but the cube's yaw did not match the pocket, so it wedged in the funnel. Lifting
- attempt 3: The cube is seated in the tray slot and the verifier passes.  | Check | Result | |---|---| | Cube distance from slot centre | 0.09 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no | | Cube yaw | -89.6°, square to the pocket |  **What I did**  - Opened the gripper and did a top-down grasp of the cube on the bed, with the wrist rolled to match the cube's 12° yaw. - Lifted it, car
- attempt 4: The verifier passes. The cube is seated in the tray slot.  **Result**  | Check | Value | |---|---| | Cube distance from slot centre | 0.07 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no | | Cube yaw | 0° (squared to the pocket) |  **What I did**  - Opened the gripper and moved to a top-down pose above the cube on the bed, then descended and closed to grasp it. - Lifted it, ca
- attempt 5: The cube is seated in the tray slot and the verifier passes.  | Check | Result | |---|---| | in_slot | true | | distance from slot centre | 0.12 mm (tolerance 3 mm) | | speed | 0 mm/s | | held by gripper | false |  **What I did**  - Opened the gripper and did a top-down approach over the cube on the bed, descended to the cube centre height, and closed to grasp it. - Lifted, carried it over the slo
- attempt 6: The verifier passes. The cube is seated in the tray slot and released, so the task is done.  What I did: - Opened the gripper and made a top-down grasp of the cube on the bed. - Lifted it and carried it over the slot. The pan rotation had turned the cube about 60 degrees off the pocket axis, so I rolled the wrist to realign it before descending. - Lowered into the funnel and released.  Verifier re
- attempt 7: The verifier passes. The cube is seated in the tray slot and released.  | Check | Result | |---|---| | Distance from slot centre | 0.1 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no |  **What I did**  - Opened the gripper and moved to a top-down pose above the cube on the bed, matching the cube's yaw with the wrist roll. - Descended to cube height and closed the gripper, whic
- attempt 8: The cube is seated in the tray slot and the verifier passes.  | Check | Result | |---|---| | Cube centre offset from slot centre | 0.03 mm (tolerance 3 mm) | | Cube speed | 0 mm/s | | Held by gripper | no |  What I did: - Opened the gripper, moved over the cube on the bed, descended top-down, and closed to grasp. - Lifted and carried the cube over the slot at a safe height. - The cube's yaw was ab
- attempt 9: The verifier passes. The cube is seated in the tray slot.  | Check | Result | |---|---| | Distance from slot centre | 0.14 mm (tolerance 3 mm) | | Speed | 0 mm/s | | Held by gripper | no |  **What I did:** opened the gripper, descended top-down onto the cube on the bed, grasped it, lifted, carried it over the slot, rolled the wrist to bring the cube's yaw from about -49° to under 1° so it would fi

Raw per-attempt CLI records: `studies/out/zero_shot/attempt-NN.json`; raw tool log: `runs/` with `run_tag` = `zero-shot-20261015-193207-NN`.

## Notes

- Plumbing runs before the 10 attempts, excluded from the denominator because they did not run the
  instruction: `smoke-3` (MCP client check: get_scene, one move, verifier; cube never moved) and
  `zero-shot-rehearsal-99` (a hook-block test with a different prompt, 3 calls, $0.21). Both logged
  to scratch directories, not `runs/`.
- The harness report generator was extended after the data existed (the `releases`, `first release
  passed`, `cube disturbed after pass` columns, the decision-rule section and the audit section); the
  success, tool-call and moved-after-pass logic is unchanged, and every number is recomputed from
  `runs/` on each regeneration.
- Cost: mean $0.76 per attempt, median $0.61. Attempt 0 took 140 s before its first arm command
  (cold start); the others 10-18 s.
- Sim artefacts seen in attempt 2: the soft weld let a held cube tilt 39-47 deg while pressed into the
  funnel, and a cube wedged in the funnel at 34 deg tilt was "grasped" from 12.6 mm with the jaws only
  40 % open. The weld rule checks only closure < 20 % and distance <= 15 mm, never jaw opening or
  geometry. Both first-placement recoveries relied on this. A harder sim version should require the
  jaws to be open wider than the part and the part to lie between them.
- What this does not show: grasping, perception error, backlash, kinematic error. The verifier is
  simulator ground truth, not an independent instrument. 10/10 here says nothing about the hardware
  success rate; it says the tools and the stop-on-verifier loop work.

## Closure-auditor report (verbatim)

Produced by the `closure-auditor` subagent on 2026-10-15 from `runs/2026-10-15.jsonl`, `studies/out/zero_shot/attempt-NN.json`, the `claude -p` transcripts and git history. No file was modified by the auditor.

| # | Claim | Verdict | Evidence | Corrected number |
|---|---|---|---|---|
| 1 | 10/10 passed, Wilson [72%, 100%], none dropped | holds | Exactly 10 run_tags in `runs/`; last `tool_call` of every tag has `in_slot = true`, `held = false`, distance 0.03-0.14 mm. All attempt JSONs: `is_error false`, exit 0, not timed out, model `claude-fable-5-1` only. Transcript tool_use count equals server tool_call count for all 10; 0 tool errors, 0 hook blocks. | 10/10, Wilson 95% [72.2%, 100%]. |
| 2 | Prediction predates results, never edited | holds | Single commit 42674a3 at 19:27:09 +0530; harness started 19:32:07; first logged tool call 19:34:12. Reflog clean. Pre-commit CLI sessions were "reply ok" checks with no tools. | Committed 5 min before the harness started. Caveat: the same commit created scene, verifier, weld, IK and harness, and the scripted 9-command rehearsal test had been run, so the prediction was informed by a scripted solution, not by LLM pilots. |
| 3 | Median 16 calls; 2 moved after pass, cube disturbed 0; 2 first-release failures; 0 off-table | holds | Calls 15,29,42,17,15,15,16,16,18,16. Tags 03 and 08 each made one open-gripper retreat to z=70 after passing; cube delta 0.00 mm. First release failed in tag 01 (cube on the tray rim, d 10.4 mm) and 02 (wedged in the funnel, pitch -38 deg, d 4.06 mm). `off_table` false in all 352 records. | As reported. Median wall 74.5 s, total cost 7.647 USD. |
| 4 | Verifier leak | holds (no leak found) | Verifier requires 3-D distance <= 3 mm to the slot centre at z = 12, speed <= 5 mm/s, not held. A cube on the funnel has z >= 16 mm so is rejected (observed in tags 01, 02). Every passing record has z = 11.99, roll/pitch 0.00, yaw within 1.07 deg of 0 or -90. | No correction. Sim artefact: the weld grasped a wedged tilted cube at 40% jaw opening (tag 02); the grasp rule ignores jaw opening and geometry. |
| 5 | Hidden help | holds | Each transcript's only user text is the instruction byte-for-byte; tools used are 6 of the 10 MCP tools, no unknown tools; work dirs contain only mcp.json and settings.json; no CLAUDE.md anywhere; one process per tag; seed-k cube pose matches `default_rng(k)` exactly for k = 0..9. | No correction. Caveat: tool docstrings disclose the weld rule (20% / 15 mm), the funnel capture and the 3 mm verifier rule, so "zero-shot" includes the sim's own cheat sheet, per protocol. The rehearsal-99 prompt accidentally included harness source; none of the 10 scored attempts did. |
| 6 | Cherry-picking | holds | `runs/` holds only the 10 reported tags. Two unreported plumbing runs exist in scratch dirs (`smoke-3`, `zero-shot-rehearsal-99`), neither ran the instruction. | Denominator stays 10 (10/11 = 90.9% if rehearsal-99 were counted, but its instruction differed). |

Hardware caveat from the auditor: the weld deletes grasping entirely; object poses are exact; the arm has zero backlash or kinematic error (final placement 0.03-0.14 mm against the repo's 3.5 mm / 0.5 mm budgets); the funnel reoriented every dropped cube to within 1 deg; the verifier is simulator ground truth. Both first-placement failures were recovered only via sim-only moves. 10/10 here says nothing about the hardware success rate.
