"""Criteria 5 and 6 (story MS-P1a): the `school` block is read with exactly its keys, and the repository's is off."""

import pytest

from fno.config import load_app_config
from fno.school.settings import SchoolSettingsError, school_settings

GOOD = {"enabled": False, "reports": False, "first_counted": None, "account_rs": 2_000_000, "max_loss_rs": 10_000,
        "daily_stop_rs": 25_000, "brake_rs": 120_000, "max_new_trades_per_slot": 5, "bucket_rs": 30_000,
        "open_risk_rs": 150_000, "new_risk_day_rs": 50_000}  # fmt: skip


def test_the_repository_settings_are_off_with_todays_limits():
    settings = school_settings(load_app_config())
    assert settings.enabled is False and settings.reports is False and settings.first_counted is None
    assert (settings.max_loss_rs, settings.daily_stop_rs, settings.brake_rs) == (10_000, 25_000, 120_000)


def test_the_school_limits_equal_the_books_caps_today():
    books = load_app_config()["risk"]["profiles"]["books"]
    settings = school_settings(load_app_config())
    school = (settings.account_rs, settings.bucket_rs, settings.open_risk_rs, settings.new_risk_day_rs)
    keys = ("paper_account_rs", "bucket_cap_rs", "open_risk_cap_rs", "new_risk_per_day_rs")
    assert school == tuple(books[key] for key in keys)


def test_a_first_counted_date_is_read_as_a_date():
    assert str(school_settings({"school": {**GOOD, "first_counted": "2026-11-23"}}).first_counted) == "2026-11-23"


@pytest.mark.parametrize("block", [
    None, {**GOOD, "extra": 1}, {k: v for k, v in GOOD.items() if k != "brake_rs"}, {**GOOD, "enabled": "yes"},
    {**GOOD, "max_loss_rs": -1}, {**GOOD, "max_loss_rs": 10_000.5}, {**GOOD, "max_loss_rs": True},
    {**GOOD, "first_counted": "23 Nov"}])  # fmt: skip
def test_a_wrong_block_is_an_error(block):
    with pytest.raises(SchoolSettingsError):
        school_settings({} if block is None else {"school": block})


def test_zero_limits_are_allowed_at_the_boundary():
    assert school_settings({"school": {**GOOD, "max_new_trades_per_slot": 0}}).max_new_trades_per_slot == 0
