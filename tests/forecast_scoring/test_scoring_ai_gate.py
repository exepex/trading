"""Story G4's AI reader through F1's one scoring rule (`fno.ai.scoring_gate.scoring_status`, judge 62 addendum 1):
a transcript breach is unscored, a day awaiting its audit is pending, and neither is scored or counted in coverage.
The files are written the way F1 writes them (fire log, collection audit, `TranscriptAudits.record`)."""

from __future__ import annotations

import json
from datetime import date, datetime

from fno.ai.paths import audit_path, fired_path, records_path
from fno.ai.transcript_audit import TranscriptAudits, new_audit
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, FORECAST_QUESTIONS
from fno.forecast.record_files import records_csv_v2
from fno.forecast.schema import ForecastRecord
from fno.forecast.schema_v2 import ForecastRecordV2
from fno.forecast_scoring.ai_sources import ai_forecasts
from fno.forecast_scoring.coverage import book_coverage
from fno.forecast_scoring.score_inputs import LIVE, ScoredForecast
from fno.forecast_scoring.score_report import ReportContext, report_document, weekly_summary
from fno.models import IST

DAY, AS_OF, PACK = date(2026, 10, 14), date(2026, 10, 15), "b" * 64
FIRE = {"fired": True, "version": "v1", "session": "https://claude.ai/code/session_x"}


def write_day(root, book, status="on_time", pack=PACK):
    """One AI book-day as F1 leaves it after collection: the fire log entry, five records and the collection audit."""
    cutoff, generated = (datetime(2026, 10, 14, h, m, tzinfo=IST) for h, m in ((15, 0), (15, 10)))
    records = [ForecastRecordV2(ForecastRecord(book, DAY, cutoff, q, 0.6, f"{book}/v1/sha256:{'c' * 64}", pack),
                                LIVE, "interpolated", generated) for q in FORECAST_QUESTIONS]  # fmt: skip
    fired = root / fired_path(DAY)
    fired.parent.mkdir(parents=True, exist_ok=True)
    log = json.loads(fired.read_text()) if fired.is_file() else {}
    fired.write_text(json.dumps({**log, book: FIRE}))
    (root / records_path(DAY, book)).write_text(records_csv_v2(records), encoding="utf-8")
    audit = {"book": book, "day": DAY.isoformat(), "status": status, "isolation": "sealed_same_day"}
    (root / audit_path(DAY, book)).write_text(json.dumps(audit), encoding="utf-8")


def transcript(root, book, breaches):
    audit = new_audit(DAY, book, FIRE, breaches, "opened research/forecasts/live_v2", "judge 62",
                      datetime(2026, 10, 14, 18, tzinfo=IST))  # fmt: skip
    TranscriptAudits(root).record(DAY, audit)


def test_a_planted_transcript_breach_is_unscored_and_not_covered(tmp_path):
    write_day(tmp_path, BOOK2_HYBRID)
    write_day(tmp_path, BOOK3_AI)
    transcript(tmp_path, BOOK2_HYBRID, ["read_other_records"])
    transcript(tmp_path, BOOK3_AI, [])
    out = ai_forecasts(tmp_path, {DAY: PACK}, {})
    assert {f.book for f in out.forecasts} == {BOOK3_AI} and out.pending == []
    assert out.unscored == [{"day": "2026-10-14", "book": BOOK2_HYBRID,
                             "reason": "transcript breach: read_other_records"}]  # fmt: skip
    book1 = [ScoredForecast(LIVE, BOOK1_RULES, DAY, q, 0.5, "interpolated") for q in FORECAST_QUESTIONS]
    cov = book_coverage([DAY], book1 + out.forecasts, DAY, AS_OF)
    assert cov[BOOK2_HYBRID] == {"counted_days": 0, "pack_days": 1} and cov[BOOK3_AI]["counted_days"] == 1
    context = ReportContext(AS_OF, {}, False, 0, (), DAY, cov, {}, tuple(out.unscored), tuple(out.pending))
    document = report_document(context, [])
    assert document["unscored_ai_days"][0]["reason"] == "transcript breach: read_other_records"
    assert "AI book-days not scored: 1 unscored, 0 pending audit" in weekly_summary(document)


def test_a_day_awaiting_its_transcript_audit_is_pending_then_scored_once_clean(tmp_path):
    write_day(tmp_path, BOOK2_HYBRID)  # one of the first 10 fired days: every session is audited
    out = ai_forecasts(tmp_path, {DAY: PACK}, {})
    assert out.forecasts == [] and out.unscored == []
    assert out.pending == [{"day": "2026-10-14", "book": BOOK2_HYBRID, "reason": "transcript audit due"}]
    assert book_coverage([DAY], out.forecasts, DAY, AS_OF)[BOOK2_HYBRID]["counted_days"] == 0
    transcript(tmp_path, BOOK2_HYBRID, [])
    cleared = ai_forecasts(tmp_path, {DAY: PACK}, {})
    assert (
        len(cleared.forecasts) == 5
        and cleared.pending == []
        and cleared.isolation == {BOOK2_HYBRID: {"sealed_same_day"}}
    )


def test_withdrawn_collections_are_unscored_with_the_gate_reason(tmp_path):
    write_day(tmp_path, BOOK2_HYBRID, status="exposed")
    write_day(tmp_path, BOOK3_AI, status="model_mismatch")
    out = ai_forecasts(tmp_path, {DAY: PACK}, {})
    assert out.forecasts == [] and {(e["book"], e["reason"]) for e in out.unscored} == {
        (BOOK2_HYBRID, "exposed"), (BOOK3_AI, "model_mismatch")
    }  # fmt: skip


def test_a_scored_day_still_needs_its_verified_pack(tmp_path):
    write_day(tmp_path, BOOK3_AI, pack="d" * 64)
    transcript(tmp_path, BOOK3_AI, [])
    assert "another pack" in ai_forecasts(tmp_path, {DAY: PACK}, {}).unscored[0]["reason"]
    assert "receipt" in ai_forecasts(tmp_path, {}, {}).unscored[0]["reason"]
