# Pre-release abort signal, scored on held-out releases

Prediction: `predictions/2026-10-15-pre-release-tilt-signal.md` (committed before the held-out run; see git log).
Rule: do not release while the held part is tilted > 1 deg, or while its underside (centre z - 10 mm) is at or below the pocket top (slot centre z) with > 1 mm of xy error. Fitted on the seeds 0-9 runs of 2026-10-15; held-out data = `zero-shot-v2nh` run tags (seeds 10-29 in two pre-registered batches of 10, task v2 with 2 mm RMS placement noise, tilt- and height-aware verifier): zero-shot-v2nh-20261015-225943, zero-shot-v2nh-20261015-233831.

Every number below is recomputed from `runs/*.jsonl` by `swayam.experiments.pre_release_signal`. Pre-release state = last server-logged scene before the `released` move; outcome = the current verifier rule on the scene logged with the releasing tool call. Hit = fired and not seated; false alarm = fired and seated.

| Quantity | Fitted data (seeds 0-9, v1 + v2 + v2-noise) | **Held out (v2-noise, seeds 10-29, pooled)** |
|---|---|---|
| Attempts (verifier passes) | 30 (26) | 20 (18) |
| Releases scored (unscorable) | 33 (0) | 20 (0) |
| Releases that did not seat | 7 | 2 |
| Hits / misses | 6 / 1 | **1 / 1** |
| Hit rate, Wilson 95% | 86% [49%, 97%] | **50% [9%, 91%]** |
| Releases that seated | 26 | 18 |
| False alarms / correct rejections | 0 / 26 | **0 / 18** |
| False-alarm rate, Wilson 95% | 0% [0%, 13%] | **0% [0%, 18%]** |

**Verdict (rule 2: hit rate 1/2 = 50% [9%, 91%] is below 60 %, so the tilt/height signal did not generalise to held-out releases).** False-alarm rate 0% [0%, 18%].

## Held-out releases

| run tag | pre tilt (deg) | pre xy err (mm) | pre underside (mm) | fired on | post dist (mm) | post tilt (deg) | post height err (mm) | seated | attempt |
|---|---|---|---|---|---|---|---|---|---|
| zero-shot-v2nh-20261015-225943-10 | 0.06 | 0.64 | 17.53 | - | 0.65 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-225943-11 | 0.07 | 2.39 | 16.49 | - | 0.98 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-225943-12 | 0.07 | 0.67 | 18.52 | - | 0.66 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-225943-13 | 0.07 | 0.59 | 18.54 | - | 0.6 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-225943-14 | 8.92 | 0.56 | 10.38 | tilted | 4.15 | 32.73 | 3.81 | NO | fail |
| zero-shot-v2nh-20261015-225943-15 | 0.1 | 1.51 | 14.04 | - | 0.95 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-225943-16 | 0.09 | 1.9 | 16.52 | - | 0.94 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-225943-17 | 0.07 | 2.04 | 17.52 | - | 0.82 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-225943-18 | 0.09 | 0.44 | 13.52 | - | 0.45 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-225943-19 | 0.09 | 1.74 | 18.03 | - | 0.88 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-20 | 0.09 | 1.47 | 18.51 | - | 0.82 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-21 | 0.86 | 2.22 | 12.13 | - | 4.08 | 33.25 | 3.83 | NO | fail |
| zero-shot-v2nh-20261015-233831-22 | 0.1 | 1.22 | 12.5 | - | 1.24 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-23 | 0.11 | 1.31 | 18.53 | - | 0.62 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-24 | 0.06 | 1.82 | 16.51 | - | 0.82 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-25 | 0.03 | 2.92 | 13.99 | - | 0.98 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-26 | 0.11 | 1.24 | 17.51 | - | 0.35 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-27 | 0.03 | 1.48 | 17.52 | - | 0.75 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-28 | 0.07 | 1.66 | 14.55 | - | 0.8 | 0.0 | -0.01 | yes | PASS |
| zero-shot-v2nh-20261015-233831-29 | 0.09 | 0.32 | 15.5 | - | 0.33 | 0.0 | -0.01 | yes | PASS |

## Fitted-data releases (for reference; these chose the thresholds)

| run tag | pre tilt (deg) | pre xy err (mm) | pre underside (mm) | fired on | seated |
|---|---|---|---|---|---|
| zero-shot-20261015-193207-00 | 0.09 | 0.12 | 12.52 | - | yes |
| zero-shot-20261015-193207-01 | 0.56 | 2.82 | 11.63 | low_and_off_centre | NO |
| zero-shot-20261015-193207-01 | 0.03 | 0.06 | 15.62 | - | yes |
| zero-shot-20261015-193207-02 | 26.96 | 1.34 | 8.09 | tilted, low_and_off_centre | NO |
| zero-shot-20261015-193207-02 | 34.02 | 179.9 | 4.49 | tilted, low_and_off_centre | NO |
| zero-shot-20261015-193207-02 | 0.08 | 0.1 | 17.53 | - | yes |
| zero-shot-20261015-193207-03 | 0.06 | 0.08 | 11.49 | - | yes |
| zero-shot-20261015-193207-04 | 0.05 | 0.07 | 14.54 | - | yes |
| zero-shot-20261015-193207-05 | 0.09 | 0.1 | 12.54 | - | yes |
| zero-shot-20261015-193207-06 | 0.09 | 0.07 | 16.52 | - | yes |
| zero-shot-20261015-193207-07 | 0.08 | 0.09 | 14.53 | - | yes |
| zero-shot-20261015-193207-08 | 0.02 | 0.03 | 14.52 | - | yes |
| zero-shot-20261015-193207-09 | 0.08 | 0.12 | 13.53 | - | yes |
| zero-shot-v2-20261015-202023-00 | 0.09 | 0.12 | 15.52 | - | yes |
| zero-shot-v2-20261015-202023-01 | 0.12 | 0.15 | 16.53 | - | yes |
| zero-shot-v2-20261015-202023-02 | 0.06 | 0.08 | 9.5 | - | yes |
| zero-shot-v2-20261015-202023-03 | 0.06 | 0.08 | 17.49 | - | yes |
| zero-shot-v2-20261015-202023-04 | 0.05 | 0.07 | 16.54 | - | yes |
| zero-shot-v2-20261015-202023-05 | 6.86 | 0.81 | 10.5 | tilted | NO |
| zero-shot-v2-20261015-202023-06 | 0.07 | 0.08 | 18.51 | - | yes |
| zero-shot-v2-20261015-202023-07 | 0.08 | 0.09 | 21.53 | - | yes |
| zero-shot-v2-20261015-202023-08 | 0.13 | 0.37 | 10.78 | - | yes |
| zero-shot-v2-20261015-202023-09 | 3.68 | 1.72 | 11.74 | tilted, low_and_off_centre | NO |
| zero-shot-v2n-20261015-221203-00 | 0.03 | 1.36 | 12.02 | - | NO |
| zero-shot-v2n-20261015-221203-01 | 0.11 | 1.5 | 16.53 | - | yes |
| zero-shot-v2n-20261015-221203-02 | 8.34 | 1.12 | 10.03 | tilted, low_and_off_centre | NO |
| zero-shot-v2n-20261015-221203-03 | 0.07 | 0.32 | 13.49 | - | yes |
| zero-shot-v2n-20261015-221203-04 | 0.05 | 1.85 | 13.54 | - | yes |
| zero-shot-v2n-20261015-221203-05 | 0.05 | 2.0 | 18.54 | - | yes |
| zero-shot-v2n-20261015-221203-06 | 0.07 | 1.12 | 17.5 | - | yes |
| zero-shot-v2n-20261015-221203-07 | 0.06 | 1.96 | 15.53 | - | yes |
| zero-shot-v2n-20261015-221203-08 | 0.03 | 1.48 | 18.53 | - | yes |
| zero-shot-v2n-20261015-221203-09 | 0.12 | 2.91 | 18.42 | - | yes |

## Notes

Two pre-registered held-out batches under one prediction file, both started by
`uv run python -m swayam.experiments.zero_shot --condition v2-noise-heldout --attempts 10 --start NN`
with keep-awake requested through the app first (not part of the evidence record), model `claude-fable-5-1`, fresh `claude -p` per attempt, swayam-arm
MCP tools only, task v2, 4 mm funnel, 2 mm RMS placement noise on every `move_gripper_to`, tilt- and
height-aware verifier (5253316). Prediction commit 71ab529 is dated 22:59:33 IST and the file is
byte-identical since (blob 6823afa5). Every number below is recomputed from `runs/2026-10-15.jsonl`
(append-only; 384 + 346 rows added, 0 deleted) by `swayam.experiments.pre_release_signal` and checked
with a separate scratch recompute.

| | Batch 1: seeds 10-19 | Batch 2: seeds 20-29 |
|---|---|---|
| Run tag family | `zero-shot-v2nh-20261015-225943` | `zero-shot-v2nh-20261015-233831` |
| Records (IST) | 22:59:47 - 23:21:50 | 23:38:40 - 23:59:51 |
| Started after | prediction commit 71ab529 by 14 s | 71ab529 by 39 min; batch-1 report commit f4b2acf (23:34:19) by 4 min |
| Exit code / timeouts / CLI errors | 0 / 0 / 0 in all 10 | 0 / 0 / 0 in all 10 |
| API cost, USD | 10.52 | 9.17 |
| Wall per attempt, median (max) | 94.7 s (506.3 s, seed 14) | 108.3 s (326.2 s, seed 21) |
| Tool calls per attempt, median | 19 | 18 |
| Refused grasps (v2 grasp rule) | 4 (seeds 10, 14 x2, 19) | 2 (seed 21 x2) |
| `move_gripper_to` calls = noise draws (legs stamped) | 81 (118) | 70 (111) |
| Radial RMS of the draws | 2.05 mm | 1.94 mm |
| Rows / tool-call states; old-vs-new verifier flips | 384 / 222; 0 | 346 / 196; 0 |
| Transcripts: one per attempt, one user message | yes (10/10) | yes (10/10) |
| tool_use blocks vs logged tool calls | equal in 9; seed 14 had 2 extra `Write` calls, refused by the harness | equal in 9; seed 24 had 1 extra `move_gripper_to` (pitch -103 deg) blocked by the PreToolUse safety hook before it reached the server |
| Non-MCP tools attempted | 2 (seed 14, both refused) | 0 |
| Gaps > 60 s | seed 14: 132 s and 100 s, both after the jam | seed 21: 96 s after the jam (one 6455-output-token turn); seed 24: 86 s while holding the cube above the slot (two turns, 5035 then 1200 output tokens, around the hook-blocked call) |

No sleep, stream-suspended, or API-error strings in any of the 20 transcripts; every gap is one or two
long assistant turns and the cube state is unchanged across it. Batch 2 ran under scoring code that
was fully committed before it started (f4b2acf includes the `_tags()` run-tag selector fix), so the
batch-1 caveat below does not apply to batch 2.

**Scoring-code caveat (batch 1, found by the first audit):** the thresholds and the scoring logic were
committed before batch 1 (5253316), but the run-tag selector in that commit matched the full stamp
prefix and would have selected zero `zero-shot-v2nh` tags. It was fixed after batch 1 and committed in
f4b2acf (`git diff 71ab529 f4b2acf -- src/swayam/experiments/pre_release_signal.py`: adds `_tags()`,
no constant or comparison changed), so the prediction file's "scoring fixed" is true of the thresholds,
not of the batch-1 selector.

**Two bookkeeping notes for the auditor.** (a) The harness writes one `run.json` per condition
directory, so batch 2 overwrote batch 1's `studies/out/zero_shot_v2_noise_heldout/run.json` (stamp
225943 -> 233831); batch 1's copy is in git at f4b2acf. (b) After batch 2, two header strings in
`pre_release_signal.write_report` that said "seeds 10-19" were changed to "seeds 10-29" so the pooled
column is labelled correctly (`git diff f4b2acf -- src/`); the constants, the rule, the scoring and the
selector are untouched.

### Prediction vs measured, per batch (the prediction file's windows are per 10-attempt run)

| Quantity | Predicted | Holds if | Seeds 10-19 | Seeds 20-29 | Verdict |
|---|---|---|---|---|---|
| Verifier passes | 7 / 10 | 5-9 | 9 / 10 (90 % [60 %, 98 %]) | 9 / 10 (90 % [60 %, 98 %]) | holds twice, both at the top of the window |
| Releases logged | 12 | 10-16 | 10 (0 unscorable) | 10 (0 unscorable) | holds twice, at the bottom |
| Releases that did not seat | 3 | 1-5 | 1 | 1 | holds twice, at the bottom |
| Hit rate within the batch | 75 % | >= 60 % with >= 2 non-seating | 1 / 1 (not a measurement, [21 %, 100 %]) | 0 / 1 (not a measurement, [0 %, 79 %]) | each batch alone is rule 4 (unmeasured) |
| False-alarm rate | 0 of ~9 | <= 1 false alarm | 0 / 9 (0 % [0 %, 30 %]) | 0 / 9 (0 % [0 %, 30 %]) | holds twice |
| Held tilt before every seated release | <= 0.5 deg | none > 0.5 | max 0.10 deg (seed 15) | max 0.11 deg (seed 23) | holds twice |
| Most likely miss, if any | flat cube on the rim, underside within 0.1 mm of the pocket top | - | no miss | **seed 21: tilt 0.86 deg, underside 0.13 mm above the pocket top, 2.22 mm off** | the predicted miss pattern, 0.03 mm outside the stated band |
| Most likely false alarm | flat cube released inside the funnel mouth > 1 mm off that still seats | - | none | none | - |

### Pooled held-out result (seeds 10-29, 20 attempts, 20 releases, 0 unscorable)

| Quantity | Pooled held out | Wilson 95 % |
|---|---|---|
| Verifier passes | 18 / 20 | 90 % [70 %, 97 %] |
| Releases that did not seat | 2 (seeds 14 and 21) | - |
| Hits / misses | **1 / 1** | hit rate 50 % **[9 %, 91 %]** |
| Releases that seated | 18 | - |
| False alarms / correct rejections | **0 / 18** | false-alarm rate 0 % **[0 %, 18 %]** |
| Max held tilt before a seated release | 0.11 deg | - |

**Decision, by the pre-registered rule applied as written to the pooled held-out releases:**

1. *Holds* needs hit rate >= 60 % on >= 2 non-seating releases AND <= 1 false alarm. There are now 2
   non-seating releases and the hit rate is 1/2 = 50 %. **Does not hold.**
2. *Hit rate < 60 % on >= 2 non-seating releases* **applies.** By the rule's own words the tilt/height
   signal did not generalise, and the next step is to go back to the raw moves of the misses and look
   for the earliest differing telemetry before proposing another rule. The honest size of this
   measurement: 1 of 2, Wilson [9 %, 91 %]; it is compatible with the fitted 86 % and with 10 %.
3. *>= 2 false alarms* does not apply (0 of 18).
4. *Fewer than 2 non-seating releases* no longer applies; it applied to each batch alone.
5. Pass counts (9 and 9) are inside 5-9; the verifier/noise condition prediction holds, again at the top.

Pooled fitted plus held-out, for the record only: 7 of 9 non-seating releases caught (78 % [45 %, 94 %])
and 0 of 44 seated releases flagged (0 % [0 %, 8 %]). The hit side is dominated by the 6/7 it was
fitted on and is not generalisation evidence; the false-alarm side is the one number that has now held
on 18 fresh seated releases.

### The second failure (seed 21), from the raw log

Grasp at 23:41:08 was clean (one close, cube shifted 0.1 mm at the weld). The cube was carried over the
slot at z 60 (held xy error 0.91 mm) and lowered at 23:41:38 to a commanded z of 24 mm: the held cube
then read 14.41 deg of tilt, underside 9.26 mm (2.7 mm below the pocket top), 1.37 mm off. **Both
clauses of the rule fired at that moment**, but no release happened: the subject called get_scene,
saw the tilt, and re-placed at 23:41:48 with a corrected xy target (200.1, -89.05) and z 27. That call
drew the largest of the six noise samples before the release, [0.66, 2.75] mm (2.83 mm radial; the
attempt's largest, 3.20 mm, came after the jam), so the cube came to rest
flat on the pocket rim: tilt 0.86 deg, xy error 2.22 mm, underside 12.13 mm, i.e. 0.13 mm above the
pocket top. Neither clause fires there (0.86 < 1 deg; "at or below" needs underside <= 12.00 mm). The
subject released at 23:41:52 and the cube jammed at 33.25 deg, 4.08 mm from the slot centre, 3.83 mm
high: the same end state as the five earlier jams. Both subsequent close commands (23:42:34, 23:45:19)
were refused by the v2 grasp rule (cube tilted 33 deg, limit 10); 21 further calls probed and parked at
home. The 95.6 s gap (23:43:23 -> 23:44:59) is a single 6455-output-token turn after the jam.

What the two misses share (v2-noise seed 0, fitted, and v2-noise-heldout seed 21): the cube is flat
(0.03 and 0.86 deg), resting on the rim with its underside 0.02 and 0.13 mm *above* the pocket top,
and 1.36 and 2.22 mm off centre. The rule only consults the xy error when the underside is at or below
the pocket top, and a cube resting on the rim sits a contact-solver margin above it. An xy clause on its
own is not the answer: xy error > 1 mm alone would also have fired on 13 of the 18 held-out seated
releases (72 % [49 %, 88 %]), and widening the height clause to catch these two misses would be fitting
the test data, which the prediction file forbids. The shared pattern is recorded here as the precursor
rule 2 asks for, to be tested only under a separately pre-registered rule; nothing has been re-scored.

### The rule fired earlier in three held-out attempts; the subject recovered two of them itself

Counting every held, logged state within 10 mm (in xy) of the slot before the release: the rule fired in seeds
14, 21 and 24 and in no other held-out attempt. Seed 14 released while it fired (jam, the one hit).
Seeds 21 and 24 both lowered a cube that landed tilted on the rim (14.41 and 12.97 deg), both subjects
called get_scene, lifted and re-placed without being told to; seed 24 then seated, seed 21 landed
2.22 mm off and jammed. So an abort-and-retry gate on this rule would have changed nothing in batch 2:
the subject already aborted the tilted hold, and the release that failed is one the gate would have
allowed. In seed 24 the subject's first retry command (pitch -103 deg) was blocked by the safety hook,
and its second (pitch -90) went through.

### What these runs say about the verifier change

All 18 passes ended at z 11.99, tilt 0.0, within 1.24 mm of the slot centre; the old distance-only rule
and the new rule agree on every one of the 418 tool-call states (730 logged rows) of the two held-out
batches and on all 679 tool-call states of the seeds 0-9 runs. The verifier change decided nothing
here. Its value is the ~1 mm margin it removes between a jam and a pass.

### Caveats

Same simplified MuJoCo task: weld grasp, ground-truth poses, noise applied to the commanded target
only and the reached pose reported exactly. The pre-release state is the server-logged scene; a subject
that never calls get_scene while holding would not see the tilt, so as an abort gate the rule belongs
in the controller, not in the instruction. 9/10 and 9/10 against a predicted 7/10 are inside the window,
but all five sim runs to date sit at or above their point predictions (10, 8, 8, 9, 9 of 10 against
7, 7, 5, 7, 7; 5 of 5, Wilson [57 %, 100 %]): the pass predictions are systematically low, not merely
lucky, and the next prediction file should say so. The verifier still has no yaw or pocket-geometry term and remains the simulator reading
its own state. With two non-seating releases in 20 held-out attempts, any hit rate for this rule will
stay wide until the failure count, not the attempt count, grows; the cheapest way to get more
non-seating releases is a harder condition (more noise or a narrower funnel), which would be a new
prediction file.

## Closure-auditor report (verbatim)

Produced by the `closure-auditor` subagent on 2026-10-15 (after the held-out run) from `runs/2026-10-15.jsonl`, `studies/out/zero_shot_v2_noise_heldout/attempt-NN.json` + `run.json`, the ten `claude -p` transcripts, git history and the source, with its own recompute script (not the project module). No file was modified by the auditor. The Notes section above was corrected after this audit (items 1-7 of the bottom line); the audit refers to the first draft where it quotes the write-up.

| # | Claim | Verdict | Evidence (file, run tag, timestamp) | Corrected number |
|---|---|---|---|---|
| 1 | Held-out run: 10 attempts, seeds 10-19, none dropped, 9/10 passes, Wilson [60%, 98%]; model claude-fable-5-1 only; task v2, funnel_top_z 17.5, 2 mm noise on every move_gripper_to; exit 0, no timeouts | **holds** | `runs/2026-10-15.jsonl` lines 1189-1572: 384 rows, contiguous, chronological, exactly 10 tags `-10`..`-19`, `git diff HEAD` shows 384 insertions and 0 deletions. Last tool_call verifier `in_slot` true for 9; seed 14 false (dist 4.15, tilt 32.73, dz 3.81). All 384 scenes carry `task_version: 2`, `funnel_top_z_mm: 17.5`. All 81 `move_gripper_to` calls carry `placement_noise_mm` (no noiseless target move). `attempt-NN.json`: `model_requested` and the sole `modelUsage` key = claude-fable-5-1 in all 10; `exit_code 0`, `timed_out false`, `is_error false`, `stderr_tail ""` in all 10. | 9/10 = 90.0% [59.6%, 98.2%] (same) |
| 2 | Prediction committed before the first record and unedited; scoring constants committed in 5253316 and unchanged; post-run edit to `pre_release_signal.py` touches tag matching only | **holds, with one caveat** | 71ab529 author = committer date 2026-10-15 22:59:33 +0530 (epoch 1792085373); first held-out record `t = 1792085387.95` = 22:59:47 IST (+14.95 s); first transcript timestamp 22:59:44; `run.json` stamp 225943. Reflog: no amend/rebase after 71ab529. Working tree: `predictions/` clean; SHA-1 of the file equals the 71ab529 blob (42610649...). `git show 5253316:src/swayam/experiments/pre_release_signal.py` lines 34-69: `PRE_RELEASE_TILT_DEG = 1.0`, `PRE_RELEASE_XY_MM = 1.0`, `underside = z - CUBE_SIZE_MM/2`, `pocket_top = s[2]`, `low_and_off = underside <= pocket_top and xy > PRE_RELEASE_XY_MM`. `git diff 5253316 -- src/swayam/arm/sim.py src/swayam/mcp_server.py src/swayam/experiments/zero_shot.py` is empty. `git diff 71ab529 -- pre_release_signal.py`: adds `_tags()` and swaps two selectors; no constant or comparison changed. **Caveat:** the committed selector `rsplit("-", 1)[0] in families` yields `zero-shot-v2nh-20261015-225943`, which is not `zero-shot-v2nh`, so the code as committed in 5253316/71ab529 would have selected **zero** held-out tags. The uncommitted edit was necessary to score the run at all and was written after the data existed. It selects exactly the 10 tags and nothing else, so it is a selection fix, not a tuning, but the prediction file's "Scoring (fixed, implemented in the same module before this run)" is overstated: the thresholds were, the held-out selector was not functional. | n/a |
| 3 | Exactly 10 `released` events, one per attempt; table numbers; seed 14 fires on tilt only (8.92 / 0.56 / 10.38); 0 of 9 seated fire; max seated pre-tilt 0.10 | **holds** | Independent recompute of tilt from logged ZYX rpy (third row of Rz·Ry·Rx), xy from slot centre [200, -90, 12], underside = z - 10. Ten `grasp_event: "released"` rows at 23:01:26, 23:03:10, 23:04:45, 23:06:21, 23:07:55, 23:16:18, 23:17:29, 23:18:57, 23:20:11, 23:21:48, one per tag, 0 unscorable (every one has a held scene immediately before and a tool_call record after). All 30 pre-release values match the write-up table to 0.01. Seed 14: tilt 8.92 > 1 (fires), xy 0.56 < 1 so the height clause does not fire; post 4.15 mm / 32.73 deg / +3.81 mm. Seated releases: pre-tilt 0.06-0.10, max 0.10 at seed 15; post dist 0.45-0.98, tilt 0.0, dz -0.01 for all 9. | same |
| 4 | Decision-rule verdict honest: rule 4 applies, hit rate unmeasured, only FA 0/9 [0%, 30%] counts | **holds in the text, slightly inflated in the headline table** | Notes table row "Hit rate ... unmeasured: only 1 non-seating release (rule 4)" and the decision paragraph apply rule 4 as written and queue seeds 20-29. But the top summary table prints `**1 / 0**` and `**100% [21%, 100%]**` in bold under "Hit rate, Wilson 95%" with no "unmeasured" marker; a reader who stops at the table takes away a measured 100%. | FA 0/9 = 0.0% [0.0%, 29.9%] (same). Hit rate: 1/1, [20.7%, 100%], not a measurement under the pre-registered rule; the table cell should say so. |
| 5 | Fitted column: 33 releases in 30 attempts, 7 not seated, 6 hits, 1 miss (v2n seed 0, underside 12.02), 0 FA in 26 | **holds** | Recompute over tags `zero-shot-20261015-193207-NN`, `zero-shot-v2-20261015-202023-NN`, `zero-shot-v2n-20261015-221203-NN`: 33 releases, 0 unscorable; not seated 7 (v1-01 19:36:03, v1-02 19:38:45 and 19:40:07, v2-05 21:53:13, v2-09 22:05:27, v2n-00 22:14:12, v2n-02 22:22:02); rule fires on 6; miss v2n-00: tilt 0.03, xy 1.36, underside 12.02 (0.02 mm above pocket top). 26 seated, 0 fire; max seated pre-tilt 0.13 (v2-08). | 6/7 = 85.7% [48.7%, 97.4%]; 0/26 = 0% [0%, 12.9%] (same) |
| 6 | Verifier change agrees with the old rule on all 679 seeds-0-9 states and all 384 held-out records; 26 + 9 passes unchanged; four jam poses still fail; probe for pass-but-not-seated poses | **holds on the data; probe finds latent leaks** | Old rule (dist <= 3, speed <= 5, not held) vs new rule recomputed on every scene: seeds 0-9 = 679 tool_call states (1186 scenes incl. move results), 0 flips; held-out = 384 rows, all carry a scene (222 tool_call + 162 move), 0 flips. Logged `verifier.in_slot` equals both recomputed rules on all 901 tool_call rows; logged `tilt_deg`/`height_error_mm`/`distance_mm` agree with my recompute within 0.02 on all held-out rows. Final passes 26/30 and 9/10 under both rules; the four non-passing finals (v2-05, v2-09, v2n-00, v2n-02) fail under both (e.g. v2-05 4.12 mm / 32.73 deg / +3.81 mm; v2-09 8.83 / 44.2 / +7.84). Units note: "679 states" counts tool_call rows only while "384 records" counts all rows; on a common basis it is 222 vs 679 tool_call states or 384 vs 1186 scenes. **Probe** (own rule function, five scalar tests, no yaw and no pocket-geometry term): cube at slot centre, on the floor, yawed 45 deg -> PASS; cube 2.9 mm off-centre on the floor -> PASS (a 22 mm pocket only admits 1 mm per axis for a 20 mm cube); cube 0.99 mm above the floor -> PASS; cube on its side (roll 90) -> PASS (cube symmetry makes this unavoidable); resting on the funnel top (dz +15.5) -> fail; tilt 5.1 deg -> fail. In this MuJoCo scene a rigid 20 mm cube cannot physically occupy the first two poses inside the 22 mm pocket, so the leak is latent here, not realised; on hardware (looser pocket, a chip under the part, a non-cubic part) it is real. The verifier also remains the simulator's own state, i.e. self-grading. | Agreement counts hold. Verifier passes a yaw-45 / 2.9 mm-offset / 0.99 mm-high cube in principle. |
| 7 | Seed 14 narrative: grasp 23:07:14, release 23:07:55 with underside 10.38 and tilt 8.92; jam 32.73 deg, 4.15 mm, 3.81 mm; two refused re-grasps; 132 s and 100 s gaps are thinking/API latency, not sleep | **holds, two wording nits** | Log tag `-14`: `grasped` 23:07:14 (cube z 9.89 -> 9.87, xy shift 0.06 mm); move to z 22 at 23:07:53 gives logged gripper-site z 22.28 mm and cube centre z 20.38, tilt 8.92, xy 0.56; `released` 23:07:55 -> 32.73 deg, 4.15 mm, +3.81 mm; `close: no grasp` at 23:08:32 and 23:12:31, both citing "cube tilted 33 deg, limit 10"; 15 tool_calls up to and including the release, 35 after it, ending with `home` at 23:14:32. Gaps > 60 s: 23:09:10 -> 23:11:22 (131.9 s) and 23:12:31 -> 23:14:11 (99.8 s), both after the jam, cube pose [199.48, -91.56, 15.81] identical on both sides. Transcript: zero matches for `asleep`, `StreamSuspended`, `ENOTFOUND`, `api_error`, `overloaded`, `ECONNRESET`; the two gaps are single assistant turns with 8862 and 6310 output tokens (thinking redacted), i.e. generation latency. Nits: "reached 20.38 mm" is the cube centre z, not the TCP (the TCP reached is not in `runs/`; the logged gripper site was at 22.28 mm); "35 more calls" includes the two refused closes and the home. | same |
| 8 | Hidden help / cherry-picking: one transcript per attempt, one user message, only swayam-arm MCP tools, tool_use = logged tool_call, no other v2nh tags, cost 10.52, median wall 94.7 s, median 19 calls, refused grasps seeds 10/14/19, 118 noise draws | **inflated on two items** | Ten transcript dirs, one `.jsonl` each; exactly one string user message per attempt = "Move the cube from the bed into the tray slot and stop when the verifier passes."; no other user text blocks; every assistant message `model: claude-fable-5-1`. tool_use = logged tool_call in 9 attempts (22, 19, 19, 19, 19, 17, 19, 17, 21). **Attempt 14: 52 tool_use vs 50 logged.** The two extras are `Write` calls at ~23:14:13 to `.../attempt-14/memory/swayam-release-above-funnel.md` and `memory/MEMORY.md` (content: "release cube with TCP z >= 28 mm ..."), both refused by the harness ("No such tool available: Write"). So the statement "swayam-arm MCP tools only" is true of executed tools, false of attempted tools; nothing leaked into later attempts (the path is per-attempt and the call failed), but the subject tried to carry knowledge across attempts and the write-up does not say so. `zero-shot-v2nh` appears only in `runs/2026-10-15.jsonl` and the prediction file; `~/.claude/projects` holds only these 10 heldout dirs; `studies/out` has one heldout dir. Cost sum 10.523 USD; walls 71.2-506.3 s, median 94.7; median tool calls 19.0; `close: no grasp` in seeds 10 (1), 14 (2), 19 (1). **Noise draws:** `_placement_noise()` is called once per `move_gripper_to` call (`src/swayam/mcp_server.py` lines 76-86, 223) and the same pair is stamped on every logged travel leg; 81 calls, 81 distinct pairs, 118 legs, no call with more than one distinct pair. Radial RMS of the 81 draws 2.05 mm (per-axis sigma 1.45). | Non-MCP tool calls attempted: 2 (seed 14, both refused). Noise draws: **81**, not 118 (118 = logged legs). Other numbers hold. |
| 9 | Other inflation; caveats on "would not have cost a single re-place" and "7 of 8 caught, 0 of 35 flagged" | **partly inflated / stale** | (a) "would not have cost a single re-place in this run" is a correct point statement and the [0%, 30%] interval sits two lines above it; acceptable, but 0/9 is compatible with a 30% false-alarm rate. (b) "7 of 8 ... 0 of 35" pools fitted and held-out data; the sentence does flag "only the 1 + 9 of those are held out", but gives no Wilson intervals (CLAUDE.md: always), and the pooled figure is 7/8 fitted-dominated, so it must not be read as generalisation evidence. (c) "the third run in a row at or above the point prediction (10, 8, 8, 9 of 10 over four sim runs)": all four listed runs are at or above their point predictions (7, 7, 5, 7), so it is the fourth in a row; understated, not inflated, but inconsistent. (d) Headline table bolds the 1/1 hit rate without the rule-4 marker (row 4). (e) `ROADMAP.md` (last changed in 985d7c8) still reads "v2-noise is the sim reference ... sim is not hardened further before the arm arrives (needs a decision)"; the verifier was then tightened in 5253316 with no decision recorded. It is a tightening (allowed without approval) and flipped no outcome on 1570 scenes, so it is not a moved goalpost for this result, but the ROADMAP line is stale and has no row for the held-out run. (f) `git fsck` shows one dangling blob 2ce8de2, an unreferenced copy of `tests/test_task_v2.py`; benign, no log or prediction content. (g) "cube shifted 0.1 mm at the weld": logged shift 0.06 mm; rounding, fine. | 7/8 = 87.5% [52.9%, 97.8%]; 0/35 = 0% [0%, 9.9%]; "fourth run in a row". |

**Bottom line (auditor):** the headline numbers recompute exactly from the raw log and the attempt files: 9/10 (Wilson [59.6%, 98.2%]), 10 releases with 0 unscorable, seed 14 the only non-seating release and caught by the tilt clause alone (8.92 deg), 0/9 false alarms ([0%, 29.9%]), max seated pre-release tilt 0.10 deg, fitted 6/7 and 0/26, verifier change flipping none of 1570 logged scenes, cost 10.52 USD, median 94.7 s and 19 calls, prediction committed 14.95 s before the first record and byte-identical since. The run is not cherry-picked, not pre-dated, and not helped by extra user input. The write-up applies its own rule 4 honestly in the Notes. The inflated or missing parts are: (1) "swayam-arm MCP tools only" omits two refused `Write` calls in seed 14 in which the subject tried to save "release with TCP z >= 28 mm" to memory; (2) "118 noise draws" is the number of logged travel legs, the number of draws is 81; (3) the committed scoring module could not select any `zero-shot-v2nh` tag, so the "scoring fixed before the run" claim is true of the thresholds but not of the selector, which was fixed, uncommitted, after the data existed; (4) the summary table presents a bold "100% [21%, 100%]" hit rate that the pre-registered rule says is unmeasured; (5) the pooled 7/8 and 0/35 lack intervals ([52.9%, 97.8%] and [0%, 9.9%]); (6) "reached 20.38 mm" is the cube centre, not the TCP; (7) ROADMAP.md is stale on the verifier change and has no entry for this run. With one non-seating release, this run confirms only the false-alarm side; the hit side rests on 1 held-out observation plus the 6/7 it was fitted on.

**Hardware caveat (auditor).** Everything above is a MuJoCo result with a weld grasp (no contact forces, slip or compliance), ground-truth poses instead of perception, and a verifier that is the simulator's own state reading its own cube. The "pre-release tilt" that the rule keys on is a constraint-softness artefact of the weld being pressed against the pocket rim; a real gripper may slip, comply, or hold the part rigidly, so the 1 deg threshold and the 0.10 deg seated-release bound transfer to hardware only as hypotheses to re-fit on an independent instrument (dial indicator or AprilTag on the part), not as numbers. The noise condition perturbs only the commanded xy target and then reports the reached pose exactly, which is more forgiving than real camera error. The new verifier still has no yaw term and no pocket-geometry term: it passes, in principle, a cube yawed 45 deg at the slot centre, a cube 2.9 mm off-centre on the floor, and a cube 0.99 mm above the floor; this sim's rigid geometry makes those poses unreachable, a real tray with a chip under the part or a looser pocket does not. Treat 9/10 and 0/9 as a sim reference only, keep the hit rate labelled unmeasured until seeds 20-29 run under the same prediction file, and require a bought-instrument check of seated height and tilt before any hardware success rate or abort-gate hit rate is reported.

**Response to the audit (lab engineer):** corrections (1)-(7) applied to the Notes, the report's hit-rate cell and ROADMAP.md before committing; no number in the result tables changed. The selector defect (3) is stated in the Notes and the prediction file is left as written.

---

## Second audit: batch 2 (seeds 20-29) and the pooled held-out decision

Produced by the `closure-auditor` subagent on 2026-10-16 (after batch 2) from the raw log, attempt files, the twenty transcripts, git history and the source, with its own recompute scripts. No file was modified by the auditor. The Notes section above was corrected after this audit (items 1-8 of the bottom line); the audit refers to the Notes draft where it quotes line numbers.

**Closure-auditor report, batch 2 and pooled (verbatim).** I examined `runs/2026-10-15.jsonl` (1918 rows, working tree; 346 rows added and 0 removed since f4b2acf, 384/0 between 71ab529 and f4b2acf), the twenty `studies/out/zero_shot_v2_noise_heldout/attempt-NN.json` files and `run.json`, the twenty `claude -p` transcripts under `~/.claude/projects/-private-var-folders-...-T-swayam-zero-shot-v2-noise-heldout-<stamp>-attempt-NN/`, `predictions/2026-10-15-pre-release-tilt-signal.md`, `src/swayam/experiments/pre_release_signal.py`, `src/swayam/arm/sim.py`, `src/swayam/mcp_server.py`, `.claude/hooks/check_arm_command.py`, `ROADMAP.md`, and git history (`git log`, `git diff 71ab529 f4b2acf`, `git diff f4b2acf`, `git ls-tree`, `git fsck`, reflog). Every number below was recomputed by my own scripts in `/private/tmp/claude-501/-Users-shubhamsharma-Documents-Swayam-Labs/9939d19e-3db6-4d6b-bab3-46b99847703a/scratchpad/audit/` (recompute.py, attempts.py, transcripts.py, seed21.py, tx_detail.py, tx_turns.py, misc.py, sysprompt.py, spdiff.py) directly from the raw log and transcripts, not from the module's output. I modified no file in the repository. Batch 1 was not re-audited from scratch; its numbers quoted in the new Notes were re-checked.

| # | Claim | Verdict | Evidence (file, run tag, timestamp) | Corrected number |
|---|---|---|---|---|
| 1a | Batch 2 = `zero-shot-v2nh-20261015-233831-20..29`, 10 attempts, seeds 20-29, none dropped; 9/10 passes (Wilson 60-98%) | holds | `runs/2026-10-15.jsonl`: exactly 10 tags in this family, 31/68/31/28/33/27/34/31/30/33 rows, first record 23:38:40.935 IST, last 23:59:51.374; `attempt-20..29.json` seeds 20-29; final tool-call scene passes new rule in all but `-21` (dist 4.12, tilt 32.73, dz +3.81). No other tag families in the log besides the three fitted ones and the two v2nh batches. | 9/10 = 90.0% [59.6%, 98.2%] |
| 1b | 10 releases, 0 unscorable, 1 non-seating (seed 21), 0 hits / 1 miss, 0 of 9 seated fired, max pre-release tilt before a seated release 0.11 deg (seed 23) | holds | One `grasp_event = released` per tag; pre-release scene held in all 10; `-21` release 23:41:52.935, pre tilt 0.86 / xy 2.22 / underside 12.13 -> neither clause; post 4.08 mm / 33.25 deg / +3.83 mm. Seated pre-tilts 0.03-0.112 deg; max 0.1118 at `-23` (23:48:21.398). | 0/1 hit = 0% [0%, 79.3%]; 0/9 FA = 0% [0%, 29.9%]; max 0.11 deg |
| 1c | Cost 9.17 USD; median wall 108.3 s; median 18 tool calls; exit 0, no timeouts, no CLI errors; model claude-fable-5-1 only | holds | `attempt-20..29.json`: `total_cost_usd` sum 9.168; walls 75.0-326.2 s, median 108.3 (max seed 21); `exit_code` 0, `timed_out` false, `is_error` false, `stderr_tail` "" in all 10; `modelUsage` key only `claude-fable-5-1`; every transcript assistant message `model: claude-fable-5-1`. Logged tool_call counts 18/38/18/16/19/15/20/18/17/17, median 18. | 9.17 USD; 108.3 s; 18 calls |
| 1d | 2 refused grasps (seed 21); 70 `move_gripper_to` calls = 70 noise draws on 111 legs; radial RMS 1.94 mm; 346 rows / 196 tool-call states; 0 old-vs-new verifier flips | holds | `close: no grasp ... cube tilted 33 deg, limit 10` at `-21` 23:42:34.818 and 23:45:19.021, none elsewhere in batch 2. 70 `move_gripper_to` tool_call rows, 111 `move` legs, exactly one distinct `placement_noise_mm` pair per call, 70 unique pairs; RMS sqrt(mean(dx^2+dy^2)) = 1.940 mm (per-axis sigma 1.37). 346 rows, 196 tool_call rows; `in_slot_rule` vs distance-only rule agree on all 196; logged `verifier.in_slot` agrees with the old rule on every row. | as claimed |
| 2a | Pooled held-out: 20 attempts, 18 passes 90% [70%, 97%], 20 releases, 2 non-seating, 1 hit / 1 miss 50% [9%, 91%], 0/18 false alarms [0%, 18%] | holds | Both batches recomputed: 18/20 passes; releases 20, 0 unscorable; non-seating `-14` (fired, tilted 8.92) and `-21` (did not fire); seated 18, 0 fired; 418 tool-call states / 730 rows, 0 flips. | 90.0% [69.9%, 97.2%]; 50.0% [9.5%, 90.5%]; 0.0% [0.0%, 17.6%] |
| 2b | Decision rule applied as written: rule 1 fails, rule 2 applies, rule 3 and 4 do not | holds, but softened by placement | Prediction file rule 1 needs >= 60% on >= 2 non-seating AND <= 1 FA: 1/2 = 50% fails. Rule 2 (< 60% on >= 2) applies. Rule 4 explicitly pre-registered pooling ("queue 10 more seeds (20-29) under this same file"), so pooling is legitimate. Notes lines 71-81 state this correctly. However the headline report (`pre_release_tilt_signal.md` lines 1-20, generated by `write_report`) carries no verdict sentence at all: it bolds "1 / 1" and "50% [9%, 91%]" (the `_hit_cell` rule-4 marker disappears once not_seated >= 2) and a reader reaches "the tilt/height signal did not generalise" only ~60 lines down inside the embedded Notes. Notes line 78 "compatible with the fitted 86% and with 10%" is correct but is the one sentence that leans toward the fitted number after a fail verdict. | Verdict should be stated in the headline: rule 2, signal did not generalise, 1/2 [9.5%, 90.5%] |
| 2c | Pooled fitted + held-out 7/9 [45%, 94%] and 0/44 [0%, 8%] | holds | Fitted: 30 attempts, 26 passes, 33 releases, 0 unscorable, 7 non-seating, 6 fired, 26 seated, 0 fired, 679 states, 0 flips. Pooled 7/9 and 0/44. Notes correctly label it fitted-dominated. | 77.8% [45.3%, 93.7%]; 0.0% [0.0%, 8.0%] |
| 3a | Seed 21 narrative timestamps and numbers | holds | `runs/` `-21`: grasp 23:41:08.095 (shift 0.11 mm, notes say 0.1); carry at z 54.5 held xy 0.91 at 23:41:27.863 (command z 60); lower to commanded z 24 at 23:41:38.286 -> tilt 14.41, underside 9.26, xy 1.37 (both clauses fire); get_scene 23:41:41.254; re-place 23:41:48.426 target (200.1, -89.05, 27) noise [0.663, 2.75] (2.829 mm radial) -> tilt 0.86, xy 2.22, underside 12.13; release 23:41:52.935; post 33.25 deg / 4.08 mm / +3.83 mm; refused closes 23:42:34.818 and 23:45:19.021; 38 tool calls, release is call 17, 21 after it; gap 23:43:23.639 -> 23:44:59.244 = 95.6 s. Transcript: api-request 23:43:23, next assistant message 23:44:58 with `output_tokens` 6455, no intermediate events; so one long turn, not sleep. "Same end state as the five earlier jams": five earlier releases end at 32.7-38.1 deg / 4.06-4.22 mm / +3.81-4.02 mm (v1-02, v2-05, v2n-00, v2n-02, v2nh-14); v2-09 (41.4 deg, 8.88 mm) and v1-01 (flat on top, 10.4 mm) are different end states, so "five" is right for this pattern. | as claimed |
| 3b | "That call drew the attempt's largest noise sample, [0.66, 2.75] mm (2.83 mm radial)" | inflated (wording) | `-21` draws sorted by radial: [-2.188, -2.341] = 3.204 mm at 23:43:10.658 (post-jam probe), then [0.663, 2.75] = 2.829 mm at 23:41:48.426. The re-place draw is the largest of the six draws before the release, not of the attempt. | largest in attempt 3.20 mm; largest pre-release 2.83 mm |
| 4a | Rule fired on an earlier held state near the slot in exactly seeds 14, 21, 24 and no other held-out attempt; seed 24 tilt 12.97 deg at 23:49:05-07 | holds | Scan of every held logged scene (both batches), with and without the 10 mm restriction: tilt > 1 deg occurs only in `-14` (8.92), `-21` (14.41, 3 rows 23:41:38-41) and `-24` (12.97 at 23:49:05.255 move+tool_call and 23:49:07.579 get_scene; xy 3.06 mm, 3-D distance 13.46 mm, so "within 10 mm" is true in xy only). The low-and-off clause fires in no other held-out held state near the slot. 3/20 attempts = 15% [5.2%, 36.0%]. | as claimed |
| 4b | Seed 24: one tool_use blocked by the PreToolUse hook (pitch -103) so not in `runs/`; otherwise tool_use = logged tool_call in all 10; one user message each; no non-MCP tools; no sleep/API-error strings | holds | Transcript `-24`: tool_use at 23:50:15 `move_gripper_to {x 200, y -90, z 35, pitch_deg -103, roll -22.5}` -> tool_result "PreToolUse:mcp__swayam-arm__move_gripper_to hook error ... Blocked by safety hook"; retry 23:50:33 with pitch -90 succeeded and is logged (`runs/` 23:50:33.664). tool_use counts 18/38/18/16/20/15/20/18/17/17 vs logged 18/38/18/16/19/15/20/18/17/17. Each of the 20 transcripts: one `.jsonl`, exactly one string user message "Move the cube from the bed into the tray slot and stop when the verifier passes.", no user text blocks, zero non-`mcp__swayam-arm__` tool_use in batch 2 (batch 1: the two refused `Write` in `-14`, as before). Regex for sleep/stream-suspend/API Error/overloaded/rate limit: no matches in any of the 20. Subject system prompt (prompt_snapshot, 12989 chars) is byte-identical across all 20 attempts once the per-attempt cwd is masked; harness `zero_shot.py` and `mcp_server.py` unchanged between 71ab529, f4b2acf and the working tree. | as claimed |
| 4c | Notes line 26/28: "seed 24: 86 s ... (single 5035-output-token turn)"; "every gap is a single long assistant turn" | inflated (wording) | `runs/` gap `-24` 23:49:07.579 (get_scene) -> 23:50:33.664 (move) = 86.1 s. Transcript: api-request 23:49:07 -> assistant 23:50:14 (5035 output tokens, 67 s) -> hook-blocked tool_use 23:50:15 -> api-request 23:50:15 -> assistant 23:50:32 (1200 output tokens, 17 s) -> move 23:50:33. So the 86 s gap spans two assistant turns and the blocked call, not one turn. Still not sleep; conclusion unaffected. Seed 21's 95.6 s gap is a single 6455-token turn as stated. Batch-1 gaps re-checked: `-14` 131.9 s and 99.8 s in `runs/` (notes round to 132 and 100). | 67 s turn + blocked call + 17 s turn |
| 5a | Prediction blob unchanged (6823afa5) | holds | `git ls-tree 71ab529` and `HEAD` both 6823afa51fad...; `git hash-object` of the working-tree file 6823afa51fad... | as claimed |
| 5b | Batch 2 first record 23:38:40 after f4b2acf (23:34:19), which already contained the `_tags()` fix; "batch 2 ran under fully committed scoring code" | holds | f4b2acf committed 23:34:19 +0530; `run.json` stamp 233831; `attempt-20.json` started_at 23:38:31; first `runs/` row 23:38:40.935 (4 min 21 s after the commit, 39 min 7 s after 71ab529). `git diff f4b2acf -- src/` touches only two header strings. The committed `_tags()` selects `zero-shot-v2nh-*` by prefix, so both batches would have been selected by HEAD's code. | as claimed |
| 5c | Only post-batch-2 source change is two header strings; `run.json` overwritten, batch-1 copy at f4b2acf | holds | `git diff f4b2acf -- src/`: lines 188 and 196 of `pre_release_signal.py`, "seeds 10-19" -> "seeds 10-29 ..." twice; constants, `rule_fires`, `releases`, `_tags` untouched. `git diff f4b2acf --stat`: `run.json` 1 line changed (stamp 225943 -> 233831, start 10 -> 20); `git show f4b2acf:studies/out/zero_shot_v2_noise_heldout/run.json` holds batch 1's. `git fsck`: one dangling blob 2ce8de2 (the benign `tests/test_task_v2.py` copy found last time); no stashes. Subject temp work dirs under `/private/var/folders/.../T/swayam-zero-shot-*` no longer exist, so "no CLAUDE.md in the work dir" rests on `zero_shot.py` line 6/110 (`--allowedTools mcp__swayam-arm__*`, settings file) and the identical prompt snapshots, not on inspection of the dirs. | as claimed |
| 6a | "What the two misses share ... The xy error alone would have flagged both" (precursor hypothesis, nothing re-scored) | one-sided, not retuning | Notes lines 103-108 state it as a hypothesis for a separately pre-registered rule and no number is re-scored; the constants are unchanged in `src/` and the prediction file forbids widening. But the sentence gives only the hit side: an xy > 1 mm clause alone would also have fired on 13 of the 18 held-out seated releases (pre-release xy 1.22-2.92 mm in seeds 11, 15, 16, 17, 19, 20, 22, 23, 24, 25, 26, 27, 28). The implied "underside within ~0.2 mm above the pocket top" widening would catch both misses with 0/18 held-out false alarms, which is exactly the fit-on-test-data the prediction file rules out; the notes correctly do not propose it. | xy-alone false alarms 13/18 = 72.2% [49.1%, 87.5%] |
| 6b | "An abort-and-retry gate on this rule would have changed nothing in batch 2" | holds | All 10 batch-2 releases occurred on non-firing states; the two batch-2 held states that fired (`-21` 23:41:38-41, `-24` 23:49:05-07) were each followed by get_scene and a lift command, never by a `set_gripper` open. 2 of the 3 self-recoveries seated (66.7% [20.8%, 93.9%]); n is too small to say the subject reliably recovers. | as claimed |
| 6c | Batch-1 numbers quoted in the new Notes (384/222, 0 flips, 10.52 USD, 94.7 s / 506.3 s, 19 calls, 4 refused grasps seeds 10/14x2/19, 81 draws / 118 legs, RMS 2.05, max tilt 0.10 seed 15, 1/1 and 0/9) | holds | Recomputed: 384 rows, 222 states, 0 flips, cost 10.523, walls 71.2-506.3 median 94.7, logged calls median 19, `close: no grasp` at `-10` 23:00:26, `-14` 23:08:32 and 23:12:31, `-19` 23:20:56; 81 calls / 81 unique draws / 118 legs, RMS 2.047; max seated pre-tilt 0.1020 deg at `-15`. | as quoted |
| 6d | "9/10 and 9/10 against a predicted 7/10 are inside the window" | holds, understated as calibration | Both 9/10 inside 5-9. But five sim runs in a row now sit at or above the point prediction (10, 8, 8, 9, 9 vs 7, 7, 5, 7, 7): 5/5 = 100% [56.6%, 100%]. The notes say so; the write-up should name it a systematic under-prediction, not only "at the top of the window". | 5/5 runs over-performed |
| 6e | ROADMAP current | missing | `ROADMAP.md` unchanged since f4b2acf (`git diff f4b2acf -- ROADMAP.md` empty); lines 55-60 still describe only batch 1 and end "Next, pre-registered: seeds 20-29 under the same file before any hit rate is claimed". No row for batch 2, the pooled 1/2, or the rule-2 verdict; the "needs a decision" line (49-51) on v2-noise as the sim reference is still open. | add batch-2 row with rule-2 verdict |
| 6f | "keep-awake requested first" (Notes line 3) | unverifiable | No caffeinate/keep-awake record in `runs/`, the attempt files or the subject transcripts; only evidence is the absence of >60 s gaps that are not single or double assistant turns. | - |
| 6g | Hidden human touches / cherry-picking | holds (none found) | 20 run tags in the log store = 20 in the report; no deleted rows (`git diff` shows 0 removed lines in `runs/`); 20 transcript dirs, no others matching heldout/v2nh under `~/.claude/projects`; no mid-run user input; no manual scene reset (every attempt starts with a fresh get_scene and a cube on the bed); every refused grasp and the hook block are in the record. | - |
| 6h | Cpk / closure | not claimed | The report makes no Cpk or closure-% claim. For the record: the 18 seated post-release distances have mean 0.76 mm, sd 0.24 mm, max 1.24 mm against a 3 mm tolerance (one-sided Cpk about 3.2), but this is the simulator reading its own state, not an instrument. | - |

**Bottom line (auditor):** every headline number recomputes exactly from the raw log and attempt files: batch 2 is 9/10 passes (Wilson [59.6%, 98.2%]), 10 releases, 0 unscorable, seed 21 the one non-seating release and a miss (pre-release tilt 0.86 deg, xy 2.22 mm, underside 12.13 mm, neither clause fires), 0/9 false alarms ([0%, 29.9%]), max seated pre-tilt 0.11 deg; pooled 18/20 ([69.9%, 97.2%]), 1 hit / 1 miss (50.0% [9.5%, 90.5%]), 0/18 false alarms ([0%, 17.6%]); fitted+held-out 7/9 ([45.3%, 93.7%]) and 0/44 ([0%, 8.0%]); 346 rows appended and none removed; prediction blob unchanged; batch 2 started 4 min 21 s after f4b2acf, which already carried the selector fix; the only post-run source change is two header strings; the subject's system prompt is identical across all 20 attempts; no extra user input, no non-MCP tool attempts in batch 2, no sleep. The decision rule was applied as written and rule 2 (did not generalise) is the right verdict. The inflated or missing items are: (1) the headline report has no verdict sentence; the rule-2 "did not generalise" conclusion appears only inside the embedded Notes while the top table bolds 50% [9%, 91%] without a marker, so the verdict must be stated in the headline and in the commit title; (2) Notes line 95: [0.66, 2.75] mm is the largest of the six pre-release draws in seed 21, not "the attempt's largest" (that is [-2.188, -2.341], 3.20 mm, at 23:43:10 after the jam); (3) Notes lines 26 and 28: the seed-24 86 s gap is two assistant turns (5035 then 1200 output tokens) around the hook-blocked call, not a single turn; (4) Notes lines 103-108: "the xy error alone would have flagged both" omits that it would also have flagged 13/18 held-out seated releases (72.2% [49.1%, 87.5%]); state the false-alarm side or drop the sentence; (5) `ROADMAP.md` still has only the batch-1 row and the "seeds 20-29 queued" line; it needs the batch-2 row with the rule-2 verdict, and the open v2-noise decision is still undecided; (6) five sim runs in a row at or above the point prediction (5/5, [56.6%, 100%]) should be reported as a systematic under-prediction, not only "inside the window"; (7) "keep-awake requested first" is unverifiable from the evidence; (8) "within 10 mm of the slot" for seed 24's fired state is true in xy (3.06 mm) but not in 3-D (13.46 mm); say xy. None of these changes a headline number; items 1 and 4 are the ones that would make the write-up read softer than the data.

**Hardware caveat (auditor):** everything here is MuJoCo with a weld grasp, ground-truth cube pose, noise added only to the commanded xy target with the reached pose reported exactly, no finger-to-cube contact (the seed-21 subject's own words: "finger-to-cube contact is not simulated"), and a verifier that is the simulator reading its own state, which is the process checking itself and so does not meet the "bought instrument or independent sensor" bar in CLAUDE.md; the Notes say so. The 1 deg tilt threshold sits ~0.9 deg above the largest seated pre-release tilt ever logged (0.11 deg), but on hardware the tilt will come from an AprilTag pose with its own noise, so the margin is meaningless until a gauge R&R on the tag-pose tilt exists; the same applies to the 1 mm xy and 0.13 mm underside margins that decided the seed-21 miss. The pre-release state is only observable if the subject calls get_scene while holding, so as a gate the rule belongs in the controller. Two non-seating releases in 20 held-out attempts give a hit-rate interval of [9.5%, 90.5%] that no amount of further 90%-pass runs will narrow; only more failures (a harder condition under a new prediction file) will. Nothing in this result transfers to the SO-101 until the Phase 0 repeatability and tag-pose measurements exist.

**Response to the second audit (lab engineer):** corrections (1)-(8) applied before committing: a verdict sentence generated from the decision rule now sits under the headline table (report text only, `_verdict()` in `write_report`; constants, scoring and selector untouched), the Notes wording on the seed-21 draw, the seed-24 gap, the xy-alone clause (now with its 13/18 false-alarm side), the "within 10 mm (in xy)" qualifier, the keep-awake provenance and the five-of-five under-prediction were changed, and ROADMAP.md carries the batch-2 row with the rule-2 verdict. No number in the result tables changed. The v2-noise sim-reference decision remains open for the user.
