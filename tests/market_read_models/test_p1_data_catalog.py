"""Story P1, the F&O data catalog (owner decision, 15 Oct 2026): this repository's side of the drift tests. The
pinned dashboard contract (contracts/omenix-dashboard, 2.7.0) holds the five F&O screens' schemas and Mock examples.
These tests fail when the backend and the catalog drift apart:
- every catalog example validates against its pinned schema with this repository's validator, and its payload_sha256 is
  this repository's canonical hash (the publisher's);
- every x-record (<record>:<field>; the dashboard check requires one on every built field) names a record field that
  exists here today, with a matching type where the record is typed;
- fixtures built from this repository's own records (the trial ledger, a fresh paper account, the live forecasts of
  14 Oct 2026) validate against the schemas, so a renamed or retyped record breaks a test here;
- no example names a strategy internal, and the card says PAPER ONLY."""

from __future__ import annotations

import copy
import csv
import dataclasses
import hashlib
import inspect
import re
import types
import typing
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml

from fno.accounting.ledgers import TradeLine
from fno.ai.scoring_gate import ScoringStatus
from fno.books.account import EQUITY_COLUMNS, STARTING_CASH_RS, PaperAccount
from fno.books.equity import AccountState, account_state
from fno.checks.data_checks import CheckReport
from fno.desk.records import DeskEvent
from fno.forecast.schema_v2 import RECORD_COLUMNS_V2, ForecastRecordV2
from fno.forecast_scoring.block_bootstrap import BootstrapResult
from fno.forecast_scoring.coverage import book_coverage
from fno.forecast_scoring.scores import CalibrationBin, ScoreSummary
from fno.market_read_models.contract import ContractBroken, PinnedContract
from fno.market_read_models.publication import canonical
from fno.market_read_models.wiring import CONTRACT_FOLDER

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = PinnedContract(CONTRACT_FOLDER)
SCREENS = {  # operation -> its response schema
    "getFnoCard": "FnoCardResponse",
    "getFnoWeather": "FnoWeatherResponse",
    "getFnoForecastLab": "FnoForecastLabResponse",
    "getFnoStrategyLab": "FnoStrategyLabResponse",
    "getFnoPaperTrades": "FnoPaperTradesResponse",
}
PAGES = {
    "getFnoCard": "card",
    "getFnoWeather": "weather",
    "getFnoForecastLab": "forecast_lab",
    "getFnoStrategyLab": "strategy_lab",
    "getFnoPaperTrades": "paper_trades",
}
CATALOG = {name: e for name, e in CONTRACT.examples().items() if name.split("_")[0] in SCREENS}
PRIVATE = re.compile(
    r"(^|_)(rules?|thresholds?|filters?|params?|parameters|prompts?|weights?|features?|coefficients?)($|_)"
)
LIVE_FORECASTS = ROOT / "research" / "forecasts" / "live_v2" / "2026" / "2026-10-14_forecasts.csv"


def fields_of(cls) -> set[str]:
    """A record class's fields and properties."""
    names = {f.name for f in dataclasses.fields(cls)} if dataclasses.is_dataclass(cls) else set()
    return names | {name for name, value in vars(cls).items() if isinstance(value, property)}


def ledger_header() -> set[str]:
    with (ROOT / "research" / "ledger.csv").open(encoding="utf-8") as handle:
        return set(next(csv.reader(handle)))


RECORD_FIELDS = {  # the records the catalog may name (tools/api/check_fno_screens.py RECORDS in the dashboard)
    "ledger_csv": ledger_header,
    "forecast_record_v2": lambda: set(RECORD_COLUMNS_V2),
    "score_summary": lambda: fields_of(ScoreSummary),
    "calibration_bin": lambda: fields_of(CalibrationBin),
    "bootstrap_result": lambda: fields_of(BootstrapResult),
    "check_report": lambda: fields_of(CheckReport),
    "scoring_status": lambda: fields_of(ScoringStatus),
    "book_coverage": lambda: set(
        next(iter(book_coverage([date(2026, 1, 1)], [], date(2026, 1, 1), date(2026, 1, 2)).values()))
    ),
    "paper_account": lambda: set(inspect.signature(PaperAccount.__init__).parameters) - {"self"},
    "account_state": lambda: fields_of(AccountState),
    "equity_history": lambda: set(EQUITY_COLUMNS),
    "trade_line": lambda: fields_of(TradeLine),
    "desk_event": lambda: fields_of(DeskEvent),
}


TYPED_RECORDS = {  # the records with Python types: the schema's type must match the field's annotation
    "score_summary": ScoreSummary,
    "calibration_bin": CalibrationBin,
    "bootstrap_result": BootstrapResult,
    "check_report": CheckReport,
    "scoring_status": ScoringStatus,
    "account_state": AccountState,
    "trade_line": TradeLine,
    "desk_event": DeskEvent,
}
SCHEMA_TYPES = {"number": (float, int), "integer": (int,), "string": (str, date, datetime), "boolean": (bool,)}


def x_record_nodes(node):
    """(x-record, the schema node that carries it) of every field marked built."""
    if isinstance(node, dict):
        if "x-record" in node:
            yield node["x-record"], node
        for value in node.values():
            yield from x_record_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from x_record_nodes(value)


def catalog_nodes() -> list[tuple[str, dict]]:
    folder = CONTRACT_FOLDER / "api" / "schemas"
    return [
        pair
        for path in sorted(folder.glob("fno-*.yaml"))
        for pair in x_record_nodes(yaml.safe_load(path.read_text("utf-8")))
    ]


def catalog_records() -> list[str]:
    return sorted({record for record, _ in catalog_nodes()})


def annotation(cls, name: str):
    """A field's or a property's type, without None and with a tuple's element type (an interval is two numbers)."""
    hint = typing.get_type_hints(cls).get(name) or typing.get_type_hints(getattr(cls, name).fget)["return"]
    args = [a for a in typing.get_args(hint) if a is not type(None)] if isinstance(hint, types.UnionType) else [hint]
    return tuple(typing.get_args(a)[0] if typing.get_origin(a) is tuple else a for a in args)


def payload_of(name: str) -> dict:
    return copy.deepcopy(CATALOG[name]["value"])


def validated(operation: str, value: dict) -> None:
    value["payload_sha256"] = hashlib.sha256(canonical(value["payload"])).hexdigest()
    CONTRACT.validate(SCREENS[operation], value)


def test_the_catalog_has_every_screen_in_its_three_cases_all_labelled_mock():
    for operation in SCREENS:
        examples = [e for name, e in CATALOG.items() if name.startswith(operation + "_")]
        assert {e["x-case"] for e in examples} >= {"positive", "negative", "empty"}, operation
        assert all(e["summary"].startswith("Mock") for e in examples), operation


@pytest.mark.parametrize("name", sorted(CATALOG))
def test_every_catalog_example_validates_here_and_carries_this_repositorys_hash(name):
    value = CATALOG[name]["value"]
    CONTRACT.validate(SCREENS[name.split("_")[0]], value)
    assert value["payload_sha256"] == hashlib.sha256(canonical(value["payload"])).hexdigest()
    assert value["schema_version"] == CONTRACT.version and value["product"] == "fno" and value["market"] == "india"
    assert value["page_key"] == PAGES[name.split("_")[0]]


def test_every_built_field_names_a_record_field_that_exists_here():
    records = catalog_records()
    assert len(records) >= 15  # the catalog marks real records, not a token few
    missing = [r for r in records if r.split(":")[1] not in RECORD_FIELDS[r.split(":")[0]]()]
    assert missing == []


def test_every_built_field_has_the_type_of_its_typed_record_field():
    wrong = []
    for record, node in catalog_nodes():
        cls, name = TYPED_RECORDS.get(record.split(":")[0]), record.split(":")[1]
        types_ = [
            t
            for t in ([node.get("type")] if isinstance(node.get("type"), str) else node.get("type", []))
            if t != "null"
        ]
        if cls and not all(
            issubclass(typing.get_origin(a) or a, SCHEMA_TYPES[types_[0]]) for a in annotation(cls, name)
        ):
            wrong.append(f"{record}: {types_[0]} vs {annotation(cls, name)}")
    assert wrong == []
    assert len([r for r, _ in catalog_nodes() if r.split(":")[0] in TYPED_RECORDS]) >= 10  # most built fields are typed


def test_a_strategy_lab_fixture_from_the_real_ledger_validates():
    trials = sum(1 for _ in csv.DictReader((ROOT / "research" / "ledger.csv").open(encoding="utf-8")))
    value = payload_of("getFnoStrategyLab_india_none")
    value["payload"]["factory"]["trials_total"] = (
        trials  # built today; by_status waits for R1's status column (not built)
    )
    value["payload"]["ideas"] = []
    validated("getFnoStrategyLab", value)
    assert trials >= 53


def test_a_paper_trades_fixture_from_a_fresh_account_validates():
    state = account_state(STARTING_CASH_RS, [], {})
    value = payload_of("getFnoPaperTrades_india_none")
    for account in value["payload"]["accounts"]:
        account |= {
            "opening_value": state.starting_cash,
            "value": state.marked_equity,
            "cash": state.cash,
            "open_trades": state.open_trades,
        }
    validated("getFnoPaperTrades", value)


def forecast_status(record: ForecastRecordV2) -> str:
    """A live forecast generated after its deadline is late and never counted (judge 102 must-fix 1)."""
    return "counted" if record.on_time else "late"


def test_a_forecast_lab_fixture_from_the_live_forecasts_of_14_october_shows_them_late():
    with LIVE_FORECASTS.open(encoding="utf-8") as handle:
        records = [ForecastRecordV2.from_row(row) for row in csv.DictReader(handle)]
    q1 = [r for r in records if r.record.question.startswith("q1_") and r.record.probability is not None]
    value = payload_of("getFnoForecastLab_india_waiting")
    question = value["payload"]["questions"][0]
    assert question["id"] == "Q1" and q1
    question["today"] = {
        "made_on": q1[0].record.date.isoformat(),
        "answer_on": "2026-11-11",
        "values": [
            {
                "forecaster": r.record.book,
                "probability": r.record.probability,
                "variance": None,
                "status": forecast_status(r),
            }
            for r in q1
        ],
    }
    validated("getFnoForecastLab", value)
    assert {v["status"] for v in question["today"]["values"]} == {"late"}  # generated at 19:27 IST, after 15:15


def test_a_renamed_field_fails_validation():
    value = payload_of("getFnoCard_india_trade")
    value["payload"]["trade"]["entry_range"] = value["payload"]["trade"].pop("entry")
    with pytest.raises(ContractBroken, match="entry_range"):
        validated("getFnoCard", value)


def test_no_example_names_a_strategy_internal_and_the_card_says_paper_only():
    def keys(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key
                yield from keys(value)
        elif isinstance(node, list):
            for value in node:
                yield from keys(value)

    assert [k for e in CATALOG.values() for k in keys(e["value"]["payload"]) if PRIVATE.search(k)] == []
    assert all(
        e["value"]["payload"]["label"] == "PAPER ONLY" for n, e in CATALOG.items() if n.startswith("getFnoCard_")
    )
