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
    SLOT_HEIGHT_TOL_M,
    SLOT_TILT_TOL_DEG,
    SLOT_TOL_M,
    SimArm,
    in_slot_rule,
    task_version,
)
from swayam.kinematics import TcpKinematics


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
    ik = TcpKinematics()
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
    ik = TcpKinematics()
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
    ik = TcpKinematics()
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


# ---- tilt- and height-aware verifier ------------------------------------------------------

# Final logged cube poses of the four jammed attempts (runs/2026-10-15.jsonl, last tool_call
# of each run tag). Under the old distance-only rule they failed by ~1 mm; under the new rule
# they fail on tilt and height as well.
JAM_POSES = {
    "zero-shot-v2-20261015-202023-05": ([198.44, -90.23, 15.81], [-0.0, -32.73, 0.0]),
    "zero-shot-v2-20261015-202023-09": ([198.74, -86.14, 19.84], [-33.41, -30.82, 18.67]),
    "zero-shot-v2n-20261015-221203-00": ([198.44, -90.27, 15.81], [32.73, 0.0, -90.0]),
    "zero-shot-v2n-20261015-221203-02": ([198.44, -90.92, 15.81], [-0.0, -32.73, 0.0]),
}


def _quat_from_rpy(rpy_deg):
    """ZYX roll/pitch/yaw -> (w, x, y, z), the inverse of SimArm._cube_pose."""
    r, p, y = (math.radians(v) / 2 for v in rpy_deg)
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return [cy * cp * cr + sy * sp * sr, cy * cp * sr - sy * sp * cr,
            sy * cp * sr + cy * sp * cr, sy * cp * cr - cy * sp * sr]


def _place_cube(arm, xyz_mm, rpy_deg):
    """Pose probe: put the free cube at a logged pose with zero velocity, no settling."""
    q = arm._cube_q
    arm.data.qpos[q:q + 3] = [v / 1000 for v in xyz_mm]
    arm.data.qpos[q + 3:q + 7] = _quat_from_rpy(rpy_deg)
    arm.data.qvel[arm._cube_v:arm._cube_v + 6] = 0
    mujoco.mj_forward(arm.model, arm.data)


def test_jam_poses_in_test_match_the_run_log():
    """Keep the hard-coded poses honest against the append-only evidence (if present)."""
    from swayam import REPO_ROOT

    log = REPO_ROOT / "runs" / "2026-10-15.jsonl"
    if not log.exists():
        pytest.skip("runs/2026-10-15.jsonl not present")
    import json

    last = {}
    for line in log.read_text().splitlines():
        r = json.loads(line)
        if r.get("event") == "tool_call" and r.get("run_tag") in JAM_POSES:
            last[r["run_tag"]] = r
    assert set(last) == set(JAM_POSES)
    for tag, (xyz, rpy) in JAM_POSES.items():
        cube = last[tag]["scene"]["cube"]
        assert cube["xyz_mm"] == xyz and cube["rpy_deg"] == rpy, tag
        assert last[tag]["verifier"]["in_slot"] is False and last[tag]["verifier"]["distance_mm"] > SLOT_TOL_M * 1000


@pytest.mark.parametrize("version", [1, 2])
def test_logged_jam_poses_fail_the_verifier_on_tilt_and_height(version):
    arm = SimArm(scene="task", cube_seed=0, task_version=version)
    for tag, (xyz, rpy) in JAM_POSES.items():
        _place_cube(arm, xyz, rpy)
        pos, back, _ = arm._cube_pose()
        assert max(abs(a - b) for a, b in zip(back, rpy)) < 0.02, (tag, back)  # pose round-trips
        v = arm.cube_in_slot()
        assert v["in_slot"] is False, (tag, v)
        assert v["distance_mm"] > SLOT_TOL_M * 1000, (tag, v)  # failed under the old rule too
        assert v["tilt_deg"] > SLOT_TILT_TOL_DEG, (tag, v)
        assert v["height_error_mm"] > SLOT_HEIGHT_TOL_M * 1000, (tag, v)
        assert abs(v["tilt_deg"] - 32.73) < 0.05 or abs(v["tilt_deg"] - 44.2) < 0.2, (tag, v)


@pytest.mark.parametrize("version", [1, 2])
def test_seated_cube_passes_and_the_new_terms_bite_inside_3_mm(version):
    arm = SimArm(scene="task", cube_seed=0, task_version=version)
    sx, sy, sz = arm.scene()["slot"]["centre_xyz_mm"]
    # dropped in from just above the pocket and allowed to settle: seated
    _place_cube(arm, [sx, sy, sz + 3], [0, 0, 0])
    arm._settle(1.0)
    v = arm.cube_in_slot()
    assert v["in_slot"] is True, v
    assert v["tilt_deg"] < 0.5 and abs(v["height_error_mm"]) < 0.5 and v["distance_mm"] < 1, v
    assert v["tilt_tolerance_deg"] == SLOT_TILT_TOL_DEG and v["height_tolerance_mm"] == SLOT_HEIGHT_TOL_M * 1000
    # same centre, tilted just past the limit: within 3 mm, at height, yet not seated
    _place_cube(arm, [sx, sy, sz], [0, SLOT_TILT_TOL_DEG + 1, 0])
    v = arm.cube_in_slot()
    assert v["distance_mm"] < 0.01 and abs(v["height_error_mm"]) < 0.01 and v["in_slot"] is False, v
    _place_cube(arm, [sx, sy, sz], [0, SLOT_TILT_TOL_DEG - 1, 0])
    assert arm.cube_in_slot()["in_slot"] is True
    # flat and centred in xy but 1.5 mm high: within 3 mm, yet not seated
    _place_cube(arm, [sx, sy, sz + 1.5], [0, 0, 0])
    v = arm.cube_in_slot()
    assert v["distance_mm"] < 1.51 and v["tilt_deg"] < 0.01 and v["in_slot"] is False, v
    _place_cube(arm, [sx, sy, sz + 0.5], [0, 0, 0])
    assert arm.cube_in_slot()["in_slot"] is True
    # the pure rule agrees with the method on the same numbers
    assert in_slot_rule(0.0, 0.0, False, SLOT_TILT_TOL_DEG, SLOT_HEIGHT_TOL_M * 1000) is True
    assert in_slot_rule(0.0, 0.0, False, SLOT_TILT_TOL_DEG + 0.01, 0.0) is False
    assert in_slot_rule(0.0, 0.0, False, 0.0, -(SLOT_HEIGHT_TOL_M * 1000 + 0.01)) is False
    assert in_slot_rule(0.0, 0.0, True, 0.0, 0.0) is False


def test_verifier_docstring_names_the_new_terms():
    from swayam import mcp_server

    tools = {t.name: t for t in asyncio.run(mcp_server.mcp.list_tools())}
    d = tools["is_cube_in_slot"].description
    assert "5 deg" in d and "1 mm" in d and "jammed" in d


def test_pre_release_rule_and_logged_verifier_recompute():
    from swayam.experiments.pre_release_signal import (
        PRE_RELEASE_TILT_DEG,
        PRE_RELEASE_XY_MM,
        rule_fires,
        verifier_from_scene,
    )

    def scene(xyz, rpy, held=False, speed=0.0):
        return {"cube": {"xyz_mm": xyz, "rpy_deg": rpy, "speed_mm_s": speed, "held_by_gripper": held},
                "slot": {"centre_xyz_mm": [200.0, -90.0, 12.0]}}

    assert PRE_RELEASE_TILT_DEG == 1.0 and PRE_RELEASE_XY_MM == 1.0
    # v2n seed 0 pre-release: flat, underside 0.02 mm above the pocket top -> the rule does not fire
    assert rule_fires(scene([200.9, -91.0, 22.02], [0.03, 0.0, -90.0], held=True))[0] is False
    # v2 seed 9 pre-release: tilted 3.68 deg, underside 11.74 mm, 1.72 mm off -> both clauses fire
    fires, why = rule_fires(scene([201.0, -91.4, 21.74], [3.68, 0.0, 0.0], held=True))
    assert fires and why["tilted"] and why["low_and_off_centre"]
    # tilted alone, well above the pocket
    fires, why = rule_fires(scene([200.0, -90.0, 30.0], [3.68, 0.0, 0.0], held=True))
    assert fires and why["tilted"] and not why["low_and_off_centre"]
    # flat, pressed to the pocket top, 1.5 mm off centre -> fires on the height/xy clause
    fires, why = rule_fires(scene([201.5, -90.0, 22.0], [0.0, 0.0, 0.0], held=True))
    assert fires and why["low_and_off_centre"] and not why["tilted"]
    # the same but centred within 1 mm -> does not fire
    assert rule_fires(scene([200.5, -90.0, 22.0], [0.0, 0.0, 0.0], held=True))[0] is False
    # logged jam pose: old rule and new rule both fail; seated pose: both pass; tilted inside 3 mm: only new fails
    jam = verifier_from_scene(scene(*JAM_POSES["zero-shot-v2-20261015-202023-05"]))
    assert jam["in_slot"] is False and jam["old_rule"] is False and jam["tilt_deg"] == 32.73
    seated = verifier_from_scene(scene([199.99, -89.86, 11.99], [0.0, 0.0, -0.84]))
    assert seated["in_slot"] is True and seated["old_rule"] is True
    leaning = verifier_from_scene(scene([200.0, -90.0, 12.0], [0.0, 6.0, 0.0]))
    assert leaning["old_rule"] is True and leaning["in_slot"] is False
