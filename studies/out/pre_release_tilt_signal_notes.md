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
