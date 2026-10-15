"""Story F8 criterion 6: a (session, day) is written once, only for complete IST days; attributions are checked."""

from dataclasses import replace
from datetime import date

import pytest

from fno.budget.usage_export import ExportFileUsageReader
from fno.budget.usage_ledger import COLUMNS, LEDGER_FILE, Attribution, UsageLedger, UsageRefused
from tests.budget.exports import REPLY, TWO_DAYS, export, write_export

BUILDER = Attribution("development", "", "builder")


def record(tmp_path, today=date(2026, 10, 16), who=BUILDER):
    days = ExportFileUsageReader(write_export(tmp_path, export(TWO_DAYS))).days()
    return UsageLedger(tmp_path).record(days, who, today)


def test_complete_days_are_recorded_with_the_ledger_columns(tmp_path):
    record(tmp_path)
    text = (tmp_path / LEDGER_FILE).read_text(encoding="utf-8")
    assert text.splitlines()[0] == ",".join(COLUMNS) and REPLY not in text
    rows = UsageLedger(tmp_path).rows()
    assert [(r["date"], r["minutes"], r["output_tokens"]) for r in rows] == [("2026-10-14", "1.00", "100"),
                                                                             ("2026-10-15", "2.00", "200")]  # fmt: skip


def test_today_is_not_recorded_until_it_is_complete(tmp_path):
    lines = record(tmp_path, today=date(2026, 10, 15))
    assert [r["date"] for r in UsageLedger(tmp_path).rows()] == ["2026-10-14"]
    assert any("not complete in this reading" in line for line in lines)


def test_a_recorded_day_is_never_rewritten(tmp_path):
    record(tmp_path)
    before = (tmp_path / LEDGER_FILE).read_bytes()
    lines = record(tmp_path)
    assert (tmp_path / LEDGER_FILE).read_bytes() == before
    assert all("already recorded" in line for line in lines)


@pytest.mark.parametrize(
    "who",
    [
        Attribution("fun", "", "x"),
        Attribution("development", "book2_hybrid"),
        Attribution("books_and_roles", "book9"),
        Attribution("books_and_roles"),
    ],  # fmt: skip
)
def test_a_bad_attribution_is_refused(tmp_path, who):
    with pytest.raises(UsageRefused):
        record(tmp_path, who=who)
    assert not (tmp_path / LEDGER_FILE).exists()


def test_a_ledger_with_other_columns_is_refused(tmp_path):
    (tmp_path / "accounting").mkdir()
    (tmp_path / LEDGER_FILE).write_text("date,minutes\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columns"):
        UsageLedger(tmp_path).rows()


def test_a_day_still_running_at_the_capture_is_not_frozen_short(tmp_path, monkeypatch, capsys):
    """Reviewer finding: an export read on 15 Oct at 09:00 IST, recorded on 16 Oct, must not record 15 Oct."""
    from datetime import datetime
    from types import SimpleNamespace

    from fno import models
    from fno.budget import cli, wiring

    monkeypatch.setattr(wiring, "build_usage_ledger", lambda: UsageLedger(tmp_path))
    monkeypatch.setattr(models, "now_ist", lambda: datetime(2026, 10, 16, 9, 0, tzinfo=models.IST))
    path = write_export(tmp_path, export(TWO_DAYS, captured_at="2026-10-15T09:00:00+05:30"))
    args = SimpleNamespace(
        budget_cmd="record-usage", export=path, self_timed=False, purpose="development", book="", role="judge"
    )
    assert cli.cmd_budget(args) == 0
    assert [r["date"] for r in UsageLedger(tmp_path).rows()] == ["2026-10-14"]
    assert "2026-10-15 is not complete in this reading (complete days are before 2026-10-15)" in capsys.readouterr().out


@pytest.mark.parametrize("session_id", ["cse_01TESTxyz", " session_01TESTxyz", "session_01-x", "https://x/session_1"])
def test_a_session_id_not_in_get_session_form_is_refused(tmp_path, session_id):
    days = ExportFileUsageReader(write_export(tmp_path, export(TWO_DAYS))).days()
    odd = [replace(d, session_id=session_id) for d in days]
    with pytest.raises(UsageRefused, match="is not of the form session_"):
        UsageLedger(tmp_path).record(odd, BUILDER, date(2026, 10, 16))


def test_a_damaged_ledger_is_refused_not_read_as_fewer_rows(tmp_path):
    record(tmp_path)
    path = tmp_path / LEDGER_FILE
    path.write_text(path.read_text(encoding="utf-8").rstrip("\n") + ",extra\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 3: wrong number of fields"):
        UsageLedger(tmp_path).rows()
    path.write_text(path.read_text(encoding="utf-8").replace(",extra", "").replace(",1.00,", ",one,"), encoding="utf-8")
    with pytest.raises(ValueError, match="line 2: minutes 'one'"):
        UsageLedger(tmp_path).rows()


def test_nan_minutes_are_refused(tmp_path):
    record(tmp_path)
    path = tmp_path / LEDGER_FILE
    path.write_text(path.read_text(encoding="utf-8").replace(",1.00,", ",nan,"), encoding="utf-8")
    with pytest.raises(ValueError, match="line 2: minutes 'nan'"):
        UsageLedger(tmp_path).rows()


def test_the_ledger_is_replaced_whole_and_leaves_no_temporary_file(tmp_path):
    record(tmp_path)
    assert not list((tmp_path / "accounting").glob("*.tmp"))
    assert (tmp_path / LEDGER_FILE).read_text(encoding="utf-8").endswith("\n")


def test_a_data_routine_session_is_recorded_under_its_own_purpose(tmp_path):
    record(tmp_path, who=Attribution("data_routines", "", "3 pm quote recorder"))
    assert {r["purpose"] for r in UsageLedger(tmp_path).rows()} == {"data_routines"}
