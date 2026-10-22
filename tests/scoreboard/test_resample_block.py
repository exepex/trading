"""S2's resampler with a caller's block length (story MS-INS, part d; orchestrator, 22 Oct 2026): the default output
is byte-identical to the output before the argument existed, pinned by its digest."""

import hashlib
import random
from datetime import date, timedelta

from fno.scoreboard.series import DailySeries
from fno.scoreboard.uncertainty import BLOCK_DAYS, resampled_ratios

DEFAULT_DIGEST = "9cc2938b0e0105ea1f3e11c8d1879bf14b3ea29bba0887dde01b0a3f73e9bca3"  # before the argument existed


def _series(n: int = 45) -> DailySeries:
    draw = random.Random(7)
    days = tuple(date(2026, 1, 1) + timedelta(i) for i in range(n))
    nets = tuple(round(draw.uniform(-500, 600), 2) for _ in range(n))
    return DailySeries(days, nets, tuple(round(draw.uniform(1000, 5000), 2) for _ in range(n)))


def test_the_default_output_is_byte_identical_to_before():
    assert hashlib.sha256(repr(resampled_ratios(_series(), resamples=2000)).encode()).hexdigest() == DEFAULT_DIGEST
    assert resampled_ratios(_series(), resamples=200) == resampled_ratios(_series(), resamples=200, block=BLOCK_DAYS)


def test_a_shorter_block_resamples_a_series_shorter_than_s1s():
    short = _series(12)
    assert resampled_ratios(short) is None and len(resampled_ratios(short, resamples=50, block=5)) == 50
    assert resampled_ratios(_series(4), block=5) is None
