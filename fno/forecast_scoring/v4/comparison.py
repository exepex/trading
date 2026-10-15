"""One forecaster against its question's primary baseline (protocol v4 sections 4-5 and 7; story G8): the two frozen
date sets, the mean difference, the relative improvement, the reported sensitivities, stability, the scored window's
regime and, from 60 scored outcomes, the power report. Descriptive: verdicts are made only at a look (`look.py`)."""

from __future__ import annotations

import math
import zlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from ...forecast_v4.bootstrap import hac_one_sided_p, one_sided_test, relative_improvement
from ...forecast_v4.confirmatory import batch_means_p, studentized_bootstrap_p
from ...forecast_v4.pairs import DatedForecasts, Pairing, pair_point, pair_probability
from ...forecast_v4.power import PowerReport, power_report
from ...forecast_v4.regime import WindowRegime, window_regime
from ...forecast_v4.terms import (
    BLOCK_LENGTH,
    BRIER_MIN_EFFECT,
    FAMILY,
    FAMILY_SIZE,
    POINT_QUESTIONS,
    POWER_REPORT_AT,
    QLIKE_MIN_EFFECT,
    family_seed_word,
)
from .inputs import ForecastValue, Outcome


@dataclass(frozen=True)
class Comparison:
    question: str
    forecaster: str
    baseline: str
    pairing: Pairing
    mean_difference: float | None  # D on the scored set; negative favours the forecaster
    relative_improvement: float | None  # on the gate set
    batch_means_p: float
    studentized_p: float
    centred_bootstrap_p: float
    hac_p: float | None
    half_signs: tuple[int, int] | None  # sign of D in the first and second half of the scored dates
    regime: WindowRegime | None  # None: no scored outcome
    power: PowerReport | None  # from 60 gate-set outcomes


def margin(question: str) -> float:
    return QLIKE_MIN_EFFECT if question in POINT_QUESTIONS else BRIER_MIN_EFFECT


def seed_word(question: str, slot: str | None, forecaster: str) -> int:
    """A member's place in the family; any other comparison a stable number after it (reported values only)."""
    if slot is not None and (question, slot) in FAMILY:
        return family_seed_word(question, slot)
    return FAMILY_SIZE + 1 + zlib.crc32(f"{question}/{forecaster}".encode()) % 2**31


def paired_rows(
    forecasts: Mapping[date, ForecastValue], baseline: Mapping[date, ForecastValue], outcomes: Mapping[date, Outcome]
) -> list[DatedForecasts]:
    """One row per day either file holds; a day without an outcome entry is unresolved."""
    rows = []
    for day in sorted(set(forecasts) | set(baseline)):
        outcome = outcomes.get(day, Outcome(None))
        own, base = forecasts.get(day), baseline.get(day)
        rows.append(DatedForecasts(day, own.value if own else None, base.value if base else None, outcome.value,
                                   outcome.void))  # fmt: skip
    return rows


def compare(question: str, forecaster: str, baseline: str, rows: list[DatedForecasts],
            outcomes: Mapping[date, Outcome], k: int) -> Comparison:  # fmt: skip
    pairing = (pair_point if question in POINT_QUESTIONS else pair_probability)(rows)
    scored, gate, block = pairing.scored, pairing.gate, BLOCK_LENGTH[question]
    d = scored.differences
    return Comparison(
        question, forecaster, baseline, pairing,
        math.fsum(d) / len(d) if d else None,
        relative_improvement(gate) if gate.differences and math.fsum(gate.baseline_losses) > 0 else None,
        batch_means_p(d, block), studentized_bootstrap_p(d, block, k), one_sided_test(d, block, k).p_value,
        hac_one_sided_p(d, block), _half_signs(d), scored_regime(scored.days, outcomes),
        _power(question, gate.differences, gate.baseline_losses),
    )  # fmt: skip


def scored_regime(days, outcomes: Mapping[date, Outcome]) -> WindowRegime | None:
    if not days:
        return None
    return window_regime([outcomes[d].vix for d in days], [outcomes[d].log_return for d in days])


def _half_signs(d) -> tuple[int, int] | None:
    if len(d) < 2:
        return None
    half = len(d) // 2
    return _sign(math.fsum(d[:half])), _sign(math.fsum(d[half:]))


def _sign(value: float) -> int:
    return (value > 0) - (value < 0)


def _power(question: str, differences, baseline_losses) -> PowerReport | None:
    if len(differences) < POWER_REPORT_AT:
        return None
    return power_report(question, differences, math.fsum(baseline_losses) / len(baseline_losses), margin(question))
