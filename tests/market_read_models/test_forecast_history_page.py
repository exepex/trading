"""Story P2 (contract 2.9): the `forecast_history` page from G4's committed score reports. Every point is re-read from
the report files; live and back-fill never join; one point per report; one back-fill file per series."""

import copy
import json
from datetime import date

from fno.config import ROOT
from fno.forecast_scoring.wiring import SCORES_FOLDER
from fno.market_read_models.blocks import SessionRows
from fno.market_read_models.forecast_history_block import FnoForecastHistoryBlock, forecast_history
from fno.market_read_models.forecast_history_inputs import ScoreReportsReader
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.wiring import build_pinned_contract

DAY = date(2026, 10, 16)
# The reports the page may read on DAY: the scorer commits one a day, so later ones exist and must stay out
FILES = [p for p in sorted((ROOT / SCORES_FOLDER).glob("*.json")) if date.fromisoformat(p.stem) <= DAY]
LABEL = {"close_proxy": "backfill_exploratory", "live_1500_proxy": "live"}


def published(reports: list[dict]) -> dict:
    rows = SessionRows(DAY, [], [], [], [], score_reports=reports)
    builder = PublicationBuilder([FnoForecastHistoryBlock()], build_pinned_contract(), "c" * 40)
    return builder.build(rows).records["forecast_history"]["payload"]


def test_every_point_is_the_reports_own_scored_count_and_mean_brier():
    page = published(ScoreReportsReader(ROOT / SCORES_FOLDER).on(DAY))
    expected = {}
    for path in FILES:
        report = json.loads(path.read_text())
        for mode in report["modes"]:
            for s in mode["scores"]:
                if s["primary"]["scored"] >= 1:
                    label = LABEL[mode["mode"]]
                    sha = report["inputs"]["backfill_sha256"] if label == "backfill_exploratory" else None
                    key = (s["question"], label, s["forecaster"], sha)
                    expected.setdefault(key, []).append(
                        (report["as_of"], s["primary"]["scored"], s["primary"]["mean_brier"])
                    )
    ids = {"Q1": "q1_nifty_up_20d", "Q2": "q2_nifty_move_3pct_20d", "Q3": "q3_rv20_above_trailing",
           "Q4": "q4_vix_up_10d", "Q5": "q5_rv20_below_atm_iv30"}  # fmt: skip
    got = {(ids[q["id"]], s["label"], s["forecaster"], s["backfill_sha256"]):
           [(p["as_of"], p["n"], p["mean_loss"]) for p in s["points"]]
           for q in page["questions"] for s in q["series"]}  # fmt: skip
    assert got == expected and got  # the real reports up to DAY, one point each per series
    shas = {json.loads(p.read_text())["inputs"]["backfill_sha256"] for p in FILES}
    series = [s for q in page["questions"] for s in q["series"]]
    assert {s["backfill_sha256"] for s in series if s["label"] == "backfill_exploratory"} == shas
    assert all(s["backfill_sha256"] is None for s in series if s["label"] == "live")


def test_a_report_with_no_scored_answer_gives_no_point_and_the_live_mode_stays_apart():
    page = published(ScoreReportsReader(ROOT / SCORES_FOLDER).on(DAY))
    series = [s for q in page["questions"] for s in q["series"]]
    assert all(p["n"] >= 1 for s in series for p in s["points"])
    assert {s["label"] for s in series} <= {"live", "backfill_exploratory"}
    keys = {
        (q["id"], s["forecaster"], s["label"], s["backfill_sha256"]) for q in page["questions"] for s in q["series"]
    }
    assert len(keys) == len(series)  # a rebuilt back-fill is its own series (judge 231 note)


def test_a_rebuilt_back_fill_starts_a_new_series_and_never_joins_the_old_one():
    reports = [json.loads(p.read_text()) for p in FILES]
    old = reports[-1]["inputs"]["backfill_sha256"]
    rebuilt = copy.deepcopy(reports[-1]) | {"as_of": "2026-10-17"}
    rebuilt["inputs"] = rebuilt["inputs"] | {"backfill_sha256": "f" * 64}
    page = forecast_history([*reports, rebuilt])
    q1 = next(q for q in page["questions"] if q["id"] == "Q1")
    book1 = [s for s in q1["series"] if s["forecaster"] == "book1_rules" and s["label"] == "backfill_exploratory"]
    assert [s["backfill_sha256"] for s in book1] == [old, "f" * 64]
    assert [p["as_of"] for p in book1[0]["points"]] == [r["as_of"] for r in reports]
    assert [p["as_of"] for p in book1[1]["points"]] == ["2026-10-17"]


def test_no_report_gives_the_empty_page():
    assert published([]) == {"questions": []}
