"""Response 198 (exploratory): the candidate comparison's own machinery, on hand-made fixtures."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "breadth" / "candidates"))

import compare  # noqa: E402


def holm_by_hand(ps: list[float], member: int, alpha: float) -> bool:
    order = sorted(range(3), key=lambda m: ps[m])
    for j, m in enumerate(order):
        if ps[m] > alpha / (3 - j):
            return False
        if m == member:
            return True
    return True


def test_member_claimed_is_holms_step_down():
    rng = np.random.default_rng(5)
    ps = rng.uniform(0, 0.05, size=(3, 400))
    for member in range(3):
        got = compare.member_claimed(ps, member, 0.03)
        assert list(got) == [holm_by_hand(list(ps[:, i]), member, 0.03) for i in range(400)]


def test_v4_gate_needs_five_2pct_days_and_cuts_a_crash_dominated_window():
    big = np.zeros((3, 100), dtype=bool)
    big[0, :4] = True  # 4 days: too few
    big[1, :5] = True  # 5 days in 100: judged
    big[2, :11] = True  # 11 of 100: crash-dominated
    assert list(compare.judgeable(big, 100)) == [False, True, False]


def test_the_calibrated_alpha_is_the_largest_grid_value_within_every_limit():
    ps = np.full((3, 1000), 0.9)
    ps[0, :20] = 0.001  # 2% of paths claimed once alpha / 3 >= 0.001
    ps[0, 20:50] = 0.004  # 5% once alpha / 3 >= 0.004
    alpha = compare.calibrated_alpha({"x": (ps, ps)}, (10, 20))
    assert alpha == 0.0115  # alpha / 3 just below 0.004: 2% claimed at each look and at either
    assert compare.calibrated_alpha({"x": (ps * 0 + 1e-9, ps)}, (10, 20)) is None


def test_the_per_path_early_stop_gives_holms_any_claim_on_the_full_p_values():
    from multiprocessing import Pool

    rng = np.random.default_rng(9)
    paths = rng.standard_normal((3, 24, 120)) - 0.12
    with Pool(2) as pool:
        early = compare.path_claims(paths, 120, 0.05, pool)
        full = compare.any_claim(compare.p_values(paths, 120, 1.0, pool), 0.05)
    assert list(early) == list(full) and early.any() and not early.all()
