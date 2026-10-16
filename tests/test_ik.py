import math

import numpy as np
import pytest

from swayam import JOINTS
from swayam.kinematics import TCP_OFFSET_M, Kinematics, TcpKinematics, Unreachable
from swayam.limits import load_limits

LIMITS = load_limits()


@pytest.fixture(scope="module")
def ik():
    return TcpKinematics()


@pytest.fixture(scope="module")
def kin():
    return Kinematics()


def _within_limits(joints):
    for j in JOINTS:
        rng = LIMITS["joints"][j]
        assert rng["min"] - 1e-6 <= joints[j] <= rng["max"] + 1e-6, (j, joints[j])


def test_ik_round_trips_against_forward_kinematics(ik, kin):
    """Solve for the gripper site itself (zero offset) and check with the independent FK."""
    rng = np.random.default_rng(3)
    worst = 0.0
    tested = 0
    for _ in range(40):
        q = {j: float(rng.uniform(LIMITS["joints"][j]["min"] * 0.6, LIMITS["joints"][j]["max"] * 0.6)) for j in JOINTS}
        q["wrist_roll"] = 0.0
        target = kin.gripper_xyz(q)
        pitch = ik.tcp_pose(q, offset=(0, 0, 0))["pitch_deg"]
        if target[2] < 0.02 or abs(pitch) > 89:
            continue
        try:
            sol = ik.solve(target, pitch, offset=(0, 0, 0))
        except Unreachable:
            continue
        _within_limits(sol)
        back = kin.gripper_xyz(sol)
        err = math.dist(back, target) * 1000
        worst = max(worst, err)
        tested += 1
        assert err < 2.0, (q, sol, err)
    assert tested >= 20, "too few random poses were solvable"


def test_ik_hits_tcp_targets_with_pitch(ik):
    for target, pitch in [((0.20, 0.09, 0.012), -90), ((0.20, -0.09, 0.035), -90),
                          ((0.30, 0.0, 0.15), 0), ((0.25, 0.05, 0.05), -45)]:
        sol = ik.solve(target, pitch)
        _within_limits(sol)
        pose = ik.tcp_pose(sol)
        assert math.dist([v / 1000 for v in pose["xyz_mm"]], target) * 1000 < 1.0
        assert abs(pose["pitch_deg"] - pitch) < 0.5


def test_tcp_offset_is_along_jaw_axis(ik):
    site = ik.tcp_pose({}, offset=(0, 0, 0))["xyz_mm"]
    tcp = ik.tcp_pose({})["xyz_mm"]
    # at home the jaw axis is world z (within the model's 2.8 deg wrist tilt),
    # so the TCP sits straight above the site
    assert abs(tcp[2] - site[2] - TCP_OFFSET_M[2] * 1000) < 0.1
    assert abs(tcp[0] - site[0]) < 0.1


def test_unreachable_targets_are_refused_with_a_reason(ik):
    with pytest.raises(Unreachable, match="unreachable"):
        ik.solve((0.60, 0.0, 0.10), -90)
    with pytest.raises(Unreachable):
        ik.solve((0.20, 0.0, 0.40), -90)
