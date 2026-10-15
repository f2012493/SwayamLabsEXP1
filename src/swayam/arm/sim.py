"""Simulated SO-101 using TheRobotStudio's official MuJoCo model.

Scenes (swayam.kinematics.SCENES): "plain" (default) or "task" (cube on a bed plus a
kit-tray slot, sim/so101/scene_task.xml). Select with SimArm(scene="task") or
SWAYAM_SCENE=task. The cube spawn is seeded (SWAYAM_CUBE_SEED or cube_seed=).

SIMPLIFIED GRASP - NOT A PHYSICS MEASUREMENT
MuJoCo two-finger mesh contacts are unreliable and grasp physics is not what the
task scene measures. So in the task scene a close command below GRASP_CLOSE_PCT
welds the cube to the gripper body (equality "grasp") and switches cube-arm contacts
off; an open command releases it. Grasp success on hardware is a separate Phase 0
measurement. Two versions of the rule exist (SWAYAM_TASK_VERSION, default 1):

  v1  the cube centre is within GRASP_RADIUS_M (15 mm) of the gripperframe site.
      Nothing else is checked: v1 grasped a wedged, 34 deg tilted cube with the jaws
      40 % open (studies/out/sim_pick_place_zero_shot.md).
  v2  all of, evaluated in the gripperframe site frame at the moment of the command
      (x = approach axis, y = across the finger pads, z = jaw axis from the fixed-jaw
      face towards the moving jaw):
        - the jaws are being closed from a gap wider than the part: the moving-jaw
          pad's lowest point is more than CUBE_SIZE_MM above the fixed-jaw face;
        - the cube body lies between the pads along the jaw axis (its centre is in
          [CUBE/2 - JAW_PENETRATION_MM, gap - CUBE/2 + JAW_PENETRATION_MM]);
        - the cube centre is over the pads: |y| <= FINGER_HALF_WIDTH_MM and
          PAD_X_MIN_MM <= x <= PAD_X_MAX_MM (finger root to fixed-jaw tip);
        - the cube is within FLAT_TOL_DEG of flat on the table (one face normal
          within 10 deg of vertical).
      Still a simplified grasp: no contact forces, no slip, no finger compliance; the
      jaw gap comes from the model's own moving-jaw mesh. Scene v2 also has a 4 mm
      outer funnel (sim/so101/scene_task_v2.xml) instead of 8 mm.
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
SLOT_TILT_TOL_DEG = 5.0  # ... and its most vertical face normal within 5 deg of vertical
SLOT_HEIGHT_TOL_M = 0.001  # ... and its centre within 1 mm of the slot centre height
CUBE_SIZE_MM = 20.0
BED_CENTRE_M = (0.200, 0.090)
BED_HALF_M = 0.040
SPAWN_HALF_M = 0.025  # cube centre spawns within +-25 mm of the bed centre
SPAWN_YAW_DEG = 20.0  # ... with a yaw within +-20 deg
CUBE_HELD_CONTYPE = 2  # collides with table/tray (7) but not the arm (1) while held
CUBE_FREE_CONTYPE = 3  # also collides with arm links (1), never with the gripper hulls (4)
GRIPPER_HULL_CONTYPE = 4  # see scene_task.xml: jaw mesh hulls are too fat to touch the cube
OFF_TABLE_Z_M = -0.05

# task version 2 grasp rule (mm / deg; measured from the official model, see docstring)
FINGER_HALF_WIDTH_MM = 7.0  # finger pads are 10-14 mm wide along the site y axis
PAD_X_MIN_MM = -45.0  # finger root (the jaws still clamp a 20 mm part there)
PAD_X_MAX_MM = 6.3  # fixed-jaw tip
JAW_PENETRATION_MM = 2.0  # the cube may overlap a pad by this much (pads do not collide with it)
FLAT_TOL_DEG = 10.0
# funnel numbers reported by get_scene per task version (must match the scene files)
FUNNEL = {1: {"funnel_top_z_mm": 21.5, "funnel_half_width_mm": 20.5, "outer_funnel_mm": 8.0},
          2: {"funnel_top_z_mm": 17.5, "funnel_half_width_mm": 16.5, "outer_funnel_mm": 4.0}}
SCENE_FILE = {1: "task", 2: "task_v2"}


def task_version(explicit: int | None = None) -> int:
    v = int(explicit if explicit is not None else os.environ.get("SWAYAM_TASK_VERSION", "1"))
    if v not in SCENE_FILE:
        raise ValueError(f"SWAYAM_TASK_VERSION must be one of {sorted(SCENE_FILE)}, got {v}")
    return v


def in_slot_rule(distance_mm: float, speed_mm_s: float, held: bool,
                 tilt_deg: float, height_error_mm: float) -> bool:
    """The verifier rule on already-measured numbers (also applied to logged scenes by
    the experiment reports, so the two can never disagree). A jammed cube can sit within
    3 mm of the slot centre; the tilt and height terms are what separate it from a
    seated one (studies/out/sim_pick_place_zero_shot_v2.md, audit rows 5d and 10)."""
    return (distance_mm <= SLOT_TOL_M * 1000 and speed_mm_s <= SLOT_REST_SPEED_M_S * 1000
            and not held and tilt_deg <= SLOT_TILT_TOL_DEG
            and abs(height_error_mm) <= SLOT_HEIGHT_TOL_M * 1000)


class SimArm:
    def __init__(self, scene: str | None = None, cube_seed: int | None = None,
                 task_version: int | None = None):
        self.scene_name = scene or os.environ.get("SWAYAM_SCENE", "plain")
        self.task_version = globals()["task_version"](task_version)
        self.scene_file = SCENE_FILE[self.task_version] if self.scene_name == "task" else self.scene_name
        self.model = load_model(self.scene_file)
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
            self._moving_jaw = self.model.body("moving_jaw_so101_v1").id
            self._pad_verts = self._find_moving_pad()
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

    # ---- task v2 grasp geometry ------------------------------------------------------
    def _moving_jaw_mesh(self) -> tuple[int, np.ndarray]:
        """(collision geom id, local vertices) of the moving-jaw mesh."""
        for g in range(self.model.ngeom):
            if self.model.geom_bodyid[g] == self._moving_jaw and self.model.geom_contype[g] \
                    and self.model.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
                mid = self.model.geom_dataid[g]
                a, n = self.model.mesh_vertadr[mid], self.model.mesh_vertnum[mid]
                return g, self.model.mesh_vert[a:a + n]
        raise RuntimeError("moving jaw collision mesh not found")

    def _mesh_in_site_frame(self, geom: int, verts: np.ndarray, data: mujoco.MjData) -> np.ndarray:
        world = verts @ data.geom_xmat[geom].reshape(3, 3).T + data.geom_xpos[geom]
        R = data.site_xmat[self._site].reshape(3, 3)
        return (world - data.site_xpos[self._site]) @ R

    def _find_moving_pad(self) -> np.ndarray:
        """Indices of the moving-jaw vertices that form its contact pad: the vertices that
        sit within 6 mm of the fixed-jaw face, over the front 14 mm of the finger, when
        the gripper is fully closed. Evaluated on a scratch copy so the scene is untouched."""
        g, verts = self._moving_jaw_mesh()
        scratch = mujoco.MjData(self.model)
        scratch.qpos[:] = self.data.qpos
        scratch.qpos[self._qadr[GRIPPER]] = self.model.jnt_range[self.model.joint(GRIPPER).id][0]
        mujoco.mj_kinematics(self.model, scratch)
        v = self._mesh_in_site_frame(g, verts, scratch)
        idx = np.where((v[:, 2] < 0.006) & (np.abs(v[:, 1]) < 0.008) & (v[:, 0] > -0.009) & (v[:, 0] < 0.005))[0]
        assert len(idx) > 100, len(idx)
        return idx

    def jaw_gap_mm(self) -> float:
        """Height of the moving-jaw pad's lowest point above the fixed-jaw face (site z),
        at the current opening: 1.9 mm closed, ~31 mm at 20 % open, ~98 mm fully open."""
        g, verts = self._moving_jaw_mesh()
        v = self._mesh_in_site_frame(g, verts[self._pad_verts], self.data)
        return float(v[:, 2].min() * 1000)

    def cube_in_site_frame(self) -> np.ndarray:
        """Cube centre in the gripperframe site frame (mm)."""
        R = self.data.site_xmat[self._site].reshape(3, 3)
        return R.T @ (self.data.xpos[self._cube_body] - self.data.site_xpos[self._site]) * 1000

    def cube_tilt_deg(self) -> float:
        """Angle between the cube's most vertical face normal and world z (0 = flat)."""
        Rc = self.data.xmat[self._cube_body].reshape(3, 3)
        return math.degrees(math.acos(min(1.0, float(np.max(np.abs(Rc[2, :]))))))

    def grasp_check_v2(self) -> tuple[bool, str, dict]:
        """Apply the v2 rule to the current state; (ok, reason, numbers)."""
        gap = self.jaw_gap_mm()
        x, y, z = (float(v) for v in self.cube_in_site_frame())
        tilt = self.cube_tilt_deg()
        half = CUBE_SIZE_MM / 2
        info = {"jaw_gap_mm": round(gap, 1), "cube_in_jaw_frame_mm": [round(x, 1), round(y, 1), round(z, 1)],
                "cube_tilt_deg": round(tilt, 1)}
        problems = []
        if gap <= CUBE_SIZE_MM:
            problems.append(f"jaws closing from a {gap:.0f} mm gap, not wider than the {CUBE_SIZE_MM:.0f} mm part")
        if not (half - JAW_PENETRATION_MM <= z <= gap - half + JAW_PENETRATION_MM):
            problems.append(f"cube centre {z:.1f} mm along the jaw axis, not between the pads "
                            f"[{half - JAW_PENETRATION_MM:.0f}, {gap - half + JAW_PENETRATION_MM:.0f}]")
        if abs(y) > FINGER_HALF_WIDTH_MM:
            problems.append(f"cube centre {y:.1f} mm across the pads, limit +-{FINGER_HALF_WIDTH_MM:.0f}")
        if not (PAD_X_MIN_MM <= x <= PAD_X_MAX_MM):
            problems.append(f"cube centre {x:.1f} mm along the fingers, pads span [{PAD_X_MIN_MM:.0f}, {PAD_X_MAX_MM:.1f}]")
        if tilt > FLAT_TOL_DEG:
            problems.append(f"cube tilted {tilt:.0f} deg, limit {FLAT_TOL_DEG:.0f}")
        return not problems, "; ".join(problems), info

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
                "lead_in_mm": 1.5,
                **FUNNEL[self.task_version],
            },
            "task_version": self.task_version,
            "bed": {"centre_xy_mm": [v * 1000 for v in BED_CENTRE_M], "half_size_mm": BED_HALF_M * 1000},
            "gripper": {
                "site_xyz_mm": [round(float(v) * 1000, 2) for v in site],
                "approach_axis": [round(float(v), 3) for v in approach],
                "jaw_axis": [round(float(v), 3) for v in R[:, 2]],
                "percent_open": round(self.positions()[GRIPPER], 1),
            },
        }

    def cube_in_slot(self) -> dict:
        """The verifier (both task versions). True only if the cube centre is within
        SLOT_TOL_M of the slot centre, moving slower than SLOT_REST_SPEED_M_S, not held,
        tilted no more than SLOT_TILT_TOL_DEG and within SLOT_HEIGHT_TOL_M of the slot
        centre height. Every number the decision used is returned alongside it."""
        pos, _, vel = self._cube_pose()
        slot = self.data.site_xpos[self._slot_site]
        dist = float(np.linalg.norm(pos - slot))
        speed = float(np.linalg.norm(vel[:3]))
        tilt = self.cube_tilt_deg()
        dz = float(pos[2] - slot[2])
        ok = in_slot_rule(dist * 1000, speed * 1000, self.held, tilt, dz * 1000)
        return {
            "in_slot": ok,
            "distance_mm": round(dist * 1000, 2),
            "tolerance_mm": SLOT_TOL_M * 1000,
            "speed_mm_s": round(speed * 1000, 2),
            "held_by_gripper": self.held,
            "tilt_deg": round(tilt, 2),
            "tilt_tolerance_deg": SLOT_TILT_TOL_DEG,
            "height_error_mm": round(dz * 1000, 2),
            "height_tolerance_mm": SLOT_HEIGHT_TOL_M * 1000,
        }

    def _set_cube_contacts(self, cls: int) -> None:
        self.model.geom_contype[self._cube_geom] = cls
        self.model.geom_conaffinity[self._cube_geom] = cls

    def _grasp_logic(self, gripper_target_pct: float) -> str | None:
        if gripper_target_pct < GRASP_CLOSE_PCT and not self.held:
            if self.task_version == 1:
                pos, _, _ = self._cube_pose()
                dist = float(np.linalg.norm(pos - self.data.site_xpos[self._site]))
                if dist <= GRASP_RADIUS_M:
                    self._grasp()
                    return "grasped"
                return f"close: cube {dist * 1000:.1f} mm from gripper site, no grasp (limit {GRASP_RADIUS_M * 1000:.0f} mm)"
            ok, why, info = self.grasp_check_v2()
            if ok:
                self._grasp()
                return "grasped"
            return f"close: no grasp ({why}); {info}"
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
