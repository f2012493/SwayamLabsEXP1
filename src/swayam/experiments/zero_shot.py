"""Zero-shot pick-and-place baseline (ROADMAP Phase 0 step 4, AA-Robotics style).

Prediction: predictions/2026-10-15-sim-pick-place-zero-shot.md (committed first).

Each attempt is a fresh, non-interactive `claude -p` conversation whose only tools
are the swayam-arm MCP tools, started in an empty directory (no CLAUDE.md, no
source code), with the independent safety hook attached. Each attempt starts its
own MCP server on the task scene with the cube at seed k. The MCP server logs every
tool call (with the post-call scene and verifier result) to runs/ under a run tag,
so every number in the report is recomputed from the raw log, never from the
subject's own account of what happened.

    uv run python -m swayam.experiments.zero_shot --attempts 10                    # task v1
    uv run python -m swayam.experiments.zero_shot --condition v2 --attempts 10     # task v2
    uv run python -m swayam.experiments.zero_shot --condition v2-noise --attempts 10
    uv run python -m swayam.experiments.zero_shot --condition v2-noise-heldout --attempts 10 --start 10
    uv run python -m swayam.experiments.zero_shot --report <stamp>   # rebuild the v1 report only
    uv run python -m swayam.experiments.zero_shot --report-v2        # rebuild the v2 report

Conditions (CONDITIONS): "v1" is the 2026-10-15 baseline (8 mm funnel, 15 mm weld);
"v2" is task version 2 (4 mm funnel, geometric grasp rule, see swayam.arm.sim);
"v2-noise" is v2 plus a seeded 2 mm RMS xy placement error on every move_gripper_to;
"v2-noise-heldout" is the same condition on fresh seeds, reported by
swayam.experiments.pre_release_signal (predictions/2026-10-15-pre-release-tilt-signal.md).
Prediction for v2: predictions/2026-10-15-sim-pick-place-zero-shot-v2.md.
"""

from __future__ import annotations

import argparse
import json
import math
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
PREDICTION_V2 = "predictions/2026-10-15-sim-pick-place-zero-shot-v2.md"
OUT_DIR = REPO_ROOT / "studies" / "out" / "zero_shot"
REPORT = REPO_ROOT / "studies" / "out" / "sim_pick_place_zero_shot.md"
REPORT_V2 = REPO_ROOT / "studies" / "out" / "sim_pick_place_zero_shot_v2.md"
MOVE_TOOLS = {"move_gripper_to", "move_joints", "travel_to", "set_gripper", "home"}
# numbers copied from the prediction file, for the side-by-side table
PREDICTED = {"successes": 7, "median_tool_calls": 14, "irrecoverable": 0,
             "kept_moving_after_pass": "<= 1 attempt",
             "failure_mode": "cube released with yaw outside the funnel's +-20 deg capture"}
# numbers copied from PREDICTION_V2 (per condition)
PREDICTED_V2 = {
    "v2": {"successes": 7, "median_tool_calls": 20, "refused_grasp_attempts": ">= 3",
           "success_window": (5, 9)},
    "v2-noise": {"successes": 5, "median_tool_calls": 24, "refused_grasp_attempts": ">= 4",
                 "success_window": (3, 7)},
}
FAILURE_MODE_V2 = ("cube jammed tilted (> 10 deg) in the funnel or pocket, centre within 12 mm of the "
                   "slot centre, after a release; the v2 rule then refuses every re-grasp")
CONDITIONS = {
    "v1": {"task_version": 1, "noise_mm": 0.0, "out_dir": OUT_DIR, "tag": "zero-shot"},
    "v2": {"task_version": 2, "noise_mm": 0.0, "out_dir": REPO_ROOT / "studies" / "out" / "zero_shot_v2",
           "tag": "zero-shot-v2"},
    "v2-noise": {"task_version": 2, "noise_mm": 2.0,
                 "out_dir": REPO_ROOT / "studies" / "out" / "zero_shot_v2_noise", "tag": "zero-shot-v2n"},
    # the same condition on fresh seeds, kept in its own folder and tag family so the audited
    # seeds 0-9 report is never rebuilt with extra attempts; scored by pre_release_signal
    "v2-noise-heldout": {"task_version": 2, "noise_mm": 2.0,
                         "out_dir": REPO_ROOT / "studies" / "out" / "zero_shot_v2_noise_heldout",
                         "tag": "zero-shot-v2nh"},
}


def run_attempt(k: int, stamp: str, model: str, max_turns: int, timeout_s: float,
                budget_usd: float, work: Path, condition: str = "v1") -> dict:
    cond = CONDITIONS[condition]
    out_dir = cond["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{cond['tag']}-{stamp}-{k:02d}"
    cwd = work / f"attempt-{k:02d}"
    if cwd.exists():
        shutil.rmtree(cwd)
    cwd.mkdir(parents=True)
    mcp_cfg = cwd / "mcp.json"
    env = {"SWAYAM_BACKEND": "sim", "SWAYAM_SCENE": "task", "SWAYAM_CUBE_SEED": str(k),
           "SWAYAM_RUN_TAG": tag, "SWAYAM_RUNS_DIR": str(runs_dir()),
           "SWAYAM_TASK_VERSION": str(cond["task_version"])}
    if cond["noise_mm"]:
        env["SWAYAM_PLACE_NOISE_MM"] = str(cond["noise_mm"])
    mcp_cfg.write_text(json.dumps({"mcpServers": {"swayam-arm": {
        "command": "uv",
        "args": ["run", "--directory", str(REPO_ROOT), "swayam-arm-mcp"],
        "env": env,
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
        "attempt": k, "seed": k, "run_tag": tag, "model_requested": model, "condition": condition,
        "task_version": cond["task_version"], "noise_mm": cond["noise_mm"],
        "started_at": t0, "wall_s": round(wall, 1), "timed_out": timed_out, "exit_code": rc,
        "cli": {key: cli.get(key) for key in ("num_turns", "duration_ms", "duration_api_ms",
                                               "total_cost_usd", "is_error", "result",
                                               "session_id", "modelUsage", "stop_reason")},
        "stderr_tail": stderr[-2000:],
    }
    (out_dir / f"attempt-{k:02d}.json").write_text(json.dumps(record, indent=1, default=str))
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
    # did the cube itself move after the verifier first passed (vs. the empty gripper retreating)?
    cube_xyz = [((r.get("scene") or {}).get("cube") or {}).get("xyz_mm") for r in calls]
    disturbed = False
    if first_pass is not None and cube_xyz[first_pass]:
        ref = cube_xyz[first_pass]
        disturbed = any(c and max(abs(a - b) for a, b in zip(c, ref)) > 0.5 for c in cube_xyz[first_pass + 1:])
    # first release after a grasp: did it already pass? (the predicted failure is a bad first placement)
    moves = [r for r in rows if r["event"] == "move"]
    releases = [r for r in moves if (r.get("result") or {}).get("grasp_event") == "released"]
    first_release_passed = None
    if releases:
        t = releases[0]["t"]
        after = [r for r in calls if r["t"] >= t]
        first_release_passed = bool(after and (after[0].get("verifier") or {}).get("in_slot"))
    refused_grasps = [r for r in moves if str((r.get("result") or {}).get("grasp_event", "")).startswith("close: no grasp")]
    final_rpy = ((calls[-1].get("scene") or {}).get("cube") or {}).get("rpy_deg") if calls else None
    return {
        "cube_disturbed_after_pass": disturbed,
        "first_release_passed": first_release_passed,
        "releases": len(releases),
        "refused_grasps": len(refused_grasps),
        "final_cube_tilt_deg": round(tilt_from_rpy(final_rpy), 1) if final_rpy else None,
        "noise_moves": sum(1 for r in moves if r.get("placement_noise_mm")),
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


def tilt_from_rpy(rpy_deg) -> float:
    """Angle (deg) between the cube's most vertical face normal and world z, from the
    logged roll/pitch/yaw (ZYX convention, as swayam.arm.sim._cube_pose writes it)."""
    r, p = math.radians(rpy_deg[0]), math.radians(rpy_deg[1])
    best = max(abs(math.sin(p)), abs(math.cos(p) * math.sin(r)), abs(math.cos(p) * math.cos(r)))
    return math.degrees(math.acos(min(1.0, best)))


def _failure_mode_verdict_v2(rows: list[dict]) -> str:
    """Computed, not asserted: among failed attempts, is the modal final state the predicted one
    (tilt > 10 deg, centre within 12 mm of the slot centre)?"""
    failed = [r for r in rows if not r["success"]]
    if not failed:
        return "no attempt failed, so it holds vacuously."
    n_pred = sum(1 for r in failed if (r["final_cube_tilt_deg"] or 0) > 10 and (r["final_distance_mm"] or 99) <= 12)
    verdict = "holds" if n_pred * 2 > len(failed) else "does not hold"
    return (f"**{verdict}** ({n_pred} of {len(failed)} failures end with the cube tilted > 10 deg within "
            f"12 mm of the slot centre).")


def _failure_mode_verdict(rows: list[dict]) -> str:
    """Computed, not asserted: among failed attempts, is the modal final state the predicted one?"""
    failed = [r for r in rows if not r["success"]]
    if not failed:
        return "no attempt failed, so it holds vacuously."
    def predicted(r):
        yaw = r["final_cube_yaw_deg"]
        off = abs(((yaw + 45) % 90) - 45) if yaw is not None else 0
        return off > 20 and (r["final_distance_mm"] or 0) > 3
    n_pred = sum(1 for r in failed if predicted(r))
    verdict = "holds" if n_pred * 2 > len(failed) else "does not hold"
    return f"**{verdict}** ({n_pred} of {len(failed)} failures end with |yaw mod 90| > 20 deg off the slot)."


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
        f"| Attempts that commanded motion after the verifier first passed | {PREDICTED['kept_moving_after_pass']} | {sum(1 for r in rows if r['kept_moving_after_pass'])} (cube disturbed in {sum(1 for r in rows if r['cube_disturbed_after_pass'])}) |",
        f"| Attempts whose first release did not pass (predicted modal failure, then recovered) | - | {sum(1 for r in rows if r['first_release_passed'] is False)} |",
        f"| Irrecoverable events (cube off the table) | {PREDICTED['irrecoverable']} | {sum(1 for r in rows if r['irrecoverable'])} |",
        f"| Total API cost (USD) | - | {sum(costs):.2f} |",
        f"| Most likely failure mode | {PREDICTED['failure_mode']} | see table |",
        "",
        "## Attempts",
        "",
        "| # | seed | verifier | tool calls | verifier calls | refused | aborted | releases | first release passed | moved after pass | cube disturbed after pass | off table | first action (s) | wall (s) | cost (USD) | final dist (mm) | final cube yaw (deg) | timed out |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['attempt']} | {r['seed']} | {'PASS' if r['success'] else 'fail'} | {r['tool_calls']} | "
            f"{r['verifier_calls']} | {r['refused']} | {r['aborted_moves']} | {r['releases']} | "
            f"{r['first_release_passed']} | {r['kept_moving_after_pass']} | {'yes' if r['cube_disturbed_after_pass'] else 'no'} | "
            f"{'yes' if r['irrecoverable'] else 'no'} | {r['time_to_first_action_s']} | {r['wall_s']} | "
            f"{(r['cli'].get('total_cost_usd') or 0):.2f} | {r['final_distance_mm']} | {r['final_cube_yaw_deg']} | "
            f"{'yes' if r['timed_out'] else 'no'} |"
        )
    lines += [
        "",
        "Columns: `verifier` is the last logged verifier state of the attempt (`is_cube_in_slot`); "
        "`first release passed` is the verifier state right after the first gripper-open following a grasp; "
        "`moved after pass` counts arm commands logged after the first call whose post-call verifier was true "
        "(the AA-Robotics 'refine past success' failure) and `cube disturbed after pass` whether the cube centre "
        "moved more than 0.5 mm after that; `off table` is the cube falling below the table top. "
        "Tool calls are counted from the server log, so a call blocked by the safety hook before reaching the "
        "server is not counted.",
        "",
        "## Decision rule (from the prediction file, applied as written)",
        "",
        f"- Success-rate prediction (hold if 5-9 of 10): **{'holds' if 5 <= succ <= 9 else 'does not hold'}** ({succ}/10).",
        f"- Tool-call prediction (hold if median in 8-25): **{'holds' if calls and 8 <= statistics.median(calls) <= 25 else 'does not hold'}** (median {statistics.median(calls) if calls else 'n/a'}).",
        f"- Failure-mode prediction: {_failure_mode_verdict(rows)} The predicted mode (release with the "
        f"cube yaw outside the funnel's capture) appeared as a first-placement failure in "
        f"{sum(1 for r in rows if r['first_release_passed'] is False)} attempts.",
        "- The pre-registered consequence of >= 9 successes applies: the simulated task is too easy to be a useful "
        "baseline. The next version removes the weld's 15 mm forgiveness and/or shrinks the funnel, with a new "
        "prediction file; the same instruction and seeds are rerun on hardware in Phase 0 step 4.",
        "",
        "## What the subject said (last message of each attempt, verbatim, not used for scoring)",
        "",
    ]
    for r in rows:
        msg = (r["cli"].get("result") or "").strip().replace("\n", " ")
        lines.append(f"- attempt {r['attempt']}: {msg[:400]}")
    lines += ["", f"Raw per-attempt CLI records: `studies/out/zero_shot/attempt-NN.json`; raw tool log: `runs/` with `run_tag` = `zero-shot-{stamp}-NN`.", ""]
    notes = OUT_DIR / "notes.md"
    if notes.exists():
        lines += ["## Notes", "", notes.read_text().strip(), ""]
    audit = OUT_DIR / "audit.md"
    if audit.exists():
        lines += ["## Closure-auditor report (verbatim)", "", audit.read_text().strip(), ""]
    REPORT.write_text("\n".join(lines))
    print(REPORT)
    print(f"successes {succ}/{n}  Wilson 95% [{lo:.0%}, {hi:.0%}]  median calls {statistics.median(calls) if calls else 'n/a'}")


def _load_records(condition: str) -> list[dict]:
    out_dir = CONDITIONS[condition]["out_dir"]
    recs = [json.loads(p.read_text()) for p in sorted(out_dir.glob("attempt-*.json"))]
    return [{**r, **analyse(r)} for r in recs]


def _summary(rows: list[dict]) -> dict:
    n = len(rows)
    succ = sum(r["success"] for r in rows)
    p, lo, hi = wilson(succ, n)
    calls = [r["tool_calls"] for r in rows]
    return {
        "n": n, "successes": succ, "rate": p, "lo": lo, "hi": hi,
        "median_calls": statistics.median(calls) if calls else None,
        "median_wall": statistics.median([r["wall_s"] for r in rows]) if rows else None,
        "cost": sum(r["cli"].get("total_cost_usd") or 0 for r in rows),
        "moved_after_pass": sum(1 for r in rows if r["kept_moving_after_pass"]),
        "disturbed": sum(1 for r in rows if r["cube_disturbed_after_pass"]),
        "first_release_failed": sum(1 for r in rows if r["first_release_passed"] is False),
        "refused_grasp_attempts": sum(1 for r in rows if r["refused_grasps"]),
        "irrecoverable": sum(1 for r in rows if r["irrecoverable"]),
        "timed_out": sum(1 for r in rows if r["timed_out"]),
        "failed_tilted": sum(1 for r in rows if not r["success"] and (r["final_cube_tilt_deg"] or 0) > 10),
    }


def write_report_v2() -> None:
    """studies/out/sim_pick_place_zero_shot_v2.md: v2 and v2-noise side by side with the v2
    prediction and the v1 result. Every number is recomputed from runs/ and the attempt
    records; conditions without records are shown as 'not run'."""
    data = {c: _load_records(c) for c in ("v1", "v2", "v2-noise")}
    summ = {c: _summary(rows) for c, rows in data.items() if rows}
    models = sorted({m for rows in data.values() for r in rows for m in (r["cli"].get("modelUsage") or {})})
    stamps = {c: sorted({r["run_tag"].rsplit("-", 1)[0] for r in rows}) for c, rows in data.items() if rows}

    def cell(c, key, fmt="{}"):
        return fmt.format(summ[c][key]) if c in summ and summ[c][key] is not None else "not run"

    def rate(c):
        if c not in summ:
            return "not run"
        s = summ[c]
        return f"**{s['successes']} / {s['n']}** ({s['rate']:.0%} [{s['lo']:.0%}, {s['hi']:.0%}])"

    def pred_rate(c):
        k = PREDICTED_V2[c]["successes"]
        p, lo, hi = wilson(k, 10)
        return f"{k} / 10 ({p:.0%} [{lo:.0%}, {hi:.0%}])"

    v1p, v1lo, v1hi = wilson(PREDICTED["successes"], 10)
    lines = [
        "# Zero-shot pick-and-place in simulation, task v2 (harder sim)",
        "",
        f"Prediction: `{PREDICTION_V2}` (committed before the v2 runs; see git log). v1 reference: "
        f"`{PREDICTION}` and `studies/out/sim_pick_place_zero_shot.md`.",
        f"Model: {', '.join(models) or 'unknown'} via `claude -p`, fresh conversation per attempt, tools = "
        f"swayam-arm MCP only, no CLAUDE.md, safety hook on. Instruction (unchanged): \"{INSTRUCTION}\"",
        "Run stamps: " + "; ".join(f"{c} = {', '.join(v)}" for c, v in stamps.items()) + ".",
        "",
        "What changed from v1 (`SWAYAM_TASK_VERSION=2`, `sim/so101/scene_task_v2.xml`, `swayam.arm.sim`):",
        "the outer funnel is 4 mm per side instead of 8 (lead-in still 1.5 mm); the weld grasp requires the jaws "
        "to close from a gap wider than the cube, the cube to lie between the finger pads (jaw axis window, "
        "+-7 mm across the pads, -45..6 mm along the fingers) and the cube to be within 10 deg of flat. "
        "`v2-noise` adds a seeded N(0, 1.41 mm) error per axis (2 mm RMS radial) to every move_gripper_to "
        "target, from the 3.5 mm camera-guided placement budget. The tool descriptions tell the subject the "
        "active rule, as in v1.",
        "",
        "Every row is recomputed from `runs/*.jsonl` (append-only, tagged `run_tag`). No attempt was dropped.",
        "",
        "## Result vs prediction (and v1)",
        "",
        "| Quantity | v1 predicted | v1 measured | v2 predicted | **v2 measured** | v2-noise predicted | **v2-noise measured** |",
        "|---|---|---|---|---|---|---|",
        f"| Successes / attempts (Wilson 95%) | {PREDICTED['successes']} / 10 ({v1p:.0%} [{v1lo:.0%}, {v1hi:.0%}]) | {rate('v1')} | {pred_rate('v2')} | {rate('v2')} | {pred_rate('v2-noise')} | {rate('v2-noise')} |",
        f"| Median tool calls per attempt | {PREDICTED['median_tool_calls']} | {cell('v1', 'median_calls')} | {PREDICTED_V2['v2']['median_tool_calls']} | {cell('v2', 'median_calls')} | {PREDICTED_V2['v2-noise']['median_tool_calls']} | {cell('v2-noise', 'median_calls')} |",
        f"| Median wall time per attempt (s) | - | {cell('v1', 'median_wall')} | - | {cell('v2', 'median_wall')} | - | {cell('v2-noise', 'median_wall')} |",
        f"| Attempts with >= 1 refused grasp | - | {cell('v1', 'refused_grasp_attempts')} | {PREDICTED_V2['v2']['refused_grasp_attempts']} | {cell('v2', 'refused_grasp_attempts')} | {PREDICTED_V2['v2-noise']['refused_grasp_attempts']} | {cell('v2-noise', 'refused_grasp_attempts')} |",
        f"| Attempts whose first release did not pass | - | {cell('v1', 'first_release_failed')} | - | {cell('v2', 'first_release_failed')} | - | {cell('v2-noise', 'first_release_failed')} |",
        f"| Failed attempts ending with the cube tilted > 10 deg | - | {cell('v1', 'failed_tilted')} | modal failure | {cell('v2', 'failed_tilted')} | modal failure | {cell('v2-noise', 'failed_tilted')} |",
        f"| Attempts that commanded motion after the verifier first passed | <= 1 | {cell('v1', 'moved_after_pass')} | <= 1 | {cell('v2', 'moved_after_pass')} | <= 1 | {cell('v2-noise', 'moved_after_pass')} |",
        f"| Irrecoverable events (cube off the table) | 0 | {cell('v1', 'irrecoverable')} | 0 | {cell('v2', 'irrecoverable')} | 0 | {cell('v2-noise', 'irrecoverable')} |",
        f"| Timed out / errored attempts | - | {cell('v1', 'timed_out')} | - | {cell('v2', 'timed_out')} | - | {cell('v2-noise', 'timed_out')} |",
        f"| Total API cost (USD) | - | {cell('v1', 'cost', '{:.2f}')} | - | {cell('v2', 'cost', '{:.2f}')} | - | {cell('v2-noise', 'cost', '{:.2f}')} |",
        "",
    ]
    for c in ("v2", "v2-noise"):
        rows = data[c]
        lines += [f"## Attempts: {c}" + ("" if rows else " (not run)"), ""]
        if not rows:
            continue
        lines += [
            "| # | seed | verifier | tool calls | verifier calls | refused moves | aborted | grasps | refused grasps | releases | first release passed | moved after pass | cube disturbed after pass | off table | first action (s) | wall (s) | cost (USD) | final dist (mm) | final tilt (deg) | final yaw (deg) | timed out |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for r in rows:
            lines.append(
                f"| {r['attempt']} | {r['seed']} | {'PASS' if r['success'] else 'fail'} | {r['tool_calls']} | "
                f"{r['verifier_calls']} | {r['refused']} | {r['aborted_moves']} | {r['grasps']} | {r['refused_grasps']} | "
                f"{r['releases']} | {r['first_release_passed']} | {r['kept_moving_after_pass']} | "
                f"{'yes' if r['cube_disturbed_after_pass'] else 'no'} | {'yes' if r['irrecoverable'] else 'no'} | "
                f"{r['time_to_first_action_s']} | {r['wall_s']} | {(r['cli'].get('total_cost_usd') or 0):.2f} | "
                f"{r['final_distance_mm']} | {r['final_cube_tilt_deg']} | {r['final_cube_yaw_deg']} | "
                f"{'yes' if r['timed_out'] else 'no'} |"
            )
        lines.append("")
    lines += [
        "Columns as in the v1 report, plus `grasps` / `refused grasps` (close commands that did / did not "
        "attach the cube, from the logged grasp_event) and `final tilt` (angle of the cube's most vertical "
        "face normal from vertical, from the logged final pose). `refused moves` are commands the server "
        "refused on limits; calls blocked by the hook never reach the server and are not counted.",
        "",
        "## Decision rule (from the v2 prediction file, applied as written)",
        "",
    ]
    for c in ("v2", "v2-noise"):
        if c not in summ:
            lines.append(f"- {c}: not run.")
            continue
        s = summ[c]
        lo_w, hi_w = PREDICTED_V2[c]["success_window"]
        lines += [
            f"- {c} success-rate prediction (hold if {lo_w}-{hi_w} of 10): "
            f"**{'holds' if lo_w <= s['successes'] <= hi_w else 'does not hold'}** ({s['successes']}/{s['n']}).",
            f"- {c} tool-call prediction (hold if median in 12-35): "
            f"**{'holds' if s['median_calls'] is not None and 12 <= s['median_calls'] <= 35 else 'does not hold'}** "
            f"(median {s['median_calls']}).",
            f"- {c} failure-mode prediction: {_failure_mode_verdict_v2(data[c])}",
        ]
    if "v2" in summ and "v2-noise" in summ:
        d = summ["v2"]["successes"] - summ["v2-noise"]["successes"]
        lines.append(f"- Noise effect: v2 minus v2-noise = {d} successes "
                     f"({'>= 3: the 4 mm funnel is not 2x the placement error in practice' if d >= 3 else 'under 3: no evidence against the funnel >= 2x error rule at this sample size'}).")
    if "v2" in summ:
        s = summ["v2"]
        if s["successes"] >= 9:
            lines.append("- v2 scored >= 9: by the pre-registered rule the sim is still too easy; v2-noise becomes the "
                         "sim reference for hardware and no further sim hardening happens before the arm arrives.")
        elif s["successes"] <= 4:
            lines.append("- v2 scored <= 4: by the pre-registered rule the first suspect is the tooling (read every "
                         "`no grasp` and `refused` record before blaming the model).")
    lines += ["", "## What the subject said (last message of each attempt, verbatim, not used for scoring)", ""]
    for c in ("v2", "v2-noise"):
        for r in data[c]:
            msg = (r["cli"].get("result") or "").strip().replace("\n", " ")
            lines.append(f"- {c} attempt {r['attempt']}: {msg[:400]}")
    lines += ["", "Raw per-attempt CLI records: `studies/out/zero_shot_v2/attempt-NN.json` and "
              "`studies/out/zero_shot_v2_noise/attempt-NN.json`; raw tool log: `runs/` with the run tags above. "
              "Funnel characterisation: `studies/out/funnel_capture.md`.", ""]
    for name, title in (("notes.md", "Notes"), ("audit.md", "Closure-auditor report (verbatim)")):
        path = CONDITIONS["v2"]["out_dir"] / name
        if path.exists():
            lines += [f"## {title}", "", path.read_text().strip(), ""]
    REPORT_V2.write_text("\n".join(lines))
    print(REPORT_V2)
    for c, s in summ.items():
        print(f"{c}: successes {s['successes']}/{s['n']}  Wilson 95% [{s['lo']:.0%}, {s['hi']:.0%}]  "
              f"median calls {s['median_calls']}  cost {s['cost']:.2f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--condition", choices=sorted(CONDITIONS), default="v1")
    ap.add_argument("--attempts", type=int, default=10)
    ap.add_argument("--start", type=int, default=0, help="first seed/attempt index")
    ap.add_argument("--model", default="claude-fable-5-1")
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--timeout", type=float, default=900.0, help="seconds per attempt")
    ap.add_argument("--budget-usd", type=float, default=10.0, help="per attempt")
    ap.add_argument("--work", type=Path, default=None, help="scratch dir for attempt cwds")
    ap.add_argument("--report", default=None, help="only rebuild the v1 report for this run stamp")
    ap.add_argument("--report-v2", action="store_true", help="only rebuild the v2 report from existing records")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.report:
        recs = [json.loads(p.read_text()) for p in sorted(OUT_DIR.glob("attempt-*.json"))]
        recs = [r for r in recs if r["run_tag"].startswith(f"zero-shot-{args.report}-")]
        write_report(recs, args.report)
        return
    if args.report_v2:
        write_report_v2()
        return
    cond = CONDITIONS[args.condition]
    cond["out_dir"].mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    work = args.work or Path(os.environ.get("TMPDIR", "/tmp")) / "swayam-zero-shot" / f"{args.condition}-{stamp}"
    (cond["out_dir"] / "run.json").write_text(json.dumps({"stamp": stamp, "args": vars(args), "instruction": INSTRUCTION}, default=str))
    records = []
    for k in range(args.start, args.start + args.attempts):
        print(f"[{args.condition}] attempt {k} ...", flush=True)
        rec = run_attempt(k, stamp, args.model, args.max_turns, args.timeout, args.budget_usd, work, args.condition)
        a = analyse(rec)
        print(f"  {'PASS' if a['success'] else 'fail'}  calls={a['tool_calls']} grasps={a['grasps']} "
              f"refused_grasps={a['refused_grasps']} wall={rec['wall_s']}s "
              f"cost={rec['cli'].get('total_cost_usd')} err={rec['cli'].get('is_error')}", flush=True)
        records.append(rec)
    if args.condition == "v1":
        write_report(records, stamp)
    elif args.condition == "v2-noise-heldout":
        from swayam.experiments.pre_release_signal import load_rows, write_report as write_signal_report

        print(write_signal_report(load_rows()))
    else:
        write_report_v2()


if __name__ == "__main__":
    main()
