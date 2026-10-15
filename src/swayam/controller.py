"""Guarded arm controller shared by the MCP server and experiment scripts.

Every move passes the same checks (joint ranges, step, speed, duration, predicted
gripper height and reach) and is logged to runs/, whichever path it came from.
"""

from __future__ import annotations

from swayam import GRIPPER, JOINTS
from swayam.arm import Arm, make_arm
from swayam.kinematics import Kinematics
from swayam.limits import check_gripper_pose, check_move, load_limits
from swayam.motion import approach_waypoints
from swayam.runlog import log_event


class Controller:
    def __init__(self, backend: str | None = None, limits: dict | None = None):
        self.limits = limits or load_limits()
        self.arm: Arm = make_arm(backend)
        self.kin = Kinematics()

    def telemetry(self) -> dict:
        return self.arm.telemetry()

    def positions(self) -> dict[str, float]:
        return self.arm.positions()

    def check(
        self, targets: dict[str, float], duration_s: float, same_direction: bool,
        from_pose: dict[str, float] | None = None,
    ) -> tuple[list[dict], list[float], list[str]]:
        """Plan waypoints and return (waypoints, durations, problems) without moving.
        `from_pose` defaults to where the arm is now."""
        current = from_pose if from_pose is not None else self.arm.positions()
        waypoints = approach_waypoints(current, targets, self.limits) if same_direction else [targets]
        # The final approach is short; give it the minimum safe duration.
        durations = [duration_s] + [max(self.limits["min_duration_s"], 0.5)] * (len(waypoints) - 1)
        problems: list[str] = []
        here = current
        for wp, dur in zip(waypoints, durations):
            problems += check_move(wp, dur, here, self.limits)
            here = {**here, **wp}
            problems += check_gripper_pose(self.kin.gripper_xyz(here), self.limits)
        return waypoints, durations, problems

    def move(
        self, targets: dict[str, float], duration_s: float = 1.0,
        same_direction: bool = True, tool: str = "move", **extra,
    ) -> dict:
        waypoints, durations, problems = self.check(targets, duration_s, same_direction)
        if problems:
            log_event("refused", tool=tool, targets=targets, duration_s=duration_s,
                      problems=problems, **extra)
            return {"ok": False, "refused": problems}
        for wp, dur in zip(waypoints, durations):
            result = self.arm.move(wp, dur)
            if result.get("aborted"):
                break
        log_event("move", tool=tool, targets=targets, duration_s=duration_s,
                  waypoints=waypoints, result=result, **extra)
        return {"ok": result.get("aborted") is None, "waypoints": len(waypoints), **result}

    def travel(
        self, targets: dict[str, float], deg_per_s: float = 30.0,
        same_direction: bool = True, tool: str = "travel", **extra,
    ) -> dict:
        """Move any distance by splitting into legs that each respect max_step_deg.
        Only the final leg uses the same-direction approach."""
        current = self.arm.positions()
        goal = {**current, **targets}
        biggest = max(abs(goal[j] - current[j]) for j in JOINTS)
        legs = max(1, int(biggest // (0.8 * self.limits["max_step_deg"])) + 1)
        result: dict = {"ok": True}
        for k in range(1, legs + 1):
            a = k / legs
            wp = {j: current[j] + (goal[j] - current[j]) * a for j in JOINTS}
            dur = max(self.limits["min_duration_s"], (biggest / legs) / deg_per_s)
            result = self.move(wp, dur, same_direction and k == legs, tool=tool,
                               travel_leg=f"{k}/{legs}", **extra)
            if not result["ok"]:
                return result
        return result

    def gripper(self, percent_open: float, duration_s: float = 0.5) -> dict:
        return self.move({GRIPPER: percent_open}, duration_s, same_direction=False, tool="set_gripper")

    def home(self, duration_s: float = 3.0) -> dict:
        pose = {n: v for n, v in self.limits["home"].items() if n in JOINTS}
        result = self.travel(pose, tool="home")
        if result["ok"]:
            result = self.gripper(self.limits["home"][GRIPPER])
        return result

    def stop(self) -> dict:
        self.arm.stop()
        log_event("stop")
        return {"ok": True}
