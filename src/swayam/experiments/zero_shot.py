"""Zero-shot pick-and-place baseline (ROADMAP Phase 0 step 4, AA-Robotics style).

Prediction: predictions/2026-10-15-sim-pick-place-zero-shot.md (committed first).

Each attempt is a fresh, non-interactive `claude -p` conversation whose only tools
are the swayam-arm MCP tools, started in an empty directory (no CLAUDE.md, no
source code), with the independent safety hook attached. Each attempt starts its
own MCP server on the task scene with the cube at seed k. The MCP server logs every
tool call (with the post-call scene and verifier result) to runs/ under a run tag,
so every number in the report is recomputed from the raw log, never from the
subject's own account of what happened.

    uv run python -m swayam.experiments.zero_shot --attempts 10
    uv run python -m swayam.experiments.zero_shot --report <stamp>   # rebuild the report only
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

from swayam import REPO_ROOT
from swayam.runlog import runs_dir
from swayam.stats import wilson

INSTRUCTION = "Move the cube from the bed into the tray slot and stop when the verifier passes."
PREDICTION = "predictions/2026-10-15-sim-pick-place-zero-shot.md"
OUT_DIR = REPO_ROOT / "studies" / "out" / "zero_shot"
REPORT = REPO_ROOT / "studies" / "out" / "sim_pick_place_zero_shot.md"
MOVE_TOOLS = {"move_gripper_to", "move_joints", "travel_to", "set_gripper", "home"}
# numbers copied from the prediction file, for the side-by-side table
PREDICTED = {"successes": 7, "median_tool_calls": 14, "irrecoverable": 0,
             "kept_moving_after_pass": "<= 1 attempt",
             "failure_mode": "cube released with yaw outside the funnel's +-20 deg capture"}


def run_attempt(k: int, stamp: str, model: str, max_turns: int, timeout_s: float,
                budget_usd: float, work: Path) -> dict:
    tag = f"zero-shot-{stamp}-{k:02d}"
    cwd = work / f"attempt-{k:02d}"
    if cwd.exists():
        shutil.rmtree(cwd)
    cwd.mkdir(parents=True)
    mcp_cfg = cwd / "mcp.json"
    mcp_cfg.write_text(json.dumps({"mcpServers": {"swayam-arm": {
        "command": "uv",
        "args": ["run", "--directory", str(REPO_ROOT), "swayam-arm-mcp"],
        "env": {"SWAYAM_BACKEND": "sim", "SWAYAM_SCENE": "task", "SWAYAM_CUBE_SEED": str(k),
                "SWAYAM_RUN_TAG": tag, "SWAYAM_RUNS_DIR": str(runs_dir())},
    }}}))
    hook = REPO_ROOT / ".claude" / "hooks" / "check_arm_command.py"
    settings = cwd / "settings.json"
    settings.write_text(json.dumps({"hooks": {"PreToolUse": [{
        "matcher": "mcp__swayam-arm__.*",
        "hooks": [{"type": "command",
                   "command": f'CLAUDE_PROJECT_DIR="{REPO_ROOT}" python3 "{hook}"'}],
    }]}}))
    cmd = [
        "claude", "-p", INSTRUCTION, "--model", model, "--output-format", "json",
        "--tools", "", "--mcp-config", str(mcp_cfg), "--strict-mcp-config",
        "--allowedTools", "mcp__swayam-arm__*", "--settings", str(settings),
        "--max-turns", str(max_turns), "--max-budget-usd", str(budget_usd),
    ]
    env = {k_: v for k_, v in os.environ.items() if not k_.startswith("SWAYAM_")}
    t0 = time.time()
    timed_out = False
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout_s)
        rc, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        rc, stdout, stderr = -1, (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), \
            (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
    wall = time.time() - t0
    try:
        cli = json.loads(stdout) if stdout.strip() else {}
    except json.JSONDecodeError:
        cli = {"unparsed_stdout": stdout[-2000:]}
    record = {
        "attempt": k, "seed": k, "run_tag": tag, "model_requested": model,
        "started_at": t0, "wall_s": round(wall, 1), "timed_out": timed_out, "exit_code": rc,
        "cli": {key: cli.get(key) for key in ("num_turns", "duration_ms", "duration_api_ms",
                                               "total_cost_usd", "is_error", "result",
                                               "session_id", "modelUsage", "stop_reason")},
        "stderr_tail": stderr[-2000:],
    }
    (OUT_DIR / f"attempt-{k:02d}.json").write_text(json.dumps(record, indent=1, default=str))
    return record


def load_log(tag: str) -> list[dict]:
    rows = []
    for path in sorted(runs_dir().glob("*.jsonl")):
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("run_tag") == tag:
                rows.append(r)
    return rows


def analyse(record: dict) -> dict:
    """Everything below is recomputed from runs/ (raw, append-only)."""
    rows = load_log(record["run_tag"])
    calls = [r for r in rows if r["event"] == "tool_call"]
    refused = [r for r in rows if r["event"] == "refused"]
    aborted = [r for r in rows if r["event"] == "move" and r.get("result", {}).get("aborted")]
    passes = [i for i, r in enumerate(calls) if (r.get("verifier") or {}).get("in_slot")]
    first_pass = passes[0] if passes else None
    final = calls[-1].get("verifier") if calls else None
    moves_after = [r for r in calls[first_pass + 1:] if r["tool"] in MOVE_TOOLS] if first_pass is not None else []
    off_table = any(((r.get("scene") or {}).get("cube") or {}).get("off_table") for r in calls)
    first_move = next((r["t"] for r in calls if r["tool"] in MOVE_TOOLS), None)
    verifier_calls = [r for r in calls if r["tool"] == "is_cube_in_slot"]
    return {
        "success": bool(final and final.get("in_slot")),
        "tool_calls": len(calls),
        "verifier_calls": len(verifier_calls),
        "refused": len(refused),
        "aborted_moves": len(aborted),
        "first_pass_call": first_pass,
        "kept_moving_after_pass": len(moves_after),
        "irrecoverable": off_table,
        "time_to_first_action_s": round(first_move - record["started_at"], 1) if first_move else None,
        "final_distance_mm": final.get("distance_mm") if final else None,
        "final_cube_yaw_deg": ((calls[-1].get("scene") or {}).get("cube") or {}).get("rpy_deg", [None] * 3)[2] if calls else None,
        "grasps": sum(1 for r in rows if r["event"] == "move"
                      and (r.get("result") or {}).get("grasp_event") == "grasped"),
    }


def write_report(records: list[dict], stamp: str) -> None:
    rows = []
    for rec in records:
        a = analyse(rec)
        rows.append({**rec, **a})
    n = len(rows)
    succ = sum(r["success"] for r in rows)
    p, lo, hi = wilson(succ, n)
    calls = [r["tool_calls"] for r in rows]
    walls = [r["wall_s"] for r in rows]
    costs = [r["cli"].get("total_cost_usd") or 0 for r in rows]
    models = sorted({m for r in rows for m in (r["cli"].get("modelUsage") or {})})
    lines = [
        "# Zero-shot pick-and-place in simulation (Phase 0 step 4 baseline)",
        "",
        f"Run `{stamp}`. Prediction: `{PREDICTION}` (committed before this run; see git log).",
        f"Model: {', '.join(models) or 'unknown'} via `claude -p`, fresh conversation per attempt, "
        f"tools = swayam-arm MCP only, no CLAUDE.md, safety hook on. Instruction: \"{INSTRUCTION}\"",
        "",
        "Every row is recomputed from `runs/*.jsonl` (append-only, tagged `run_tag`). No attempt was dropped.",
        "",
        "## Result vs prediction",
        "",
        "| Quantity | Predicted | Measured |",
        "|---|---|---|",
        f"| Successes / attempts | {PREDICTED['successes']} / 10 | **{succ} / {n}** |",
        f"| Success rate, Wilson 95% | {wilson(PREDICTED['successes'], 10)[0]:.0%} [{wilson(PREDICTED['successes'], 10)[1]:.0%}, {wilson(PREDICTED['successes'], 10)[2]:.0%}] | **{p:.0%} [{lo:.0%}, {hi:.0%}]** |",
        f"| Median tool calls per attempt | {PREDICTED['median_tool_calls']} | {statistics.median(calls) if calls else 'n/a'} |",
        f"| Median wall time per attempt (s) | - | {statistics.median(walls) if walls else 'n/a'} |",
        f"| Attempts that kept moving after the verifier passed | {PREDICTED['kept_moving_after_pass']} | {sum(1 for r in rows if r['kept_moving_after_pass'])} |",
        f"| Irrecoverable events (cube off the table) | {PREDICTED['irrecoverable']} | {sum(1 for r in rows if r['irrecoverable'])} |",
        f"| Total API cost (USD) | - | {sum(costs):.2f} |",
        f"| Most likely failure mode | {PREDICTED['failure_mode']} | see table |",
        "",
        "## Attempts",
        "",
        "| # | seed | verifier | tool calls | verifier calls | refused | aborted | moved after pass | off table | first action (s) | wall (s) | cost (USD) | final dist (mm) | final cube yaw (deg) | timed out |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['attempt']} | {r['seed']} | {'PASS' if r['success'] else 'fail'} | {r['tool_calls']} | "
            f"{r['verifier_calls']} | {r['refused']} | {r['aborted_moves']} | {r['kept_moving_after_pass']} | "
            f"{'yes' if r['irrecoverable'] else 'no'} | {r['time_to_first_action_s']} | {r['wall_s']} | "
            f"{(r['cli'].get('total_cost_usd') or 0):.2f} | {r['final_distance_mm']} | {r['final_cube_yaw_deg']} | "
            f"{'yes' if r['timed_out'] else 'no'} |"
        )
    lines += [
        "",
        "Columns: `verifier` is the last logged verifier state of the attempt (`is_cube_in_slot`), "
        "`moved after pass` counts arm commands logged after the first call whose post-call verifier was true "
        "(the AA-Robotics 'refine past success' failure), `off table` is the cube falling below the table top.",
        "",
        "## What the subject said (last message of each attempt, verbatim, not used for scoring)",
        "",
    ]
    for r in rows:
        msg = (r["cli"].get("result") or "").strip().replace("\n", " ")
        lines.append(f"- attempt {r['attempt']}: {msg[:400]}")
    lines += ["", f"Raw per-attempt CLI records: `studies/out/zero_shot/attempt-NN.json`; raw tool log: `runs/` with `run_tag` = `zero-shot-{stamp}-NN`.", ""]
    REPORT.write_text("\n".join(lines))
    print(REPORT)
    print(f"successes {succ}/{n}  Wilson 95% [{lo:.0%}, {hi:.0%}]  median calls {statistics.median(calls) if calls else 'n/a'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--attempts", type=int, default=10)
    ap.add_argument("--start", type=int, default=0, help="first seed/attempt index")
    ap.add_argument("--model", default="claude-fable-5-1")
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--timeout", type=float, default=900.0, help="seconds per attempt")
    ap.add_argument("--budget-usd", type=float, default=10.0, help="per attempt")
    ap.add_argument("--work", type=Path, default=None, help="scratch dir for attempt cwds")
    ap.add_argument("--report", default=None, help="only rebuild the report for this run stamp")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.report:
        recs = [json.loads(p.read_text()) for p in sorted(OUT_DIR.glob("attempt-*.json"))]
        recs = [r for r in recs if r["run_tag"].startswith(f"zero-shot-{args.report}-")]
        write_report(recs, args.report)
        return
    stamp = time.strftime("%Y%m%d-%H%M%S")
    work = args.work or Path(os.environ.get("TMPDIR", "/tmp")) / "swayam-zero-shot" / stamp
    (OUT_DIR / "run.json").write_text(json.dumps({"stamp": stamp, "args": vars(args), "instruction": INSTRUCTION}, default=str))
    records = []
    for k in range(args.start, args.start + args.attempts):
        print(f"attempt {k} ...", flush=True)
        rec = run_attempt(k, stamp, args.model, args.max_turns, args.timeout, args.budget_usd, work)
        a = analyse(rec)
        print(f"  {'PASS' if a['success'] else 'fail'}  calls={a['tool_calls']} wall={rec['wall_s']}s "
              f"cost={rec['cli'].get('total_cost_usd')} err={rec['cli'].get('is_error')}", flush=True)
        records.append(rec)
    write_report(records, stamp)


if __name__ == "__main__":
    main()
