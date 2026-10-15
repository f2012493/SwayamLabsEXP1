# Pre-release abort signal, scored on held-out releases

Prediction: `predictions/2026-10-15-pre-release-tilt-signal.md` (committed before the held-out run; see git log).
Rule: do not release while the held part is tilted > 1 deg, or while its underside (centre z - 10 mm) is at or below the pocket top (slot centre z) with > 1 mm of xy error. Fitted on the seeds 0-9 runs of 2026-10-15; held-out data = `zero-shot-v2nh` run tags (seeds 10-19, task v2 with 2 mm RMS placement noise, tilt- and height-aware verifier): zero-shot-v2nh-20261015-225943.

Every number below is recomputed from `runs/*.jsonl` by `swayam.experiments.pre_release_signal`. Pre-release state = last server-logged scene before the `released` move; outcome = the current verifier rule on the scene logged with the releasing tool call. Hit = fired and not seated; false alarm = fired and seated.

| Quantity | Fitted data (seeds 0-9, v1 + v2 + v2-noise) | **Held out (v2-noise, seeds 10-19)** |
|---|---|---|
| Attempts (verifier passes) | 30 (26) | 10 (9) |
| Releases scored (unscorable) | 33 (0) | 10 (0) |
| Releases that did not seat | 7 | 1 |
| Hits / misses | 6 / 1 | **1 / 0** |
| Hit rate, Wilson 95% | 86% [49%, 97%] | unmeasured (rule 4: 1 non-seating release; 1/1 fired, interval 100% [21%, 100%] is not a measurement) |
| Releases that seated | 26 | 9 |
| False alarms / correct rejections | 0 / 26 | **0 / 9** |
| False-alarm rate, Wilson 95% | 0% [0%, 13%] | **0% [0%, 30%]** |

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

Run `zero-shot-v2nh-20261015-225943`, seeds 10-19, 22:59:47-23:21:50 IST, started by
`uv run python -m swayam.experiments.zero_shot --condition v2-noise-heldout --attempts 10 --start 10`
with keep-awake requested first. Prediction commit 71ab529 is dated 22:59:33 IST; the
first held-out record is at 22:59:47 (14 s later). Verifier in force: the tilt- and
height-aware one from 5253316 (every logged verifier record carries `tilt_deg` and
`height_error_mm`). Model `claude-fable-5-1` in all 10 attempts; exit code 0, no
timeouts, no CLI errors; total API cost 10.52 USD; median wall 94.7 s; median 19 tool
calls; 3 attempts had a refused grasp (seeds 10, 14, 19); 2 mm placement noise applied to
every move_gripper_to (81 calls, 81 draws, radial RMS 2.05 mm; the draw is stamped on all
118 logged travel legs). One transcript per attempt with the instruction as its only user
message; executed tools were swayam-arm MCP tools only, but in seed 14 the subject also
attempted two `Write` calls (a memory note "release cube with TCP z >= 28 mm") that the
harness refused, so nothing carried across attempts.

**Scoring-code caveat (found by the audit):** the thresholds and the scoring logic were
committed before the run (5253316), but the run-tag selector in that commit matched the
full stamp prefix and would have selected zero `zero-shot-v2nh` tags. It was fixed after
the run (`git diff 71ab529 -- src/swayam/experiments/pre_release_signal.py`: adds
`_tags()`, no constant or comparison changed) so the prediction file's "scoring fixed" is
true of the thresholds, not of the selector.

### Prediction vs measured (from the prediction file, applied as written)

| Quantity | Predicted | Holds if | Measured | Verdict |
|---|---|---|---|---|
| Verifier passes | 7 / 10 | 5-9 | **9 / 10** (90 % [60 %, 98 %]) | holds, at the top of the window |
| Releases logged | 12 | 10-16 | 10 | holds, at the bottom |
| Releases that did not seat | 3 | 1-5 | 1 | holds, at the bottom |
| Hit rate | 75 % | >= 60 % with >= 2 non-seating releases | 1 / 1 (not a measurement: [21 %, 100 %]) | **unmeasured: only 1 non-seating release (rule 4)** |
| False-alarm rate | 0 of ~9 | <= 1 false alarm | **0 / 9** (0 % [0 %, 30 %]) | holds |
| Held tilt before every seated release | <= 0.5 deg | none > 0.5 | max 0.10 deg (seed 15) | holds |

**Decision, by the pre-registered rule:** item 4 applies. Fewer than 2 held-out releases
failed to seat, so the hit rate is not measured by this run; the one non-seating release
(seed 14) is a hit, which is consistent with the rule but is one observation. The
false-alarm side is measured: 0 of 9 seated releases fired, so the rule would not have
cost a single re-place in this run. As pre-registered, the next step is 10 more seeds
(20-29) under the same prediction file before claiming a hit rate. Pooled, fitted plus
held-out, the tally is 7 of 8 non-seating releases caught (88 % [53 %, 98 %]) and 0 of 35
seated releases flagged (0 % [0 %, 10 %]); the pooled figure is dominated by the fitted
half and is not generalisation evidence. Only the 1 + 9 held-out releases are.

### The one failure (seed 14), from the raw log

The subject grasped cleanly (one close command, the cube shifted 0.1 mm at the weld), carried the cube over the
slot, descended to a commanded TCP z of 22 mm (gripper site logged at 22.28 mm, cube
centre at 20.38 mm): the held cube's underside was 10.38 mm, i.e. 1.6 mm below the pocket top, with 0.56 mm of xy error and
8.92 deg of tilt (pressed onto the pocket mouth). It released there at 23:07:55 and the
cube jammed at 32.73 deg, 4.15 mm from the slot centre, 3.81 mm high: the same end
state as the four seeds 0-9 jams. The tilt clause fired (8.92 > 1 deg); the
height/xy clause did not (0.56 mm < 1 mm). Both subsequent close commands were refused
by the v2 grasp rule (tilted 33 deg); the subject then spent 35 more calls (including
those two closes and the final home) probing and parked at home. The attempt's two gaps over 60 s (132 s and 100 s, both after the jam)
are API/thinking latency, not sleep: no sleep or stream-suspended errors in the
transcript, and the cube state is identical across them.

### What this run says about the verifier change

All 9 passes ended at z 11.99, tilt 0.0, within 0.98 mm of the slot centre; the old
distance-only rule and the new rule agree on every one of the 222 tool-call states (384
logged rows including move results) of this run and on all 679 tool-call states (1186
scenes) of the seeds 0-9 runs. The verifier change decided nothing here.
Its value is the ~1 mm margin it removes between a jam and a pass; the subject now also
reads in the tool description that a jammed cube fails.

### Caveats

Same simplified MuJoCo task as before: weld grasp, ground-truth poses, noise applied to
the commanded target only and the reached pose reported exactly. The pre-release state
is the server-logged scene; a subject that never calls get_scene while holding would not
see the tilt itself, so as an abort gate the rule belongs in the controller, not in the
instruction. 9/10 vs the predicted 7/10 is inside the window but the fourth run in a row
at or above the point prediction (10, 8, 8, 9 of 10 against 7, 7, 5, 7 predicted).
The new verifier still has no yaw or pocket-geometry term: in principle it passes a
cube yawed 45 deg at the slot centre, one 2.9 mm off-centre on the pocket floor, or one
0.99 mm above it; this rigid sim cannot reach those poses, a real tray with a chip under
the part can. It also remains the simulator reading its own state.

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
