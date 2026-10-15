"""Forward kinematics from the official SO-101 model, used by both backends.

The real arm has no position sensor at the gripper, so the server predicts where
the gripper will end up before moving and refuses poses that hit the table.
"""

from __future__ import annotations

import math

import mujoco

from swayam import GRIPPER, JOINTS, REPO_ROOT

SCENES = {
    "plain": REPO_ROOT / "sim" / "so101" / "scene.xml",  # arm + floor only
    "task": REPO_ROOT / "sim" / "so101" / "scene_task.xml",  # + cube on bed + kit tray slot
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
