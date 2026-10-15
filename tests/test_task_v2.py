"""Task version 2: 4 mm funnel, geometric grasp rule, optional placement noise.
v1 must stay byte-for-byte reproducible (default)."""

import asyncio
import math

import mujoco
import pytest

from swayam.arm.sim import (
    CUBE_SIZE_MM,
    FINGER_HALF_WIDTH_MM,
    FLAT_TOL_DEG,
    FUNNEL,
    GRASP_RADIUS_M,
    SimArm,
    task_version,
)
from swayam.ik import IK


def _goto(arm, ik, x, y, z, roll=None):
    seed = arm.positions()
    if roll is not None:
        seed["wrist_roll"] = roll
    q = ik.solve([x / 1000, y / 1000, z / 1000], -90, seed_deg=seed)
    if roll is not None:
        q["wrist_roll"] = roll
    return arm.move(q, 2.0)


def _tilt_cube(arm, deg, axis=(0, 1, 0)):
    """Rotate the cube in place about a horizontal axis (no settling: a pose probe)."""
    q = arm._cube_q
    h = math.radians(deg) / 2
    ax = [a * math.sin(h) for a in axis]
    arm.data.qpos[q + 3:q + 7] = [math.cos(h), *ax]
    mujoco.mj_forward(arm.model, arm.data)


def test_v1_is_the_default_and_unchanged(monkeypatch):
    monkeypatch.delenv("SWAYAM_TASK_VERSION", raising=False)
    arm = SimArm(scene="task", cube_seed=0)
    assert arm.task_version == 1 and arm.scene_file == "task"
    slot = arm.scene()["slot"]
    assert slot["funnel_top_z_mm"] == 21.5 and slot["funnel_half_width_mm"] == 20.5
    assert arm.scene()["task_version"] == 1


def test_v2_selected_by_env_and_has_the_small_funnel(monkeypatch):
    monkeypatch.setenv("SWAYAM_TASK_VERSION", "2")
    arm = SimArm(scene="task", cube_seed=0)
    assert arm.task_version == 2 and arm.scene_file == "task_v2"
    slot = arm.scene()["slot"]
    assert slot["funnel_top_z_mm"] == 17.5 and slot["funnel_half_width_mm"] == 16.5
    assert slot["outer_funnel_mm"] == 4.0 and slot["lead_in_mm"] == 1.5
    # the chamfer geoms really run from half-width 11 at z 12 to 16.5 at z 17.5
    g = arm.model.geom("funnel_px").id
    px, _, pz = arm.model.geom_pos[g] * 1000  # tray-local position, mm
    assert abs(px - 14.457) < 0.01 and abs(pz - 14.043) < 0.01
    half = arm.model.geom_size[g][0] * 1000
    assert abs(half - 5.5 * math.sqrt(2) / 2) < 0.01
    with pytest.raises(ValueError):
        task_version(3)


def test_v1_and_v2_scenes_differ_only_in_the_funnel():
    a = SimArm(scene="task", cube_seed=3, task_version=1)
    b = SimArm(scene="task", cube_seed=3, task_version=2)
    assert a.scene()["cube"] == b.scene()["cube"]
    assert a.scene()["slot"]["centre_xyz_mm"] == b.scene()["slot"]["centre_xyz_mm"]
    assert a.model.ngeom == b.model.ngeom and a.model.nq == b.model.nq


def test_jaw_gap_tracks_the_opening():
    arm = SimArm(scene="task", cube_seed=0, task_version=2)
    gaps = {}
    for pct in (0, 20, 50, 100):
        arm.move({"gripper": pct}, 0.5)
        gaps[pct] = arm.jaw_gap_mm()
    assert gaps[0] < 5 and 25 < gaps[20] < 40 and 60 < gaps[50] < 80 and gaps[100] > 90, gaps
    assert gaps[0] < gaps[20] < gaps[50] < gaps[100]


def test_v2_scripted_pick_and_place_passes_the_verifier():
    """Feasible with the tools alone under the v2 rule and the 4 mm funnel."""
    arm = SimArm(scene="task", cube_seed=0, task_version=2)
    ik = IK()
    sc = arm.scene()
    cx, cy, _ = sc["cube"]["xyz_mm"]
    sx, sy, sz = sc["slot"]["centre_xyz_mm"]
    arm.move({"gripper": 100}, 0.5)
    _goto(arm, ik, cx, cy, 60)
    _goto(arm, ik, cx, cy, 12)
    ok, why, info = arm.grasp_check_v2()
    assert ok, (why, info)
    x, y, z = info["cube_in_jaw_frame_mm"]
    assert abs(x) < 3 and abs(y) < 3 and 8 < z < 14, info  # TCP offset puts the cube ~11 mm from the fixed jaw
    assert arm.move({"gripper": 0}, 0.5)["grasp_event"] == "grasped" and arm.held
    _goto(arm, ik, cx, cy, 60)
    _goto(arm, ik, sx, sy, 60)
    yaw = arm.scene()["cube"]["rpy_deg"][2]
    _goto(arm, ik, sx, sy, 60, roll=arm.positions()["wrist_roll"] - yaw)
    assert abs(arm.scene()["cube"]["rpy_deg"][2]) < 5
    _goto(arm, ik, sx, sy, 32)  # cube bottom ~10 mm above the v2 funnel mouth
    assert arm.cube_in_slot()["in_slot"] is False
    assert arm.move({"gripper": 100}, 0.5)["grasp_event"] == "released" and not arm.held
    arm._settle(1.0)
    v = arm.cube_in_slot()
    assert v["in_slot"] is True and v["distance_mm"] < 3, v


def test_v2_refuses_what_v1_accepted():
    """The v1 audit's artefact: a tilted cube grasped at 40 % open from 12.6 mm away."""
    ik = IK()
    for version in (1, 2):
        arm = SimArm(scene="task", cube_seed=0, task_version=version)
        cx, cy, _ = arm.scene()["cube"]["xyz_mm"]
        arm.move({"gripper": 40}, 0.5)
        _goto(arm, ik, cx, cy, 12)
        _tilt_cube(arm, 34)
        assert arm.scene()["cube"]["distance_to_gripper_site_mm"] < GRASP_RADIUS_M * 1000
        r = arm.move({"gripper": 0}, 0.5)
        if version == 1:
            assert r["grasp_event"] == "grasped", r["grasp_event"]
        else:
            assert r["grasp_event"].startswith("close: no grasp") and "tilted" in r["grasp_event"], r["grasp_event"]
            assert not arm.held


def test_v2_rule_rejects_each_geometric_fault_separately():
    arm = SimArm(scene="task", cube_seed=0, task_version=2)
    ik = IK()
    cx, cy, _ = arm.scene()["cube"]["xyz_mm"]
    arm.move({"gripper": 100}, 0.5)
    _goto(arm, ik, cx, cy, 60)
    _goto(arm, ik, cx, cy, 12)
    assert arm.grasp_check_v2()[0]
    # closing from a gap narrower than the part (10 % open ~ 17 mm)
    arm.move({"gripper": 10}, 0.5)
    ok, why, info = arm.grasp_check_v2()
    assert not ok and "not wider than" in why and info["jaw_gap_mm"] < CUBE_SIZE_MM, (why, info)
    arm.move({"gripper": 100}, 0.5)
    # cube displaced across the pads (site y) by more than the pad half-width
    q = arm._cube_q
    R = arm.data.site_xmat[arm._site].reshape(3, 3)
    home = arm.data.qpos[q:q + 3].copy()
    arm.data.qpos[q:q + 3] = home + R[:, 1] * (FINGER_HALF_WIDTH_MM + 4) / 1000
    mujoco.mj_forward(arm.model, arm.data)
    ok, why, _ = arm.grasp_check_v2()
    assert not ok and "across the pads" in why, why
    # cube displaced along the fingers past the tip
    arm.data.qpos[q:q + 3] = home + R[:, 0] * 0.015
    mujoco.mj_forward(arm.model, arm.data)
    ok, why, _ = arm.grasp_check_v2()
    assert not ok and "along the fingers" in why, why
    # cube pushed into the fixed jaw (centre < 8 mm from its face)
    arm.data.qpos[q:q + 3] = home - R[:, 2] * 0.006
    mujoco.mj_forward(arm.model, arm.data)
    ok, why, _ = arm.grasp_check_v2()
    assert not ok and "jaw axis" in why, why
    # tilt just inside / outside the tolerance
    arm.data.qpos[q:q + 3] = home
    _tilt_cube(arm, FLAT_TOL_DEG - 1)
    assert arm.grasp_check_v2()[0]
    _tilt_cube(arm, FLAT_TOL_DEG + 1)
    assert not arm.grasp_check_v2()[0]
    # a cube lying flat on a different face (roll 90) is still flat
    _tilt_cube(arm, 90, axis=(1, 0, 0))
    assert arm.cube_tilt_deg() < 1e-6


def test_v2_funnel_seats_a_flat_cube_dropped_4_mm_off_centre():
    from swayam.studies.funnel_capture import drop

    arm = SimArm(scene="task", cube_seed=0, task_version=2)
    arm.move({"shoulder_pan": 60}, 1.0)
    assert drop(arm, 0, 0, 0)["in_slot"]
    assert drop(arm, 4 / math.sqrt(2), 4 / math.sqrt(2), 0)["in_slot"]
    far = drop(arm, 10 / math.sqrt(2), 10 / math.sqrt(2), 0)
    assert not far["in_slot"] and far["distance_mm"] > 12


def test_mcp_docstrings_follow_the_task_version():
    from swayam import mcp_server

    assert "15 mm" in mcp_server.grasp_rule_text(1) and "flat" not in mcp_server.grasp_rule_text(1)
    t2 = mcp_server.grasp_rule_text(2)
    assert "wider than the 20 mm cube" in t2 and "10 deg of flat" in t2 and "+-7 mm" in t2
    assert "8 mm funnel" in mcp_server.funnel_text(1) and "4 mm funnel" in mcp_server.funnel_text(2)
    assert mcp_server.noise_text(0) == "" and "2.0 mm RMS" in mcp_server.noise_text(2.0)
    tools = {t.name: t for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert mcp_server.grasp_rule_text(mcp_server.TASK_VERSION) in tools["set_gripper"].description


def test_placement_noise_is_seeded_and_logged(monkeypatch, tmp_path):
    monkeypatch.setenv("SWAYAM_SCENE", "task")
    monkeypatch.setenv("SWAYAM_CUBE_SEED", "5")
    from swayam import mcp_server

    monkeypatch.setattr(mcp_server, "PLACE_NOISE_MM", 2.0)
    reached = []
    noises = []
    for _ in range(2):
        mcp_server._state.clear()
        n1 = mcp_server._placement_noise()
        n2 = mcp_server._placement_noise()
        noises.append((n1, n2))
        mcp_server._state.clear()
        out = mcp_server.move_gripper_to.__wrapped__(200, 90, 60)
        assert out["ok"]
        reached.append(out["tcp"]["xyz_mm"])
    assert noises[0] == noises[1], "same seed, same error stream"
    assert noises[0][0] != noises[0][1], "fresh error per call"
    assert reached[0] == reached[1]
    assert 0.3 < math.hypot(reached[0][0] - 200, reached[0][1] - 90) < 8, reached
    text = "".join(p.read_text() for p in (tmp_path / "runs").glob("*.jsonl"))
    assert '"placement_noise_mm": [' in text
    mcp_server._state.clear()
    # off by default: no noise field, target hit
    monkeypatch.setattr(mcp_server, "PLACE_NOISE_MM", 0.0)
    assert mcp_server._placement_noise() is None
    out = mcp_server.move_gripper_to.__wrapped__(200, 90, 60)
    assert math.hypot(out["tcp"]["xyz_mm"][0] - 200, out["tcp"]["xyz_mm"][1] - 90) < 1.0
    mcp_server._state.clear()


def test_harness_tilt_matches_sim():
    from swayam.experiments.zero_shot import CONDITIONS, tilt_from_rpy

    arm = SimArm(scene="task", cube_seed=0, task_version=2)
    for deg in (0, 7, 34, 90):
        _tilt_cube(arm, deg)
        _, rpy, _ = arm._cube_pose()
        assert abs(tilt_from_rpy(rpy) - arm.cube_tilt_deg()) < 0.1, deg
    assert CONDITIONS["v2"]["task_version"] == 2 and CONDITIONS["v2-noise"]["noise_mm"] == 2.0
    assert CONDITIONS["v1"]["task_version"] == 1 and CONDITIONS["v1"]["noise_mm"] == 0
    assert FUNNEL[2]["outer_funnel_mm"] == 4.0
