"""Arm error budget: predict how precisely the SO-101 can place its gripper,
before the real arm exists, so the real arm can prove the prediction wrong.

Method (standard precision-engineering error budget, done by Monte Carlo):
sample many poses in the work zone, perturb every joint by its error sources,
push the perturbed joints through the official kinematic model, and measure how
far the gripper moves. Each scenario is a different way of running the arm.

Error sources per joint:
- backlash: uniform +/- b. Approaching every pose from the same direction (as CNC
  machinists do) leaves only a small residual.
- encoder quantisation: uniform +/- half a count (STS3215: 4096 counts/rev).
- calibration zero offset: normal, sigma c. Kinematic calibration against a ChArUco
  board measures and removes most of it.
- vision: normal per horizontal axis, for targets located by camera.

Not modelled (measure on the real arm): gravity sag under load, link-length
errors, base flex, thermal drift.

Run: uv run python -m swayam.studies.error_budget
"""

from __future__ import annotations

import argparse
import json
import math

import numpy as np

from swayam import JOINTS, REPO_ROOT
from swayam.kinematics import Kinematics
from swayam.limits import load_limits

ENCODER_COUNTS = 4096
# backlash_deg: +/- per joint; 0.5 is the "backlash" class in the official sim model.
# calibration_sigma_deg and vision_sigma_mm are ASSUMPTIONS, to be replaced by
# measurements in Phase 0.
SCENARIOS = {
    "repeat_any_direction": {
        "what": "Return to the same pose, approaching from any direction",
        "backlash_deg": 0.5, "calibration_sigma_deg": 0.0, "vision_sigma_mm": 0.0,
    },
    "repeat_same_direction": {
        "what": "Return to the same pose, always approaching from the same direction",
        "backlash_deg": 0.05, "calibration_sigma_deg": 0.0, "vision_sigma_mm": 0.0,
    },
    "place_manual_calibration": {
        "what": "Land on a camera-located target; LeRobot manual calibration only",
        "backlash_deg": 0.5, "calibration_sigma_deg": 1.0, "vision_sigma_mm": 1.0,
    },
    "place_kinematic_calibration": {
        "what": "Land on a camera-located target; kinematic calibration + same-direction approach",
        "backlash_deg": 0.05, "calibration_sigma_deg": 0.2, "vision_sigma_mm": 1.0,
    },
}
# Where the cell's work happens: printer bed, trays and fixtures on the table.
WORK_ZONE = {"z_m": (0.01, 0.15), "reach_m": (0.12, 0.35), "azimuth_deg": (-60.0, 60.0)}
OUT_PATH = REPO_ROOT / "studies" / "out" / "arm_error_budget.json"


def sample_poses(kin: Kinematics, limits: dict, n: int, rng: np.random.Generator) -> list[dict]:
    poses: list[dict] = []
    for _ in range(500 * n):
        if len(poses) == n:
            break
        q = {
            j: rng.uniform(limits["joints"][j]["min"], limits["joints"][j]["max"])
            for j in JOINTS
        }
        x, y, z = kin.gripper_xyz(q)
        reach = math.hypot(x, y)
        azimuth = math.degrees(math.atan2(y, x))  # 0 = straight ahead of the base
        if (
            WORK_ZONE["azimuth_deg"][0] <= azimuth <= WORK_ZONE["azimuth_deg"][1]
            and WORK_ZONE["z_m"][0] <= z <= WORK_ZONE["z_m"][1]
            and WORK_ZONE["reach_m"][0] <= reach <= WORK_ZONE["reach_m"][1]
        ):
            poses.append(q)
    return poses


def pose_errors_mm(
    kin: Kinematics, q: dict, draws: int, rng: np.random.Generator, s: dict
) -> np.ndarray:
    half_count = 180.0 / ENCODER_COUNTS
    p0 = np.array(kin.gripper_xyz(q))
    out = np.empty(draws)
    for k in range(draws):
        dq = {
            j: q[j]
            + rng.uniform(-s["backlash_deg"], s["backlash_deg"])
            + rng.uniform(-half_count, half_count)
            + rng.normal(0.0, s["calibration_sigma_deg"])
            for j in JOINTS
        }
        err = np.array(kin.gripper_xyz(dq)) - p0
        err[:2] += rng.normal(0.0, s["vision_sigma_mm"] / 1000.0, size=2)
        out[k] = np.linalg.norm(err) * 1000.0
    return out


def joint_sensitivity_mm(kin: Kinematics, poses: list[dict], delta_deg: float) -> dict:
    """Mean gripper displacement (mm) when one joint alone is off by delta_deg."""
    out = {}
    for j in JOINTS:
        moves = [
            np.linalg.norm(
                np.array(kin.gripper_xyz({**q, j: q[j] + delta_deg}))
                - np.array(kin.gripper_xyz(q))
            ) * 1000.0
            for q in poses
        ]
        out[j] = round(float(np.mean(moves)), 2)
    return out


def summarise(per_pose_p95: list[float]) -> dict:
    a = np.array(per_pose_p95)
    worst = float(np.percentile(a, 95))
    return {
        "median_pose_p95_mm": round(float(np.median(a)), 2),
        "worst_5pct_pose_p95_mm": round(worst, 2),
        "max_pose_p95_mm": round(float(np.max(a)), 2),
        # design rule from CLAUDE.md: lead-ins capture >= 2x the arm's error
        "min_lead_in_mm": math.ceil(2 * worst * 2) / 2,
    }


def run(n_poses: int = 300, draws: int = 300, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    kin = Kinematics()
    poses = sample_poses(kin, load_limits(), n_poses, rng)
    results = {}
    for name, s in SCENARIOS.items():
        p95 = [float(np.percentile(pose_errors_mm(kin, q, draws, rng, s), 95)) for q in poses]
        results[name] = {**s, **summarise(p95)}
    return {
        "work_zone": WORK_ZONE,
        "encoder_counts": ENCODER_COUNTS,
        "n_poses": len(poses),
        "draws_per_pose": draws,
        "seed": seed,
        "scenarios": results,
        "joint_sensitivity_mm_per_1deg": joint_sensitivity_mm(kin, poses, 1.0),
    }


def protocol_poses(n: int = 5, seed: int = 2026, draws: int = 2000) -> list[dict]:
    """The fixed poses for the Phase 0 repeatability test, with per-pose predictions.
    Fixed seed: the poses must not be chosen after seeing the real arm."""
    rng = np.random.default_rng(seed)
    kin = Kinematics()
    out = []
    for q in sample_poses(kin, load_limits(), n, rng):
        row = {"joints_deg": {j: round(v, 1) for j, v in q.items()}}
        q = row["joints_deg"]
        row["gripper_xyz_mm"] = [round(v * 1000, 1) for v in kin.gripper_xyz(q)]
        for name in ("repeat_any_direction", "repeat_same_direction"):
            e = pose_errors_mm(kin, q, draws, rng, SCENARIOS[name])
            row[f"{name}_p95_mm"] = round(float(np.percentile(e, 95)), 2)
        out.append(row)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--poses", type=int, default=300)
    ap.add_argument("--draws", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--protocol", action="store_true", help="print the Phase 0 test poses")
    args = ap.parse_args()
    if args.protocol:
        print(json.dumps(protocol_poses(), indent=2))
        return
    result = run(args.poses, args.draws, args.seed)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    for name, r in result["scenarios"].items():
        print(f"{name:30s} median {r['median_pose_p95_mm']:6.2f} mm   "
              f"worst-5% {r['worst_5pct_pose_p95_mm']:6.2f} mm   lead-in >= {r['min_lead_in_mm']} mm")
    print("sensitivity mm per 1 deg:", result["joint_sensitivity_mm_per_1deg"])


if __name__ == "__main__":
    main()
