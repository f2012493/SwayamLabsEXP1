"""Simulated SO-101 using TheRobotStudio's official MuJoCo model."""

from __future__ import annotations

import math
import time

import mujoco
import numpy as np

from swayam import GRIPPER, JOINTS
from swayam.kinematics import (
    GRIPPER_SITE,
    gripper_percent_to_rad,
    gripper_rad_to_percent,
    load_model,
)

CONTROL_HZ = 50
ALL = (*JOINTS, GRIPPER)


class SimArm:
    def __init__(self):
        self.model = load_model()
        self.data = mujoco.MjData(self.model)
        self._qadr = {n: self.model.jnt_qposadr[self.model.joint(n).id] for n in ALL}
        self._act = {n: self.model.actuator(n).id for n in ALL}
        self._site = self.model.site(GRIPPER_SITE).id
        self._floor = self.model.geom("floor").id
        mujoco.mj_forward(self.model, self.data)
        self._settle(0.5)

    def _to_ctrl(self, name: str, value: float) -> float:
        if name == GRIPPER:
            return gripper_percent_to_rad(self.model, value)
        return math.radians(value)

    def positions(self) -> dict[str, float]:
        out = {n: math.degrees(self.data.qpos[self._qadr[n]]) for n in JOINTS}
        out[GRIPPER] = gripper_rad_to_percent(self.model, self.data.qpos[self._qadr[GRIPPER]])
        return out

    def _floor_contacts(self) -> int:
        n = 0
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            if self._floor in (c.geom1, c.geom2):
                n += 1
        return n

    def telemetry(self) -> dict:
        return {
            "backend": "sim",
            "t": time.time(),
            "positions": self.positions(),
            "load": {n: float(self.data.actuator_force[self._act[n]]) for n in ALL},
            "current_ma": None,
            "temperature_c": None,
            "voltage_v": None,
            "gripper_xyz_m": [float(v) for v in self.data.site_xpos[self._site]],
            "floor_contacts": self._floor_contacts(),
        }

    def _settle(self, seconds: float) -> None:
        for _ in range(int(seconds / self.model.opt.timestep)):
            mujoco.mj_step(self.model, self.data)

    def move(self, targets: dict[str, float], duration_s: float) -> dict:
        start = self.positions()
        goal = {**start, **targets}
        ticks = max(1, int(duration_s * CONTROL_HZ))
        substeps = max(1, int(round(1.0 / CONTROL_HZ / self.model.opt.timestep)))
        aborted = None
        for k in range(1, ticks + 1):
            a = k / ticks
            for n in ALL:
                value = start[n] + (goal[n] - start[n]) * a
                self.data.ctrl[self._act[n]] = self._to_ctrl(n, value)
            for _ in range(substeps):
                mujoco.mj_step(self.model, self.data)
            if self._floor_contacts():
                aborted = "floor contact"
                self.stop()
                break
        if aborted is None:
            self._settle(0.3)
        tel = self.telemetry()
        tel["aborted"] = aborted
        tel["target"] = goal
        tel["max_error_deg"] = float(
            np.max([abs(tel["positions"][n] - goal[n]) for n in JOINTS])
        )
        return tel

    def stop(self) -> None:
        for n in ALL:
            self.data.ctrl[self._act[n]] = self.data.qpos[self._qadr[n]]
