"""Story O11, the built stages: 16 Oct 2026 replayed through O1's daily run, from the forecasts to the scoreboards.
Each stage's output exists and agrees with the one before it; a clean day sends no alert."""

import hashlib
import json

import pytest

from fno.books.account import PaperAccount
from fno.checks.validity_constitution import ConstitutionMode
from fno.checks.validity_envelope import EnvelopeMode
from fno.checks.wiring import build_trade_validator, validity_modes
from fno.config import load_app_config
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, DAILY_RUN_STEPS, OUTCOME_OPENED, REVIEWS_STEP
from fno.desk.records import DeskRecords
from fno.forecast_v4_rules import records as v4
from fno.forecast_v4_rules.records import LIVE
from fno.playbook import decision_run
from fno.quotes.recorder import DATASET
from fno.scoreboard.committed_runs import CommittedRuns
from fno.weather.records import WeatherRecords
from tests.desk.conftest import RecordingAlerts

from . import real_day as rd
from .replay import EXECUTION_ID, Replay

STEPS = [
    "weather",
    "forecasts_v4",
    "versions",
    "pack",
    "book1",
    "decisions",
    "snapshot",
    "fills",
    "exits",
    "trade_marks",
    REVIEWS_STEP,
    "price_distribution",  # G13
    "price_ranges",  # G13b
    "lab_close",  # FL1-1
]  # O1's DAILY_RUN_STEPS without the quote parts, the margin check, the card and the candles


def chosen_record(root) -> dict:
    runs = CommittedRuns(root)
    return next(r for run in runs.runs() for r in runs.records(run) if r["opportunity_id"] != "no_trade")


def test_weather_and_v4_forecasts_are_live_rows_of_the_day(day):
    out, root, _ = day
    weather = WeatherRecords(root / "weather").for_day(rd.DAY)
    assert weather["label"] == LIVE and weather["made_at"].startswith("2026-10-16T08:35")  # 14:05 IST, O1's start
    assert out.log.result("weather")["lines"][0].startswith("weather 2026-10-16: ")
    v4_line = out.log.result("forecasts_v4")["reason"]
    written = int(v4_line.split()[0])
    rows = {path.stem: row for path in (root / "v4").rglob("*.csv") for d, row in v4.read(path).items()
            if d == "2026-10-16"}  # fmt: skip
    assert len([*(root / "v4").rglob("*.csv")]) == written + 4  # G7's rows, the weather's 2 x 2
    assert {row.label for row in rows.values()} == {LIVE}
    waiting = {question for question, row in rows.items() if row.status != "ok"}
    assert waiting == {"v1_rv_next_session"}  # V1 waits for 20 A16 sessions (G7 phase 1); every other row is made


def test_the_pack_freezes_the_real_snapshot_and_the_previous_close(day):
    out, root, _ = day
    csv_path = root / rd.QUOTES / DATASET / "2026" / "10" / f"{rd.SNAPSHOT_ID}.csv"
    snapshot = out.pack.body["provenance"]["a4_snapshot"]
    assert snapshot["snapshot_id"] == rd.SNAPSHOT_ID
    assert snapshot["csv_sha256"] == hashlib.sha256(csv_path.read_bytes()).hexdigest()
    close = next(item["value"] for item in out.pack.body["items"] if item["name"] == "close:2026-10-15")
    assert close["nifty"] > 0 and close["vix"] > 0
    assert out.log.result("pack") == {"built": True, "sha256": out.pack.sha256}
    assert (root / "journal" / BOOK1_RULES / "packs" / "2026-10-16" / "private.sha256").is_file()


def test_book1_chooses_a_trade_on_the_pack_that_passes_risk_and_every_c4_check(day):
    out, root, _ = day
    record = chosen_record(root)
    assert record["chosen_action"] == "trade" and record["common_pack_sha256"] == out.pack.sha256
    assert record["risk"]["ok"] is True and record["risk"]["entry_cash_rs"] > 0
    c4 = record["validity"]["c4"]
    assert c4["ok"] is True and c4["checks"] and all(check["ok"] for check in c4["checks"])
    assert {"listing", "lot_size", "max_loss", "loss_limit", "bucket_cap"} <= {c["check"] for c in c4["checks"]}


def test_the_daily_run_collects_checks_fills_reviews_and_marks_the_same_trade(day):
    out, root, alerts = day
    log, record = out.log, chosen_record(root)
    assert list(log.steps) == STEPS and [s for s in DAILY_RUN_STEPS if s in STEPS] == STEPS
    assert all(log.result(name)["status"] == "ok" for name in ("weather", "forecasts_v4", "book1", REVIEWS_STEP))
    assert log.result("book1")["reason"].startswith("Book 1 2026-10-16: decided (2026-10-16-r1)")
    assert log.result("decisions")[BOOK1_RULES]["run_id"] == "2026-10-16-r1"
    snapshot = log.result("snapshot")
    assert snapshot["valid"] is True and snapshot["snapshot_id"] == EXECUTION_ID
    trade_id = f"2026-10-16-{record['opportunity_id']}"
    fill = log.result("fills")[trade_id]
    assert (fill["outcome"], fill["reason"], fill["sha256"]) == (OUTCOME_OPENED, "4 legs filled", snapshot["sha256"])
    legs = DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows()
    assert len(legs) == 4 and {leg["trade_id"] for leg in legs} == {trade_id}
    assert log.result("exits")[BOOK1_RULES]["results"] == [
        {"trade_id": trade_id, "outcome": "held", "reason": "no exit rule reached"}
    ]
    marks = log.result("trade_marks")[BOOK1_RULES]
    assert marks["marked"] and marks["equity_row"] and marks["trades"] == [{"trade_id": trade_id, "status": "valued"}]
    assert alerts.sent == []


def test_scorecard_and_both_scoreboards_read_the_same_trade_and_maximum_loss(day):
    out, root, _ = day
    record = chosen_record(root)
    trade_id = f"2026-10-16-{record['opportunity_id']}"
    max_loss = next(
        v["numbers"]["max_loss_rs"] for v in record["risk"]["verdicts"] if v["rule"] == "max_loss_per_trade"
    )
    (card,) = out.scorecards
    assert (card.account, card.strategy, card.costs.opened, out.pauses) == (BOOK1_RULES, "sc-a-v1", 1, [])
    book = out.board["books"][BOOK1_RULES]["overall"]
    assert book["trades"]["ids"] == [trade_id] and book["risk"]["max_loss_at_entry_rs"] == pytest.approx(max_loss)
    assert book["net_rs"] < 0  # one session held: the entry's charges and half-spread, nothing closed
    matched = out.matched["books"][BOOK1_RULES]
    assert (matched["eligible_days"], matched["pilot"]["takes"]["open"]) == (1, 1)
    assert json.dumps(out.board)  # the board is plain data, ready to publish


def test_the_days_trade_as_a_book2_or_book3_trade_is_refused_outside_the_envelope_and_the_constitution(
    tmp_path, monkeypatch
):
    """D4 and D5 merged: the recorded day's own chosen trade, checked by C4 as Book 2's and Book 3's at the same
    decision, is refused: no envelope permits it and no constitution registers it (none exists yet)."""
    seen, validate = {}, decision_run.validate_chosen

    def also_books_2_and_3(evaluation, validator, market, playbook, book):
        for name in (BOOK2_HYBRID, BOOK3_AI):
            other = build_trade_validator(load_app_config(), name, tmp_path, log=False)
            seen[name] = validate(evaluation, other, market, playbook, book)
        return validate(evaluation, validator, market, playbook, book)

    monkeypatch.setattr(decision_run, "validate_chosen", also_books_2_and_3)
    Replay(tmp_path, monkeypatch, RecordingAlerts()).run()
    (book2,), (book3,) = seen[BOOK2_HYBRID].values(), seen[BOOK3_AI].values()
    assert (book2.ok, book2.reason) == (False, "envelope: no trade envelope for sc-a v1")
    assert (book3.ok, book3.reason) == (False, "constitution: no constitution file matches the registered D6 component")
    assert isinstance(validity_modes()[BOOK2_HYBRID], EnvelopeMode)
    assert isinstance(validity_modes()[BOOK3_AI], ConstitutionMode)


def test_the_day_has_a_price_distribution_and_valuation_record(day):
    """G13 merged: O1's `price_distribution` step writes the day's live NIFTY record from the recorded chain: two
    expiries valued with their implied distributions, every rule forecaster at every horizon, no problem."""
    out, _, _ = day
    assert out.log.result("price_distribution")["status"] == "ok"
    (path,) = [p for p in out.distribution_drive.files if p.endswith(f"nifty_{rd.DAY.isoformat()}.json")]
    record = json.loads(out.distribution_drive.files[path])
    assert (record["label"], record["status"], record["problems"]) == ("live", "ok", [])
    assert [e["distribution"]["status"] for e in record["valuation"]["expiries"]] == ["ok", "ok"]
    assert len(record["forecasts"]) == 12 and {r["status"] for r in record["forecasts"]} == {"ok"}
