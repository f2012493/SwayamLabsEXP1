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
