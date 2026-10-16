# Swayam Labs

**Self-made machines, made in the open.**

Swayam Labs builds the smallest open "design file in, machine out" cell, and measures
how much of that loop an AI engineer closes. One cheap arm (SO-101), one printer, Claude
Code as the engineer, and a public log of how far that goes. *Swayam* (स्वयं) means
"self": machines that make themselves, and a person who decided he could make such
machines without permission.

Two numbers: **closure %** (share of a machine's build done with no human hands) and
**design iterations per week with no human CAD**. Predictions are published before
measurements; failures beside successes; every result is audited and replayable.

- `docs/DIRECTION.md` — where the field is going and the gap this lab works on.
- `docs/LANDSCAPE.md` — what already exists at every layer, what we duplicated, what
  remains ours.
- `ROADMAP.md` — the toy ladder: eight experiments, each adding one capability.
- `CLAUDE.md` — the AI engineer's standing mandate, rules and methods.
- `SHOPPING.md` — what to buy, in the order you need it.
- `baseline/` — how to film your own SO-101 build (the closure denominator).
- `predictions/` — pre-registered predictions and their verdicts.

## What exists today

| Part | Path | Status |
|---|---|---|
| Arm control server for Claude (MCP) | `src/swayam/mcp_server.py` | Works on the simulated SO-101 |
| Simulated SO-101 (official model, Apache-2.0) | `sim/so101/` | From TheRobotStudio/SO-ARM100 |
| Real-arm backend via LeRobot 0.6.1 | `src/swayam/arm/real.py` | Checked against source; **untested on hardware** |
| Safety limits | `config/limits.json` | Checked by the server **and** an independent hook |
| Independent safety hook | `.claude/hooks/check_arm_command.py` | Blocks out-of-range commands before they reach the server |
| Clearance-matrix coupon (first experiment) | `cad/coupon.py` | Generates `cad/out/*.stl` |
| Red-team auditor | `.claude/agents/closure-auditor.md` | Ready |
| Arm error-budget study | `src/swayam/studies/error_budget.py` | Predicts repeatability and placement error |
| Pre-registered predictions | `predictions/` | Judged by the real arm in Toy 0 |
| CI (tests on every push) | `.github/workflows/tests.yml` | GitHub Actions |
| Repeatability experiment (sim rehearsal / real measurement) | `src/swayam/experiments/repeatability.py` | Rehearsed in sim |
| Task scene: cube on bed + kit-tray slot with funnel (sim only) | `sim/so101/scene_task.xml` | `SWAYAM_SCENE=task` |
| Inverse kinematics and `move_gripper_to` | `src/swayam/kinematics.py` (`TcpKinematics`), `src/swayam/mcp_server.py` | LeRobot placo `RobotKinematics` on the official SO-101 URDF; MuJoCo FK stays as the safety check |
| Zero-shot pick-and-place baseline harness | `src/swayam/experiments/zero_shot.py` | Fresh `claude -p` per attempt |
| First-72-hours runbook | `docs/DAY_ONE.md` | For 2026-10-17 |

## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest
```

Open this folder in Claude Code: `.mcp.json` registers the `swayam-arm` server
(simulation by default) and `.claude/settings.json` turns on the safety hook.

Generate the coupon STLs:

```bash
uv run --extra cad python cad/coupon.py
```

When the arm arrives:

```bash
uv sync --extra real
```

then set `SWAYAM_BACKEND=real` and `SWAYAM_PORT` (the arm's serial port) in
`.mcp.json`, and work through the checks at the top of `src/swayam/arm/real.py`.
