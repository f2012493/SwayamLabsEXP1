"""Capture map of the kit-tray funnel, task v1 (8 mm) vs v2 (4 mm): drop a flat cube
from just above the funnel mouth at a grid of xy offsets and yaws and record whether
the verifier passes. Pure scene characterisation (no arm, no LLM); it feeds the v2
prediction and the get_scene docstring's "within ~N mm" claim.

    uv run python -m swayam.studies.funnel_capture      # writes studies/out/funnel_capture.md
"""

from __future__ import annotations

import math

import mujoco
import numpy as np

from swayam import REPO_ROOT
from swayam.arm.sim import CUBE_SIZE_MM, FUNNEL, SimArm

OUT = REPO_ROOT / "studies" / "out" / "funnel_capture.md"
OFFSETS_MM = (0, 2, 4, 6, 8, 10)
YAWS_DEG = (0, 5, 10, 15, 20, 30)
DROP_ABOVE_MOUTH_MM = 1.0  # cube bottom face this far above the funnel mouth


def drop(arm: SimArm, dx_mm: float, dy_mm: float, yaw_deg: float, settle_s: float = 2.0) -> dict:
    """Place the cube still and flat above the slot, let it fall, return the verifier."""
    slot = arm.data.site_xpos[arm._slot_site]
    top = FUNNEL[arm.task_version]["funnel_top_z_mm"] / 1000
    q = arm._cube_q
    yaw = math.radians(yaw_deg)
    arm.data.qpos[q:q + 3] = [slot[0] + dx_mm / 1000, slot[1] + dy_mm / 1000,
                              top + DROP_ABOVE_MOUTH_MM / 1000 + CUBE_SIZE_MM / 2000]
    arm.data.qpos[q + 3:q + 7] = [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]
    arm.data.qvel[arm._cube_v:arm._cube_v + 6] = 0
    mujoco.mj_forward(arm.model, arm.data)
    arm._settle(settle_s)
    v = arm.cube_in_slot()
    v["tilt_deg"] = round(arm.cube_tilt_deg(), 1)
    return v


def capture_map(version: int) -> dict[tuple[float, float], dict]:
    arm = SimArm(scene="task", cube_seed=0, task_version=version)
    # park the arm away from the tray so nothing touches the cube
    arm.move({"shoulder_pan": 60}, 1.0)
    out = {}
    for off in OFFSETS_MM:
        for yaw in YAWS_DEG:
            out[(off, yaw)] = drop(arm, off / math.sqrt(2), off / math.sqrt(2), yaw)
    return out


def main() -> None:
    lines = ["# Funnel capture map (sim, flat cube dropped from 1 mm above the funnel mouth)", "",
             "Offset is radial along the slot's xy diagonal (dx = dy = offset / sqrt 2). Cell = verifier "
             "result after 2 s; `seat` = in_slot true; otherwise the final tilt in degrees and distance to "
             "the slot centre in mm. Pure scene characterisation, no arm involved.", ""]
    summary = {}
    for version in (1, 2):
        m = capture_map(version)
        f = FUNNEL[version]
        lines += [f"## Task v{version}: outer funnel {f['outer_funnel_mm']:.0f} mm + 1.5 mm lead-in "
                  f"(mouth half-width {f['funnel_half_width_mm']} mm at z {f['funnel_top_z_mm']} mm)", "",
                  "| offset (mm) \\ yaw (deg) | " + " | ".join(str(y) for y in YAWS_DEG) + " |",
                  "|---|" + "---|" * len(YAWS_DEG)]
        for off in OFFSETS_MM:
            cells = []
            for yaw in YAWS_DEG:
                v = m[(off, yaw)]
                cells.append("seat" if v["in_slot"] else f"tilt {v['tilt_deg']:.0f}, d {v['distance_mm']:.0f}")
            lines.append(f"| {off} | " + " | ".join(cells) + " |")
        seats = sum(v["in_slot"] for v in m.values())
        max_off = max((o for (o, y), v in m.items() if y == 0 and v["in_slot"]), default=None)
        max_yaw = max((y for (o, y), v in m.items() if o == 0 and v["in_slot"]), default=None)
        summary[version] = (seats, len(m), max_off, max_yaw)
        lines += ["", f"Seated {seats}/{len(m)} cells; largest seated offset at yaw 0: {max_off} mm; "
                  f"largest seated yaw at offset 0: {max_yaw} deg.", ""]
    OUT.write_text("\n".join(lines))
    print(OUT)
    for v, (s, n, mo, my) in summary.items():
        print(f"v{v}: seated {s}/{n}, max offset {mo} mm, max yaw {my} deg")


if __name__ == "__main__":
    main()
