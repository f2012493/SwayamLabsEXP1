"""Damped-least-squares inverse kinematics on the official SO-101 model.

Task: put the tool centre point (TCP) at an xyz position in the arm base frame with
a given pitch of the approach axis, using shoulder_pan, shoulder_lift, elbow_flex and
wrist_flex. wrist_roll is held at the seed value.

Frames (from the model, see tests/test_ik.py):
  - `gripperframe` site: on the inner face of the fixed jaw; its +x axis is the
    approach direction (where the fingers point), its +z axis is the direction the
    jaws close across, so a grasped 20 mm object is centred about 10 mm along +z.
  - TCP = site origin + TCP_OFFSET_M expressed in the site frame (the jaw centre).
  - pitch: angle of the approach axis above horizontal. 0 = fingers horizontal
    (home pose), -90 = fingers pointing straight down.

The Jacobian comes from mujoco.mj_jac at the TCP point on the gripper body (the
same routine behind mj_jacSite). Joint ranges come from config/limits.json, which
is tighter than the model's own ranges.
"""

from __future__ import annotations

import math

import mujoco
import numpy as np

from swayam import JOINTS
from swayam.kinematics import GRIPPER_SITE, load_model
from swayam.limits import load_limits

IK_JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex")
TCP_OFFSET_M = (0.0, 0.0, 0.011)  # jaw centre: 10 mm half-cube + 1 mm clearance from the fixed jaw
PITCH_WEIGHT_M_PER_RAD = 0.05  # 1 rad of pitch error counts like 50 mm of position error
DAMPING = 0.02
MAX_STEP_RAD = 0.25


class Unreachable(ValueError):
    pass


class IK:
    def __init__(self, model: mujoco.MjModel | None = None, limits: dict | None = None):
        self.model = model or load_model()
        self.data = mujoco.MjData(self.model)
        self.limits = limits or load_limits()
        self._site = self.model.site(GRIPPER_SITE).id
        self._body = int(self.model.site_bodyid[self._site])
        self._qadr = {j: int(self.model.jnt_qposadr[self.model.joint(j).id]) for j in JOINTS}
        self._dof = {j: int(self.model.jnt_dofadr[self.model.joint(j).id]) for j in JOINTS}
        self._lo = np.array([math.radians(self.limits["joints"][j]["min"]) for j in IK_JOINTS])
        self._hi = np.array([math.radians(self.limits["joints"][j]["max"]) for j in IK_JOINTS])

    # ---- forward -------------------------------------------------------------------
    def _set(self, joints_deg: dict[str, float]) -> None:
        for j in JOINTS:
            self.data.qpos[self._qadr[j]] = math.radians(joints_deg.get(j, 0.0))
        mujoco.mj_kinematics(self.model, self.data)
        mujoco.mj_comPos(self.model, self.data)

    def _tcp(self, offset: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
        """TCP position (m), approach axis (unit, world) and pitch (rad)."""
        R = self.data.site_xmat[self._site].reshape(3, 3)
        p = self.data.site_xpos[self._site] + R @ offset
        a = R[:, 0]
        pan = self.data.qpos[self._qadr["shoulder_pan"]]
        h = np.array([math.cos(pan), -math.sin(pan), 0.0])  # arm's forward direction
        pitch = math.atan2(a[2], float(a @ h))
        return p.copy(), a.copy(), pitch

    def tcp_pose(self, joints_deg: dict[str, float], offset=TCP_OFFSET_M) -> dict:
        """TCP pose for a joint configuration: xyz in mm, pitch and yaw in degrees."""
        self._set(joints_deg)
        p, a, pitch = self._tcp(np.asarray(offset, dtype=float))
        return {
            "xyz_mm": [float(v) * 1000 for v in p],
            "pitch_deg": math.degrees(pitch),
            "yaw_deg": math.degrees(math.atan2(a[1], a[0])),
        }

    # ---- inverse -------------------------------------------------------------------
    def solve(
        self, xyz_m, pitch_deg: float, seed_deg: dict[str, float] | None = None,
        offset=TCP_OFFSET_M, max_iters: int = 300, tol_m: float = 5e-4, tol_deg: float = 0.5,
    ) -> dict[str, float]:
        """Joint angles (deg, all five) that put the TCP at xyz_m with the given pitch.
        Raises Unreachable with the best residual if no seed converges."""
        target = np.asarray(xyz_m, dtype=float)
        pitch_d = math.radians(pitch_deg)
        off = np.asarray(offset, dtype=float)
        seeds = [seed_deg or {}] + [s for s in _CANONICAL_SEEDS if s != seed_deg]
        best: tuple[float, float, dict] | None = None
        for seed in seeds:
            q, pos_err, pitch_err = self._solve_from(target, pitch_d, seed, off, max_iters)
            if pos_err <= tol_m and abs(pitch_err) <= math.radians(tol_deg):
                return q
            if best is None or pos_err < best[0]:
                best = (pos_err, pitch_err, q)
        pos_err, pitch_err, _ = best
        raise Unreachable(
            f"target {np.round(target * 1000, 1).tolist()} mm at pitch {pitch_deg:.0f} deg is "
            f"unreachable within joint limits: best residual {pos_err * 1000:.1f} mm, "
            f"{math.degrees(pitch_err):.1f} deg"
        )

    def _solve_from(self, target, pitch_d, seed, off, max_iters):
        joints = {j: float(seed.get(j, 0.0)) for j in JOINTS}
        q = np.array([math.radians(joints[j]) for j in IK_JOINTS])
        q = np.clip(q, self._lo, self._hi)
        cols = [self._dof[j] for j in IK_JOINTS]
        jacp = np.zeros((3, self.model.nv))
        jacr = np.zeros((3, self.model.nv))
        lam2 = DAMPING ** 2
        pos_err = math.inf
        pitch_err = math.inf
        for _ in range(max_iters):
            for j, v in zip(IK_JOINTS, q):
                joints[j] = math.degrees(v)
            self._set(joints)
            p, a, pitch = self._tcp(off)
            e_pos = target - p
            e_pitch = _wrap(pitch_d - pitch)
            pos_err = float(np.linalg.norm(e_pos))
            pitch_err = e_pitch
            if pos_err < 1e-4 and abs(e_pitch) < 1e-3:
                break
            mujoco.mj_jac(self.model, self.data, jacp, jacr, p, self._body)
            pan = q[0]
            n = np.array([math.sin(pan), math.cos(pan), 0.0])  # pitch axis (normal to arm plane)
            J = np.vstack([jacp[:, cols], -(n @ jacr[:, cols]) * PITCH_WEIGHT_M_PER_RAD])
            e = np.concatenate([e_pos, [e_pitch * PITCH_WEIGHT_M_PER_RAD]])
            dq = J.T @ np.linalg.solve(J @ J.T + lam2 * np.eye(4), e)
            scale = MAX_STEP_RAD / max(MAX_STEP_RAD, float(np.max(np.abs(dq))))
            q = np.clip(q + dq * scale, self._lo, self._hi)
        for j, v in zip(IK_JOINTS, q):
            joints[j] = math.degrees(v)
        return joints, pos_err, pitch_err


def _wrap(a: float) -> float:
    return (a + math.pi) % (2 * math.pi) - math.pi


# Elbow-up / elbow-down style starting points so a bad seed does not mean "unreachable".
_CANONICAL_SEEDS = [
    {},
    {"shoulder_lift": 40, "elbow_flex": 60, "wrist_flex": 60},
    {"shoulder_lift": 60, "elbow_flex": 20, "wrist_flex": 80},
    {"shoulder_lift": -30, "elbow_flex": 70, "wrist_flex": 40},
    {"shoulder_lift": 20, "elbow_flex": -40, "wrist_flex": -60},
]
