# Swayam Labs

Machines making machines, starting from one SO-101 arm and Claude Code.

- `CLAUDE.md` — Claude's standing mandate, rules and methods.
- `ROADMAP.md` — phases, exit criteria and target dates.
- `SHOPPING.md` — what to buy, in the order you need it.
- `baseline/` — how to film your own SO-101 build (the human baseline).

## What exists today

| Part | Path | Status |
|---|---|---|
| Arm control server for Claude (MCP) | `src/swayam/mcp_server.py` | Works on the simulated SO-101 |
| Simulated SO-101 (official model, Apache-2.0) | `sim/so101/` | From TheRobotStudio/SO-ARM100 |
| Real-arm backend via LeRobot | `src/swayam/arm/real.py` | Written, **untested** until the arm arrives |
| Safety limits | `config/limits.json` | Checked by the server **and** an independent hook |
| Independent safety hook | `.claude/hooks/check_arm_command.py` | Blocks out-of-range commands before they reach the server |
| Clearance-matrix coupon (first experiment) | `cad/coupon.py` | Generates `cad/out/*.stl` |
| Red-team auditor | `.claude/agents/closure-auditor.md` | Ready |
| Arm error-budget study | `src/swayam/studies/error_budget.py` | Predicts repeatability and placement error |
| Pre-registered predictions | `predictions/` | Judged by the real arm in Phase 0 |
| CI (tests on every push) | `.github/workflows/tests.yml` | GitHub Actions |

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
