"""FL1-1d: each edition is live from its own `forecast_lab.live_from` date (none: not live), and each commits only
its own receipts' folder."""

from datetime import date

from fno.config import load_app_config
from fno.forecast_lab.wiring import live_from, receipt_pathspecs


def test_each_edition_reads_its_own_live_date_and_none_is_set_in_the_repository():
    assert live_from({"forecast_lab": {"live_from": {"evening": "2026-11-02"}}}) == {
        "morning": None, "evening": date(2026, 11, 2)}  # fmt: skip
    assert live_from({}) == {"morning": None, "evening": None}
    live = date(2026, 10, 23)  # orchestrator, 22 Oct: both editions from Fri 23 Oct
    assert live_from(load_app_config()) == {"morning": live, "evening": live}


def test_each_edition_commits_only_its_own_receipts():
    assert receipt_pathspecs("morning") == ("receipts/data/forecast_lab/v1/morning/",)
    assert receipt_pathspecs("evening") == ("receipts/data/forecast_lab/v1/evening/",)


def test_the_reports_are_drawn_by_the_owner_s_signed_off_design():
    import inspect

    from fno.forecast_lab import page_wiring

    assert page_wiring.PICTURE_WIDTH == 1100 and "DesignRenderer()" in inspect.getsource(page_wiring.build_report_maker)
