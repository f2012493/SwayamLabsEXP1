from swayam import mcp_server
from swayam.limits import load_limits
from swayam.motion import approach_waypoints

LIMITS = load_limits()
HERE = {"shoulder_pan": 0, "shoulder_lift": 0, "elbow_flex": 0, "wrist_flex": 0, "wrist_roll": 0}


def test_move_in_approach_direction_is_direct():
    assert approach_waypoints(HERE, {"shoulder_pan": 10}, LIMITS) == [{"shoulder_pan": 10}]


def test_move_against_direction_overshoots_then_returns():
    wps = approach_waypoints(HERE, {"shoulder_pan": -10, "elbow_flex": 5}, LIMITS)
    overshoot = LIMITS["approach"]["overshoot_deg"]
    assert wps == [{"shoulder_pan": -10 - overshoot, "elbow_flex": 5},
                   {"shoulder_pan": -10, "elbow_flex": 5}]


def test_overshoot_never_leaves_joint_range():
    lo = LIMITS["joints"]["wrist_flex"]["min"]
    wps = approach_waypoints(HERE, {"wrist_flex": lo + 1}, LIMITS)
    assert wps[0]["wrist_flex"] >= lo


def test_travel_splits_long_moves_and_arrives():
    from swayam.controller import Controller
    ctl = Controller("sim")
    r = ctl.travel({"wrist_roll": 130, "shoulder_pan": -58})
    assert r["ok"], r
    pos = ctl.positions()
    assert abs(pos["wrist_roll"] - 130) < 1.5 and abs(pos["shoulder_pan"] + 58) < 1.5
    assert ctl.home()["ok"]


def test_server_uses_same_direction_by_default_in_sim():
    r = mcp_server.move_joints({"shoulder_pan": -15}, 1.0)
    assert r["ok"] and r["waypoints"] == 2
    assert abs(r["positions"]["shoulder_pan"] + 15) < 1.0
    r = mcp_server.move_joints({"shoulder_pan": -20}, 1.0, same_direction=False)
    assert r["ok"] and r["waypoints"] == 1
