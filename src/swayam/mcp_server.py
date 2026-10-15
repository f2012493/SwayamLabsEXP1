"""MCP server that lets Claude Code drive the SO-101 (simulated or real) safely.

Every command goes through swayam.controller.Controller, which checks it against
config/limits.json and logs it to runs/.
Backend: SWAYAM_BACKEND=sim (default) or real (also needs SWAYAM_PORT).
Task scene version: SWAYAM_TASK_VERSION=1 (default) or 2; the tool descriptions
below describe the active version (they are built when this module is imported).
Placement noise: SWAYAM_PLACE_NOISE_MM=<xy RMS in mm> adds a seeded Gaussian error to
every move_gripper_to target (0 = off, the default); see _placement_noise.
"""

from __future__ import annotations

import functools
import math
import os
import time

import numpy as np
from mcp.server.fastmcp import FastMCP

from swayam.arm.sim import (
    CUBE_SIZE_MM,
    FINGER_HALF_WIDTH_MM,
    FLAT_TOL_DEG,
    FUNNEL,
    JAW_PENETRATION_MM,
    PAD_X_MAX_MM,
    PAD_X_MIN_MM,
    task_version,
)
from swayam.controller import Controller
from swayam.ik import IK, Unreachable
from swayam.runlog import log_event

mcp = FastMCP("swayam-arm")
_state: dict = {}
TASK_VERSION = task_version()
PLACE_NOISE_MM = float(os.environ.get("SWAYAM_PLACE_NOISE_MM", "0") or 0)


def grasp_rule_text(version: int) -> str:
    """The simulator's grasp rule as the subject is told it (per task version)."""
    if version == 1:
        return ("Simulator task scene only: grasp physics is NOT simulated. Commanding below 20 % "
                "open while the cube centre is within 15 mm of the gripper site attaches the cube "
                "to the gripper; commanding 20 % or more releases it. The result's grasp_event "
                "says which happened.")
    return (f"Simulator task scene only: grasp physics is NOT simulated. Commanding below 20 % open "
            f"attaches the cube to the gripper only if, at that moment, all of: the jaws are closing "
            f"from a gap wider than the {CUBE_SIZE_MM:.0f} mm cube; the cube lies between the finger "
            f"pads (its centre within {JAW_PENETRATION_MM:.0f} mm of the gap along jaw_axis, within "
            f"+-{FINGER_HALF_WIDTH_MM:.0f} mm of the pad centreline, and between {PAD_X_MIN_MM:.0f} and "
            f"{PAD_X_MAX_MM:.0f} mm along approach_axis from the gripper site); and the cube is within "
            f"{FLAT_TOL_DEG:.0f} deg of flat. Otherwise nothing is grasped and the result's grasp_event "
            f"says why. Commanding 20 % or more releases a held cube.")


def funnel_text(version: int) -> str:
    f = FUNNEL[version]
    return (f"above the pocket a 1.5 mm lead-in and a {f['outer_funnel_mm']:.0f} mm funnel widen to "
            f"funnel_half_width_mm ({f['funnel_half_width_mm']} mm) at funnel_top_z_mm "
            f"({f['funnel_top_z_mm']} mm), so a flat cube released above the funnel with its centre "
            f"within ~{f['outer_funnel_mm'] + 1.5:.0f} mm of the slot centre and its yaw near the "
            f"pocket's slides in")


def noise_text(rms_mm: float) -> str:
    if not rms_mm:
        return ""
    return (f" This server adds a seeded random xy error of {rms_mm:.1f} mm RMS to every target "
            f"(standing in for camera-guided placement error); the returned tcp is the pose actually "
            f"reached, so read it back when precision matters.")


def _placement_noise() -> list[float] | None:
    """Seeded N(0, sigma) xy error in metres per move_gripper_to call, or None when off.
    sigma per axis = RMS / sqrt(2) so the radial RMS equals SWAYAM_PLACE_NOISE_MM. The
    stream is seeded from the cube seed so a rerun of the same attempt sees the same errors."""
    if not PLACE_NOISE_MM:
        return None
    if "noise_rng" not in _state:
        seed = int(os.environ.get("SWAYAM_CUBE_SEED", "0"))
        _state["noise_rng"] = np.random.default_rng(10_000 + seed)
    sigma = PLACE_NOISE_MM / 1000 / math.sqrt(2)
    return [float(v) for v in _state["noise_rng"].normal(0.0, sigma, size=2)]


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


def set_gripper(percent_open: float, duration_s: float = 0.5) -> dict:
    return _public(_ctl().gripper(percent_open, duration_s))


set_gripper.__doc__ = f"""Open (100) or close (0) the gripper. Watch load/current to detect a grasp.

    {grasp_rule_text(TASK_VERSION)}
    """
set_gripper = tool(set_gripper)


@tool
def home(duration_s: float = 3.0) -> dict:
    """Return to the home pose defined in config/limits.json."""
    return _public(_ctl().home(duration_s))


def get_scene() -> dict:
    sim = _sim()
    if sim is None:
        return {"error": "no scene objects on this backend"}
    return sim.scene()


get_scene.__doc__ = f"""Object poses as numbers in the arm base frame (mm, degrees), no images.

    cube: centre xyz_mm, rpy_deg (yaw about z), speed, size (20 mm), off_table.
    slot: centre_xyz_mm = where the cube centre sits when seated in the 22 mm pocket
      (pocket yaw 0: its walls are parallel to the x and y axes); {funnel_text(TASK_VERSION)}.
    gripper: site_xyz_mm = gripperframe site (on the inner face of the fixed jaw),
      approach_axis = direction the fingers point, jaw_axis = direction the jaws
      close across (a held object is centred ~10 mm along it from the site),
      percent_open.
    """
get_scene = tool(get_scene)


@tool
def is_cube_in_slot() -> dict:
    """The task verifier: true only when the cube centre is within 3 mm of the slot
    centre, moving slower than 5 mm/s, released by the gripper, within 5 deg of flat
    (one face normal within 5 deg of vertical) and at the seated height (centre within
    1 mm of the slot centre z). A cube jammed tilted in the pocket mouth fails. This
    decides success; nothing else does."""
    sim = _sim()
    if sim is None:
        return {"error": "no verifier on this backend"}
    return sim.cube_in_slot()


def move_gripper_to(
    x_mm: float, y_mm: float, z_mm: float, pitch_deg: float = -90.0,
    roll_deg: float | None = None, deg_per_s: float = 30.0,
) -> dict:
    ctl = _ctl()
    current = ctl.positions()
    seed = dict(current)
    if roll_deg is not None:
        seed["wrist_roll"] = roll_deg
    noise = _placement_noise()
    target = [x_mm / 1000, y_mm / 1000, z_mm / 1000]
    if noise:
        target = [target[0] + noise[0], target[1] + noise[1], target[2]]
    noise_mm = [round(v * 1000, 3) for v in noise] if noise else None
    try:
        joints = _ik().solve(target, pitch_deg, seed_deg=seed)
    except Unreachable as e:
        log_event("refused", tool="move_gripper_to", target_mm=[x_mm, y_mm, z_mm],
                  pitch_deg=pitch_deg, problems=[str(e)], placement_noise_mm=noise_mm)
        return {"ok": False, "refused": [str(e)]}
    if roll_deg is not None:
        joints["wrist_roll"] = float(roll_deg)
    _, _, problems = ctl.check(joints, 1.0, same_direction=True, from_pose=joints)
    if problems:
        log_event("refused", tool="move_gripper_to", target_mm=[x_mm, y_mm, z_mm],
                  pitch_deg=pitch_deg, joints=joints, problems=problems, placement_noise_mm=noise_mm)
        return {"ok": False, "refused": problems, "planned_joints_deg": joints}
    result = ctl.travel(joints, deg_per_s, tool="move_gripper_to",
                        target_mm=[x_mm, y_mm, z_mm], pitch_deg=pitch_deg,
                        placement_noise_mm=noise_mm)
    out = _public(result)
    out["tcp"] = _ik().tcp_pose(ctl.positions())
    out["planned_joints_deg"] = {k: round(v, 2) for k, v in joints.items()}
    return out


move_gripper_to.__doc__ = f"""Move the tool centre point (TCP, the point midway between the jaws, ~11 mm
    from the gripper site along jaw_axis) to x, y, z in the arm base frame (mm).

    pitch_deg is the angle of the fingers above horizontal: 0 = fingers horizontal,
    -90 = fingers pointing straight down (top-down grasp). roll_deg sets the
    wrist_roll joint (rotates the jaws about the finger axis; default: unchanged).
    Plans with inverse kinematics, checks the pose against config/limits.json
    (gripper site must stay >= 10 mm above the table, reach <= 450 mm), then travels
    there in joint space. Unreachable or unsafe targets are refused with a reason and
    nothing moves. Returns the pose reached (tcp) and the joint angles.{noise_text(PLACE_NOISE_MM)}
    """
move_gripper_to = tool(move_gripper_to)


@tool
def stop() -> dict:
    """Hold position immediately."""
    return _ctl().stop()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
