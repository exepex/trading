"""Story P2b (screen W3b): the `forecast_lab` page from G4's reports and the committed forecast records. Criterion 1
(real source, every number re-read), 3 (in test_contract_log_line.py) and 4 (never sent: an AI book's reasons, its
version, its session). Criterion 2 does not apply: every input is committed and public."""

import copy
import json
from datetime import date
from pathlib import Path

import pytest

from fno.ai.paths import AI_FOLDER
from fno.constants import V4_QUESTIONS
from fno.forecast.capture import LIVE_FOLDER
from fno.forecast.record_files import read_records_v2
from fno.forecast_scoring.wiring import SCORES_FOLDER
from fno.market_read_models.blocks import SessionRows
from fno.market_read_models.contract import ContractBroken
from fno.market_read_models.forecast_history_inputs import ScoreReportsReader
from fno.market_read_models.forecast_lab_block import V4_IDS, FnoForecastLabBlock
from fno.market_read_models.forecast_lab_inputs import ForecastLabInputs, ForecastLabReader, SessionsAhead
from fno.market_read_models.forecast_questions import V3_QUESTIONS
from fno.market_read_models.home_blocks import FiguresNotComputed
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.wiring import build_forecast_lab_inputs, build_pinned_contract
from fno.storage.wiring import build_session_calendar

ROOT = Path(__file__).parents[2]
CALENDAR = build_session_calendar()
IDS = {question: contract_id for question, (contract_id, _) in V3_QUESTIONS.items()}


def published(inputs: ForecastLabInputs) -> dict:
    """The stored payload, after the publication checked it against the pinned contract as stored and as served."""
    rows = SessionRows(inputs.day, [], [], [], [], forecast_lab=inputs)
    builder = PublicationBuilder([FnoForecastLabBlock()], build_pinned_contract(), "c" * 40)
    return builder.build(rows).records["forecast_lab"]["payload"]


def real(day: date) -> ForecastLabInputs:
    return build_forecast_lab_inputs(CALENDAR).on(day)


def report_of(day: date) -> dict:
    return json.loads((ROOT / SCORES_FOLDER / f"{day.isoformat()}.json").read_text())


def test_every_score_and_comparison_is_g4s_live_mode_of_its_latest_report():
    day = date(2026, 10, 16)
    page, report = published(real(day)), report_of(day)
    live = next(m for m in report["modes"] if m["mode"] == "live_1500_proxy")
    for q in page["questions"]:
        question = next(k for k, v in IDS.items() if v == q["id"])
        expected = [(s["forecaster"], s["primary"]["scored"], s["counts"]["no_forecast"], s["primary"]["mean_brier"])
                    for s in live["scores"] if s["question"] == question]  # fmt: skip
        got = [(p["forecaster"], p["n"], p["n_missing"], p["mean_loss"]) for p in q["scores"]["per_forecaster"]]
        assert got == expected and got
        rows = [c for c in live["primary"] if c["question"] == question]
        assert [(c["forecaster"], c["baseline"], c["n_pairs"]) for c in q["scores"]["comparisons"]] == [
            (c["first"], c["second"], c["n"]) for c in rows
        ]
        assert q["primary_baseline"] == "book1_rules" and q["scores"]["n_needed"] == 40
    assert page["standing"] == report["standing"]
    assert page["protocols"][0] == {"version": "v3", "status": "frozen", "questions": ["Q1", "Q2", "Q3", "Q4", "Q5"],
                                    "frozen_commit": report["inputs"]["protocol_v3_commit"]}  # fmt: skip


def test_coverage_is_g4s_pack_and_counted_days_split_by_why_the_rest_did_not_count():
    page = published(real(date(2026, 10, 16)))
    coverage = report_of(date(2026, 10, 16))["coverage"]
    by_id = {f["id"]: f for f in page["forecasters"]}
    for book, counted in coverage.items():
        c = by_id[book]["coverage"]
        assert (c["pack_days"], c["counted_days"]) == (counted["pack_days"], counted["counted_days"])
        assert c["counted_days"] + c["missing_days"] + c["late_days"] + c["unscored_days"] == c["pack_days"]
    # 14 Oct: Book 1's records were generated at 19:27 IST (late); the AI books sent nothing (missing). 15 Oct: Book 1
    # on time; the AI books late (G5's reason)
    assert by_id["book1_rules"]["coverage"] == {"pack_days": 2, "counted_days": 1, "missing_days": 0,
                                                     "late_days": 1, "unscored_days": 0}  # fmt: skip
    assert all(by_id[b]["coverage"]["late_days"] == 1 and by_id[b]["coverage"]["missing_days"] == 1
               for b in ("book2_hybrid", "book3_ai"))  # fmt: skip
    assert all(by_id[b]["coverage"] is None for b in by_id if b.startswith("baseline_"))  # G4 measures books only


def test_todays_values_are_the_sessions_own_records_and_a_report_before_the_ai_records_leaves_them_pending():
    day = date(2026, 10, 15)
    page = published(real(day))
    records = read_records_v2((ROOT / LIVE_FOLDER / "2026" / "2026-10-15_forecasts.csv").read_text())
    for q in page["questions"]:
        question = next(k for k, v in IDS.items() if v == q["id"])
        said = {r.record.book: r.record.probability for r in records if r.record.question == question}
        values = {v["forecaster"]: v for v in q["today"]["values"]}
        assert {b: v["probability"] for b, v in values.items() if not b.startswith("book2") and
                not b.startswith("book3")} == {b: p for b, p in said.items() if p is not None}  # fmt: skip
        assert all(values[b]["status"] == "counted" for b in said if said[b] is not None)
        assert values["book2_hybrid"]["status"] == values["book3_ai"]["status"] == "pending"  # G4 ran before them
        assert q["today"]["answer_on"] == SessionsAhead(CALENDAR)(day, q["horizon_sessions"]).isoformat()
    assert q["today"]["made_on"] == "2026-10-15"


def g4_report(unscored=(), pending=(), allowed=False, primary=(), as_of="2026-10-20") -> dict:
    report = copy.deepcopy(report_of(date(2026, 10, 16)))
    report |= {"as_of": as_of, "confirmatory_allowed": allowed, "unscored_ai_days": list(unscored),
               "pending_ai_days": list(pending)}  # fmt: skip
    live = next(m for m in report["modes"] if m["mode"] == "live_1500_proxy")
    live["primary"] = list(primary) or live["primary"]
    return report


def lab_on(tmp_path, report: dict, day: date, ai_folder: Path = ROOT / AI_FOLDER) -> ForecastLabInputs:
    scores = tmp_path / "scores"
    scores.mkdir(exist_ok=True)
    (scores / f"{report['as_of']}.json").write_text(json.dumps(report))
    reader = ForecastLabReader(ScoreReportsReader(scores), [ROOT / LIVE_FOLDER, ai_folder], SessionsAhead(CALENDAR))
    return reader.on(day)


def ai_records_with_probabilities(tmp_path) -> Path:
    """The two AI books' real 15 Oct records, each probability filled in (0.5) as an on-time collection would."""
    folder = tmp_path / "ai" / "2026"
    folder.mkdir(parents=True)
    for book in ("book2_hybrid", "book3_ai"):
        name = f"2026-10-15_{book}_forecasts.csv"
        lines = (ROOT / AI_FOLDER / "2026" / name).read_text().splitlines()
        cells = [line.split(",") for line in lines[1:]]
        rows = [",".join([*c[:4], "0.5", *c[5:9], "2026-10-15T15:10:00+05:30"]) for c in cells]
        (folder / name).write_text("\n".join([lines[0], *rows]) + "\n")
    return tmp_path / "ai"


@pytest.mark.parametrize(
    ("reason", "status"),
    [("late", "late"), ("model_mismatch", "model_mismatch"), ("exposed", "breach"),
     ("transcript breach: tool call", "breach"), ("no_submission", None), ("invalid", None)],
)  # fmt: skip
def test_an_ai_books_status_is_g5s_reason_and_a_book_that_gave_nothing_is_left_out(tmp_path, reason, status):
    day = date(2026, 10, 15)
    held = [{"day": day.isoformat(), "book": "book3_ai", "reason": reason}]
    page = published(lab_on(tmp_path, g4_report(unscored=held, as_of=day.isoformat()), day))
    values = {v["forecaster"]: v["status"] for v in page["questions"][0]["today"]["values"]}
    assert values.get("book3_ai") == status
    assert values["book2_hybrid"] == "pending"  # listed nowhere, no probability recorded


def test_a_listed_pending_day_is_pending_and_an_unlisted_day_with_a_probability_is_counted(tmp_path):
    held = [{"day": "2026-10-15", "book": "book2_hybrid", "reason": "transcript audit due"}]
    report = g4_report(pending=held, as_of="2026-10-15")
    page = published(lab_on(tmp_path, report, date(2026, 10, 15), ai_records_with_probabilities(tmp_path)))
    values = {v["forecaster"]: v for v in page["questions"][1]["today"]["values"]}
    assert values["book2_hybrid"]["status"] == "pending" and values["book3_ai"]["status"] == "counted"
    assert values["book3_ai"]["probability"] == 0.5


def comparison(k, tested, significant, diff) -> dict:
    return {"first": "book2_hybrid", "second": "book1_rules", "k": k, "question": "q1_nifty_up_20d", "n": 60,
            "tested": tested, "holm_significant": significant, "mean_brier_difference": diff, "p_value": 0.01,
            "interval_unadjusted_95": [diff - 0.01, diff + 0.01]}  # fmt: skip


@pytest.mark.parametrize(
    ("allowed", "tested", "significant", "diff", "verdict"),
    [(True, False, None, -0.02, "not_tested"), (False, True, True, -0.02, "before_review"),
     (True, True, True, -0.02, "better"), (True, True, True, 0.02, "worse"),
     (True, True, False, -0.02, "no_difference")],
)  # fmt: skip
def test_a_verdict_is_never_given_before_the_review_and_an_untested_comparison_has_no_p_value(
    tmp_path, allowed, tested, significant, diff, verdict
):
    report = g4_report(allowed=allowed, primary=[comparison(1, tested, significant, diff)])
    page = published(lab_on(tmp_path, report, date(2026, 10, 20)))
    (row,) = page["questions"][0]["scores"]["comparisons"]
    assert row["verdict"] == verdict and (row["p_value"] is None) == (not tested)
    assert row["mean_diff"] == diff and row["min_effect_met"] is None and row["futility_upper_bound"] is None


def test_v4_is_listed_as_a_draft_with_no_question_until_g6_freezes_it():
    page = published(real(date(2026, 10, 16)))
    assert page["protocols"][1] == {
        "version": "v4",
        "status": "draft",
        "frozen_commit": None,
        "questions": list(V4_IDS),
    }
    assert {q["protocol"] for q in page["questions"]} == {"v3"} and len(V4_IDS) == len(V4_QUESTIONS)
    assert not (ROOT / "research" / "forecasts" / "FREEZE_v4.md").exists(), "v4 is frozen: build its questions (P2b)"


def test_a_session_before_any_report_publishes_the_standing_and_no_scores(tmp_path):
    reader = ForecastLabReader(ScoreReportsReader(tmp_path), [tmp_path], SessionsAhead(CALENDAR))
    page = published(reader.on(date(2026, 10, 12)))
    assert page["standing"].startswith("Forecast scores are secondary to net profit")
    assert all(q["today"] is None and q["scores"]["per_forecaster"] == [] for q in page["questions"])
    assert {f["status"] for f in page["forecasters"]} == {"not_started"}


def test_coverage_that_does_not_add_up_stops_the_build_named(tmp_path):
    report = g4_report(as_of="2026-10-16")
    report["coverage"]["book1_rules"]["counted_days"] = 3  # more counted days than pack days
    with pytest.raises(FiguresNotComputed, match="book1_rules: G4's coverage does not add up"):
        published(lab_on(tmp_path, report, date(2026, 10, 16)))


def test_the_page_never_carries_an_ai_books_reasons_version_or_session():
    text = json.dumps([published(real(day)) for day in (date(2026, 10, 14), date(2026, 10, 15), date(2026, 10, 16))])
    assert "sha256:" not in text and "claude.ai" not in text and "cse_" not in text and "isolation:" not in text
    audit = json.loads((ROOT / AI_FOLDER / "2026" / "2026-10-15_book2_hybrid_audit.json").read_text())
    assert not any(a["reason"][:40] in text for a in audit["attempted"].values())


def test_a_bad_g4_figure_is_named_by_path_and_rule_never_by_value(tmp_path):
    row = comparison(1, False, None, -0.02) | {"n": -987654}  # n_pairs' minimum is 0
    with pytest.raises(ContractBroken) as broken:
        published(lab_on(tmp_path, g4_report(primary=[row]), date(2026, 10, 20)))
    assert "n_pairs: breaks 'minimum'" in str(broken.value) and "987654" not in str(broken.value)


def test_an_on_time_live_record_is_pending_until_g4_verified_its_day(tmp_path):
    report = g4_report(as_of="2026-10-15") | {"unverified_live_days": ["2026-10-15"]}
    report["coverage"]["book1_rules"]["counted_days"] = 0  # G4 never counts a day it could not verify
    page = published(lab_on(tmp_path, report, date(2026, 10, 15)))
    assert {v["forecaster"]: v["status"] for v in page["questions"][0]["today"]["values"]}["book1_rules"] == "pending"


def test_an_answer_day_beyond_nses_calendar_stops_the_publish_named_never_a_guessed_date():
    with pytest.raises(FiguresNotComputed, match="beyond NSE's session calendar: add NSE's 2027 holiday circular rows"):
        SessionsAhead(CALENDAR)(date(2026, 12, 3), 20)  # 20 sessions after 3 Dec 2026 reach 2027 (response 241)
    assert SessionsAhead(CALENDAR)(date(2026, 12, 2), 20) == date(2026, 12, 31)  # a target inside 2026 is answered
