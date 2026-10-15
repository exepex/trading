"""Story F8 criterion 6: a (session, day) is written once, only for complete IST days; attributions are checked."""

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
    assert any("not a complete day" in line for line in lines)


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
