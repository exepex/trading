"""Story C4 fixtures: one correct trade of each structure (SF, SC, BF) on 14 Oct 2026, its committed A4 snapshot in a
raw store, and the checker as the app wires it. The claimed maximum loss is the PROPOSER's (B2's cost model, imported
here in the tests only), so a correct trade passing also shows the independent arithmetic agrees with it."""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import date, datetime, time

from fno.checks.validity import Sources, ValidityChecker
from fno.checks.validity_evidence import EvidenceReader
from fno.checks.validity_limits import LimitChecks
from fno.checks.validity_listing import NseListing
from fno.checks.validity_money import ProposedLeg
from fno.checks.validity_proposal import ValidityLeg, ValidityProposal
from fno.checks.wiring import validity_modes
from fno.constants import BOOK1_RULES
from fno.models import IST
from fno.playbook.schema import parse_strategy
from fno.quotes.recorder import DATASET
from fno.research_engine.structures import BOUGHT, SOLD
from fno.risk.trade_costs import SimulatorTradeCosts
from tests.checks.builders import committed_record
from tests.desk.builders import CHARGES, LOT, DictStore, contract, row, write_snapshot
from tests.playbook.builders import document
from tests.risk.builders import market as risk_market
from tests.risk.builders import proposal as risk_proposal

from .validity_sources import Accounts, Margins, NseFiles, limits

DAY, EXPIRY, WEEKLY = date(2026, 10, 14), date(2026, 10, 27), date(2026, 10, 20)
SPOT = 25_000.0
CUTOFF = datetime.combine(DAY, time(15, 0), IST)
STARTED, RECEIVED = datetime.combine(DAY, time(14, 55), IST), datetime.combine(DAY, time(14, 55, 10), IST)
STRIKES = range(24_400, 25_650, 50)


def mid(strike: float, kind: str) -> float:
    """A smooth chain on a 0.05 tick: intrinsic value plus a time value falling away from the money."""
    intrinsic = max(SPOT - strike, 0.0) if kind == "CE" else max(strike - SPOT, 0.0)
    return round((intrinsic + 200 * math.exp(-abs(strike - SPOT) / 400)) * 20) / 20


def fly(body: float, width: float, body_side: int) -> list[tuple[float, str, int]]:
    return [(body, "CE", body_side), (body, "PE", body_side), (body + width, "CE", -body_side),
            (body - width, "PE", -body_side)]  # fmt: skip


def condor(call: float, put: float, width: float) -> list[tuple[float, str, int]]:
    return [(call, "CE", SOLD), (put, "PE", SOLD), (call + width, "CE", BOUGHT), (put - width, "PE", BOUGHT)]


SHAPES = {"SF": (fly(25_000, 200, SOLD), 200.0), "SC": (condor(25_500, 24_500, 100), 100.0),
          "BF": (fly(25_000, 100, BOUGHT), 100.0)}  # fmt: skip


def strategy(code: str):
    doc = document(name=f"c4-{code.lower()}", status="paper")
    doc["structure"] = dict(doc["structure"], code=code)
    return parse_strategy(doc)


def proposer_max_loss(code: str, spec, width: float, lots: int = 1, lot_size: int = LOT) -> float:
    prices = {(k, kind): mid(k, kind) for k in STRIKES for kind in ("CE", "PE")}
    market = risk_market(SPOT, prices, EXPIRY, day=DAY)
    trade = replace(risk_proposal("t", code, width, spec, EXPIRY, lots), lot_size=lot_size)
    return SimulatorTradeCosts(CHARGES).max_loss(trade, market)


def legs_of(spec, expiry: date = EXPIRY) -> tuple[ValidityLeg, ...]:
    return tuple(
        ValidityLeg(contract(k, kind, expiry), expiry.isoformat(), ProposedLeg(k, kind, side, mid(k, kind)))
        for k, kind, side in spec
    )


def proposal(code: str = "SF", **changes) -> ValidityProposal:
    """A correct Book 1 trade of the structure, as D2 would choose it; `changes` seed a wrong one."""
    spec, width = SHAPES[code]
    version = strategy(code)
    correct = ValidityProposal(
        BOOK1_RULES, f"{version.name}-v1:{EXPIRY}", DAY, CUTOFF, EXPIRY.isoformat(), code, width, 1, LOT,
        legs_of(spec), proposer_max_loss(code, spec, width), True, version.parameters_sha256, version,
        frozenset({version.key}),
    )  # fmt: skip
    return replace(correct, **changes)


def snapshot_rows(received: datetime = RECEIVED) -> list[dict]:
    """The monthly chain plus a few weekly contracts (listed, but not the monthly expiry)."""
    rows = [row(k, kind, mid(k, kind) - 0.5, mid(k, kind) + 0.5) for k in STRIKES for kind in ("CE", "PE")]
    rows += [row(k, kind, 10.0, 11.0, expiry=WEEKLY) for k in STRIKES for kind in ("CE", "PE")]
    for r in rows:
        r["response_received_at"] = received.isoformat()
    return rows


def committed_store(rows=None, started: datetime = STARTED, spot: float | None = None) -> DictStore:
    store = DictStore()
    write_snapshot(store, "exec", rows or snapshot_rows(), started, started.replace(minute=56), day=DAY, spot=spot)
    return store


def checker(
    store, nse=None, account=None, margins=None, owner_limits=None, accounts=None, modes=None
) -> ValidityChecker:
    """The app's checker over these sources: by default a fresh Rs 5 lakh account, NSE's file of 13 Oct with lot 65,
    A14 margin rows of 13 Oct and config.yaml's limits with a stressed-margin factor set."""
    sources = Sources(EvidenceReader(store, DATASET), NseListing(nse or NseFiles()), accounts or Accounts(account))
    checks = LimitChecks(owner_limits or limits(), CHARGES, margins or Margins())
    return ValidityChecker(sources, checks, modes or validity_modes())


def check(the_proposal: ValidityProposal | None = None, store=None, record="committed", **sources):
    """C4's report on the proposal (correct SF by default) against the committed capture."""
    store = store or committed_store()
    capture = committed_record(store, DAY, "exec") if record == "committed" else record
    return checker(store, **sources).check(the_proposal or proposal(), capture)


def failed(report) -> set[str]:
    return {r.name for r in report.failures}
