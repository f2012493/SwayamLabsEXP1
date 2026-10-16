# Fabrica and after: the state of CAD-to-assembly, and where we cut in

Written 2026-10-16. Fabrica (MIT CSAIL + Autodesk Research, CoRL 2025 best paper) is
the closest published system to Swayam's thesis. This is what it proves, what it
assumes, what has moved in the sixteen months since, and the seams nobody has closed.

## 1. What Fabrica is

**Pipeline** (CAD in, assembled object out): precedence planning → grasp sampling and
filtering → sequence and grasp optimisation → **automated pickup-fixture generation** →
motion planning → learned residual insertion policy (RL, SE(3)-equivariant) on top of
the planned path.

**Fixture generator** (the part we care most about): each part's pickup orientation is
its planned assembly grasp rotated to top-down, so no regrasp is needed; 2D footprints
are bin-packed (Maximal Rectangles) with an iterative loop that adds clearance where
the gripper would collide; each cavity is the part's projected outline extruded to a
depth that keeps the centre of mass supported, with **countersunk pads for alignment**.
Fixtures are exported as STL for printing. This is a funnel-and-nest generator, which
is exactly Toy 1.

**Results.** Seven assemblies of 5–9 parts (beam, plumber block, car, gamepad, cooling
manifold, duct, stool). Planning 3–10 minutes per assembly. Real-robot per-step success
80% (specialist and generalist alike). **Multi-step success with zero human
interventions: 15% specialist, 10% generalist**; 81% with one intervention. Failure
modes: small parts slipping in the gripper, cumulative error over many steps, the
holding gripper obstructing, unstabilised parts shifting earlier ones. The sim assumes
3 mm pose noise and the authors say real errors are often larger.

**Assumptions** (their list): insertion-only mating (no screws, no sliding); no
subassembly reorientation; monotonic (each part moves once, no regrasp or handover);
parts light relative to payload; finite grasp set; parts presented at known poses in
the generated fixture; two Franka Panda arms, parallel grippers, **no vision, no
force sensing**, joint encoders only.

**Released**: MIT licence; planner, RL (Isaac Gym Preview 4, now deprecated), simulator,
renderers, real-robot runner (frankapy) with optional VLM error recovery, benchmark
assets, STL export of parts and fixtures. Maintainers state limited bandwidth.
First author now at Amazon FAR.

## 2. What has moved since (2025 → October 2026)

**Insertion is becoming reliable on industrial arms.** NVIDIA SPARR (ICRA 2026):
sim-trained base policy + real-world residual learned from vision and sparse reward,
no human expertise, near-perfect two-part assembly, +38% success and −30% cycle time
over zero-shot sim-to-real. NVIDIA Refinery (ICRA 2026): Bayesian-optimisation
fine-tuning plus deployment-time initial-condition selection; chains policies to
assemble up to 8 parts without multi-step training. AlphaNIST (2026): one policy across
20 NIST Task Board #1 tasks in sim from binary rewards.

**Planning from CAD got faster and more tolerant.** Harlacher & Friedrich (Sept 2026):
learn part relations from imperfect CAD point clouds, geometric-symbolic planner,
85.8% on the ASAP test set, >50× faster for assemblies over 30 parts, human verifies
uncertain relations. Manual2Skill++ (2025–26): connector-aware plans from instruction
manuals via VLMs. VLM-MSGraph: sequences from drawings.

**Agents now do kernel-grounded CAD.** Embodied CAD (June 2026): an LLM agent builds
parametric B-rep *assemblies* through a layered skill library, every operation accepted
by an exact geometric kernel, trained with solver rewards. ArtiCAD, ASSEMCAD (2026)
generate CAD assemblies from language; OmniCAD benchmarks spatial reasoning on them.

**The verification loop exists for plans, not for parts.** IDfRA (ICRA 2026,
"Self-Verification for Iterative Design in Robotic Assembly"): LLM plans → robot
executes → VLM judges → replan; 86.9% construction success; no accurate world model
needed. It iterates the *plan*. The geometry stays fixed.

**The community has a gearbox benchmark.** RoCo Challenge at AAAI 2026: high-precision
**planetary gearbox assembly** (sun, three planets, ring), 60+ teams, step-wise scoring,
CAD, dataset and code released (per the challenge report; the resource URL has moved,
verify). Winners used a dual-model long-horizon framework; the key ingredient reported
was **recovery-from-failure curriculum data**. The IROS 2026 edition moved to an
industrial board (connectors, wire routing, screws, battery) and brick assembly;
$20k prize pool.

**VLAs reached furniture.** FurnitureVLA, A3D, BrickCraft-Duo (2026): long-horizon
bimanual assembly with learned policies; all on research-grade arms.

## 3. The seams: what no one has closed

1. **The design is always fixed.** Every system above takes the CAD as given. When
   Fabrica fails because a small part slips, the proposed fix is a better gripper or
   policy. Classical design-for-assembly says most assembly cost is decided at the
   drawing board. Nobody has an agent that answers a failed assembly step by **changing
   the part**: a lead-in, a snap-fit, a grasp feature, two parts merged into one, then
   re-plans and re-measures. Embodied CAD proves agents can edit kernel-valid CAD;
   IDfRA proves a physical verification loop; Fabrica proves the planner. The three have
   not been composed. That composition is design closure, and it is ours to build.
2. **The cost floor is a Franka.** Fabrica simulates 3 mm noise and calls real errors
   larger; our arm's budget is ~4 mm camera-guided and ~0.5 mm same-direction. Nobody has
   published what assembly looks like when designed around a 4 mm arm. Fabrica's own
   fixture generator is the right instrument: fixtures and funnels absorb arm error.
3. **Kitting is assumed.** Fabrica generates the pickup fixture, then a human loads it.
   We own the fabrication step, so the printer can **print the kit**: parts produced
   inside (or ejected into) their own pickup nest, one tray per assembly, no human
   placement. Nobody in this literature controls the printer.
4. **Second arm as holder.** In Fabrica the second Panda mostly holds the subassembly.
   A printed holding fixture generated by the same algorithm can hold. One-arm Fabrica
   with printed holders is an unclaimed, publishable reduction.
5. **Zero-intervention multi-step is 10–15%.** Reliability over many steps is the open
   problem, and interventions are human minutes: closure % is exactly the metric that
   captures it. Recovery-from-failure data (RoCo's lesson) is what our append-only logs
   already collect.

## 4. The play

**Now, before the arm arrives (software only):**
- **Run Fabrica's planner on the SO-101's own CAD.** We have the STEP files. The output
  is a precedence graph, grasps, generated fixtures, and, most valuable, the list of
  steps that violate Fabrica's assumptions (screws, cables, reorientation, parts too
  large for the jaws). That list *is* the Toy 4 redesign agenda, produced by the best
  planner in the field rather than by guesswork.
- Run it on the RoCo gearbox CAD too, so Toy 5 starts from a benchmark 60 teams used.
- Check which Fabrica stages run without a GPU (planner should; RL needs Isaac Gym).

**Toy 1 becomes "Fabrica's fixture generator, arm-aware."** Reuse the generator;
parameterise cavity clearance and funnel by our measured arm error; add print-the-kit
(part nested in its own fixture). Measure design iterations to 10/10 on Peg-in-Bench
and NIST sizes, then SO-101 parts.

**Toy 4 becomes the design-closure loop, explicitly composed from the three pieces:**
Fabrica planner (what fails and why) → engineer edits CAD as code, kernel-validated
(CadQuery/build123d; Embodied CAD's discipline) → print → execute → verifier judges
(IDfRA's loop, with sensors instead of a VLM where we can) → re-plan. Metric: design
iterations per week with no human CAD, and closure % on the subassembly.

**Toy 5 uses the RoCo gearbox** as the mechanism, printed in place where possible,
with SPARR-style residual learning only if fixtures and same-direction approach cannot
reach the tolerance. Our arm has no force sensor; motor current is the proxy, and
whether residual learning works without F/T is itself a result.

**Toy 7/8 target the number Fabrica could not move:** multi-step assembly with zero
interventions, reported beside Fabrica's 10–15%, on hardware two orders of magnitude
cheaper, with the design loop allowed to change the parts.

**Compete.** RoCo 2027 with the cheapest rig in the field, or replicate the 2026
gearbox task publicly with our closure numbers next to theirs.

## 5. What we take, what we leave

Take: Fabrica planner and fixture generator (MIT), its benchmark assemblies as test
cases, RoCo's CAD and data, SPARR/Refinery as the insertion recipe, Embodied CAD's
kernel-grounding discipline, IDfRA's loop structure, RoCo's recovery-data lesson.

Leave: Fabrica's RL stack (deprecated Isaac Gym; use Isaac Lab or LeRobot if needed),
dual-arm assumptions, the no-vision assumption (we have AprilTags), and the fixed-CAD
assumption, which is the point.

## Sources

- Fabrica: [paper](https://arxiv.org/html/2506.05168v1), [code (MIT)](https://github.com/yunshengtian/Fabrica), [project page](https://fabrica.csail.mit.edu), [Autodesk post](https://www.research.autodesk.com/blog/from-cad-to-robotic-assembly/), [OpenReview](https://openreview.net/forum?id=aSUNzvEJIf); predecessors [ASAP](https://arxiv.org/pdf/2309.16909), [Assemble Them All](https://dl.acm.org/doi/10.1145/3550454.3555525)
- Insertion 2026: [SPARR](https://arxiv.org/html/2602.23253) ([NVIDIA page](https://research.nvidia.com/labs/srl/projects/sparr/)), [Refinery](https://arxiv.org/html/2510.11019v1), [AlphaNIST](https://arxiv.org/html/2610.13354)
- Planning from CAD/manuals: [Harlacher & Friedrich 2026](https://arxiv.org/pdf/2609.17263), [Manual2Skill++](https://arxiv.org/pdf/2510.16344), [VLM-MSGraph](https://www.researchgate.net/publication/389260823_VLM-MSGraph_Vision_Language_Model-enabled_Multi-hierarchical_Scene_Graph_for_robotic_assembly), [AssemMate](https://arxiv.org/abs/2509.11617)
- Agents and CAD: [Embodied CAD](https://arxiv.org/abs/2606.31252), [ArtiCAD](https://arxiv.org/pdf/2604.10992), [ASSEMCAD](https://arxiv.org/pdf/2607.05123), [OmniCAD](https://www.alphaxiv.org/abs/2608.22637)
- Design loop: [IDfRA](https://arxiv.org/abs/2509.16998)
- Benchmarks and VLAs: [RoCo Challenge AAAI 2026 report](https://arxiv.org/pdf/2603.15469), [RoCo IROS 2026](https://rocochallenge.github.io/RoCo-IROS2026/), [FurnitureVLA](https://arxiv.org/pdf/2607.01212), [A3D](https://arxiv.org/pdf/2601.11076), [BrickCraft-Duo](https://arxiv.org/pdf/2609.28281)
- Autodesk Research robotics: [ARCH and skateboard truck](https://www.research.autodesk.com/research-areas/science/robotics/)
