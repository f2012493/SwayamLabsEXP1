"""Clearance-matrix coupon: the first designed experiment (ROADMAP Toy 1: the first part for fixture autogen).

One plate with 7 holes whose clearance over the peg steps from 0.0 to 0.6 mm, plus a
peg with a square grip head the SO-101 can hold. Print the peg twice, once standing
and once lying down (print orientation is the second factor). The arm inserts each
peg into each hole; motor current tells slide / press / jam. The result is the fit
table every later part is designed from.

Run:  uv run --extra cad python cad/coupon.py   -> cad/out/*.stl
"""

from pathlib import Path

import cadquery as cq

PEG_D = 6.0  # mm, nominal peg diameter
PEG_LEN = 14.0
HEAD = 12.0  # square grip head, mm
HEAD_H = 10.0
TIP_CHAMFER = 0.8
CLEARANCES = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]  # diametral, mm
HOLE_PITCH = 20.0
PLATE_T = 10.0
# Inner lead-in sized for same-direction repeatability (error budget: 0.6 mm worst-5%
# -> >= 1.5 mm). So the arm must approach these holes from taught positions with
# same_direction=True, and the plate must sit in a locating nest, not loose on the table.
LEAD_IN = 1.5
OUT = Path(__file__).parent / "out"


def plate() -> cq.Workplane:
    width = HOLE_PITCH * len(CLEARANCES)
    body = cq.Workplane("XY").box(width, 30, PLATE_T).edges("|Z").fillet(2)
    for i, c in enumerate(CLEARANCES):
        x = -width / 2 + HOLE_PITCH * (i + 0.5)
        d = PEG_D + c
        body = (
            body.faces(">Z").workplane(origin=(0, 0, PLATE_T / 2))
            .moveTo(x, 3).cskHole(d, d + 2 * LEAD_IN, 90)
        )
        label = cq.Workplane("XY").workplane(offset=PLATE_T / 2).center(x, -10).text(
            f"{c:.1f}", 5, -0.6, kind="bold"
        )
        body = body.cut(label)
    return body


def peg() -> cq.Workplane:
    head = cq.Workplane("XY").box(HEAD, HEAD, HEAD_H).edges("|Z").fillet(1)
    shaft = (
        cq.Workplane("XY").workplane(offset=-HEAD_H / 2)
        .circle(PEG_D / 2).extrude(-PEG_LEN)
        .faces("<Z").chamfer(TIP_CHAMFER)
    )
    return head.union(shaft)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    cq.exporters.export(plate(), str(OUT / "coupon_plate.stl"))
    cq.exporters.export(peg(), str(OUT / "coupon_peg.stl"))
    print("wrote", *sorted(p.name for p in OUT.glob("*.stl")))
