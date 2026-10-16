"""Story O11, the built stages: 16 Oct 2026 replayed from forecasts to the scoreboards. Each stage's output exists and
agrees with the one before it; a clean day sends no alert."""

import hashlib
import json

import pytest

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, OUTCOME_OPENED
from fno.desk.records import DeskRecords
from fno.forecast_v4_rules import records as v4
from fno.forecast_v4_rules.records import LIVE
from fno.quotes.recorder import DATASET
from fno.scoreboard.committed_runs import CommittedRuns
from fno.weather.records import WeatherRecords
from tests.desk.conftest import RecordingAlerts

from . import real_day as rd
from .replay import EXECUTION_ID, Replay

STEPS = ["versions", "pack", "decisions", "snapshot", "fills", "exits", "trade_marks"]


@pytest.fixture
def day(tmp_path, monkeypatch):
    alerts = RecordingAlerts()
    return Replay(tmp_path, monkeypatch, alerts).run(), tmp_path, alerts


def chosen_record(root) -> dict:
    runs = CommittedRuns(root)
    return next(r for run in runs.runs() for r in runs.records(run) if r["opportunity_id"] != "no_trade")


def test_weather_and_v4_forecasts_are_live_rows_of_the_day(day):
    out, root, _ = day
    weather = WeatherRecords(root / "weather").for_day(rd.DAY)
    assert weather["label"] == LIVE and weather["made_at"].startswith("2026-10-16T08:55")  # 14:25 IST
    assert out.forecast_lines[0].startswith("weather 2026-10-16: ") and out.forecast_rows > 0
    rows = {path.stem: row for path in (root / "v4").rglob("*.csv") for d, row in v4.read(path).items()
            if d == "2026-10-16"}  # fmt: skip
    assert len([*(root / "v4").rglob("*.csv")]) == out.forecast_rows + 4  # G7's rows, the weather's 2 x 2
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
    assert out.decision.startswith("Book 1 2026-10-16: decided (2026-10-16-r1)")
    assert record["chosen_action"] == "trade" and record["common_pack_sha256"] == out.pack.sha256
    assert record["risk"]["ok"] is True and record["risk"]["entry_cash_rs"] > 0
    c4 = record["validity"]["c4"]
    assert c4["ok"] is True and c4["checks"] and all(check["ok"] for check in c4["checks"])
    assert {"listing", "lot_size", "max_loss", "loss_limit", "bucket_cap"} <= {c["check"] for c in c4["checks"]}


def test_the_daily_run_collects_checks_fills_reviews_and_marks_the_same_trade(day):
    out, root, alerts = day
    log, record = out.log, chosen_record(root)
    assert list(log.steps) == STEPS
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
