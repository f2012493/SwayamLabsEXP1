- Plumbing runs before the 10 attempts, excluded from the denominator because they did not run the
  instruction: `smoke-3` (MCP client check: get_scene, one move, verifier; cube never moved) and
  `zero-shot-rehearsal-99` (a hook-block test with a different prompt, 3 calls, $0.21). Both logged
  to scratch directories, not `runs/`.
- The harness report generator was extended after the data existed (the `releases`, `first release
  passed`, `cube disturbed after pass` columns, the decision-rule section and the audit section); the
  success, tool-call and moved-after-pass logic is unchanged, and every number is recomputed from
  `runs/` on each regeneration.
- Cost: mean $0.76 per attempt, median $0.61. Attempt 0 took 140 s before its first arm command
  (cold start); the others 10-18 s.
- Sim artefacts seen in attempt 2: the soft weld let a held cube tilt 39-47 deg while pressed into the
  funnel, and a cube wedged in the funnel at 34 deg tilt was "grasped" from 12.6 mm with the jaws only
  40 % open. The weld rule checks only closure < 20 % and distance <= 15 mm, never jaw opening or
  geometry. Both first-placement recoveries relied on this. A harder sim version should require the
  jaws to be open wider than the part and the part to lie between them.
- What this does not show: grasping, perception error, backlash, kinematic error. The verifier is
  simulator ground truth, not an independent instrument. 10/10 here says nothing about the hardware
  success rate; it says the tools and the stop-on-verifier loop work.
