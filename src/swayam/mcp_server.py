"""MCP server that lets Claude Code drive the SO-101 (simulated or real) safely.

Every command is checked against config/limits.json (joint ranges, step size, speed,
duration, predicted gripper height and reach) before it runs, and logged to runs/.
Backend: SWAYAM_BACKEND=sim (default) or real (also needs SWAYAM_PORT).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from swayam import GRIPPER, JOINTS
from swayam.arm import make_arm
from swayam.kinematics import Kinematics
from swayam.limits import check_gripper_pose, check_move, load_limits
from swayam.runlog import log_event

mcp = FastMCP("swayam-arm")
_state: dict = {}


def _arm():
    if "arm" not in _state:
        _state["limits"] = load_limits()
        _state["arm"] = make_arm()
        _state["kin"] = Kinematics()
    return _state["arm"]


def _guarded_move(targets: dict[str, float], duration_s: float, tool: str) -> dict:
    arm = _arm()
    limits = _state["limits"]
    current = arm.positions()
    problems = check_move(targets, duration_s, current, limits)
    if not problems:
        goal = {**current, **targets}
        problems = check_gripper_pose(_state["kin"].gripper_xyz(goal), limits)
    if problems:
        log_event("refused", tool=tool, targets=targets, duration_s=duration_s, problems=problems)
        return {"ok": False, "refused": problems}
    result = arm.move(targets, duration_s)
    log_event("move", tool=tool, targets=targets, duration_s=duration_s, result=result)
    return {"ok": result.get("aborted") is None, **result}


@mcp.tool()
def get_telemetry() -> dict:
    """Current joint angles (deg), gripper (% open), and sensed load / current /
    temperature / voltage where the backend supports it."""
    return _arm().telemetry()


@mcp.tool()
def get_limits() -> dict:
    """The safety limits every command is checked against."""
    _arm()
    return _state["limits"]


@mcp.tool()
def move_joints(targets: dict[str, float], duration_s: float = 1.0) -> dict:
    """Move some or all joints to target angles in degrees over duration_s seconds.

    Joint names: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll.
    Joints left out hold position. Refused moves return {"ok": false, "refused": [...]}.
    """
    return _guarded_move(targets, duration_s, "move_joints")


@mcp.tool()
def set_gripper(percent_open: float, duration_s: float = 0.5) -> dict:
    """Open (100) or close (0) the gripper. Watch load/current to detect a grasp."""
    return _guarded_move({GRIPPER: percent_open}, duration_s, "set_gripper")


@mcp.tool()
def home(duration_s: float = 3.0) -> dict:
    """Return to the home pose defined in config/limits.json."""
    _arm()
    home_pose = {n: v for n, v in _state["limits"]["home"].items() if n in (*JOINTS, GRIPPER)}
    return _guarded_move(home_pose, duration_s, "home")


@mcp.tool()
def stop() -> dict:
    """Hold position immediately."""
    _arm().stop()
    log_event("stop")
    return {"ok": True}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
