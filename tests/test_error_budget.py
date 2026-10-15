from swayam.studies.error_budget import run


def test_error_budget_orders_scenarios_sensibly():
    r = run(n_poses=20, draws=60, seed=3)["scenarios"]
    assert r["repeat_same_direction"]["median_pose_p95_mm"] < r["repeat_any_direction"]["median_pose_p95_mm"]
    assert r["place_kinematic_calibration"]["median_pose_p95_mm"] < r["place_manual_calibration"]["median_pose_p95_mm"]
    for s in r.values():
        assert 0.05 < s["median_pose_p95_mm"] < 50
