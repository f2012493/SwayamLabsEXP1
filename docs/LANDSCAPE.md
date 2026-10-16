# Landscape: what already exists, what we duplicated, what remains ours

Written 2026-10-16. Purpose: stop reinventing. Each layer the lab touches, with what is
already built, how it changes our plan, and an honest list of wheels we already remade.
Sources at the end. Companion to `docs/DIRECTION.md`.

## 1. The audit: wheels we already remade

| We built | Already exists | Decision |
|---|---|---|
| `src/swayam/ik.py` (151 lines, damped least squares) and `kinematics.py` | LeRobot `lerobot[kinematics]`: placo-based `RobotKinematics` with FK/IK, plus processor steps `InverseKinematicsEEToJoints`, `EEBoundsAndSafety`, `ForwardKinematicsJointsToEE` | **Swapped** (2026-10-16): `ik.py` deleted, `TcpKinematics` in `kinematics.py` wraps `RobotKinematics`; parity in `studies/out/ik_parity.md`. MuJoCo FK kept as the independent safety check. |
| Workspace bounds in `limits.py` / `check_gripper_pose` | LeRobot `EEBoundsAndSafety` | Keep ours as the independent second layer (that was the point), but feed it the same bounds. |
| `sim/so101/scene_task.xml` and the whole sim task line | LeIsaac (Lightwheel): SO-101 in Isaac Lab, teleop, data conversion to LeRobot format, GR00T fine-tune path; official LeRobot EnvHub playground since Nov 2025 | **Frozen** already. If a sim is ever needed again, use LeIsaac. |
| MCP arm server | `IliaLarchenko/robot_MCP` (SO-ARM100/101, Apache-2.0, ~86 stars) and `phospho-mcp-server` (triggers learned behaviours via phosphobot REST) | **Keep ours.** Neither has safety limits, logging, or same-direction approach; ours does. But adopt their lesson: expose *learned behaviours* as tools too (phospho's model), not only joint moves. |
| Zero-shot harness, metrics | AA-Robotics (frontier-model harnesses), VLA-REPLICA (low-cost reproducible cross-lab VLA benchmark, 2026) | Keep the harness; adopt VLA-REPLICA's reproducibility protocol for Toy 6. |
| Hand-eye calibration plan (ChArUco) | OpenCV `calibrateHandEye`; VLA-REPLICA ships an AprilTag camera-pose script; IROS'17 method for calibrating from AprilTags during joint sweeps | Use OpenCV + the VLA-REPLICA script; do not write a calibrator. |

Net: about 200 lines and two days of sim work were duplication. The server, the safety
design, the error budget, the pre-registration discipline and the auditor were not.

## 2. Layer by layer: already built, use it

### Agent ↔ robot interface
- **Model Hardware Standard** (Anthropic): capability descriptions, device-level limits,
  deterministic scripts. Apply to the preview; mirror its vocabulary now.
- **phosphobot** (phospho): REST middleware for SO-100/101, recording, training, replay;
  its MCP server exposes *trained behaviours* as tools. Evaluate as the recording and
  replay layer for Toy 3 instead of writing one.
- **robot_MCP**: reference for joint-level tools; nothing to adopt beyond confirmation
  that Claude is the model people find works best for this.

### Kinematics, calibration, control
- **LeRobot `kinematics` extra** (placo): FK/IK and end-effector action processing. Adopt.
- **OpenCV hand-eye** and **AprilTag** pose scripts (VLA-REPLICA). Adopt.
- Community **so101_kinematics** (C++/Eigen with Python bindings, orientation-weighted
  IK, optional sub-mm fine-calibration script). Second opinion if placo disappoints.

### Learned skills and data
- **SmolVLA** (450M, trained on LeRobot community SO-101 data), **GR00T N1.6** (NVIDIA's
  own SO-101 fine-tune guides; >48 GB GPU to train, rent it), **π0** via `lerobot[pi]`.
  Never our own policy.
- **UMI** family for demonstrations without teleop: original UMI (printed gripper ~$73 +
  GoPro), **Fast-UMI** (hardware-independent, robot-side unit adapts to any arm: the
  right one for SO-101), **UMI-3D** (2026, parts interchangeable with UMI, ~$50 printed),
  **actuated-UMI** (open BoM and video guide). LeRobot also has a `phone` extra.
- **HumanEgo / EgoMimic**: Aria glasses → zero-shot policies; released pipelines. Later.
- **LeIsaac** if simulation data is ever wanted.

### Assembly: benchmarks, planners, policies
- **NIST Assembly Task Board #1**: the standard for peg insertion (4/8/12/16 mm round
  pegs), gear meshing, connectors, nut threading; laser-cut design files and
  replication instructions published. **Peg-in-Bench** (2026): fully 3D-printable
  modular insertion benchmark with STLs and a scenario generator (AIST). Use these as
  our insertion verifiers instead of inventing tasks; it makes our numbers comparable.
- **Fabrica** (Autodesk Research + MIT, CoRL 2025 best paper; code at
  github.com/yunshengtian/Fabrica): CAD model in → precedence planning → grasp
  filtering → **automated pickup-fixture generation** (geometry processing + iterative
  bin packing, orienting each part for top-down pickup) → motion planning → learned
  insertion (~80% step success). Predecessors ASAP and "Assemble Them All". **This is
  the closest prior art to Toy 1 and Toy 4.** Study it before designing fixture autogen;
  reuse its fixture method; our contribution is doing it with a $500 arm, a printer,
  and an AI engineer in the loop, publicly, with closure measured.
- **MatchMaker** (2025): automated generation of assembly assets for robot learning.
- **NVIDIA IndustReal / AutoMate / Factory** in Isaac Lab: 100 assembly assets, ~80%
  zero-shot sim-to-real insertion on UR10e/Franka; **AlphaNIST** (2026): one policy for
  20 Task Board #1 tasks in sim. If Toy 5 insertion needs learning, start here.
- **Fixture generation, commercial**: Stratasys/trinckle fixturemate, nTop FDM Fixture
  Generator (rule-based, from CAD, prints overnight). Proof the problem is tractable
  with rules; our version must be open and arm-aware.

### Printing and the print → kit loop
- **Automatic part ejection is a solved aftermarket problem**: 3DQue Auto Ejection Kit
  (bed-slingers; toolhead pushes parts off), FarmLoop ($129, Bambu A/P/X), AutoSwap and
  Swapmod plate changers (A1), queue managers SimplyPrint / AutoFarm3D / FlowQ. Even the
  trick "cool the bed, push with the X axis" works on an A1.
  **Consequence:** the arm should not harvest parts from the bed. Ejection by printer,
  parts fall into a tray or chute, arm picks from the tray. Cheaper, more reliable,
  and the arm's weakest skill (grasping on a hot, flexible sheet) disappears.
- **Printer APIs**: PrusaLink has start/stop/pause/upload but, as of 2025 firmware, no
  "set ready" endpoint for unattended loops; Bambu via LAN mode plus FarmLoop is the
  documented unattended route. This tilts the printer choice toward **Bambu A1 +
  FarmLoop** unless Prusa has closed the gap; verify before buying.

### Design tools for the engineer
- **agentcad** (build123d MCP, Apache-2.0), **flowful-ai/cad-skill** (CadQuery Claude
  Code skill), **Zoo** MCP (hosted text-to-CAD). Adopt agentcad or cad-skill.

### Human baseline and economics
- **MOST / MTM-1** predetermined motion-time systems: the manufacturing-engineering way
  to estimate human assembly minutes from the step list. Use BasicMOST as a cross-check
  on the filmed build, and to estimate closure denominators for products we have not
  built yet (Toy 8).
- **Boothroyd–Dewhurst DFA** scoring for redesign decisions (Toy 4).

### Safety
- **ISO/TS 15066 Annex A**: per-body-region force and pressure limits for collaborative
  robots (e.g. back of hand 280 N transient / 140 N quasi-static; limits are
  acknowledged to be preliminary). An SO-101 is probably below these, but *measure*
  contact force with a scale at working speed rather than assume, and put the numbers
  in `config/limits.json`. Enforce in firmware/hardware (torque limits, e-stop), not
  only in the agent layer. Project Fetch's near-collision was a 1 m/s × 5 s command.

### Lineage: who tried machines-making-machines, and what they proved
- **RepRap** (2005–): printers printing their own plastic parts; "Snappy" the most
  self-replicating; never closed assembly. Gave the word *vitamins*.
- **Lipson, Cornell/Columbia** (2005–): first physical self-reproducing modular robot;
  2025 "Robot Metabolism" (Truss Link, *Science Advances*): robots grow by absorbing
  modules; operator-controlled in physical experiments.
- **MIT CBA, Gershenfeld / Abdel-Rahman** (*Nature* 2022, ICRA 2024): voxel assembler
  swarms that can build more assemblers; "almost, but not quite" one robot making
  another that walks away.
- **Open Source Ecology**: 50-machine Global Village Construction Set; about a third
  done after 15 years; GVCS 1.0 now targeted for 2028.
- **Fabrica / ASAP** (2023–2025): CAD-to-assembly planning with real dual-arm execution.
- **NVIDIA ENPIRE / ASPIRE** (2026): coding agents running a robot fleet to improve
  skills autonomously; hardware is not redesigned.

What none of them did: close the *design* loop (AI redesigns the machine for the
machines it has) on hobby hardware, in public, with a closure number. That is still ours.

## 3. Changes this makes to the roadmap

1. **Toy 0** gains: swap IK to LeRobot placo; hand-eye via OpenCV + VLA-REPLICA script;
   measure contact force with a scale and record ISO/TS 15066 headroom.
2. **The print → kit loop drops the arm from harvesting.** Printer ejects (FarmLoop or
   X-axis push) into a tray; arm picks from the tray. Printer choice re-opened: Bambu A1
   + FarmLoop vs Prusa MK4S, decided on unattended-loop support.
3. **Toy 1 (fixture autogen)** starts by reading Fabrica's fixture generator and
   fixturemate's rules; its verification parts come from Peg-in-Bench / NIST ATB#1
   geometries so results are comparable.
4. **Toy 3 (human video)** uses the Fast-UMI design; recording/replay through LeRobot
   (evaluate phosphobot as the middleware).
5. **Toy 5 (gearbox)** insertion steps are benchmarked on NIST ATB#1 peg sizes; if
   learning is needed, start from AutoMate/IndustReal, not from scratch.
6. **Toy 6 (cell as API)** adopts VLA-REPLICA's cross-lab protocol and MHS vocabulary.
7. **Baselines** add a BasicMOST estimate beside every filmed time.

## 4. Standing rule (added to CLAUDE.md)

Before building any component, spend 30 minutes on a prior-art check and write three
lines in the PR or commit: what exists, why we are or are not using it, and what is new.
"I didn't know it existed" is the failure this document is for.

## Sources

- LeRobot 0.6.1 source (installed): `lerobot/model/kinematics.py`, `lerobot/robots/so_follower/robot_kinematic_processor.py`, extras in package metadata.
- [robot_MCP](https://github.com/IliaLarchenko/robot_MCP), [phosphobot](https://github.com/phospho-app/phosphobot), [phospho MCP server](https://github.com/phospho-app/phospho-mcp-server), [phosphobot MCP example](https://phospho.mintlify.app/examples/mcp-for-robotics)
- [LeIsaac](https://wiki.seeedstudio.com/simulate_soarm101_by_leisaac/), [so101_kinematics](https://github.com/snachi2s/so101_kinematics), [eye-to-hand with LeRobot (OpenCV forum)](https://forum.opencv.org/t/eye-to-hand-calibration-using-lerobot/24195), [VLA-REPLICA](https://arxiv.org/pdf/2605.20774), [hand-eye from AprilTags (IROS 2017)](https://elib.dlr.de/116772/1/nissler_iros17_accpeted.pdf)
- [NIST assembly metrics and Task Boards](https://www.nist.gov/el/intelligent-systems-division-73500/robotic-grasping-and-manipulation-assembly/assembly), [Peg-in-Bench](https://arxiv.org/html/2609.00906), [AlphaNIST](https://arxiv.org/html/2610.13354), [REASSEMBLE](https://arxiv.org/pdf/2502.05086), [FMB](https://functional-manipulation-benchmark.github.io/)
- [Fabrica](https://fabrica.csail.mit.edu) and [Autodesk Research post](https://www.research.autodesk.com/blog/from-cad-to-robotic-assembly/), [ASAP](https://arxiv.org/pdf/2309.16909), [MatchMaker](https://arxiv.org/pdf/2503.05887), [WRAP fixtureless assembly](https://arxiv.org/pdf/2609.29407)
- [NVIDIA sim-to-real assembly in Isaac Lab](https://developer.nvidia.com/blog/bridging-the-sim-to-real-gap-for-industrial-robotic-assembly-applications-using-nvidia-isaac-lab/), [AutoMate / diverse geometries](https://developer.nvidia.com/blog/training-sim-to-real-transferable-robotic-assembly-skills-over-diverse-geometries), [Isaac Lab paper](https://arxiv.org/html/2511.04831v1)
- Fixture generation: [fixturemate + GrabCAD Print Pro](https://tech-labs.com/blog/automated-fixture-design-arrives-fixturemate-grabcad-print-pro), [nTop FDM Fixture Generator](https://www.ntop.com/fdm-fixture-generator/), [RL fixture design (CIRP 2025)](https://www.sciencedirect.com/science/article/pii/S2212827125004640)
- Print farms: [3DQue Auto Ejection](https://www.3dque.com/products/auto-ejection), [FarmLoop](https://simplyprint.io/integrations/farmloop) and [Tom's Hardware on it](https://www.tomshardware.com/3d-printing/new-auto-ejection-tool-for-bambu-lab-print-farms-automatically-ejects-finished-3d-prints-from-the-machine-usd129-kit-includes-auto-door-opener-and-special-bed-surface-for-frictionless-part-ejection), [AutoSwap](https://simplyprint.io/features/autoprint/autoswap), [Bambu forum: remove parts with the toolhead](https://forum.bambulab.com/t/automatically-remove-prints-with-the-toolhead/54872), [PrusaLink set-ready gap](https://forum.prusa3d.com/forum/general-discussion-user-experience-ideas/prusalink-api-for-set-ready/), [PrusaLink wrapper](https://github.com/emischorr/prusa_link)
- Demonstration hardware: [UMI](https://github.com/real-stanford/universal_manipulation_interface), [Fast-UMI](https://arxiv.org/html/2409.19499v1), [UMI-3D](https://arxiv.org/html/2604.14089v1), [actuated UMI gripper](https://github.com/actuated-umi/actuated-umi-gripper), [HumanEgo](https://arxiv.org/html/2605.24934v2), [EgoMimic](https://www.alphaxiv.org/abs/2410.24221)
- Baselines: [MTM/MOST overview](https://taylorandfrancis.com/knowledge/Engineering_and_technology/Materials_science/Predetermined_motion_time_system), [DFA vs MOST dataset (Cranfield)](https://dspace.lib.cranfield.ac.uk/items/77100dc7-a682-4434-bf57-831e9ae489b2), [Boothroyd Dewhurst DFA](https://www.dfma.com/pdf/dfadescription.pdf)
- Safety: [ISO/TS 15066 explained (Robotiq)](https://blog.robotiq.com/hubfs/eBooks/ebook-ISOTS15066-Explained.pdf), [verified contact limits study](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2021.667818/full)
- Lineage: [RepRap](https://en.wikipedia.org/wiki/RepRap), [Lipson self-replication](https://www.creativemachineslab.com/self-replication.html), [Robot Metabolism](https://www.science.org/doi/10.1126/sciadv.adu6897) and [Truss Link code](https://github.com/RobotMetabolism/TrussLink), [MIT CBA assemblers (Nature 2022)](https://cba.mit.edu/docs/papers/22.11.Nature.pdf) and [ICRA 2024](https://cba.mit.edu/docs/papers/24.05.ICRA.pdf), [Open Source Ecology GVCS](https://wiki.opensourceecology.org/wiki/Global_Village_Construction_Set)
