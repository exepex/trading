"""Story F1t criterion 3c (revision 2): a misreported model, found in the transcript, is a breach that the decision stop
rule counts beside the transcript breaches (two in the last 20 decision days, under the same version, stop the book)."""

from datetime import date, datetime

import pytest

from fno.ai.transcript_audit import TranscriptAudits, new_audit
from fno.ai_trading.model_audit import MATCH, MISREPORTED, ModelAuditRefused, ModelAudits, decision_stop_reason
from fno.models import IST

from .builders import TERMS

NOW = datetime(2026, 10, 20, 18, 0, tzinfo=IST)
DAYS = [date(2026, 10, d) for d in (12, 13, 14, 15, 16)]
V1, V2 = "book2_hybrid/decision/v1", "book2_hybrid/decision/v2"


def misreport(root, day, version=V1, result=MISREPORTED):
    return ModelAudits(root).record(day, "book2_hybrid", version, result, "tool said x, answer said y", "judge", NOW)


def breach(root, day, version=V1):
    fired = {"fired": True, "version": version, "session": "https://x.invalid/cse_1"}
    audit = new_audit(day, "book2_hybrid", fired, ["file_outside_input"], "read journal/", "judge", NOW)
    TranscriptAudits(root, TERMS).record(day, audit)


def stop(root, day=date(2026, 10, 19), version=V1):
    return decision_stop_reason(root, "book2_hybrid", version, day, TERMS, DAYS)


def test_one_misreport_still_fires_and_a_match_never_counts(tmp_path):
    misreport(tmp_path, DAYS[0])
    misreport(tmp_path, DAYS[1], result=MATCH)
    assert stop(tmp_path) == ""


def test_a_misreport_and_a_transcript_breach_stop_the_book(tmp_path):
    misreport(tmp_path, DAYS[0])
    breach(tmp_path, DAYS[2])
    assert stop(tmp_path).startswith("stopped: 2 breaches") and "2026-10-12, 2026-10-14" in stop(tmp_path)


def test_two_misreports_stop_and_a_new_version_starts_clean(tmp_path):
    misreport(tmp_path, DAYS[0])
    misreport(tmp_path, DAYS[1])
    assert stop(tmp_path) and stop(tmp_path, version=V2) == ""


def test_a_breach_and_a_misreport_on_the_same_day_count_once(tmp_path):
    misreport(tmp_path, DAYS[0])
    breach(tmp_path, DAYS[0])
    assert stop(tmp_path) == ""


def test_only_days_before_the_fire_count(tmp_path):
    misreport(tmp_path, DAYS[0])
    misreport(tmp_path, DAYS[4])
    assert stop(tmp_path, day=DAYS[4]) == ""


@pytest.mark.parametrize(("version", "result", "named"), [("", MISREPORTED, "fired version"), (V1, "maybe", "result")])
def test_a_malformed_record_is_refused_and_a_second_one_too(tmp_path, version, result, named):
    with pytest.raises(ModelAuditRefused, match=named):
        misreport(tmp_path, DAYS[0], version=version, result=result)
    misreport(tmp_path, DAYS[0])
    with pytest.raises(ModelAuditRefused, match="written once"):
        misreport(tmp_path, DAYS[0])
