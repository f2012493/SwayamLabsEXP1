"""Small statistics helpers. Success rates always carry a Wilson 95% interval."""

from __future__ import annotations

import math


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """(rate, low, high) of the Wilson score interval for a binomial proportion."""
    if n <= 0:
        return math.nan, math.nan, math.nan
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return p, max(0.0, centre - half), min(1.0, centre + half)
