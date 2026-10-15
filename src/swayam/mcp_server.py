"""MCP server that lets Claude Code drive the SO-101 (simulated or real) safely.

Every command goes through swayam.controller.Controller, which checks it against
config/limits.json and logs it to runs/.
Backend: SWAYAM_BACKEND=sim (default) or real (also needs SWAYAM_PORT).
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from swayam.controller import Controller

mcp = FastMCP("swayam-arm")
_state: dict = {}


def _ctl() -> Controller:
    if "ctl" not in _state:
        _state["ctl"] = Controller()
    return _state["ctl"]


@mcp.tool()
def get_telemetry() -> dict:
    """Current joint angles (deg), gripper (% open), and sensed load / current /
    temperature / voltage where the backend supports it."""
    return _ctl().telemetry()


@mcp.tool()
def get_limits() -> dict:
    """The safety limits every command is checked against."""
    return _ctl().limits


@mcp.tool()
def move_joints(
    targets: dict[str, float], duration_s: float = 1.0, same_direction: bool = True
) -> dict:
    """Move some or all joints to target angles in degrees over duration_s seconds.

    Joint names: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll.
    Joints left out hold position. Refused moves return {"ok": false, "refused": [...]}.
    same_direction (default on) finishes every joint from its configured side to
    cancel gear backlash; turn it off only for experiments that need it off.
    """
    return _ctl().move(targets, duration_s, same_direction, tool="move_joints")


@mcp.tool()
def travel_to(targets: dict[str, float], deg_per_s: float = 30.0) -> dict:
    """Move any distance to target joint angles (deg), automatically split into legs
    that each respect the step limit. Use this for big moves; move_joints for small ones."""
    return _ctl().travel(targets, deg_per_s, tool="travel_to")


@mcp.tool()
def set_gripper(percent_open: float, duration_s: float = 0.5) -> dict:
    """Open (100) or close (0) the gripper. Watch load/current to detect a grasp."""
    return _ctl().gripper(percent_open, duration_s)


@mcp.tool()
def home(duration_s: float = 3.0) -> dict:
    """Return to the home pose defined in config/limits.json."""
    return _ctl().home(duration_s)


@mcp.tool()
def stop() -> dict:
    """Hold position immediately."""
    return _ctl().stop()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
