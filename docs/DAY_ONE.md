# Day one: the arm arrives (planned 2026-10-17)

Goal for the first 72 hours: **one real measurement that tests a prediction made
before the arm existed.** Everything here serves that.

## Before the box arrives

- [ ] Dial indicator (0.01 mm) + magnetic base in hand. Without it the measurement
      cannot be made; this is the one purchase that cannot slip.
- [ ] Table clamps, phone tripod, inline power switch for the servo supply.
- [ ] `uv sync --extra real` already done; `uv run lerobot-find-port --help` works.
- [ ] Read `baseline/BUILD_FILMING.md`.

## Day 1: build and film (Toy 0, the closure denominator)

1. Camera on, then open the box. One continuous recording.
2. Build the follower first, following TheRobotStudio's guide. Log every step in
   `baseline/build_log.csv`. If the kit includes a leader arm, build it second (and
   film that too, separately).
3. Set motor IDs with `uv run lerobot-setup-motors --robot.type=so101_follower
   --robot.port=<port>` when the guide says to. Find the port with
   `uv run lerobot-find-port`.
4. Clamp the base to the table. Mark the clamp positions with tape so it can go back
   in the same place.

## Day 2: bring-up and calibration

1. Power on with the arm in rest position and nothing in its reach.
2. Calibrate (interactive, in a terminal, not through Claude):
   `uv run lerobot-calibrate --robot.type=so101_follower --robot.port=<port> --robot.id=swayam_follower`
   This writes `~/.cache/huggingface/lerobot/calibration/robots/so101_follower/swayam_follower.json`.
3. Hand on the power switch. In a terminal:
   `SWAYAM_BACKEND=real SWAYAM_PORT=<port> uv run python -c "from swayam.controller import Controller; c=Controller(); print(c.telemetry())"`
   Confirm: six positions in degrees, raw load/current/temperature/voltage dicts.
4. **Sign and zero check.** LeRobot's degrees are 0 at the midpoint of each joint's
   calibrated range; the simulator's are 0 at its model pose. For each joint, command
   +10 deg (small, slow) and watch which way it moves. Record for each joint: the
   sign relative to the sim, and the offset between the two zeros. Put the result in
   `config/limits.json` under a new `sim_to_real` block, and adjust the joint limits
   if the calibrated range makes any of them unsafe.
5. Verify the unverified items at the top of `src/swayam/arm/real.py`:
   - `Present_Current` units: hold a joint lightly by hand, read the raw value, compare
     with the supply's current meter. Set `current_ma_per_count_unverified` accordingly
     and rename it.
   - that the jidoka stop triggers when you resist a slow move.
6. Set `.mcp.json` to the real backend only after all of the above; first command
   from Claude is `get_telemetry`, second is `home` with your hand on the switch.

## Day 3: the measurement (Toy 0)

1. Warm up: 10 minutes of slow motion across the work zone.
2. Rehearse once in sim: `uv run python -m swayam.experiments.repeatability --backend sim --returns 2`
3. Fix the dial indicator on its magnetic base so its tip touches a flat face of the
   gripper at pose 1 (x axis first). Zero it.
4. Run `--backend real --returns 50 --axis x --poses 1`, then the other poses, then
   repeat with the indicator set up for y and z. Type each reading when prompted.
   (5 poses x 2 modes x 50 returns x 3 axes = 1500 returns; about 2 hours of arm
   time plus setup. If time is short, do all poses on x first; that alone tests the
   ratio claim.)
5. Combine axes as root-sum-square per pose and mode. Apply the decision rule in the
   prediction file. Write the result in `predictions/2026-10-xx-arm-repeatability-RESULT.md`
   and commit. Do not touch the prediction file.
6. Ask the `closure-auditor` to check the result against `runs/` before believing it.

## If something does not match

The real arm will differ from the sim in signs, zeros, speeds and noise. That is
expected; record each difference as a fact in `config/limits.json` or `docs/`, and
never "fix" it by editing the prediction.
