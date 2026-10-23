"""Criterion 1: the FII statistics reader on the 2019 and 2026 layouts; participant volume through A8's reader."""

from __future__ import annotations

from datetime import date

import pytest

from fno.flow_history.values import FiiDerivativeStatsValues, ParticipantVolumeValues
from fno.fo_bhavcopy import BadFile
from fno.research_data.fii_derivative_stats import parse_fii_rows, read_fii_derivative_stats

from .sheets import participant_volume, sheet_2019, sheet_2026


def test_the_2019_layout_gives_the_four_groups_and_no_index_rows():
    stats = parse_fii_rows(sheet_2019(), "f", date(2019, 1, 2))
    flow = stats.groups["INDEX FUTURES"]
    assert (flow.buy_contracts, flow.sell_crores, flow.oi_contracts, flow.net_crores, flow.net_contracts) == (
        10, 2.5, 30, -1.0, -10)  # fmt: skip
    assert list(stats.groups) == ["INDEX FUTURES", "INDEX OPTIONS", "STOCK FUTURES", "STOCK OPTIONS"]
    assert stats.indices == {}


def test_the_2026_layout_keeps_the_per_index_rows():
    stats = parse_fii_rows(sheet_2026(), "f", date(2026, 10, 21))
    assert sorted(stats.indices) == ["BANKNIFTY FUTURES", "NIFTY FUTURES", "NIFTY OPTIONS"]
    assert stats.indices["NIFTY FUTURES"].buy_crores == 1.1


@pytest.mark.parametrize(("nifty_buy", "ok"), [("9", True), ("5", True), ("10", False), ("4", False)])
def test_index_rows_must_add_up_to_their_group_within_2_contracts(nifty_buy, ok):
    """Group 10 = BANKNIFTY 3 + NIFTY 7: NIFTY 9 or 5 is within NSE's rounding, 10 or 4 is not."""
    if ok:
        parse_fii_rows(sheet_2026(nifty_buy), "f", date(2026, 10, 21))
    else:
        with pytest.raises(BadFile, match="add up to"):
            parse_fii_rows(sheet_2026(nifty_buy), "f", date(2026, 10, 21))


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (sheet_2019("03-Jan-2019"), "the file is for"),
        ([["Some other sheet"]], "no 'FII DERIVATIVES STATISTICS"),
        (sheet_2019()[:3] + sheet_2019()[4:], "no row for"),
        (sheet_2019()[:3] + [["CURRENCY FUTURE", 1, 1, 1, 1, 1, 1]] + sheet_2019()[3:], "unknown row"),
        (sheet_2019()[:3] + [["INDEX FUTURES", "x", 1, 1, 1, 1, 1]] + sheet_2019()[4:], "not a number"),
        (sheet_2019()[:3] + [["INDEX FUTURES", 1.5, 1, 1, 1, 1, 1]] + sheet_2019()[4:], "contracts whole"),
        (sheet_2019()[:3] + [["INDEX FUTURES", 1, 1, 1]] + sheet_2019()[4:], "needs 6 numbers"),
        ([], "no 'FII DERIVATIVES STATISTICS"),
    ],
)
def test_a_sheet_outside_the_layout_is_refused_whole(rows, message):
    with pytest.raises(BadFile, match=message):
        parse_fii_rows(rows, "f", date(2019, 1, 2))


@pytest.mark.parametrize("data", [b"<html><body>Not found</body></html>", b"", b"\xd0\xcf\x11\xe0 damaged"])
def test_bytes_that_are_not_an_excel_97_workbook_are_refused(data):
    with pytest.raises(BadFile, match="not an Excel 97 workbook"):
        read_fii_derivative_stats(data, "fii_stats_02-Jan-2019.xls", date(2019, 1, 2))


def test_participant_volume_values_are_bought_and_sold_per_participant_and_group():
    triples = ParticipantVolumeValues().values(participant_volume(date(2026, 10, 19)), date(2026, 10, 19))
    assert ("FII:future_index", "bought", "1") in triples and ("Pro:total", "sold", "6") in triples
    assert len(triples) == 4 * 7 * 2  # participants x (6 groups + total) x (bought, sold)


def test_participant_volume_of_another_day_is_refused():
    with pytest.raises(BadFile):
        ParticipantVolumeValues().values(participant_volume(date(2026, 10, 19)), date(2026, 10, 20))


def test_fii_values_are_every_row_and_measure(monkeypatch):
    import fno.flow_history.values as values

    monkeypatch.setattr(values, "read_fii_derivative_stats",
                        lambda data, filename, day: parse_fii_rows(sheet_2026(), filename, day))  # fmt: skip
    triples = FiiDerivativeStatsValues().values(b"", date(2026, 10, 21))
    assert len(triples) == 7 * 6 and ("NIFTY FUTURES", "oi_crores", "2.5") in triples


def test_rows_without_a_participant_name_are_ignored_as_nse_left_them_in_2021_and_2022():
    """15 Sep 2021, 14 and 18 Oct 2022: stray sums under TOTAL with an empty first cell."""
    from fno.research_data.participant_volume import read_participant_volume

    day = date(2026, 10, 19)
    data = participant_volume(day) + b",,,999,,12345,,,,\n,,,,,,,,,,,,,,\n"
    assert read_participant_volume(data, "f", day).totals["FII"].long == 6
    with pytest.raises(BadFile):  # a named row that breaks the identities is still refused
        read_participant_volume(data.replace(b"FII,1,", b"FII,9,"), "f", day)


def test_a_fractional_contract_count_is_still_refused():
    """18 Mar 2019's file gives sixths of a contract: a sourced exception, never read as whole contracts."""
    from fno.research_data.participant_volume import read_participant_volume

    day = date(2026, 10, 19)
    with pytest.raises(BadFile, match="not a whole number"):
        read_participant_volume(participant_volume(day).replace(b"Client,1,", b"Client,1.1667,"), "f", day)


def test_the_18_march_2019_volume_file_is_a_sourced_exception():
    """Judge 437 add. 1: removing the row would turn the coverage check's explained day into a silent gap."""
    from fno.storage.raw_source import ParticipantVolumeSource
    from fno.storage.wiring import build_file_exceptions

    reason = build_file_exceptions()[(ParticipantVolumeSource.dataset, date(2019, 3, 18))]
    assert "fractional contract counts" in reason


def test_the_30_july_2019_fii_file_is_a_sourced_exception():
    """NSE serves an .xlsx under the .xls name that day; the explained day must not become a silent gap."""
    from fno.storage.raw_source import FiiDerivativeStatsSource
    from fno.storage.wiring import build_file_exceptions

    assert "Excel 2007+" in build_file_exceptions()[(FiiDerivativeStatsSource.dataset, date(2019, 7, 30))]
