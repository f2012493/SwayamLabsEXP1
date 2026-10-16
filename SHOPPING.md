# Shopping list (before Toy 0)

Ordered by when you need it. Check current prices and stock yourself; nothing here
is a brand endorsement beyond the reasons given.

## Needed the day the arm arrives

| Item | Why | Notes |
|---|---|---|
| Phone tripod or overhead phone mount | Film the SO-101 build: this is the human baseline (closure denominator) | See `baseline/BUILD_FILMING.md` |
| Rigid table + 2 C-clamps | Arm base must not move, or every calibration is wrong | Clamp the base, don't rely on rubber feet |
| Inline power switch or e-stop button on the servo power supply | A physical cut-off that works even if software hangs | Mount it where you can hit it without looking |
| Digital calipers, 0.01 mm | Bought instrument: checks printed parts; never printed | One with a USB/data output lets Claude read it directly |
| **Dial indicator 0.01 mm + magnetic base** | The Day-3 repeatability measurement (`docs/DAY_ONE.md`) cannot happen without it | Needs a steel or magnetic surface to clamp to: a small steel plate under the arm works |
| 200 g test weight (or calibrated coins) | Loaded-vs-unloaded backlash check | |

Check whether your SO-101 kit includes a **leader arm** (for teleoperation), the
**servo driver board**, and **power supplies**. If no leader arm, add one later —
it is only needed for recording demonstrations (Toy 3 learned policies).

## Needed for Toys 1–2 (within ~2 weeks)

| Item | Why | Notes |
|---|---|---|
| **3D printer, open frame (bed-slinger) with removable flexible PEI sheet** | The arm must reach the bed and flex parts off | **Recommended: Prusa MK4S** — open firmware, network API (PrusaLink), G-code pause (M601) for pause-and-embed. **Budget alternative: Bambu Lab A1** — cheaper and fast, but third-party network control is more restricted; check current LAN/developer-mode support before buying. Avoid enclosed printers for now. |
| A spare flexible PEI sheet | One printing while the arm unloads the other | |
| Filament: PLA, PETG, TPU 95A | PLA for coupons, PETG for fixtures and trays, TPU for fingertip pads | TPU needs a direct-drive extruder (both printers above have one) |
| 2–4 USB webcams, 1080p, **fixed focus** | Overhead and side views; autofocus breaks calibration | Plus the small wrist camera the SO-101 has a mount for |
| Powered USB hub | Cameras + arm + printer on one Mac | |
| ChArUco calibration board on a flat rigid backing | Hand-eye calibration | Print on paper and glue to glass, acrylic or aluminium; flatness matters more than print quality |
| AprilTag sheet (tag36h11 family), matte paper | Positions of trays, fixtures, printer bed | Laser print; avoid glossy (reflections) |

## Needed for Toys 3–5

| Item | Why |
|---|---|
| Gauge pin set (around 5–7 mm in 0.01–0.05 mm steps) | Checks printed holes without trusting the printer |
| Scale, 0.01 g | Part mass as a print-quality check |
| Small handheld force gauge (or a luggage scale to start) | Independent check of torque-at-slip and snap force |
| Small magnets (e.g. 6x3 mm neodymium) and small bearings | First vitamins for pause-and-embed |
