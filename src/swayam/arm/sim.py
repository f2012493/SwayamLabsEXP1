"""Simulated SO-101 using TheRobotStudio's official MuJoCo model.

Scenes (swayam.kinematics.SCENES): "plain" (default) or "task" (cube on a bed plus a
kit-tray slot, sim/so101/scene_task.xml). Select with SimArm(scene="task") or
SWAYAM_SCENE=task. The cube spawn is seeded (SWAYAM_CUBE_SEED or cube_seed=).

SIMPLIFIED GRASP - NOT A PHYSICS MEASUREMENT
MuJoCo two-finger mesh contacts are unreliable and grasp physics is not what the
task scene measures. So in the task scene, when the gripper is commanded below
GRASP_CLOSE_PCT and the cube centre is within GRASP_RADIUS_M of the gripperframe
site, the cube is welded to the gripper body (equality "grasp") and cube-arm contacts
are switched off; an open command releases it. Grasp success on hardware is a
separate Phase 0 measurement.
"""

from __future__ import annotations

import math
import os
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

# task scene constants (mm unless stated; must match sim/so101/scene_task.xml)
GRASP_CLOSE_PCT = 20.0
GRASP_RADIUS_M = 0.015
SLOT_TOL_M = 0.003  # verifier: cube centre within 3 mm of the slot centre
SLOT_REST_SPEED_M_S = 0.005  # ... and moving slower than 5 mm/s
CUBE_SIZE_MM = 20.0
BED_CENTRE_M = (0.200, 0.090)
BED_HALF_M = 0.040
SPAWN_HALF_M = 0.025  # cube centre spawns within +-25 mm of the bed centre
SPAWN_YAW_DEG = 20.0  # ... with a yaw within +-20 deg
CUBE_HELD_CONTYPE = 2  # collides with table/tray (7) but not the arm (1) while held
CUBE_FREE_CONTYPE = 3  # also collides with arm links (1), never with the gripper hulls (4)
GRIPPER_HULL_CONTYPE = 4  # see scene_task.xml: jaw mesh hulls are too fat to touch the cube
OFF_TABLE_Z_M = -0.05


class SimArm:
    def __init__(self, scene: str | None = None, cube_seed: int | None = None):
        self.scene_name = scene or os.environ.get("SWAYAM_SCENE", "plain")
        self.model = load_model(self.scene_name)
        self.data = mujoco.MjData(self.model)
        self._qadr = {n: self.model.jnt_qposadr[self.model.joint(n).id] for n in ALL}
        self._act = {n: self.model.actuator(n).id for n in ALL}
        self._site = self.model.site(GRIPPER_SITE).id
        self._floor = self.model.geom("floor").id
        base = self.model.body("base").id
        # geoms on the arm itself; a part resting on the table must not count as a crash
        self._arm_geoms = {
            g for g in range(self.model.ngeom) if self.model.body_rootid[self.model.geom_bodyid[g]] == base
        }
        self.has_task = self.scene_name == "task"
        self.held = False
        self._gripper_body = self.model.body("gripper").id
        if self.has_task:
            self._cube_body = self.model.body("cube").id
            self._cube_geom = self.model.geom("cube").id
            self._cube_q = self.model.jnt_qposadr[self.model.joint("cube").id]
            self._cube_v = self.model.jnt_dofadr[self.model.joint("cube").id]
            self._slot_site = self.model.site("slot_centre").id
            self._weld = self.model.equality("grasp").id
            for g in range(self.model.ngeom):
                if self.model.geom_bodyid[g] in (self._gripper_body, self.model.body("moving_jaw_so101_v1").id) \
                        and self.model.geom_contype[g]:
                    self.model.geom_contype[g] = GRIPPER_HULL_CONTYPE
                    self.model.geom_conaffinity[g] = GRIPPER_HULL_CONTYPE
            if cube_seed is None:
                cube_seed = int(os.environ.get("SWAYAM_CUBE_SEED", "0"))
            self.cube_seed = cube_seed
        mujoco.mj_forward(self.model, self.data)
        if self.has_task:
            self.reset_cube(cube_seed)
        self._settle(0.5)

    # ---- basics ------------------------------------------------------------------
    def _to_ctrl(self, name: str, value: float) -> float:
        if name == GRIPPER:
            return gripper_percent_to_rad(self.model, value)
        return math.radians(value)

    def positions(self) -> dict[str, float]:
        out = {n: math.degrees(self.data.qpos[self._qadr[n]]) for n in JOINTS}
        out[GRIPPER] = gripper_rad_to_percent(self.model, self.data.qpos[self._qadr[GRIPPER]])
        return out

    def _floor_contacts(self) -> int:
        """Contacts between the table top and any arm link."""
        n = 0
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            if self._floor in (c.geom1, c.geom2):
                other = c.geom2 if c.geom1 == self._floor else c.geom1
                if other in self._arm_geoms:
                    n += 1
        return n

    def telemetry(self) -> dict:
        tel = {
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
        if self.has_task:
            tel["scene"] = self.scene()
        return tel

    def _settle(self, seconds: float) -> None:
        for _ in range(int(seconds / self.model.opt.timestep)):
            mujoco.mj_step(self.model, self.data)

    def move(self, targets: dict[str, float], duration_s: float) -> dict:
        start = self.positions()
        goal = {**start, **targets}
        grasp_event = None
        if self.has_task and GRIPPER in targets:
            grasp_event = self._grasp_logic(targets[GRIPPER])
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
        if grasp_event == "released":
            self._set_cube_contacts(CUBE_FREE_CONTYPE)  # jaws are open again: re-enable
        tel = self.telemetry()
        tel["aborted"] = aborted
        tel["target"] = goal
        tel["max_error_deg"] = float(
            np.max([abs(tel["positions"][n] - goal[n]) for n in JOINTS])
        )
        if grasp_event:
            tel["grasp_event"] = grasp_event
        return tel

    def stop(self) -> None:
        for n in ALL:
            self.data.ctrl[self._act[n]] = self.data.qpos[self._qadr[n]]

    # ---- task scene ----------------------------------------------------------------
    def reset_cube(self, seed: int | None = None) -> dict:
        """Put the cube on the bed at a seeded position/yaw and let it settle."""
        if seed is not None:
            self.cube_seed = int(seed)
        if self.held:
            self._release()
            self._set_cube_contacts(CUBE_FREE_CONTYPE)
        rng = np.random.default_rng(self.cube_seed)
        x = BED_CENTRE_M[0] + rng.uniform(-SPAWN_HALF_M, SPAWN_HALF_M)
        y = BED_CENTRE_M[1] + rng.uniform(-SPAWN_HALF_M, SPAWN_HALF_M)
        yaw = math.radians(rng.uniform(-SPAWN_YAW_DEG, SPAWN_YAW_DEG))
        q = self._cube_q
        self.data.qpos[q:q + 3] = [x, y, CUBE_SIZE_MM / 2000 + 0.0001]
        self.data.qpos[q + 3:q + 7] = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
        self.data.qvel[self._cube_v:self._cube_v + 6] = 0
        mujoco.mj_forward(self.model, self.data)
        self._settle(0.5)
        return self.scene()["cube"]

    def _cube_pose(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        pos = self.data.xpos[self._cube_body].copy()
        w, x, y, z = self.data.xquat[self._cube_body]
        roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
        pitch = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
        yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
        vel = self.data.qvel[self._cube_v:self._cube_v + 6].copy()
        return pos, np.degrees([roll, pitch, yaw]), vel

    def scene(self) -> dict:
        """Object poses as numbers in the arm base frame (mm, deg)."""
        pos, rpy, vel = self._cube_pose()
        site = self.data.site_xpos[self._site]
        R = self.data.site_xmat[self._site].reshape(3, 3)
        approach = R[:, 0]
        slot = self.data.site_xpos[self._slot_site]
        return {
            "cube": {
                "xyz_mm": [round(float(v) * 1000, 2) for v in pos],
                "rpy_deg": [round(float(v), 2) for v in rpy],
                "speed_mm_s": round(float(np.linalg.norm(vel[:3])) * 1000, 2),
                "size_mm": CUBE_SIZE_MM,
                "off_table": bool(pos[2] < OFF_TABLE_Z_M),
                "held_by_gripper": self.held,
                "distance_to_gripper_site_mm": round(float(np.linalg.norm(pos - site)) * 1000, 2),
            },
            "slot": {
                "centre_xyz_mm": [round(float(v) * 1000, 2) for v in slot],
                "pocket_mm": 22.0,
                "pocket_depth_mm": 10.0,
                "pocket_yaw_deg": 0.0,
                "funnel_top_z_mm": 21.5,
                "funnel_half_width_mm": 20.5,
            },
            "bed": {"centre_xy_mm": [v * 1000 for v in BED_CENTRE_M], "half_size_mm": BED_HALF_M * 1000},
            "gripper": {
                "site_xyz_mm": [round(float(v) * 1000, 2) for v in site],
                "approach_axis": [round(float(v), 3) for v in approach],
                "jaw_axis": [round(float(v), 3) for v in R[:, 2]],
                "percent_open": round(self.positions()[GRIPPER], 1),
            },
        }

    def cube_in_slot(self) -> dict:
        """The verifier. True only if the cube centre is within SLOT_TOL_M of the slot
        centre, moving slower than SLOT_REST_SPEED_M_S, and not held."""
        pos, _, vel = self._cube_pose()
        slot = self.data.site_xpos[self._slot_site]
        dist = float(np.linalg.norm(pos - slot))
        speed = float(np.linalg.norm(vel[:3]))
        ok = dist <= SLOT_TOL_M and speed <= SLOT_REST_SPEED_M_S and not self.held
        return {
            "in_slot": ok,
            "distance_mm": round(dist * 1000, 2),
            "tolerance_mm": SLOT_TOL_M * 1000,
            "speed_mm_s": round(speed * 1000, 2),
            "held_by_gripper": self.held,
        }

    def _set_cube_contacts(self, cls: int) -> None:
        self.model.geom_contype[self._cube_geom] = cls
        self.model.geom_conaffinity[self._cube_geom] = cls

    def _grasp_logic(self, gripper_target_pct: float) -> str | None:
        if gripper_target_pct < GRASP_CLOSE_PCT and not self.held:
            pos, _, _ = self._cube_pose()
            dist = float(np.linalg.norm(pos - self.data.site_xpos[self._site]))
            if dist <= GRASP_RADIUS_M:
                self._grasp()
                return "grasped"
            return f"close: cube {dist * 1000:.1f} mm from gripper site, no grasp (limit {GRASP_RADIUS_M * 1000:.0f} mm)"
        if gripper_target_pct >= GRASP_CLOSE_PCT and self.held:
            self._release()
            return "released"
        return None

    def _grasp(self) -> None:
        """Weld the cube to the gripper at its current relative pose."""
        g, c = self._gripper_body, self._cube_body
        Rg = self.data.xmat[g].reshape(3, 3)
        rel_pos = Rg.T @ (self.data.xpos[c] - self.data.xpos[g])
        neg = np.zeros(4)
        rel_quat = np.zeros(4)
        mujoco.mju_negQuat(neg, self.data.xquat[g])
        mujoco.mju_mulQuat(rel_quat, neg, self.data.xquat[c])
        data = np.zeros(mujoco.mjNEQDATA)
        data[3:6] = rel_pos
        data[6:10] = rel_quat
        data[10] = 1.0
        self.model.eq_data[self._weld] = data
        self.data.eq_active[self._weld] = 1
        self._set_cube_contacts(CUBE_HELD_CONTYPE)
        self.held = True

    def _release(self) -> None:
        self.data.eq_active[self._weld] = 0
        self.held = False
