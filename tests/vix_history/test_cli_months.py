"""Story A15: a month still running is never fetched, whatever `--to` says (judge 100, should-fix 2)."""

from argparse import Namespace
from datetime import date

from fno.vix_history import wiring
from fno.vix_history.cli import cmd_vix_history, months_to_fetch

AUG, SEP, OCT = date(2026, 8, 1), date(2026, 9, 1), date(2026, 10, 1)


def test_mid_month_the_running_month_is_left_out():
    assert months_to_fetch(AUG, None, date(2026, 10, 15)) == [AUG, SEP]


def test_asking_for_the_running_month_still_leaves_it_out():
    assert months_to_fetch(AUG, OCT, date(2026, 10, 15)) == [AUG, SEP]


def test_on_the_first_day_of_a_month_the_month_that_ended_yesterday_is_in():
    assert months_to_fetch(AUG, None, date(2026, 10, 1)) == [AUG, SEP]
    assert months_to_fetch(AUG, None, date(2026, 9, 30)) == [AUG]  # September still running on its last day


def test_an_earlier_end_is_kept_and_a_start_after_it_gives_nothing():
    assert months_to_fetch(AUG, AUG, date(2026, 10, 15)) == [AUG]
    assert months_to_fetch(SEP, AUG, date(2026, 10, 15)) == []


def test_without_a_start_it_begins_at_nses_first_month():
    assert months_to_fetch(None, None, date(2010, 9, 2))[0] == date(2010, 7, 1)


def test_a_start_before_nses_first_month_is_moved_to_it():
    assert months_to_fetch(date(2007, 11, 1), date(2010, 8, 1), date(2026, 10, 15)) == [
        date(2010, 7, 1),
        AUG.replace(2010),
    ]


def test_a_drive_or_setup_failure_stops_with_a_named_line_and_exit_1(monkeypatch, capsys):
    def no_drive():
        raise RuntimeError("set FNO_GDRIVE_FOLDER_ID to use the India VIX archive in Drive")

    monkeypatch.setattr(wiring, "build_vix_table", no_drive)
    assert cmd_vix_history(Namespace(action="verify", start=None, end=None)) == 1
    assert capsys.readouterr().out.startswith("STOPPED (RuntimeError): set FNO_GDRIVE_FOLDER_ID")
