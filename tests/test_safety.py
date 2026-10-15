import json
import subprocess
import sys
from pathlib import Path

from swayam import REPO_ROOT
from swayam.limits import check_gripper_pose, check_move, load_limits

LIMITS = load_limits()
HOME = {k: v for k, v in LIMITS["home"].items()}
HOOK = REPO_ROOT / ".claude" / "hooks" / "check_arm_command.py"


def test_valid_move_passes():
    assert check_move({"shoulder_pan": 20}, 1.0, HOME, LIMITS) == []


def test_out_of_range_refused():
    problems = check_move({"shoulder_pan": 170}, 2.0, None, LIMITS)
    assert any("outside" in p for p in problems)


def test_unknown_joint_refused():
    assert check_move({"elbow": 10}, 1.0, HOME, LIMITS)


def test_big_step_and_fast_move_refused():
    problems = check_move({"shoulder_lift": 80}, 0.5, HOME, LIMITS)
    assert any("step" in p for p in problems)
    assert any("speed" in p for p in problems)


def test_too_short_duration_refused():
    assert check_move({"shoulder_pan": 1}, 0.05, HOME, LIMITS)


def test_gripper_below_table_refused():
    assert check_gripper_pose((0.2, 0.0, -0.01), LIMITS)
    assert check_gripper_pose((0.2, 0.0, 0.1), LIMITS) == []


def _run_hook(tool_name, tool_input):
    event = {"tool_name": tool_name, "tool_input": tool_input}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(REPO_ROOT)},
    )


def test_hook_blocks_out_of_range():
    r = _run_hook("mcp__swayam-arm__move_joints", {"targets": {"wrist_flex": 120}})
    assert r.returncode == 2
    assert "Blocked by safety hook" in r.stderr


def test_hook_allows_valid_and_ignores_other_tools():
    assert _run_hook("mcp__swayam-arm__move_joints", {"targets": {"wrist_flex": 10}}).returncode == 0
    assert _run_hook("mcp__swayam-arm__set_gripper", {"percent_open": 150}).returncode == 2
    assert _run_hook("mcp__swayam-arm__get_telemetry", {}).returncode == 0
