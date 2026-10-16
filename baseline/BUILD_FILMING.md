# Filming the SO-101 build (the human baseline)

Your arm arrives as a kit. Building it yourself is the most valuable measurement
Swayam Labs will ever make cheaply: it is the **closure denominator** — every human
minute the lab later removes is counted against this recording. You only get one
first build, so record it.

## Setup (10 minutes, before opening the box)

1. Phone on a tripod or overhead mount, looking straight down at the workspace.
   Landscape, 1080p, enough storage for 3–5 hours.
2. Lay out a clean, well-lit surface. Put a ruler in frame for scale.
3. Start recording before you open the box. Do not stop between steps; one
   continuous video makes timing honest.
4. Keep `build_log.csv` open on a laptop next to you.

## While building

- Say each step name out loud as you start it ("step 12, wrist servo into holder").
  The audio makes timestamps easy to find later.
- In `build_log.csv`, add one row per step. Fill in at least `step`, `start`,
  `end` (wall-clock is fine) and `action`. Fill the rest afterwards from the video.
- Do not speed up or tidy up for the camera. Fumbles, dropped screws and re-dos
  are data: they show where a robot will struggle too.

## Afterwards (Claude can help with this part)

Fill the remaining columns per step:

- `operation`: one of the ladder operations — harvest, place, insert (peg-in-hole),
  snap/press, embed, connector, cable-route, screw, solder, calibrate, other.
- `tolerance_mm`: roughly how precise the step needed to be.
- `force`: low / medium / high.
- `vitamin`: yes if a bought part (servo, screw, board, cable) is handled.
- `robot_feasible_now`: yes / with-fixture / with-redesign / no — a first guess,
  revised once Phase 0 measures the arm's real error.

Total minutes = the baseline. Claude turns this into the step graph in
`ROADMAP.md` Toy 0.
