# Direction: where the field is going, and where Swayam Labs fits

Written 2026-10-16 after studying Anthropic's Project Fetch and Model Hardware Standard,
Jim Fan's "Robotics' End Game" talk, NVIDIA's 2026 robotics stack, and the open-source
and startup landscape. Sources at the end. This is a brief for deciding, not a plan;
the plan lives in `ROADMAP.md` once we agree.

## 1. What the big players are building

**The hands.** Figure (~$39B), Tesla, 1X, Unitree and NVIDIA's GR00T reference humanoid
are building general-purpose bodies and the vision-language-action (VLA) policies that
drive them. Capital here is measured in billions; model evaluation is still weak and
self-reported. Not a place for a one-person lab to compete.

**The nervous system.** Anthropic's Model Hardware Standard (MHS, Aug 2026) is a
specification for AI agents to operate physical equipment: a standard driver with a few
read/write primitives, *capability descriptions* (natural-language notes about what a
device measures, adjusts, and its safety limits), control through MCP/CLI/code, agents
packaging learned routines into deterministic scripts, and device-level safety
interlocks. Partners include Universal Robots, Doosan, Tecan, Hugging Face (LeRobot) and
Raspberry Pi. Open-sourcing is planned; a research-preview waitlist is open. Google's
Intrinsic is doing the industrial version: software-defined modular workcells.

**The data.** Jim Fan's thesis: teleoperation is a dying data source. The pyramid is
wearables (UMI/DexUMI: a human wears or holds the robot's end-effector) and egocentric
human video (NVIDIA EgoScale: 21,000 h of human video, then ~4 h of robot data to
fine-tune). HumanEgo (2026) shows minutes of Aria-glasses video can give zero-shot robot
policies. Data no longer requires owning many robots.

**The simulator.** Isaac Lab 3.0, Cosmos 3 (open), neural simulators ("DreamDojo").
NVIDIA publishes a full *SO-101 sim-to-real* course: domain randomisation, GR00T N1.6
fine-tuning, Cosmos augmentation, actuator-gap estimation. Fine-tuning needs a rented
>48 GB GPU; inference runs on a PC GPU or AGX Orin.

**The end state, in Fan's words.** Three milestones: the *physical Turing test* (2–3
years), the *physical API* (fleets configured like software; lights-out factories that
take a design file in and output an assembled product; automated wet labs), and
*physical auto-research* (robots design and build better versions of themselves,
which he places near 2040). NVIDIA's ENPIRE/ASPIRE (2026) put coding agents in charge of
a robot fleet to improve *skills* autonomously. Nobody is doing the *hardware* half of
auto-research at small scale, in the open.

**Anthropic's own signal.** Project Fetch (Nov 2025): non-expert teams with Claude did
robotics tasks in about half the time; the biggest uplift was *connecting to unfamiliar
hardware*. Their conclusion: "uplift precedes autonomy", robotics is a candidate for
sudden capability gains, and a named open question is the difference between
*controlling existing hardware* and *designing new hardware*. Their stated model
weaknesses: little physical intuition (a bubble gets diagnosed as a software bug),
over-caution, and a need for lots of context about goals and hardware.

## 2. The gap, stated precisely

Everyone is building hands and the nervous system. The remaining unclaimed piece, the
one Fan dates to 2040 and Anthropic names as an open question, is the **engineer in the
loop who redesigns the machine for the hands it has**: takes a design file, adapts it to
the cell's real abilities, builds its own fixtures and verifiers, runs the cell, and
improves the design from logged failures. Call it **design closure**.

Design closure is testable at desk scale today, because it does not need a humanoid or
a billion-dollar model. It needs a cheap arm, a printer (the precise machine), an AI
engineer with CAD and verification tools, and honest measurement. That is exactly what
Swayam Labs already is.

So the sharpened mission:

> **Swayam Labs builds the smallest open "design file in, machine out" cell, and
> measures how much of that loop an AI engineer closes.**

Two numbers, not one: **closure %** (human labour-minutes removed) and **design
iterations per week with no human CAD** (how fast the engineer improves the machine
from its own failures).

## 3. What we adopt instead of building

| Need | Adopt | Not build |
|---|---|---|
| Learned manipulation skills | LeRobot + SmolVLA (450M, runs on modest hardware) or GR00T N1.6 fine-tunes via LeRobot; NVIDIA's SO-101 sim-to-real recipe | Our own policy architecture |
| Agent ↔ hardware interface | Shape our arm/printer/camera tools as MHS-style *capability descriptions* + limits + deterministic scripts; apply to the MHS preview | A bespoke protocol |
| CAD for the engineer | agentcad (build123d MCP server) or flowful-ai/cad-skill (CadQuery) | Hand-rolled CAD scripts per part |
| Demonstration data | A printed UMI-style handheld gripper + phone camera; later Aria glasses + HumanEgo pipeline | Teleop rigs and leader-arm hours |
| Physics simulation | Isaac Lab / MuJoCo for kinematics checks only | More simulator features (frozen) |
| Edge compute | Mac for now; a rented GPU for fine-tunes; Jetson only when a policy needs it on the robot | Early Jetson purchases ($399+) |

## 4. The experiment ladder: toys that climb toward the gap

Each toy is pre-registered (`predictions/`), judged by a sensor or bought instrument,
audited, and public. Each adds one capability the next one needs.

| # | Toy | New capability | What it proves | Judge |
|---|---|---|---|---|
| 0 | Film the build; measure repeatability (Oct 17–19) | Baseline | The error budget was right or wrong | Dial indicator |
| 1 | **Fixture autogen.** Given any part's STL, the engineer generates a locating nest with a two-stage funnel, prints it, the arm places the part in it | AI designs jigs for its own hands | First design-closure loop; count design iterations to 10/10 | AprilTag pose |
| 2 | **Self-upgrade.** Fingertip pads the arm fits to itself | Arm improves itself | Grasp success up vs stock jaws | Grasp benchmark |
| 3 | **Skill from human video.** Printed UMI gripper + phone; 50 human demos of "bed → tray"; fine-tune SmolVLA; compare to scripted and zero-shot | Learned skills without teleop | Fan's data thesis at desk scale | Verifier + success rate |
| 4 | **Redesign for the robot.** One SO-101 part (wrist housing) redesigned by the engineer as snap-fit; printed; arm assembles it | AI redesigns the machine for the machine | First "robot designs a better version of its own part" | Closure % on that subassembly |
| 5 | **Design file in, mechanism out.** The planetary gearbox, printed in place, vitamins embedded mid-print by the arm | Printer as the precision machine | Fan's physical-API loop at desk scale | Test stand: ratio, backlash, torque |
| 6 | **MHS-shaped cell.** Arm, printer and cameras exposed through capability files; a stranger sends a design file and gets a part | Cell as an API | Reproducibility by an outsider | Outsider's result |
| 7 | **Child arm** (north star 1) | Assembly closure | The convincing demo | Parent's acceptance test |
| 8 | **A product it was never shown** (north star 2) | Generalisation | It is a method, not a recipe | Stranger reproduces from the repo |

Toys 1 and 4 are the ones nobody else is doing. Toy 3 is where we learn whether learned
skills or scripted fixtures win for assembly; we should not assume.

## 5. Safety is part of the contribution

Project Fetch's near-collision (a 1 m/s × 5 s command with a table 5 m away) and MHS's
interlocks say the same thing: the field needs *evaluations* of agent-operated cells,
not just demos. Our two independent safety layers, append-only run logs and auditor are
already an evaluation harness. Publishing "what an AI engineer did wrong in 1,000 logged
hours of running a cell" would be useful to Anthropic's preview partners and is within a
one-person lab's reach.

## 6. What to decide

1. Adopt the sharpened mission and the two metrics.
2. Reorder the roadmap around the ladder (Toy 1 replaces "coupon" as the first design
   experiment; the coupon becomes Toy 1's first part).
3. Apply to the MHS research preview now; shape our tools to its vocabulary.
4. Order: dial indicator and clamps (today), printer (this week), a phone mount and a
   printed UMI gripper (Toy 3, after the printer).

## Sources

- Anthropic, [Project Fetch](https://www.anthropic.com/research/project-fetch-robot-dog) and the video [Who let the robot dogs out?](https://www.youtube.com/watch?v=NGOAUJtdk-4)
- Anthropic, [Previewing the Model Hardware Standard](https://www.anthropic.com/news/model-hardware-standard-research-preview), [modelhardwarestandard.com](https://modelhardwarestandard.com), video [Model Hardware Standard: AI operating physical equipment](https://www.youtube.com/watch?v=UxJZrCFzTHY); coverage by [CNBC](https://www.cnbc.com/2026/08/27/anthropic-pushes-into-physical-world-with-new-standard-to-help-ai-agents-operate-machines.html) and [The Decoder](https://the-decoder.com/anthropic-wants-to-do-for-physical-hardware-what-its-model-context-protocol-did-for-software/)
- Jim Fan, [Robotics' End Game](https://www.youtube.com/watch?v=3Y8aq_ofEVs) (Sequoia AI Ascent 2026); recaps by [eventual.ai](https://www.eventual.ai/blog/vlas-are-dead-long-live-world-action-models), [thedeepfeed](https://www.thedeepfeed.ai/posts/2026-05-01-jim-fan-robotics-llm-playbook/), [Humanoids Daily](https://www.humanoidsdaily.com/news/the-great-parallel-nvidia-s-jim-fan-outlines-the-robotics-end-game-strategy)
- NVIDIA: [Isaac GR00T reference humanoid](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-NVIDIA-Isaac-GR00T-Reference-Humanoid-Robot-for-Academic-Research/default.aspx), [GTC 2026 robotics](https://www.trendforce.com/news/2026/03/19/insights-nvidia-expands-robotics-ecosystem-at-gtc-as-physical-ai-moves-toward-large-scale-deployment/), [Train an SO-101 from sim to real](https://docs.nvidia.com/learning/physical-ai/sim-to-real-so-101/latest/index.html), [GR00T N1.5 on SO-101](https://huggingface.co/blog/nvidia/gr00t-n1-5-so101-tuning), [GR00T N1.6 on SO-101 (Seeed)](https://wiki.seeedstudio.com/fine_tune_gr00t_n1.6_for_lerobot_so_arm_and_deploy_on_agx_orin/), [Jetson repricing](https://www.cnx-software.com/2026/07/22/nvidia-increases-the-price-of-jetson-modules-and-devkits-by-up-to-101/)
- Hugging Face: [SmolVLA](https://huggingface.co/blog/smolvla), [LeRobot paper](https://arxiv.org/html/2602.22818v1)
- Human data: [EgoScale overview](https://www.labellerr.com/blog/egoscale-robot-training-framework/), [HumanEgo](https://arxiv.org/html/2605.24934v2) and [code](https://github.com/TX-Leo/HumanEgo), [EgoMimic](https://www.alphaxiv.org/abs/2410.24221)
- Landscape: [robot foundation models 2026](https://humanoid-world.com/en/foundation-models/), [physical AI companies](https://www.opencurious.com/explore-physical-ai), [Intrinsic workcell at Automate 2026](https://roboticsandautomationnews.com/2026/07/09/intrinsics-vision-for-physical-ai-building-the-software-defined-factory/103211/), [1X factory](https://interestingengineering.com/ai-robotics/1x-humanoid-robot-neo-factory-california)
- CAD for agents: [agentcad](https://github.com/jdilla1277/agentcad), [flowful-ai/cad-skill](https://github.com/flowful-ai/cad-skill), [Zoo text-to-CAD](https://zoo.dev/blog/introducing-text-to-cad)
- Auto-research and self-replication: [ENPIRE/ASPIRE coverage](https://exawizards.com/column/ai-trend/news-06-19-2026/), [Cambridge "mother robot" (2015)](https://qz.com/479565/the-end-is-nigh-robots-are-learning-how-to-build-better-clones-of-themselves)
