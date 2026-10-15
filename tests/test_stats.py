from swayam.stats import wilson


def test_wilson_matches_known_values():
    p, lo, hi = wilson(7, 10)
    assert abs(p - 0.7) < 1e-9
    assert abs(lo - 0.3968) < 0.001 and abs(hi - 0.8922) < 0.001
    p, lo, hi = wilson(0, 10)
    assert lo == 0.0 and abs(hi - 0.2775) < 0.001
    p, lo, hi = wilson(10, 10)
    assert hi == 1.0 and abs(lo - 0.7225) < 0.001
