#!/usr/bin/env python3
"""Independent safety check on arm commands, run by Claude Code before the tool call.

Deliberately separate from the arm server's own checks and stdlib-only (runs on the
system python3), so one bug cannot disable both. Checks absolute joint ranges and
move duration; the server additionally checks step size, speed and workspace.
Exit code 2 blocks the call and shows the reason to Claude.
"""

import json
import os
import sys

ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def main():
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    args = event.get("tool_input", {}) or {}
    with open(os.path.join(ROOT, "config", "limits.json")) as f:
        limits = json.load(f)

    if tool.endswith("__move_joints"):
        targets = args.get("targets", {}) or {}
    elif tool.endswith("__set_gripper"):
        targets = {"gripper": args.get("percent_open")}
    else:
        return 0

    problems = []
    for name, value in targets.items():
        rng = limits["gripper"] if name == "gripper" else limits["joints"].get(name)
        if rng is None:
            problems.append("unknown joint '%s'" % name)
        elif not isinstance(value, (int, float)):
            problems.append("%s has non-numeric target %r" % (name, value))
        elif not rng["min"] <= value <= rng["max"]:
            problems.append("%s=%s outside [%s, %s]" % (name, value, rng["min"], rng["max"]))

    duration = args.get("duration_s")
    if duration is not None and duration < limits["min_duration_s"]:
        problems.append("duration_s %s below min %s" % (duration, limits["min_duration_s"]))

    if problems:
        sys.stderr.write("Blocked by safety hook: " + "; ".join(problems) + "\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
