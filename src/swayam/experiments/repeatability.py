"""Repeatability protocol from predictions/2026-10-15-arm-repeatability.md.

Runs the same way on the simulator (rehearsal) and the real arm (the measurement):

    uv run python -m swayam.experiments.repeatability --backend sim --returns 3
    SWAYAM_PORT=/dev/tty.usbmodemXXXX uv run python -m swayam.experiments.repeatability \
        --backend real --returns 50 --axis x

For each of the five fixed poses and each approach mode (any direction / same
direction), the arm goes to a random nearby staging pose, then returns to the target.
After each return the gripper position is recorded:
  - sim: the simulator's own gripper position (validates the procedure; the sim has
    no backlash, so the numbers mean nothing about the real arm)
  - real: you type the dial-indicator reading in mm (one axis per run; --axis names it)

Every return is logged through the Controller to runs/ (append-only). The summary
applies the pre-registered decision rule. Do not edit the prediction after running.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np

from swayam import JOINTS
from swayam.controller import Controller
from swayam.runlog import runs_dir
from swayam.studies.error_budget import protocol_poses

PREDICTION = "predictions/2026-10-15-arm-repeatability.md"
MODES = {"any": False, "same": True}


def staging_pose(target: dict, ctl: Controller, rng: np.random.Generator) -> dict:
    """A random pose 5-20 deg away on every joint, inside limits and workspace."""
    for _ in range(200):
        cand = {}
        for j in JOINTS:
            off = rng.uniform(5, 20) * rng.choice([-1, 1])
            rng_j = ctl.limits["joints"][j]
            cand[j] = float(min(max(target[j] + off, rng_j["min"]), rng_j["max"]))
        # the arm leaves from the target pose, so check the move from there
        _, _, problems = ctl.check(cand, 2.0, same_direction=False, from_pose=target)
        if not problems:
            return cand
    raise RuntimeError(f"no safe staging pose near {target}")


def read_measurement(ctl: Controller, backend: str, axis: str) -> dict:
    if backend == "sim":
        x, y, z = ctl.telemetry()["gripper_xyz_m"]
        return {"x_mm": x * 1000, "y_mm": y * 1000, "z_mm": z * 1000}
    while True:
        raw = input(f"  dial indicator {axis} (mm, or 'r' to redo this return): ").strip()
        if raw.lower() == "r":
            return {"redo": True}
        try:
            return {f"{axis}_mm": float(raw)}
        except ValueError:
            print("  enter a number")


def p95_spread(rows: list[dict], keys: list[str]) -> float:
    """3D 95th-percentile distance from the mean position (root-sum-square over axes)."""
    per_axis = []
    for k in keys:
        v = np.array([r[k] for r in rows if k in r])
        if len(v):
            per_axis.append(np.percentile(np.abs(v - v.mean()), 95))
    return float(np.sqrt(np.sum(np.square(per_axis)))) if per_axis else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--backend", choices=["sim", "real"], default="sim")
    ap.add_argument("--returns", type=int, default=50)
    ap.add_argument("--axis", choices=["x", "y", "z"], default="x",
                    help="real only: which axis the dial indicator measures this run")
    ap.add_argument("--poses", type=str, default="1,2,3,4,5")
    ap.add_argument("--seed", type=int, default=17)
    args = ap.parse_args()

    ctl = Controller(args.backend)
    rng = np.random.default_rng(args.seed)
    poses = protocol_poses()
    chosen = [int(i) for i in args.poses.split(",")]
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = runs_dir() / f"repeatability-{args.backend}-{args.axis}-{stamp}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["pose", "mode", "i", "staging", "x_mm", "y_mm", "z_mm", "max_error_deg", "t"]
    rows: list[dict] = []

    print(f"Protocol: {PREDICTION}\nBackend: {args.backend}  returns/block: {args.returns}  -> {out}")
    if not ctl.home(3.0)["ok"]:
        raise SystemExit("could not reach home pose; check limits and clearance")

    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for idx in chosen:
            target = poses[idx - 1]["joints_deg"]
            print(f"\nPose {idx}: {target}")
            arrive = ctl.travel(target, tool="repeatability", pose=idx, leg="travel")
            if not arrive["ok"]:
                print("  cannot reach pose:", arrive.get("refused") or arrive.get("aborted"))
                continue
            for mode, same in MODES.items():
                print(f" mode={mode}")
                i = 0
                while i < args.returns:
                    stg = staging_pose(target, ctl, rng)
                    r1 = ctl.move(stg, 2.0, same_direction=False, tool="repeatability",
                                  pose=idx, mode=mode, i=i, leg="staging")
                    r2 = ctl.move(target, 2.0, same_direction=same, tool="repeatability",
                                  pose=idx, mode=mode, i=i, leg="return")
                    if not (r1["ok"] and r2["ok"]):
                        print("  refused/aborted:", r1.get("refused") or r1.get("aborted"),
                              r2.get("refused") or r2.get("aborted"))
                        i += 1
                        continue
                    time.sleep(0.3)
                    m = read_measurement(ctl, args.backend, args.axis)
                    if m.get("redo"):
                        continue
                    row = {"pose": idx, "mode": mode, "i": i, "staging": json.dumps(stg),
                           "max_error_deg": round(r2["max_error_deg"], 3), "t": time.time(), **m}
                    rows.append(row)
                    w.writerow(row)
                    f.flush()
                    i += 1

    ctl.home(3.0)
    print("\n== Summary (per pose: 95th percentile distance from mean, mm)")
    keys = ["x_mm", "y_mm", "z_mm"] if args.backend == "sim" else [f"{args.axis}_mm"]
    summary = {}
    for mode in MODES:
        vals = []
        for idx in chosen:
            sub = [r for r in rows if r["pose"] == idx and r["mode"] == mode]
            p = p95_spread(sub, keys)
            vals.append(p)
            pred = poses[idx - 1][f"repeat_{'any' if mode == 'any' else 'same'}_direction_p95_mm"]
            print(f"  pose {idx} {mode:4s}: measured {p:6.2f}   predicted {pred:5.2f}")
        summary[mode] = float(np.median(vals))
    ratio = f"{summary['any'] / summary['same']:.1f}x" if summary["same"] > 0.01 else "n/a"
    print(f"  median over poses: any={summary['any']:.2f} mm  same={summary['same']:.2f} mm  ratio={ratio}")
    if args.backend == "real" and len(keys) == 1:
        print("  NOTE: single-axis run. Combine x, y, z runs as root-sum-square before applying "
              "the decision rule (any: 1.9-7.4 mm, same: 0.25-1.0 mm, ratio >= 3x).")
    if args.backend == "sim":
        print("  NOTE: simulator has no backlash; this run only validates the procedure.")


if __name__ == "__main__":
    main()
