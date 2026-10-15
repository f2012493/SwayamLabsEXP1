import asyncio

import numpy as np

from swayam.arm.sim import GRASP_RADIUS_M, SimArm
from swayam.controller import Controller
from swayam.ik import IK
from swayam.kinematics import load_model


def test_plain_scene_is_the_default(monkeypatch):
    monkeypatch.delenv("SWAYAM_SCENE", raising=False)
    arm = SimArm()
    assert arm.scene_name == "plain" and not arm.has_task
    assert "scene" not in arm.telemetry()


def test_task_scene_selected_by_env(monkeypatch):
    monkeypatch.setenv("SWAYAM_SCENE", "task")
    monkeypatch.setenv("SWAYAM_CUBE_SEED", "4")
    arm = SimArm()
    assert arm.has_task and arm.cube_seed == 4
    assert "scene" in arm.telemetry()


def test_kinematics_identical_in_both_scenes():
    a, b = load_model("plain"), load_model("task")
    assert a.nq < b.nq  # task scene adds the cube's free joint
    assert np.allclose(a.body_pos[: a.nbody], b.body_pos[: a.nbody])


def test_cube_spawn_is_seeded_and_on_the_bed():
    c1 = SimArm(scene="task", cube_seed=7).scene()["cube"]
    c2 = SimArm(scene="task", cube_seed=7).scene()["cube"]
    c3 = SimArm(scene="task", cube_seed=8).scene()["cube"]
    assert c1["xyz_mm"] == c2["xyz_mm"]
    assert c1["xyz_mm"] != c3["xyz_mm"]
    x, y, z = c1["xyz_mm"]
    assert abs(x - 200) <= 25.5 and abs(y - 90) <= 25.5 and 9 < z < 11
    assert abs(c1["rpy_deg"][2]) <= 20


def test_verifier_false_at_spawn_and_cube_resting_does_not_abort_moves():
    arm = SimArm(scene="task", cube_seed=0)
    assert arm.cube_in_slot()["in_slot"] is False
    r = arm.move({"shoulder_pan": 20}, 1.0)
    assert r["aborted"] is None, "cube resting on the table must not count as a crash"


def test_grasp_refused_when_cube_is_far():
    arm = SimArm(scene="task", cube_seed=0)
    r = arm.move({"gripper": 0}, 0.5)
    assert "no grasp" in r["grasp_event"] and not arm.held


def _goto(arm, ik, x, y, z, roll=None):
    seed = arm.positions()
    if roll is not None:
        seed["wrist_roll"] = roll
    q = ik.solve([x / 1000, y / 1000, z / 1000], -90, seed_deg=seed)
    if roll is not None:
        q["wrist_roll"] = roll
    return arm.move(q, 2.0)


def test_scripted_pick_and_place_passes_the_verifier():
    """The loop is feasible with the tools alone; also pins down the weld grasp semantics."""
    arm = SimArm(scene="task", cube_seed=0)
    ik = IK()
    sc = arm.scene()
    cx, cy, _ = sc["cube"]["xyz_mm"]
    sx, sy, sz = sc["slot"]["centre_xyz_mm"]
    arm.move({"gripper": 100}, 0.5)
    _goto(arm, ik, cx, cy, 60)
    _goto(arm, ik, cx, cy, 12)
    assert arm.scene()["cube"]["distance_to_gripper_site_mm"] < GRASP_RADIUS_M * 1000
    assert arm.move({"gripper": 0}, 0.5)["grasp_event"] == "grasped" and arm.held
    _goto(arm, ik, cx, cy, 60)
    assert arm.scene()["cube"]["xyz_mm"][2] > 40, "cube must travel with the gripper"
    _goto(arm, ik, sx, sy, 60)
    yaw = arm.scene()["cube"]["rpy_deg"][2]
    _goto(arm, ik, sx, sy, 60, roll=arm.positions()["wrist_roll"] - yaw)
    assert abs(arm.scene()["cube"]["rpy_deg"][2]) < 5
    _goto(arm, ik, sx, sy, 35)
    assert arm.cube_in_slot()["in_slot"] is False, "held cube must not pass"
    assert arm.move({"gripper": 100}, 0.5)["grasp_event"] == "released" and not arm.held
    arm._settle(1.0)
    v = arm.cube_in_slot()
    assert v["in_slot"] is True and v["distance_mm"] < 3, v
    assert arm.model.geom_contype[arm._cube_geom] == 3, "collisions restored after release"


def test_mcp_server_exposes_scene_tools():
    from swayam import mcp_server

    tools = {t.name: t for t in asyncio.run(mcp_server.mcp.list_tools())}
    for name in ("get_scene", "is_cube_in_slot", "move_gripper_to", "move_joints", "set_gripper"):
        assert name in tools, sorted(tools)
    params = tools["move_gripper_to"].inputSchema["properties"]
    assert {"x_mm", "y_mm", "z_mm", "pitch_deg", "roll_deg"} <= set(params)
    assert "NOT simulated" in tools["set_gripper"].description


def test_move_gripper_to_refuses_unreachable_and_logs(monkeypatch, tmp_path):
    monkeypatch.setenv("SWAYAM_SCENE", "task")
    from swayam import mcp_server

    mcp_server._state.clear()
    # tools are wrapped by FastMCP; call the underlying function
    out = mcp_server.move_gripper_to.__wrapped__(600, 0, 50)
    assert out["ok"] is False and "unreachable" in out["refused"][0]
    out = mcp_server.move_gripper_to.__wrapped__(200, 90, 60)
    assert out["ok"] is True and abs(out["tcp"]["xyz_mm"][2] - 60) < 2
    log = (tmp_path / "runs").glob("*.jsonl")
    text = "".join(p.read_text() for p in log)
    assert '"event": "refused"' in text and '"tool": "move_gripper_to"' in text
    mcp_server._state.clear()
