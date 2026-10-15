"""Same-direction approach: finish every joint move travelling the same way.

Gear backlash makes a joint stop in a slightly different place depending on which
way it arrived. CNC machinists cancel this by always approaching a position from
one side. The error-budget study (studies/out/arm_error_budget.json) predicts this
improves SO-101 repeatability about 7x (3.9 mm -> 0.5 mm, typical pose).

A joint that must arrive from the "wrong" side first overshoots past the target by
`overshoot_deg`, then comes back. Which side is best per joint (e.g. with or against
gravity) is a Phase 0 experiment; it is configured in config/limits.json.
"""

from __future__ import annotations

from swayam import JOINTS


def approach_waypoints(
    current: dict[str, float], targets: dict[str, float], limits: dict
) -> list[dict[str, float]]:
    """Split a move into 1 or 2 waypoints so every joint ends travelling in its
    configured approach direction (+1 or -1)."""
    cfg = limits["approach"]
    pre: dict[str, float] = {}
    for j, v in targets.items():
        if j not in JOINTS or j not in current:
            continue
        direction = cfg["direction"][j]
        if (v - current[j]) * direction >= 0:
            continue  # already arriving the right way
        rng = limits["joints"][j]
        staging = v - direction * cfg["overshoot_deg"]
        staging = min(max(staging, rng["min"]), rng["max"])
        if staging != v:
            pre[j] = staging
    if not pre:
        return [dict(targets)]
    return [{**targets, **pre}, dict(targets)]
