"""MCP server that lets Claude Code drive the SO-101 (simulated or real) safely.

Every command goes through swayam.controller.Controller, which checks it against
config/limits.json and logs it to runs/.
Backend: SWAYAM_BACKEND=sim (default) or real (also needs SWAYAM_PORT).
"""

from __future__ import annotations

import functools
import time

from mcp.server.fastmcp import FastMCP

from swayam.controller import Controller
from swayam.ik import IK, Unreachable
from swayam.runlog import log_event

mcp = FastMCP("swayam-arm")
_state: dict = {}


def tool(fn):
    """Register an MCP tool and log every call (args, duration, state afterwards)."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        try:
            return fn(*args, **kwargs)
        finally:
            sim = _sim()
            log_event("tool_call", tool=fn.__name__, args=kwargs or list(args),
                      seconds=round(time.time() - t0, 3),
                      verifier=sim.cube_in_slot() if sim else None,
                      scene=sim.scene() if sim else None)

    return mcp.tool()(wrapper)


def _ctl() -> Controller:
    if "ctl" not in _state:
        _state["ctl"] = Controller()
    return _state["ctl"]


def _ik() -> IK:
    if "ik" not in _state:
        _state["ik"] = IK(limits=_ctl().limits)
    return _state["ik"]


def _public(result: dict) -> dict:
    """Object poses are logged with every move but only reported through get_scene."""
    return {k: v for k, v in result.items() if k != "scene"}


def _sim():
    """The SimArm behind the controller, or None on hardware."""
    arm = _ctl().arm
    return arm if getattr(arm, "has_task", False) else None


@tool
def get_telemetry() -> dict:
    """Current joint angles (deg), gripper (% open), and sensed load / current /
    temperature / voltage where the backend supports it."""
    return _public(_ctl().telemetry())


@tool
def get_limits() -> dict:
    """The safety limits every command is checked against."""
    return _ctl().limits


@tool
def move_joints(
    targets: dict[str, float], duration_s: float = 1.0, same_direction: bool = True
) -> dict:
    """Move some or all joints to target angles in degrees over duration_s seconds.

    Joint names: shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll.
    Joints left out hold position. Refused moves return {"ok": false, "refused": [...]}.
    same_direction (default on) finishes every joint from its configured side to
    cancel gear backlash; turn it off only for experiments that need it off.
    """
    return _public(_ctl().move(targets, duration_s, same_direction, tool="move_joints"))


@tool
def travel_to(targets: dict[str, float], deg_per_s: float = 30.0) -> dict:
    """Move any distance to target joint angles (deg), automatically split into legs
    that each respect the step limit. Use this for big moves; move_joints for small ones."""
    return _public(_ctl().travel(targets, deg_per_s, tool="travel_to"))


@tool
def set_gripper(percent_open: float, duration_s: float = 0.5) -> dict:
    """Open (100) or close (0) the gripper. Watch load/current to detect a grasp.

    Simulator task scene only: grasp physics is NOT simulated. Commanding below 20 %
    open while the cube centre is within 15 mm of the gripper site attaches the cube
    to the gripper; commanding 20 % or more releases it. The result's grasp_event
    says which happened.
    """
    return _public(_ctl().gripper(percent_open, duration_s))


@tool
def home(duration_s: float = 3.0) -> dict:
    """Return to the home pose defined in config/limits.json."""
    return _public(_ctl().home(duration_s))


@tool
def get_scene() -> dict:
    """Object poses as numbers in the arm base frame (mm, degrees), no images.

    cube: centre xyz_mm, rpy_deg (yaw about z), speed, size (20 mm), off_table.
    slot: centre_xyz_mm = where the cube centre sits when seated in the 22 mm pocket
      (pocket yaw 0: its walls are parallel to the x and y axes); above the pocket a
      funnel widens to funnel_half_width_mm at funnel_top_z_mm, so a cube released
      above the funnel with its centre within ~8 mm of the slot centre slides in.
    gripper: site_xyz_mm = gripperframe site (on the inner face of the fixed jaw),
      approach_axis = direction the fingers point, jaw_axis = direction the jaws
      close across (a held object is centred ~10 mm along it from the site),
      percent_open.
    """
    sim = _sim()
    if sim is None:
        return {"error": "no scene objects on this backend"}
    return sim.scene()


@tool
def is_cube_in_slot() -> dict:
    """The task verifier: true only when the cube centre is within 3 mm of the slot
    centre, moving slower than 5 mm/s, and released by the gripper. This decides
    success; nothing else does."""
    sim = _sim()
    if sim is None:
        return {"error": "no verifier on this backend"}
    return sim.cube_in_slot()


@tool
def move_gripper_to(
    x_mm: float, y_mm: float, z_mm: float, pitch_deg: float = -90.0,
    roll_deg: float | None = None, deg_per_s: float = 30.0,
) -> dict:
    """Move the tool centre point (TCP, the point midway between the jaws, ~11 mm
    from the gripper site along jaw_axis) to x, y, z in the arm base frame (mm).

    pitch_deg is the angle of the fingers above horizontal: 0 = fingers horizontal,
    -90 = fingers pointing straight down (top-down grasp). roll_deg sets the
    wrist_roll joint (rotates the jaws about the finger axis; default: unchanged).
    Plans with inverse kinematics, checks the pose against config/limits.json
    (gripper site must stay >= 10 mm above the table, reach <= 450 mm), then travels
    there in joint space. Unreachable or unsafe targets are refused with a reason and
    nothing moves. Returns the pose reached (tcp) and the joint angles.
    """
    ctl = _ctl()
    current = ctl.positions()
    seed = dict(current)
    if roll_deg is not None:
        seed["wrist_roll"] = roll_deg
    try:
        joints = _ik().solve([x_mm / 1000, y_mm / 1000, z_mm / 1000], pitch_deg, seed_deg=seed)
    except Unreachable as e:
        log_event("refused", tool="move_gripper_to", target_mm=[x_mm, y_mm, z_mm],
                  pitch_deg=pitch_deg, problems=[str(e)])
        return {"ok": False, "refused": [str(e)]}
    if roll_deg is not None:
        joints["wrist_roll"] = float(roll_deg)
    _, _, problems = ctl.check(joints, 1.0, same_direction=True, from_pose=joints)
    if problems:
        log_event("refused", tool="move_gripper_to", target_mm=[x_mm, y_mm, z_mm],
                  pitch_deg=pitch_deg, joints=joints, problems=problems)
        return {"ok": False, "refused": problems, "planned_joints_deg": joints}
    result = ctl.travel(joints, deg_per_s, tool="move_gripper_to",
                        target_mm=[x_mm, y_mm, z_mm], pitch_deg=pitch_deg)
    out = _public(result)
    out["tcp"] = _ik().tcp_pose(ctl.positions())
    out["planned_joints_deg"] = {k: round(v, 2) for k, v in joints.items()}
    return out


@tool
def stop() -> dict:
    """Hold position immediately."""
    return _ctl().stop()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
