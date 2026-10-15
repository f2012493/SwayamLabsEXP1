"""Real SO-101 follower through LeRobot.

Checked against LeRobot 0.6.1 SOURCE on 2026-10-15 (no hardware yet):
  - class SO101Follower / SO101FollowerConfig live in lerobot.robots.so_follower
  - use_degrees=True (the default) returns degrees with 0 at the MIDPOINT of the
    calibrated range of each joint, not at the sim model's zero. Phase 0 must
    measure the offset between the two conventions before trusting any pose.
  - observation keys are "<motor>.pos"; actions take the same keys
  - Present_Load / Present_Current / Present_Temperature / Present_Voltage exist in
    the STS3215 table. Only Position-type registers are normalised; the others come
    back as RAW register values. Present_Current units are UNVERIFIED (assumed
    6.5 mA per count, like Protection_Current); check with a bench supply.
  - connect(calibrate=True) can call input() for calibration. This backend runs
    inside an MCP server whose stdin is the protocol, so we connect with
    calibrate=False and require an existing calibration file (lerobot-calibrate).
  - max_relative_target clamps each commanded step inside LeRobot itself: a third
    safety layer after our hook and the server's checks.

Still untested on hardware: everything below. Verify on day one (docs/DAY_ONE.md).
"""

from __future__ import annotations

import time

from swayam import GRIPPER, JOINTS

CONTROL_HZ = 30
ALL = (*JOINTS, GRIPPER)
RAW_REGISTERS = ("Present_Load", "Present_Current", "Present_Temperature", "Present_Voltage")


class RealArm:
    def __init__(
        self,
        port: str,
        robot_id: str,
        max_current_ma: float = 800,
        current_ma_per_count: float = 6.5,
        max_relative_target_deg: float = 45,
    ):
        from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

        self.robot = SO101Follower(
            SO101FollowerConfig(
                port=port,
                id=robot_id,
                use_degrees=True,
                # LeRobot type-checks this with isinstance(x, float): an int raises
                max_relative_target=float(max_relative_target_deg),
            )
        )
        self.robot.connect(calibrate=False)
        if not self.robot.is_calibrated:
            self.robot.disconnect()
            raise RuntimeError(
                f"No valid calibration for robot id '{robot_id}'. Run "
                f"`uv run lerobot-calibrate --robot.type=so101_follower --robot.port={port} "
                f"--robot.id={robot_id}` in a terminal first."
            )
        self.max_current_ma = max_current_ma
        self.current_ma_per_count = current_ma_per_count

    def positions(self) -> dict[str, float]:
        obs = self.robot.get_observation()
        return {n: float(obs[f"{n}.pos"]) for n in ALL}

    def _read_raw(self, register: str) -> dict[str, float] | None:
        try:
            return {k: float(v) for k, v in self.robot.bus.sync_read(register, normalize=False).items()}
        except Exception:  # register unsupported on this firmware
            return None

    def telemetry(self) -> dict:
        tel = {"backend": "real", "t": time.time(), "positions": self.positions()}
        raw = {r: self._read_raw(r) for r in RAW_REGISTERS}
        tel["raw"] = raw
        cur = raw["Present_Current"]
        tel["current_ma"] = (
            {k: v * self.current_ma_per_count for k, v in cur.items()} if cur else None
        )
        tel["temperature_c"] = raw["Present_Temperature"]  # STS: 1 count = 1 C
        volt = raw["Present_Voltage"]
        tel["voltage_v"] = {k: v / 10 for k, v in volt.items()} if volt else None  # 0.1 V/count
        tel["load"] = raw["Present_Load"]
        return tel

    def move(self, targets: dict[str, float], duration_s: float) -> dict:
        start = self.positions()
        goal = {**start, **targets}
        ticks = max(1, int(duration_s * CONTROL_HZ))
        aborted = None
        for k in range(1, ticks + 1):
            a = k / ticks
            self.robot.send_action({f"{n}.pos": start[n] + (goal[n] - start[n]) * a for n in ALL})
            time.sleep(1.0 / CONTROL_HZ)
            cur = self._read_raw("Present_Current")
            if cur and max(cur.values()) * self.current_ma_per_count > self.max_current_ma:
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

    def close(self) -> None:
        self.robot.disconnect()
