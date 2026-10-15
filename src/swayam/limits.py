"""Safety limits for every arm command.

The arm server calls `check_move` before executing anything. The same limits file
is read by an independent Claude Code hook (.claude/hooks/check_arm_command.py), so
a bug here does not silently disable the absolute-range checks.
"""

from __future__ import annotations

import json
from pathlib import Path

from swayam import GRIPPER, JOINTS, REPO_ROOT

DEFAULT_LIMITS_PATH = REPO_ROOT / "config" / "limits.json"


def load_limits(path: Path | None = None) -> dict:
    return json.loads(Path(path or DEFAULT_LIMITS_PATH).read_text())


def check_move(
    targets: dict[str, float],
    duration_s: float,
    current: dict[str, float] | None,
    limits: dict,
) -> list[str]:
    """Return a list of violations. An empty list means the move is allowed.

    `targets` maps joint names (and optionally "gripper") to degrees / percent.
    `current` is the present position in the same units, used for step and speed checks.
    """
    problems: list[str] = []
    known = set(JOINTS) | {GRIPPER}

    for name in targets:
        if name not in known:
            problems.append(f"unknown joint '{name}'")

    if not limits["min_duration_s"] <= duration_s <= limits["max_duration_s"]:
        problems.append(
            f"duration {duration_s}s outside "
            f"[{limits['min_duration_s']}, {limits['max_duration_s']}]s"
        )

    for name, value in targets.items():
        if name not in known:
            continue
        rng = limits["gripper"] if name == GRIPPER else limits["joints"][name]
        if not rng["min"] <= value <= rng["max"]:
            problems.append(f"{name}={value} outside [{rng['min']}, {rng['max']}]")

        if current is not None and name != GRIPPER and name in current:
            step = abs(value - current[name])
            if step > limits["max_step_deg"]:
                problems.append(
                    f"{name} step {step:.1f}deg exceeds max_step_deg {limits['max_step_deg']}"
                )
            if duration_s > 0 and step / duration_s > limits["max_speed_deg_s"]:
                problems.append(
                    f"{name} speed {step / duration_s:.0f}deg/s exceeds "
                    f"max_speed_deg_s {limits['max_speed_deg_s']}"
                )
    return problems


def check_gripper_pose(xyz: tuple[float, float, float], limits: dict) -> list[str]:
    """Workspace check on the gripper position (metres, arm base frame)."""
    x, y, z = xyz
    problems = []
    if z < limits["min_gripper_height_m"]:
        problems.append(
            f"gripper height {z:.3f}m below min_gripper_height_m {limits['min_gripper_height_m']}"
        )
    reach = (x * x + y * y) ** 0.5
    if reach > limits["max_reach_m"]:
        problems.append(f"gripper reach {reach:.3f}m exceeds max_reach_m {limits['max_reach_m']}")
    return problems
