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
