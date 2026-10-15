"""Pre-release abort signal: score it on logged releases, held out from the data it was
fitted on (predictions/2026-10-15-pre-release-tilt-signal.md).

The rule (fixed before the held-out run; constants below are not to be tuned):

    do not release while the held part is tilted > PRE_RELEASE_TILT_DEG, or while its
    underside is at or below the pocket top with > PRE_RELEASE_XY_MM of xy error.

A "release" is a logged `move` event whose grasp_event is "released". Its pre-release
state is the last scene the server logged before that move (the sim only steps on
commands, so that is the state at the moment of release). Its outcome is the verifier
rule (swayam.arm.sim.in_slot_rule, tilt- and height-aware) recomputed from the scene
logged with the tool call that performed the release (0.3 s of settling after the jaws
open). Hit = rule fired and the release did not seat; false alarm = rule fired and it
did seat. Every release in the named run tags is counted; none is dropped.

    uv run python -m swayam.experiments.pre_release_signal --train            # seeds 0-9 (fitted data)
    uv run python -m swayam.experiments.pre_release_signal --heldout          # v2-noise-heldout tags
    uv run python -m swayam.experiments.pre_release_signal --check-flips      # old vs new verifier on every logged state
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from swayam import REPO_ROOT
from swayam.arm.sim import CUBE_SIZE_MM, SLOT_REST_SPEED_M_S, SLOT_TOL_M, in_slot_rule
from swayam.runlog import runs_dir
from swayam.stats import wilson

PRE_RELEASE_TILT_DEG = 1.0
PRE_RELEASE_XY_MM = 1.0
TRAIN_FAMILIES = ("zero-shot-20261015-193207", "zero-shot-v2-20261015-202023", "zero-shot-v2n-20261015-221203")
HELDOUT_FAMILY = "zero-shot-v2nh"
REPORT = REPO_ROOT / "studies" / "out" / "pre_release_tilt_signal.md"
PREDICTION = "predictions/2026-10-15-pre-release-tilt-signal.md"


def tilt_from_rpy(rpy_deg) -> float:
    """Angle (deg) between the cube's most vertical face normal and world z (ZYX rpy)."""
    r, p = math.radians(rpy_deg[0]), math.radians(rpy_deg[1])
    best = max(abs(math.sin(p)), abs(math.cos(p) * math.sin(r)), abs(math.cos(p) * math.cos(r)))
    return math.degrees(math.acos(min(1.0, best)))


def verifier_from_scene(scene: dict) -> dict:
    """The current verifier rule applied to a logged scene (what cube_in_slot would say)."""
    c, s = scene["cube"], scene["slot"]["centre_xyz_mm"]
    dist = math.dist(c["xyz_mm"], s)
    tilt = tilt_from_rpy(c["rpy_deg"])
    dz = c["xyz_mm"][2] - s[2]
    old = dist <= SLOT_TOL_M * 1000 and c["speed_mm_s"] <= SLOT_REST_SPEED_M_S * 1000 and not c["held_by_gripper"]
    return {"in_slot": in_slot_rule(dist, c["speed_mm_s"], c["held_by_gripper"], tilt, dz),
            "old_rule": old, "distance_mm": round(dist, 2), "tilt_deg": round(tilt, 2),
            "height_error_mm": round(dz, 2)}


def rule_fires(scene: dict) -> tuple[bool, dict]:
    """Apply the pre-release rule to the held cube's logged scene."""
    c, s = scene["cube"], scene["slot"]["centre_xyz_mm"]
    tilt = tilt_from_rpy(c["rpy_deg"])
    xy = math.hypot(c["xyz_mm"][0] - s[0], c["xyz_mm"][1] - s[1])
    underside = c["xyz_mm"][2] - CUBE_SIZE_MM / 2
    pocket_top = s[2]  # the seated cube's centre sits level with the tray top
    tilted = tilt > PRE_RELEASE_TILT_DEG
    low_and_off = underside <= pocket_top and xy > PRE_RELEASE_XY_MM
    return tilted or low_and_off, {"tilt_deg": round(tilt, 2), "xy_error_mm": round(xy, 2),
                                   "underside_mm": round(underside, 2), "tilted": tilted,
                                   "low_and_off_centre": low_and_off}


def load_rows() -> list[dict]:
    rows = []
    for path in sorted(runs_dir().glob("*.jsonl")):
        for line in path.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _scene_of(row: dict) -> dict | None:
    if row.get("event") == "tool_call":
        return row.get("scene")
    if row.get("event") == "move":
        return (row.get("result") or {}).get("scene")
    return None


def releases(rows: list[dict], families: tuple[str, ...]) -> list[dict]:
    tags = sorted({r["run_tag"] for r in rows if r.get("run_tag", "").rsplit("-", 1)[0] in families})
    out = []
    for tag in tags:
        rs = [r for r in rows if r.get("run_tag") == tag]
        calls = [r for r in rs if r["event"] == "tool_call"]
        attempt_pass = bool(calls and verifier_from_scene(calls[-1]["scene"])["in_slot"])
        last = None
        for i, r in enumerate(rs):
            if r["event"] == "move" and (r.get("result") or {}).get("grasp_event") == "released":
                post = next((x for x in rs[i + 1:] if x["event"] == "tool_call"), None)
                if last is None or post is None or not last["cube"]["held_by_gripper"]:
                    out.append({"tag": tag, "t": r["t"], "unscorable": True})
                    continue
                fires, why = rule_fires(last)
                seated = verifier_from_scene(post["scene"])["in_slot"]
                out.append({"tag": tag, "t": r["t"], "fires": fires, "seated": seated, "pre": why,
                            "post": verifier_from_scene(post["scene"]), "attempt_pass": attempt_pass,
                            "unscorable": False})
            sc = _scene_of(r)
            if sc:
                last = sc
    return out


def score(rel: list[dict]) -> dict:
    ok = [r for r in rel if not r["unscorable"]]
    fail = [r for r in ok if not r["seated"]]
    seat = [r for r in ok if r["seated"]]
    hits = sum(r["fires"] for r in fail)
    fa = sum(r["fires"] for r in seat)
    return {"releases": len(rel), "unscorable": len(rel) - len(ok), "not_seated": len(fail), "seated": len(seat),
            "hits": hits, "misses": len(fail) - hits, "false_alarms": fa, "correct_rejections": len(seat) - fa,
            "hit_rate": wilson(hits, len(fail)), "false_alarm_rate": wilson(fa, len(seat)),
            "attempts": len({r["tag"] for r in rel}),
            "attempt_passes": len({r["tag"] for r in ok if r["attempt_pass"]})}


def check_flips(rows: list[dict], families: tuple[str, ...]) -> dict:
    """Old (distance/speed/held) vs new verifier on every logged state and every final state."""
    tags = sorted({r["run_tag"] for r in rows if r.get("run_tag", "").rsplit("-", 1)[0] in families})
    states = flips = 0
    finals = []
    for tag in tags:
        calls = [r for r in rows if r.get("run_tag") == tag and r["event"] == "tool_call"]
        for r in calls:
            v = verifier_from_scene(r["scene"])
            states += 1
            flips += v["in_slot"] != v["old_rule"]
            if r.get("verifier") and r["verifier"]["in_slot"] != v["old_rule"]:
                raise AssertionError(f"logged verifier disagrees with the old rule recomputed: {tag} {r['t']}")
        f = verifier_from_scene(calls[-1]["scene"])
        finals.append({"tag": tag, **f})
    passes = [f for f in finals if f["old_rule"]]
    return {"tags": len(tags), "logged_states": states, "states_flipped": flips,
            "final_passes_old": len(passes), "final_passes_new": sum(f["in_slot"] for f in finals),
            "pass_tilt_max_deg": max((f["tilt_deg"] for f in passes), default=None),
            "pass_height_error_max_mm": max((abs(f["height_error_mm"]) for f in passes), default=None),
            "finals": finals}


def _fmt(w):
    p, lo, hi = w
    return "n/a" if math.isnan(p) else f"{p:.0%} [{lo:.0%}, {hi:.0%}]"


def write_report(rows: list[dict]) -> Path:
    train = releases(rows, TRAIN_FAMILIES)
    held = releases(rows, (HELDOUT_FAMILY,))
    held = [r for r in held]
    st, sh = score(train), score(held)
    stamps = sorted({r["tag"].rsplit("-", 1)[0] for r in held})
    lines = [
        "# Pre-release abort signal, scored on held-out releases",
        "",
        f"Prediction: `{PREDICTION}` (committed before the held-out run; see git log).",
        f"Rule: do not release while the held part is tilted > {PRE_RELEASE_TILT_DEG:g} deg, or while its "
        f"underside (centre z - {CUBE_SIZE_MM / 2:g} mm) is at or below the pocket top (slot centre z) with "
        f"> {PRE_RELEASE_XY_MM:g} mm of xy error. Fitted on the seeds 0-9 runs of 2026-10-15; held-out data "
        f"= `{HELDOUT_FAMILY}` run tags (seeds 10-19, task v2 with 2 mm RMS placement noise, tilt- and "
        f"height-aware verifier): {', '.join(stamps) or 'none'}.",
        "",
        "Every number below is recomputed from `runs/*.jsonl` by `swayam.experiments.pre_release_signal`. "
        "Pre-release state = last server-logged scene before the `released` move; outcome = the current "
        "verifier rule on the scene logged with the releasing tool call. Hit = fired and not seated; false "
        "alarm = fired and seated.",
        "",
        "| Quantity | Fitted data (seeds 0-9, v1 + v2 + v2-noise) | **Held out (v2-noise, seeds 10-19)** |",
        "|---|---|---|",
        f"| Attempts (verifier passes) | {st['attempts']} ({st['attempt_passes']}) | {sh['attempts']} ({sh['attempt_passes']}) |",
        f"| Releases scored (unscorable) | {st['releases'] - st['unscorable']} ({st['unscorable']}) | {sh['releases'] - sh['unscorable']} ({sh['unscorable']}) |",
        f"| Releases that did not seat | {st['not_seated']} | {sh['not_seated']} |",
        f"| Hits / misses | {st['hits']} / {st['misses']} | **{sh['hits']} / {sh['misses']}** |",
        f"| Hit rate, Wilson 95% | {_fmt(st['hit_rate'])} | **{_fmt(sh['hit_rate'])}** |",
        f"| Releases that seated | {st['seated']} | {sh['seated']} |",
        f"| False alarms / correct rejections | {st['false_alarms']} / {st['correct_rejections']} | **{sh['false_alarms']} / {sh['correct_rejections']}** |",
        f"| False-alarm rate, Wilson 95% | {_fmt(st['false_alarm_rate'])} | **{_fmt(sh['false_alarm_rate'])}** |",
        "",
        "## Held-out releases",
        "",
        "| run tag | pre tilt (deg) | pre xy err (mm) | pre underside (mm) | fired on | post dist (mm) | post tilt (deg) | post height err (mm) | seated | attempt |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in held:
        if r["unscorable"]:
            lines.append(f"| {r['tag']} | unscorable (no held scene before the release) | | | | | | | | |")
            continue
        fired = ", ".join(k for k in ("tilted", "low_and_off_centre") if r["pre"][k]) or "-"
        lines.append(f"| {r['tag']} | {r['pre']['tilt_deg']} | {r['pre']['xy_error_mm']} | {r['pre']['underside_mm']} | "
                     f"{fired} | {r['post']['distance_mm']} | {r['post']['tilt_deg']} | {r['post']['height_error_mm']} | "
                     f"{'yes' if r['seated'] else 'NO'} | {'PASS' if r['attempt_pass'] else 'fail'} |")
    lines += ["", "## Fitted-data releases (for reference; these chose the thresholds)", "",
              "| run tag | pre tilt (deg) | pre xy err (mm) | pre underside (mm) | fired on | seated |",
              "|---|---|---|---|---|---|"]
    for r in train:
        if r["unscorable"]:
            continue
        fired = ", ".join(k for k in ("tilted", "low_and_off_centre") if r["pre"][k]) or "-"
        lines.append(f"| {r['tag']} | {r['pre']['tilt_deg']} | {r['pre']['xy_error_mm']} | {r['pre']['underside_mm']} | "
                     f"{fired} | {'yes' if r['seated'] else 'NO'} |")
    lines.append("")
    notes = REPORT.with_name("pre_release_tilt_signal_notes.md")
    audit = REPORT.with_name("pre_release_tilt_signal_audit.md")
    for path, title in ((notes, "Notes"), (audit, "Closure-auditor report (verbatim)")):
        if path.exists():
            lines += [f"## {title}", "", path.read_text().strip(), ""]
    REPORT.write_text("\n".join(lines))
    return REPORT


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--train", action="store_true")
    ap.add_argument("--heldout", action="store_true")
    ap.add_argument("--check-flips", action="store_true")
    ap.add_argument("--report", action="store_true", help="write studies/out/pre_release_tilt_signal.md")
    args = ap.parse_args()
    rows = load_rows()
    if args.check_flips:
        c = check_flips(rows, TRAIN_FAMILIES)
        for f in c.pop("finals"):
            print(f"  {f['tag']:>34}  old={f['old_rule']!s:5} new={f['in_slot']!s:5} dist={f['distance_mm']:5.2f} "
                  f"tilt={f['tilt_deg']:5.2f} dz={f['height_error_mm']:+.2f}")
        print(json.dumps(c, indent=1))
    for flag, fam in ((args.train, TRAIN_FAMILIES), (args.heldout, (HELDOUT_FAMILY,))):
        if flag:
            rel = releases(rows, fam)
            for r in rel:
                print(json.dumps(r, default=str))
            s = score(rel)
            print(json.dumps({k: v for k, v in s.items()}, default=str, indent=1))
    if args.report:
        print(write_report(rows))


if __name__ == "__main__":
    main()
