"""G11's input to G8's looks: a confirmatory look refuses, recording nothing, while an AI audit of a day up to its date
is still open (judge 206); a later open audit, no file or an exploratory look do not stop it."""

from datetime import datetime, timedelta, timezone

import pytest

from fno.forecast_scoring.v4.audits import AuditFileError, LookBlocked, OpenAuditFile, require_settled
from fno.forecast_scoring.v4.cli import _look
from fno.forecast_scoring.v4.records import LookRecords, NoRegistrations
from fno.forecast_scoring.v4.scoring import V4Scoring
from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds
from fno.forecast_v4.terms import LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.test_records_and_report import OneForecaster, Outcomes

AT = datetime(2027, 5, 31, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))


def audits(tmp_path, *days, header="day,forecaster,question"):
    path = tmp_path / "open_audits.csv"
    path.write_text("\n".join([header, *(f"{d},book3_ai,v6_abs_move_2pct_next_session" for d in days)]) + "\n")
    return OpenAuditFile(path)


def test_an_open_audit_up_to_the_look_day_blocks_and_a_later_one_does_not(tmp_path):
    with pytest.raises(LookBlocked, match="2 still open, the earliest 2027-05-28"):
        require_settled(audits(tmp_path, "2027-05-31", "2027-05-28", "2027-06-01"), AT.date())
    require_settled(audits(tmp_path, "2027-06-01"), AT.date())
    require_settled(OpenAuditFile(tmp_path / "missing.csv"), AT.date())  # no AI book has an open audit


@pytest.mark.parametrize("header, day", [("day,book,question", "2027-05-28"), ("day,forecaster,question", "28/05")])
def test_a_broken_audit_file_stops_the_look(tmp_path, header, day):
    with pytest.raises(AuditFileError):
        audits(tmp_path, day, header=header).open_days()


def test_a_blocked_confirmatory_look_records_nothing_and_exits_1(tmp_path, capsys):
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    (tmp_path / "FREEZE_v4.md").write_text("# Freeze\nFrozen on: 2024-12-31\n")
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    blocked = _look(scoring, records, FrozenToolThresholds(tmp_path), audits(tmp_path, "2027-05-30"), LOOK_STOP_REVIEW,
                    AT)  # fmt: skip
    assert blocked == 1 and not records.path(LOOK_STOP_REVIEW).exists()
    assert "look NOT run, nothing recorded" in capsys.readouterr().out
    assert _look(scoring, records, FrozenToolThresholds(tmp_path), audits(tmp_path), LOOK_STOP_REVIEW, AT) == 0
    assert records.path(LOOK_STOP_REVIEW).exists()


def test_open_audits_never_stop_an_exploratory_look_before_the_freeze(tmp_path):
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    assert _look(scoring, records, FrozenToolThresholds(tmp_path), audits(tmp_path, "2027-05-30"), LOOK_STOP_REVIEW,
                 AT) == 0  # fmt: skip


def test_the_live_wiring_reads_g11s_committed_file():
    from fno.forecast_scoring.v4.wiring import OPEN_AUDITS_FILE, build_open_audits

    assert build_open_audits().path == OPEN_AUDITS_FILE
    assert OPEN_AUDITS_FILE.as_posix().endswith("research/forecasts/v4_audits/open_audits.csv")
    assert build_open_audits().open_days() == []  # no AI book runs yet
