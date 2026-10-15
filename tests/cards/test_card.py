"""Story T1: the card's content (criteria 1-5, 8, 10, 14)."""

import hashlib
import re
from datetime import date

from fno.cards.card import CardBuilder
from fno.cards.sections import ForecastSource, StatusSource
from fno.cards.session import CALENDAR_PATH
from fno.cards.status import REGISTRY_PATH
from fno.cards.weather import PendingWeather
from fno.constants import CARD_DATA_CHECK_FAILED, CARD_NO_APPROVED_STRATEGY, CARD_TRADE_FIELDS_NOT_BUILT, CardStatus
from tests.cards.fakes import CAPTURE, PAPER_ROW, REGISTRY_HEADER, REPORT, FakeRecords, account, daily_card, planted

DAY = date(2026, 10, 15)
COLOURS = re.compile(r"\b(GREEN|AMBER|RED)\b")


def card_of(files, tmp_path, day=DAY):
    return daily_card(FakeRecords(files), tmp_path).prepare(day)


def test_a_full_card_says_paper_only_no_trade_with_its_reason_and_the_owner_line(tmp_path):
    card, text = card_of(planted(), tmp_path)
    lines = text.splitlines()
    assert lines[0].startswith("PAPER ONLY.") and "Thu 15 Oct 2026 (NSE regular session)" in lines[0]
    assert "Information, no action." in lines[0]
    assert card.status == CardStatus.NO_TRADE and card.reason_code == CARD_NO_APPROVED_STRATEGY
    assert f"Status: NO TRADE ({CARD_NO_APPROVED_STRATEGY})" in lines
    assert "Paper trades so far: 0 (book1_rules 0, book2_hybrid 0, book3_ai 0)" in lines
    assert "If you cannot act by 15:25 IST, the paper record assumes: no action" in text
    assert "Valid until 15:25 IST." in lines
    assert "order" not in text.lower()  # a card never tells the owner to place an order


def test_weather_is_never_a_colour_on_a_v1_card(tmp_path):
    _, text = card_of(planted(), tmp_path)
    assert "Weather: not yet scored (M1 pending)" in text
    assert not COLOURS.search(text)


def test_each_question_shows_only_the_past_average_with_its_records_and_the_others_are_counted(tmp_path):
    _, text = card_of(planted(), tmp_path)
    assert "Forecasts on record: live capture of 2026-10-14 (not today's" in text
    assert "This capture was generated at 19:27 IST, after its 15:15 deadline: its records are not scored" in text
    assert "House forecast: past average (baseline_b_base_rate). G1 names no primary yardstick" in text
    assert "3 other forecasters recorded; none has passed its test yet." in text
    assert (
        "q1_nifty_up_20d (NIFTY higher in 20 sessions): past average 0.59 | back-fill, not live: said 0.5-0.6 on 175 "
        "days, happened on 57%, mean Brier 0.245 over 670; live: not enough data yet (0 scored)"
    ) in text
    assert text.count(" | back-fill, not live: ") == 5  # one line per question
    assert "book1_rules 0.56" not in text and "baseline_c_model" not in text


def test_a_question_the_past_average_did_not_answer_says_so(tmp_path):
    files = planted()
    capture = files[CAPTURE].decode().splitlines(keepends=True)
    blank = [line if not line.startswith("baseline_b_base_rate,2026-10-14,2026-10-14T15:00:00+05:30,q4") else
             line.replace(line.split(",")[4], "", 1) for line in capture]  # fmt: skip
    files[CAPTURE] = "".join(blank).encode()
    _, text = card_of(files, tmp_path)
    assert "q4_vix_up_10d (India VIX higher in 10 sessions): past average gave no forecast" in text


def test_the_footer_lists_every_record_used_with_the_hash_of_its_committed_bytes(tmp_path):
    files = planted()
    card, text = card_of(files, tmp_path)
    paths = {r.path for r in card.used}
    assert {CALENDAR_PATH, REGISTRY_PATH, CAPTURE, REPORT} <= paths and len(paths) == 7
    for record in card.used:
        assert record.sha256 == hashlib.sha256(files[record.path]).hexdigest()
        assert f"  {record.path} {record.sha256}" in text
    assert "Issuance time: this message's Slack server timestamp" in text


def test_a_version_at_paper_still_gives_no_trade_and_never_a_trade(tmp_path):
    files = planted() | {REGISTRY_PATH: REGISTRY_HEADER + PAPER_ROW.encode()}
    card, text = card_of(files, tmp_path)
    assert card.status == CardStatus.NO_TRADE and card.reason_code == CARD_TRADE_FIELDS_NOT_BUILT
    assert "1 version(s) at paper (sc-iv-rich-v1), but card v1 cannot show trade fields" in text


def test_an_unreadable_registry_or_account_is_a_failed_data_check_named_on_the_card(tmp_path):
    files = planted() | {REGISTRY_PATH: b"not,a,registry\n"}
    del files["journal/book2_hybrid/account/positions.json"]
    card, text = card_of(files, tmp_path)
    assert card.reason_code == CARD_DATA_CHECK_FAILED
    assert "Paper trades so far: at least 0 (book1_rules 0, book2_hybrid unknown, book3_ai 0)" in text
    assert "playbook/registry.csv: not readable (PlaybookError)" in text
    assert "journal/book2_hybrid/account/positions.json: not readable (not committed)" in text


def test_open_and_closed_trades_are_counted(tmp_path):
    files = planted() | {"journal/book1_rules/account/positions.json": account(open_trades=1, closed=2)}
    _, text = card_of(files, tmp_path)
    assert "Paper trades so far: 3 (book1_rules 3, book2_hybrid 0, book3_ai 0)" in text


def test_no_forecasts_and_no_score_report_still_give_a_card_that_names_them(tmp_path):
    files = {k: v for k, v in planted().items() if k not in (CAPTURE, REPORT)}
    card, text = card_of(files, tmp_path)
    assert "Forecasts: none on record yet" in text
    assert "live forecast capture on or before 2026-10-15" in card.missing
    files[CAPTURE] = planted()[CAPTURE]
    card, text = card_of(files, tmp_path)
    assert (
        "track record: no score report yet" in text and "forecast score report on or before 2026-10-15" in card.missing
    )


def test_a_capture_after_the_day_is_never_used(tmp_path):
    card, text = card_of(planted(), tmp_path, day=date(2026, 10, 13))
    assert "Forecasts: none on record yet" in text and CAPTURE not in {r.path for r in card.used}


class Broken(StatusSource, ForecastSource):
    def status(self, day):
        raise OSError("disk gone")

    def forecasts(self, day):
        raise ValueError("bad csv")


def test_a_source_that_raises_never_loses_the_card(tmp_path):
    records = FakeRecords()
    builder = CardBuilder(Broken(), PendingWeather(), Broken())
    answer = daily_card(records, tmp_path).sessions.answer(DAY)
    card = builder.build(DAY, answer)
    assert card.status == CardStatus.NO_TRADE and card.reason_code == CARD_DATA_CHECK_FAILED
    assert "status source failed (OSError: disk gone)" in card.missing
    assert "forecasts source failed (ValueError: bad csv)" in card.missing
    assert card.sections[2].lines == ("forecasts: not available on this card",)


def test_a_day_that_is_not_a_session_gets_no_card(tmp_path):
    assert card_of(planted(), tmp_path, day=date(2026, 10, 17)) is None  # a Saturday
    assert card_of(planted(), tmp_path, day=date(2026, 10, 2)) is None  # Gandhi Jayanti


def test_a_day_the_calendar_cannot_answer_still_gets_a_card_naming_the_gap(tmp_path):
    card, text = card_of(planted(), tmp_path, day=date(2031, 1, 6))
    assert "session unknown: calendar cannot answer" in text.splitlines()[0]
    assert any("session calendar cannot answer for 2031-01-06" in m for m in card.missing)
    files = {k: v for k, v in planted().items() if k != CALENDAR_PATH}
    card, _ = card_of(files, tmp_path)
    assert f"{CALENDAR_PATH} not committed" in card.missing
