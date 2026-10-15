from swayam.arm.sim import SimArm
from swayam.kinematics import Kinematics


def test_sim_reaches_target():
    arm = SimArm()
    result = arm.move({"shoulder_pan": 20, "shoulder_lift": -20, "elbow_flex": 20}, 1.5)
    assert result["aborted"] is None
    assert result["max_error_deg"] < 2.0, result["max_error_deg"]


def test_gripper_opens_and_closes():
    arm = SimArm()
    assert abs(arm.move({"gripper": 90}, 0.8)["positions"]["gripper"] - 90) < 5
    assert abs(arm.move({"gripper": 10}, 0.8)["positions"]["gripper"] - 10) < 5


def test_kinematics_matches_sim():
    arm = SimArm()
    result = arm.move({"shoulder_pan": 30, "elbow_flex": 30}, 1.5)
    predicted = Kinematics().gripper_xyz(result["positions"])
    actual = result["gripper_xyz_m"]
    assert max(abs(p - a) for p, a in zip(predicted, actual)) < 0.005


def test_home_pose_is_above_table():
    z = Kinematics().gripper_xyz({}) [2]
    assert z > 0.01
