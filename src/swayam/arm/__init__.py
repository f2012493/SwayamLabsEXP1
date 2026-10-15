"""Arm backends. Both expose the same interface so code written against the
simulator runs unchanged on the real SO-101."""

from __future__ import annotations

import os
from typing import Protocol


class Arm(Protocol):
    def telemetry(self) -> dict:
        """Joint positions (deg), gripper (%), and whatever the backend can sense:
        load, current (mA), temperature (C), voltage (V)."""

    def positions(self) -> dict[str, float]:
        """Joint positions in degrees plus gripper percent."""

    def move(self, targets: dict[str, float], duration_s: float) -> dict:
        """Move linearly to `targets` over `duration_s`. Returns final telemetry and
        an `aborted` reason if the move was stopped early."""

    def stop(self) -> None:
        """Hold the current position (torque on, no motion)."""


def make_arm(backend: str | None = None) -> Arm:
    backend = backend or os.environ.get("SWAYAM_BACKEND", "sim")
    if backend == "sim":
        from swayam.arm.sim import SimArm

        return SimArm()
    if backend == "real":
        from swayam.arm.real import RealArm
        from swayam.limits import load_limits

        return RealArm(
            port=os.environ["SWAYAM_PORT"],
            robot_id=os.environ.get("SWAYAM_ROBOT_ID", "swayam_follower"),
            max_current_ma=load_limits()["max_current_ma"],
        )
    raise ValueError(f"unknown SWAYAM_BACKEND '{backend}' (use 'sim' or 'real')")
