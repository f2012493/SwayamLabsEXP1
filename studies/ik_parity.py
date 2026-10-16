"""Parity study: LeRobot placo kinematics vs our MuJoCo FK and our hand-written IK.

Run: uv run python studies/ik_parity.py   (writes studies/out/ik_parity.md)

200 poses are drawn by rejection sampling joint space (inside config/limits.json) until the
TCP lies in the work zone below, so every target is reachable by construction. MuJoCo
(`swayam.kinematics.Kinematics`'s model, gripperframe site) is the reference for every error:
neither solver is graded by its own forward model.

The pre-swap IK (src/swayam/ik.py, deleted in the commit that adds this study) is loaded from
git so the comparison stays reproducible.
"""

from __future__ import annotations

import math
import statistics
import subprocess
import sys
import time
import types

import mujoco
import numpy as np

from swayam import JOINTS, REPO_ROOT
from swayam.kinematics import GRIPPER_SITE, TCP_OFFSET_M, TcpKinematics, Unreachable, load_model, site_to_urdf
from swayam.limits import load_limits

OLD_IK_COMMIT = "3363f1e"  # last commit that has src/swayam/ik.py
N = 200
SEED = 7
# Work zone for the TCP (mm, arm base frame) and approach pitch (deg): where pick-and-place happens.
ZONE = {"x": (150, 320), "y": (-130, 130), "z": (10, 160), "pitch": (-90, 5)}
Q5 = JOINTS


def load_old_ik():
    src = subprocess.run(["git", "show", f"{OLD_IK_COMMIT}:src/swayam/ik.py"], cwd=REPO_ROOT,
                         capture_output=True, text=True, check=True).stdout
    mod = types.ModuleType("old_ik")
    exec(compile(src, "old_ik.py", "exec"), mod.__dict__)
    return mod


class Ref:
    """MuJoCo reference: TCP position (mm), approach axis and pitch from joint angles (deg)."""

    def __init__(self):
        self.model = load_model()
        self.data = mujoco.MjData(self.model)
        self.site = self.model.site(GRIPPER_SITE).id
        self.adr = {j: int(self.model.jnt_qposadr[self.model.joint(j).id]) for j in JOINTS}

    def pose(self, q: dict, offset=TCP_OFFSET_M):
        for j in JOINTS:
            self.data.qpos[self.adr[j]] = math.radians(q.get(j, 0.0))
        mujoco.mj_kinematics(self.model, self.data)
        R = self.data.site_xmat[self.site].reshape(3, 3).copy()
        site = self.data.site_xpos[self.site].copy()
        p = site + R @ np.asarray(offset)
        pan = math.radians(q["shoulder_pan"])
        h = np.array([math.cos(pan), -math.sin(pan), 0.0])
        pitch = math.degrees(math.atan2(R[2, 0], float(R[:, 0] @ h)))
        return site * 1000, p * 1000, R, pitch


def sample(ref: Ref, limits: dict, rng) -> list[dict]:
    out = []
    while len(out) < N:
        q = {j: float(rng.uniform(limits["joints"][j]["min"], limits["joints"][j]["max"])) for j in JOINTS}
        q["wrist_roll"] = float(rng.uniform(-90, 90))
        _, tcp, _, pitch = ref.pose(q)
        ok = (ZONE["x"][0] <= tcp[0] <= ZONE["x"][1] and ZONE["y"][0] <= tcp[1] <= ZONE["y"][1]
              and ZONE["z"][0] <= tcp[2] <= ZONE["z"][1] and ZONE["pitch"][0] <= pitch <= ZONE["pitch"][1])
        if ok:
            out.append(q)
    return out


def stats(v):
    v = np.asarray(v, dtype=float)
    return f"mean {v.mean():.3f} / p95 {np.percentile(v, 95):.3f} / max {v.max():.3f}"


def within(limits, q, tol=1e-6):
    return all(limits["joints"][j]["min"] - tol <= q[j] <= limits["joints"][j]["max"] + tol for j in JOINTS)


def main() -> None:
    limits = load_limits()
    rng = np.random.default_rng(SEED)
    ref = Ref()
    new = TcpKinematics(limits=limits)
    old_mod = load_old_ik()
    old = old_mod.IK(limits=limits)
    qs = sample(ref, limits, rng)

    # ---- FK parity -------------------------------------------------------------------
    d_site, d_tcp, d_axis, d_pitch = [], [], [], []
    for q in qs:
        site, tcp, R, pitch = ref.pose(q)
        T = new.frame_pose(q)
        d_site.append(np.linalg.norm(T[:3, 3] * 1000 - site))
        pl = new.tcp_pose(q)
        d_tcp.append(np.linalg.norm(np.array(pl["xyz_mm"]) - tcp))
        # axis mapping: site x (approach) = URDF z, site z (jaw) = -URDF x, site y = URDF y
        Rm = np.column_stack([T[:3, 2], T[:3, 1], -T[:3, 0]])
        d_axis.append(math.degrees(math.acos(np.clip((np.trace(Rm.T @ R) - 1) / 2, -1, 1))))
        d_pitch.append(abs(pl["pitch_deg"] - pitch))
    check = site_to_urdf((0, 0, 1))  # documented mapping, asserted so the study fails if it drifts
    assert np.allclose(check, [-1, 0, 0])

    # ---- IK parity -------------------------------------------------------------------
    # Two seed policies: "home" (pan 0, all other joints 0) and "previous" (the joints of another
    # random pose, like a caller moving between targets). wrist_roll is held at the target's roll.
    def run(seed_for):
        rows = {"placo": dict(pos=[], pitch=[], t=[], ok=0, lim=0), "ours": dict(pos=[], pitch=[], t=[], ok=0, lim=0)}
        for i, q in enumerate(qs):
            _, tcp, _, pitch = ref.pose(q)
            seed = seed_for(i, q)
            for name, solver in (("placo", new), ("ours", old)):
                r = rows[name]
                t0 = time.perf_counter()
                try:
                    sol = solver.solve(tcp / 1000, pitch, seed_deg=seed)
                except (Unreachable, ValueError):
                    r["t"].append(time.perf_counter() - t0)
                    continue
                r["t"].append(time.perf_counter() - t0)
                _, p2, _, pitch2 = ref.pose(sol)
                r["pos"].append(float(np.linalg.norm(p2 - tcp)))
                r["pitch"].append(abs(pitch2 - pitch))
                r["ok"] += 1
                r["lim"] += within(limits, sol)
        return rows

    def home_seed(i, q):
        return {"wrist_roll": q["wrist_roll"]}

    def previous_seed(i, q):
        return {**qs[(i + 1) % N], "wrist_roll": q["wrist_roll"]}

    runs = {"home": run(home_seed), "previous": run(previous_seed)}

    def line(label, name, rows):
        r = rows[name]
        ms = [t * 1000 for t in r["t"]]
        return (f"| {label} | {name} | {r['ok']}/{N} | {stats(r['pos']) if r['pos'] else 'n/a'} | "
                f"{stats(r['pitch']) if r['pitch'] else 'n/a'} | {r['lim']}/{r['ok']} | "
                f"{statistics.median(ms):.1f} / {np.percentile(ms, 95):.1f} / {max(ms):.1f} |")

    ik_rows = "\n".join(line(k, n, rows) for k, rows in runs.items() for n in ("placo", "ours"))

    md = f"""# IK parity: LeRobot placo vs MuJoCo FK and our damped-least-squares IK

Generated by `studies/ik_parity.py` (seed {SEED}, {N} poses). Reference for every error: MuJoCo
`gripperframe` site from `sim/so101/so101_new_calib.xml`, TCP = site + 11 mm along the jaw axis.
URDF: `sim/so101/so101_new_calib.urdf` (same upstream commit a758567 as the MuJoCo model).
Old IK = `src/swayam/ik.py` at {OLD_IK_COMMIT}, loaded from git.

Work zone (rejection-sampled from joint space inside `config/limits.json`, wrist_roll in +-90 deg, so every
target is reachable): TCP x {ZONE['x']} mm, y {ZONE['y']} mm, z {ZONE['z']} mm, pitch {ZONE['pitch']} deg.

## 1. Forward kinematics: placo (URDF `gripper_frame_link`) vs MuJoCo (`gripperframe`)

Frame mapping (documented in `src/swayam/kinematics.py`): site +x (approach) = URDF +z, site +y = URDF +y,
site +z (jaw axis) = URDF -x. Joint angles share degrees and zero.

| quantity | mean / p95 / max |
|---|---|
| frame origin distance (mm) | {stats(d_site)} |
| TCP distance (mm) | {stats(d_tcp)} |
| orientation difference after mapping (deg) | {stats(d_axis)} |
| pitch difference (deg) | {stats(d_pitch)} |

FK parity < 0.5 mm: **{'yes' if max(d_site) < 0.5 and max(d_tcp) < 0.5 else 'no'}** (max frame {max(d_site):.3f} mm, max TCP {max(d_tcp):.3f} mm).

## 2. Inverse kinematics, wrist_roll held, scored with MuJoCo FK

| seed | solver | solved | TCP error mm (mean / p95 / max) | pitch error deg (mean / p95 / max) | joints inside limits | solve ms (median / p95 / max) |
|---|---|---|---|---|---|---|
{ik_rows}

Seeds: `home` = all joints 0; `previous` = joints of another random pose. Tolerance both solvers use to accept a solution: 0.5 mm, 0.5 deg.
"""
    out = REPO_ROOT / "studies" / "out" / "ik_parity.md"
    out.write_text(md)
    print(md)


if __name__ == "__main__":
    sys.exit(main())
