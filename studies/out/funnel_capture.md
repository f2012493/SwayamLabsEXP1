# Funnel capture map (sim, flat cube dropped from 1 mm above the funnel mouth)

Offset is radial along the slot's xy diagonal (dx = dy = offset / sqrt 2). Cell = verifier result after 2 s; `seat` = in_slot true; otherwise the final tilt in degrees and distance to the slot centre in mm. Pure scene characterisation, no arm involved.

## Task v1: outer funnel 8 mm + 1.5 mm lead-in (mouth half-width 20.5 mm at z 21.5 mm)

| offset (mm) \ yaw (deg) | 0 | 5 | 10 | 15 | 20 | 30 |
|---|---|---|---|---|---|---|
| 0 | seat | seat | seat | seat | seat | tilt 0, d 10 |
| 2 | seat | seat | seat | seat | tilt 33, d 4 | seat |
| 4 | seat | seat | seat | tilt 33, d 4 | seat | tilt 33, d 4 |
| 6 | tilt 47, d 9 | tilt 46, d 9 | seat | tilt 33, d 4 | tilt 33, d 4 | tilt 33, d 4 |
| 8 | seat | seat | seat | tilt 33, d 4 | seat | tilt 43, d 9 |
| 10 | seat | seat | seat | tilt 44, d 9 | tilt 48, d 9 | tilt 53, d 8 |

Seated 22/36 cells; largest seated offset at yaw 0: 10 mm; largest seated yaw at offset 0: 20 deg.

## Task v2: outer funnel 4 mm + 1.5 mm lead-in (mouth half-width 16.5 mm at z 17.5 mm)

| offset (mm) \ yaw (deg) | 0 | 5 | 10 | 15 | 20 | 30 |
|---|---|---|---|---|---|---|
| 0 | seat | seat | seat | seat | tilt 0, d 10 | tilt 0, d 10 |
| 2 | seat | seat | seat | seat | seat | tilt 33, d 4 |
| 4 | seat | tilt 33, d 4 | seat | tilt 33, d 4 | seat | tilt 44, d 9 |
| 6 | seat | seat | seat | tilt 35, d 9 | tilt 44, d 9 | tilt 45, d 9 |
| 8 | seat | tilt 36, d 4 | tilt 43, d 9 | tilt 46, d 9 | tilt 47, d 9 | tilt 45, d 9 |
| 10 | tilt 0, d 20 | tilt 0, d 19 | tilt 0, d 19 | tilt 45, d 9 | tilt 43, d 9 | tilt 46, d 10 |

Seated 16/36 cells; largest seated offset at yaw 0: 8 mm; largest seated yaw at offset 0: 15 deg.
