"""Real SO-101 follower through LeRobot.

UNTESTED: written before the arm arrived. When it does, verify against the installed
LeRobot version:
  - the import path and config fields of SO101Follower / SO101FollowerConfig
  - that use_degrees=True gives degrees with 0 at mid-range (matching the sim model)
  - the Feetech register names used for telemetry ("Present_Current", ...)
  - the units of Present_Current (raw counts vs mA) before trusting max_current_ma
"""

from __future__ import annotations

import time

from swayam import GRIPPER, JOINTS

CONTROL_HZ = 30
ALL = (*JOINTS, GRIPPER)
TELEMETRY_REGISTERS = {
    "load": "Present_Load",
    "current_ma": "Present_Current",
    "temperature_c": "Present_Temperature",
    "voltage_v": "Present_Voltage",
}


class RealArm:
    def __init__(self, port: str, robot_id: str, max_current_ma: float = 800):
        from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig

        self.robot = SO101Follower(
            SO101FollowerConfig(port=port, id=robot_id, use_degrees=True)
        )
        self.robot.connect()
        self.max_current_ma = max_current_ma

    def positions(self) -> dict[str, float]:
        obs = self.robot.get_observation()
        return {n: float(obs[f"{n}.pos"]) for n in ALL}

    def _read(self, register: str) -> dict | None:
        try:
            return {k: float(v) for k, v in self.robot.bus.sync_read(register).items()}
        except Exception:  # register missing in this LeRobot version
            return None

    def telemetry(self) -> dict:
        tel = {"backend": "real", "t": time.time(), "positions": self.positions()}
        for key, register in TELEMETRY_REGISTERS.items():
            tel[key] = self._read(register)
        return tel

    def move(self, targets: dict[str, float], duration_s: float) -> dict:
        start = self.positions()
        goal = {**start, **targets}
        ticks = max(1, int(duration_s * CONTROL_HZ))
        aborted = None
        for k in range(1, ticks + 1):
            a = k / ticks
            self.robot.send_action(
                {f"{n}.pos": start[n] + (goal[n] - start[n]) * a for n in ALL}
            )
            time.sleep(1.0 / CONTROL_HZ)
            current = self._read("Present_Current")
            if current and max(abs(v) for v in current.values()) > self.max_current_ma:
                aborted = f"current above {self.max_current_ma} mA (jidoka stop)"
                self.stop()
                break
        tel = self.telemetry()
        tel["aborted"] = aborted
        tel["target"] = goal
        tel["max_error_deg"] = max(abs(tel["positions"][n] - goal[n]) for n in JOINTS)
        return tel

    def stop(self) -> None:
        here = self.positions()
        self.robot.send_action({f"{n}.pos": v for n, v in here.items()})
