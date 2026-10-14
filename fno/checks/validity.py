"""Hard-validity checks (story C4, design 7 and 12.4): every proposed trade re-checked by code independent of the code
that proposed it. Common checks: evidence (the committed snapshot, its hashes, day and cutoff), the expiry, every leg
listed and quoted before the cutoff at the price used, the maximum loss recomputed, and the owner's limits. The
book's mode adds its own checks. A failure is final: no path, the owner's included, turns it into a pass."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .data_checks import CaptureRecord
from .validity_evidence import Evidence, EvidenceReader
from .validity_modes import ValidityMode
from .validity_money import max_loss
from .validity_proposal import CheckResult, ValidityProposal

PRICE_TOLERANCE, LOSS_TOLERANCE = 1e-6, 1.0  # rupees per unit; rupees (criterion 1: wrong by Rs 1 or more)


class HardValidityError(ValueError):
    """A hard-validity failure: it can never be overridden."""


@dataclass(frozen=True)
class ValidityReport:
    book: str
    opportunity_id: str
    mode: str
    results: tuple[CheckResult, ...]

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    @property
    def failures(self) -> tuple[CheckResult, ...]:
        return tuple(r for r in self.results if not r.ok)

    def record(self) -> dict:
        return {"mode": self.mode, "ok": self.ok, "checks": [r.record() for r in self.results]}


def override(report: ValidityReport, by: str, reason: str) -> ValidityReport:
    """Criterion 3: nobody, the owner included, overrides a hard-validity failure; a passing report needs nothing."""
    if not report.ok:
        failed = ", ".join(r.name for r in report.failures)
        raise HardValidityError(f"{by} cannot override hard validity ({failed}): {reason!r} refused")
    return report


@dataclass(frozen=True)
class Limits:
    max_loss_per_trade: float
    max_open_trades: int


class ValidityChecker:
    def __init__(
        self, reader: EvidenceReader, charges: Mapping[str, float], limits: Limits, modes: Mapping[str, ValidityMode]
    ):
        self.reader, self.charges, self.limits, self.modes = reader, dict(charges), limits, dict(modes)

    def check(self, proposal: ValidityProposal, capture: CaptureRecord | None) -> ValidityReport:
        mode = self.modes[proposal.book]
        evidence, problems = self.reader.read(proposal.day, capture)
        results = [CheckResult("evidence", not problems, "; ".join(problems) or "committed snapshot, hashes equal")]
        if evidence is not None:
            results += _market_checks(proposal, evidence)
        results += self._money_checks(proposal)
        results += mode.checks(proposal)
        return ValidityReport(proposal.book, proposal.opportunity_id, mode.name, tuple(results))

    def _money_checks(self, proposal: ValidityProposal) -> list[CheckResult]:
        loss = max_loss([leg.leg for leg in proposal.legs], proposal.units, self.charges)
        off = abs(loss.total - proposal.claimed_max_loss)
        numbers = {**loss.numbers(), "claimed": round(proposal.claimed_max_loss, 2), "difference": round(off, 2)}
        limits, risk_ok = self.limits, proposal.risk_verdicts_ok
        return [
            CheckResult("max_loss", off < LOSS_TOLERANCE, f"recomputed {loss.total:.2f}", numbers),
            CheckResult("loss_limit", loss.total <= limits.max_loss_per_trade, f"limit {limits.max_loss_per_trade:g}"),
            CheckResult(
                "open_trades", proposal.open_before + 1 <= limits.max_open_trades,
                f"{proposal.open_before} open before, limit {limits.max_open_trades}",
            ),
            CheckResult("risk_verdicts", risk_ok, "every C2 verdict passed" if risk_ok else "a C2 verdict failed"),
        ]  # fmt: skip


def _market_checks(proposal: ValidityProposal, evidence: Evidence) -> list[CheckResult]:
    started = evidence.started_at
    same_day = started.date() == proposal.day and started <= proposal.cutoff
    day_reason = f"snapshot started {started.isoformat()}; day {proposal.day}, cutoff {proposal.cutoff.isoformat()}"
    expiry_reason = f"opportunity {proposal.expiry}; monthly {list(evidence.monthly_expiries)}"
    results = [
        CheckResult("date", same_day, day_reason),
        CheckResult("expiry", _expiry_ok(proposal, evidence), expiry_reason),
    ]
    return results + [_leg_check(proposal, evidence, leg) for leg in proposal.legs]


def _expiry_ok(proposal: ValidityProposal, evidence: Evidence) -> bool:
    return proposal.expiry in evidence.monthly_expiries and all(leg.expiry == proposal.expiry for leg in proposal.legs)


def _leg_check(proposal: ValidityProposal, evidence: Evidence, leg) -> CheckResult:
    name = f"leg {leg.expiry} {leg.leg.strike:g} {leg.leg.kind}"
    row = evidence.rows.get((leg.expiry, leg.leg.strike, leg.leg.kind))
    if row is None:
        return CheckResult(name, False, "not listed in the snapshot")
    if row.received_at is None or row.received_at > proposal.cutoff:
        return CheckResult(name, False, f"quoted at {row.received_at}, not before the cutoff")
    numbers = {"price": leg.leg.price, "snapshot_mid": row.mid}
    if row.mid is None or abs(row.mid - leg.leg.price) > PRICE_TOLERANCE:
        return CheckResult(name, False, "price differs from the snapshot mid", numbers)
    return CheckResult(name, True, "listed, quoted before the cutoff, price equals the snapshot mid", numbers)
