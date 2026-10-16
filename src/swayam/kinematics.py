"""Kinematics for the SO-101, used by both backends.

`Kinematics` (MuJoCo FK of the gripper site) is the independent safety check: the real
arm has no position sensor at the gripper, so the controller predicts where the gripper
will end up before moving and refuses poses that hit the table.

`TcpKinematics` is the planner behind move_gripper_to: LeRobot's placo `RobotKinematics`
(lerobot/model/kinematics.py) on the official SO-101 URDF, wrapped to take an xyz + pitch
target for the tool centre point (TCP) instead of a full 4x4 pose.
"""

from __future__ import annotations

import math

import mujoco
import numpy as np
from lerobot.model import RobotKinematics

from swayam import GRIPPER, JOINTS, REPO_ROOT
from swayam.limits import load_limits

SCENES = {
    "plain": REPO_ROOT / "sim" / "so101" / "scene.xml",  # arm + floor only
    "task": REPO_ROOT / "sim" / "so101" / "scene_task.xml",  # + cube on bed + kit tray slot
    "task_v2": REPO_ROOT / "sim" / "so101" / "scene_task_v2.xml",  # same, 4 mm funnel (task version 2)
}
SCENE_PATH = SCENES["plain"]
GRIPPER_SITE = "gripperframe"


def load_model(scene: str = "plain") -> mujoco.MjModel:
    """Load a scene by name ("plain" or "task"). Kinematics are identical in both."""
    return mujoco.MjModel.from_xml_path(str(SCENES[scene]))


def gripper_percent_to_rad(model: mujoco.MjModel, percent: float) -> float:
    lo, hi = model.jnt_range[model.joint(GRIPPER).id]
    return lo + (hi - lo) * percent / 100.0


def gripper_rad_to_percent(model: mujoco.MjModel, rad: float) -> float:
    lo, hi = model.jnt_range[model.joint(GRIPPER).id]
    return 100.0 * (rad - lo) / (hi - lo)


class Kinematics:
    def __init__(self, model: mujoco.MjModel | None = None):
        self.model = model or load_model()
        self.data = mujoco.MjData(self.model)
        self._site = self.model.site(GRIPPER_SITE).id

    def gripper_xyz(self, joints_deg: dict[str, float]) -> tuple[float, float, float]:
        for name in JOINTS:
            if name in joints_deg:
                adr = self.model.jnt_qposadr[self.model.joint(name).id]
                self.data.qpos[adr] = math.radians(joints_deg[name])
        mujoco.mj_kinematics(self.model, self.data)
        x, y, z = self.data.site_xpos[self._site]
        return float(x), float(y), float(z)


# ---- placo planner -------------------------------------------------------------------

URDF_PATH = REPO_ROOT / "sim" / "so101" / "so101_new_calib.urdf"
URDF_FRAME = "gripper_frame_link"  # same point as the MuJoCo `gripperframe` site (parity: studies/out/ik_parity.md)
IK_JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex")
TCP_OFFSET_M = (0.0, 0.0, 0.011)  # jaw centre in site axes: 10 mm half-cube + 1 mm clearance from the fixed jaw
ORIENTATION_WEIGHT = 0.5  # target orientation is exactly reachable with 4 free joints, so a stiff weight is safe
POS_TOL_M = 5e-4
PITCH_TOL_DEG = 0.5
MAX_ITERS = 60

# Frame mapping. The URDF `gripper_frame_link` and the MuJoCo `gripperframe` site are the same
# point, but their axes differ (measured in studies/ik_parity.py, columns of the rotation):
#   site +x (approach, fingers point) = URDF +z
#   site +y                           = URDF +y
#   site +z (jaws close across)       = URDF -x
# A vector given in site axes (ox, oy, oz) is therefore (-oz, oy, ox) in URDF axes.
def site_to_urdf(v) -> np.ndarray:
    ox, oy, oz = v
    return np.array([-oz, oy, ox])


# Joint angles are degrees in both models and share zero (home pose); the URDF pitch of the
# approach axis (URDF +z) is -(shoulder_lift + elbow_flex + wrist_flex), independent of
# shoulder_pan and wrist_roll (checked numerically in the parity study).


_PLANAR_REF = {"shoulder_lift": 30.0, "elbow_flex": 40.0, "wrist_flex": -20.0}  # any in-plane posture works


class Unreachable(ValueError):
    pass


class TcpKinematics:
    """TCP xyz (base frame, m) + pitch (deg) <-> joint angles, via LeRobot's RobotKinematics.

    pitch: angle of the approach axis above horizontal; 0 = fingers horizontal (home pose),
    -90 = fingers straight down. wrist_roll is held at the seed value; joint ranges come from
    config/limits.json (tighter than the URDF's)."""

    def __init__(self, limits: dict | None = None, urdf: str | None = None):
        self.limits = limits or load_limits()
        self.rk = RobotKinematics(str(urdf or URDF_PATH), URDF_FRAME, list(JOINTS[:5]))
        for j in JOINTS[:5]:
            rng = self.limits["joints"][j]
            self.rk.robot.set_joint_limits(j, np.deg2rad(rng["min"]), np.deg2rad(rng["max"]))
        self.rk.solver.mask_dof("wrist_roll")
        # The pan axis is vertical but not through the URDF base origin (SO-101: ~38.8 mm ahead of
        # it). Rotating any pose 90 deg about it puts it at x = axis x, which gives the offset.
        self._pan_axis_x = float(self.frame_pose(_PLANAR_REF | {"shoulder_pan": 90.0})[0, 3])
        self._lo = np.array([self.limits["joints"][j]["min"] for j in JOINTS[:5]], dtype=float)
        self._hi = np.array([self.limits["joints"][j]["max"] for j in JOINTS[:5]], dtype=float)

    # ---- forward -------------------------------------------------------------------
    def frame_pose(self, joints_deg: dict[str, float]) -> np.ndarray:
        """4x4 pose of the URDF gripper frame for a joint configuration (degrees)."""
        return self.rk.forward_kinematics(np.array([joints_deg.get(j, 0.0) for j in JOINTS[:5]], dtype=float))

    def tcp_pose(self, joints_deg: dict[str, float], offset=TCP_OFFSET_M) -> dict:
        """TCP pose for a joint configuration: xyz in mm, pitch and yaw in degrees."""
        T = self.frame_pose(joints_deg)
        p = T[:3, 3] + T[:3, :3] @ site_to_urdf(offset)
        a = T[:3, 2]  # approach axis
        pan = math.radians(joints_deg.get("shoulder_pan", 0.0))
        h = np.array([math.cos(pan), -math.sin(pan), 0.0])  # arm's forward direction
        return {
            "xyz_mm": [float(v) * 1000 for v in p],
            "pitch_deg": math.degrees(math.atan2(a[2], float(a @ h))),
            "yaw_deg": math.degrees(math.atan2(a[1], a[0])),
        }

    # ---- inverse -------------------------------------------------------------------
    def _target_frame(self, tcp: np.ndarray, pitch_deg: float, roll_deg: float, off: np.ndarray) -> np.ndarray:
        """4x4 pose the URDF frame must take so that the TCP lands on `tcp` at `pitch_deg`.

        The orientation is read from FK at (pan, 0, 0, -pitch, roll): pitch only depends on the
        sum of the three planar joints, so this is the orientation of every configuration with
        that pan/pitch/roll. The TCP offset rotates with the orientation, so pan is iterated
        (the frame origin must lie in the vertical plane through the pan axis at angle pan)."""
        # wrist_roll swings the frame origin sideways (the frame sits ~8 mm off the roll axis), by a
        # lateral amount that depends on roll only; at pan 0 that is the origin's y.
        lateral = float(self.frame_pose(_PLANAR_REF | {"wrist_roll": roll_deg})[1, 3])
        origin = tcp
        for _ in range(6):
            dx, dy = origin[0] - self._pan_axis_x, origin[1]
            reach = math.sqrt(max(dx * dx + dy * dy - lateral * lateral, 1e-12))
            pan = -math.degrees(math.atan2(dy, dx) - math.atan2(lateral, reach))
            R = self.frame_pose({"shoulder_pan": pan, "wrist_flex": -pitch_deg, "wrist_roll": roll_deg})[:3, :3]
            origin = tcp - R @ off
        T = np.eye(4)
        T[:3, :3] = R
        T[:3, 3] = origin
        return T

    def solve(
        self, xyz_m, pitch_deg: float, seed_deg: dict[str, float] | None = None,
        offset=TCP_OFFSET_M, max_iters: int = MAX_ITERS,
        tol_m: float = POS_TOL_M, tol_deg: float = PITCH_TOL_DEG,
    ) -> dict[str, float]:
        """Joint angles (deg, all five) that put the TCP at xyz_m with the given pitch.
        Raises Unreachable with the best residual if no seed converges."""
        target = np.asarray(xyz_m, dtype=float)
        off = site_to_urdf(offset)
        seed0 = {j: 0.0 for j in JOINTS[:5]} | {j: float(v) for j, v in (seed_deg or {}).items() if j in JOINTS[:5]}
        roll = seed0["wrist_roll"]
        T = self._target_frame(target, pitch_deg, roll, off)
        best: tuple[float, float, dict] | None = None
        for seed in [seed0] + [seed0 | s for s in _CANONICAL_SEEDS]:
            q, pos_err, pitch_err = self._solve_from(T, target, pitch_deg, seed, off, max_iters, tol_m, tol_deg)
            if pos_err <= tol_m and abs(pitch_err) <= tol_deg:
                return q
            if best is None or pos_err < best[0]:
                best = (pos_err, pitch_err, q)
        pos_err, pitch_err, _ = best
        raise Unreachable(
            f"target {np.round(target * 1000, 1).tolist()} mm at pitch {pitch_deg:.0f} deg is "
            f"unreachable within joint limits: best residual {pos_err * 1000:.1f} mm, "
            f"{pitch_err:.1f} deg"
        )

    def _solve_from(self, T, target, pitch_deg, seed, off, max_iters, tol_m, tol_deg):
        q = np.clip(np.array([seed[j] for j in JOINTS[:5]], dtype=float), self._lo, self._hi)
        pos_err = pitch_err = math.inf
        for _ in range(max_iters):
            q = self.rk.inverse_kinematics(q, T, position_weight=1.0, orientation_weight=ORIENTATION_WEIGHT)
            pose = self.tcp_pose(dict(zip(JOINTS[:5], q)), offset=_urdf_to_site(off))
            pos_err = float(np.linalg.norm(np.array(pose["xyz_mm"]) / 1000 - target))
            pitch_err = pose["pitch_deg"] - pitch_deg
            if pos_err <= tol_m * 0.2 and abs(pitch_err) <= tol_deg * 0.2:
                break
        return dict(zip(JOINTS[:5], (float(v) for v in q))), pos_err, pitch_err


def _urdf_to_site(v: np.ndarray) -> tuple[float, float, float]:
    x, y, z = v
    return (float(z), float(y), float(-x))


# Elbow-up / elbow-down style starting points so a bad seed does not mean "unreachable".
_CANONICAL_SEEDS = [
    {"shoulder_lift": 0, "elbow_flex": 0, "wrist_flex": 0},
    {"shoulder_lift": 40, "elbow_flex": 60, "wrist_flex": 60},
    {"shoulder_lift": 60, "elbow_flex": 20, "wrist_flex": 80},
    {"shoulder_lift": -30, "elbow_flex": 70, "wrist_flex": 40},
    {"shoulder_lift": 20, "elbow_flex": -40, "wrist_flex": -60},
]
