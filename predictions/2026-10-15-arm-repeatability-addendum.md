# Addendum (2026-10-15, still before the arm): new evidence on backlash

The prediction in `2026-10-15-arm-repeatability.md` stands unchanged. This note
records information found after it was committed, so that whichever way the
measurement goes, nobody can say the model was adjusted to fit.

## What was found

Robo9 bench-tested single STS3215 servos and reports effective backlash of about
**0.62° unloaded and 1.30° under load**, against the **≤0.5° datasheet** figure the
model assumed ([Robo9: Testing of Feetech STS3215](https://robonine.com/testing-of-feetech-sts3215-servomotor-backlash-repeatability-and-torque/),
[Robo9: Backlash compensation](https://robonine.com/backlash-compensation-in-sts3215-servo-actuators/)).
No published repeatability figure for a complete SO-101 arm was found.

## What it implies

Repeatability in the "any direction" scenario scales almost linearly with backlash:

| Backlash per joint | Predicted any-direction p95 (typical pose) |
|---|---|
| 0.5° (model as committed) | 3.7 mm |
| 0.62° (Robo9, unloaded) | about 4.6 mm |
| 1.30° (Robo9, loaded) | about 9.7 mm |

The original pass band (1.9–7.4 mm) covers the unloaded figure but not the loaded
one. The arm's own links load the shoulder and elbow even with nothing in the
gripper, so a measured value in the 7–10 mm range would mean: model structurally
right, backlash input wrong in the direction this data points. That is still a
"fail" under the pre-registered rule and will be reported as one.

The same-direction prediction (0.5 mm) depends little on backlash magnitude and is
the more robust claim. The ratio claim (≥3×) gets stronger if backlash is larger.

## Follow-up added to Phase 0

Measure single-joint backlash directly (dial indicator at a known radius, approach
from each side, with and without a 200 g load at the gripper) before running the
full protocol, so the model's input can be replaced by a measurement.
