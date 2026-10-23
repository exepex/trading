"""Story C5: the books' and the Manual account's profiles are the owner's and checked at start-up, the Rs 1.2 lakh brake
lifts only by a written owner record, the daily stress line, the day each trade opened, and no Rs 5 lakh setting used
silently for the books."""

import copy
import inspect
import re
from dataclasses import replace
from datetime import date, datetime, timedelta

import pytest

from fno.accounting.ledgers import Order
from fno.books.account import AccountWriter
from fno.books.fills import Fill
from fno.composition import open_account_writer
from fno.config import ROOT, load_app_config
from fno.constants import BOOK1_RULES, BOOKS, RISK_PROFILE_BOOKS, RISK_PROFILE_MANUAL, SIDE_BUY, SIDE_SELL
from fno.models import IST
from fno.playbook.book_effects import book_after_entry
from fno.playbook.decision_codec import book_from_json, book_to_json
from fno.risk.book_view import load_risk_book
from fno.risk.drawdown import DrawdownBrake
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.overrides import OVERRIDE_COLUMNS, overrides_file
from fno.risk.profile_settings import RULE_SETTINGS, profile_settings
from fno.risk.settings import ExposureSettings, RiskSettingsError
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.risk.wiring import RULES, build_risk_manager, build_stress_line
from tests.margin_tables import local_tables
from tests.stress_factor_files import factor_file

from .builders import (
    CHARGES,
    DAY,
    FLY,
    LOT,
    START,
    book,
    contract,
    market,
    open_trade,
    owner_decision,
    proposal,
    short_fly,
)

CONFIG = load_app_config()
EXPIRY = DAY + timedelta(days=14)
PRICES = {(25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0}
NEW = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)


def _profile(name: str = RISK_PROFILE_BOOKS, cfg=CONFIG):
    return profile_settings(cfg, name)


def test_the_books_hold_the_owners_numbers_and_only_the_new_rules():
    books = _profile()
    assert (books.paper_account_rs, books.max_loss_per_trade_rs, books.drawdown_brake_rs) == (
        2_000_000,
        10_000,
        120_000,
    )
    assert (books.bucket_cap_rs, books.open_risk_cap_rs, books.new_risk_per_day_rs) == (30_000, 150_000, 50_000)
    assert books.rules == (
        "paper_account", "max_loss_per_trade", "bucket_cap", "open_risk_cap", "new_risk_per_day", "drawdown_brake",
        "margin_room",
    )  # fmt: skip
    assert (books.max_open_trades, books.max_stress_loss_rs, books.exposure) == (None, None, None)  # "1 A", "2 A"
    assert (books.margin_age_sessions, books.margin_age_days) == (1, None)  # design 6.1a


def test_the_manual_account_keeps_its_13_oct_limits_unchanged():
    """DESK_DECISIONS row of 13 Oct 2026, unchanged on 15 Oct: Rs 5 lakh, Rs 10,000 a trade, 3 open trades, Rs 30,000
    brake, C2's stress and exposure limits, margins up to 7 days old; no C5 cap."""
    manual = _profile(RISK_PROFILE_MANUAL)
    assert (manual.paper_account_rs, manual.max_loss_per_trade_rs, manual.max_open_trades) == (500_000, 10_000, 3)
    assert (manual.drawdown_brake_rs, manual.max_stress_loss_rs) == (30_000, 30_000)
    assert manual.exposure == ExposureSettings(2, 15_000, 5, 15_000)
    assert (manual.margin_age_days, manual.margin_age_sessions, manual.bucket_sides) == (7, None, None)
    assert manual.rules == (
        "paper_account", "max_loss_per_trade", "max_open_trades", "drawdown_brake", "stress_loss", "exposure_limit",
        "margin_room",
    )  # fmt: skip
    rules = [r.name for r in build_risk_manager(CONFIG, ROOT, RISK_PROFILE_MANUAL).rules]
    assert rules == [
        "paper_account", "max_loss_per_trade", "max_open_trades", "drawdown_brake", "stress_loss", "exposure_limit",
        "margin_room",
    ]  # fmt: skip


def _without(path: tuple[str, ...]):
    cfg = copy.deepcopy(CONFIG)
    block = cfg["risk"]["profiles"]["books"]
    for key in path[:-1]:
        block = block[key]
    del block[path[-1]]
    return cfg


@pytest.mark.parametrize(
    "key",
    ["rules", "paper_account_rs", "bucket_cap_rs", "open_risk_cap_rs", "new_risk_per_day_rs", "bucket_sides",
     "drawdown_brake_rs", "max_loss_per_trade_rs"],
)  # fmt: skip
def test_a_missing_books_setting_is_an_error_never_a_default(key):
    with pytest.raises(RiskSettingsError, match=key):
        _profile(cfg=_without((key,)))


def test_both_or_no_margin_age_is_an_error():
    with pytest.raises(RiskSettingsError, match="exactly one"):
        _profile(cfg=_without(("margin_max_age_sessions",)))
    cfg = copy.deepcopy(CONFIG)
    cfg["risk"]["profiles"]["books"]["margin_max_age_days"] = 7
    with pytest.raises(RiskSettingsError, match="exactly one"):
        _profile(cfg=cfg)


@pytest.mark.parametrize(
    ("key", "value", "problem"),
    [
        ("bucket_sides", {"SF": "sideways"}, "distinct sides"),
        ("bucket_sides", {"BPS": ["bullish", "bullish"]}, "distinct sides"),
        ("bucket_sides", {"BPS": []}, "distinct sides"),
        ("bucket_sides", {"BPS": 3}, "distinct sides"),
        ("bucket_cap_rs", 0, "positive"),
        ("open_risk_cap_rs", 2_000_001, "larger than the paper account"),
        ("max_open_trades", 3, "belong to no rule"),  # a setting without its rule is never silently ignored
        ("rules", ["paper_account", "max_loss_per_trade", "drawdown_brake"], "missing \\['margin_room'\\]"),
        ("rules", ["paper_account", "max_loss_per_trade", "drawdown_brake", "margin_room", "guess"], "unknown"),
    ],
)
def test_a_malformed_books_setting_is_an_error(key, value, problem):
    cfg = copy.deepcopy(CONFIG)
    cfg["risk"]["profiles"]["books"][key] = value
    with pytest.raises(RiskSettingsError, match=problem):
        _profile(cfg=cfg)


def test_a_two_sided_structure_is_read_as_a_list_of_sides():
    cfg = copy.deepcopy(CONFIG)
    cfg["risk"]["profiles"]["books"]["bucket_sides"] = {
        "SF": "short_volatility",
        "BPS": ["bullish", "short_volatility"],
    }
    assert _profile(cfg=cfg).bucket_sides == {"SF": ("short_volatility",), "BPS": ("bullish", "short_volatility")}


def test_every_rule_name_a_profile_may_list_is_built_by_the_composition_root():
    assert set(RULE_SETTINGS) == set(RULES)


def test_no_rs_5_lakh_account_size_or_old_brake_is_left_in_the_code():
    """The account size comes only from `risk.paper_account_rs`: the writer has no default, and no module holds the
    old Rs 5 lakh or the old Rs 30,000 brake as a number."""
    assert "opening_cash" in inspect.signature(AccountWriter).parameters
    assert inspect.signature(AccountWriter).parameters["opening_cash"].default is inspect.Parameter.empty
    old = re.compile(r"\b(500_?000|5,00,000)\b|Rs 5 lakh paper account|STARTING_CASH_RS")
    hits = [
        f"{path.relative_to(ROOT)}:{n}"
        for path in sorted((ROOT / "fno").rglob("*.py"))
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if old.search(line)
    ]
    assert hits == []


def test_the_repository_books_opened_on_rs_5_lakh_are_refused_by_the_wired_manager(tmp_path):
    margins = tmp_path / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,40000,0,0,test calculator,2026-10-12\n")
    stressed = {"factor_file": str(factor_file(1.5, date(2026, 10, 12)))}  # the day before the decision
    cfg = load_app_config(overrides={"risk": {"stressed_margin": stressed}})
    the_book = book()
    the_book = replace(the_book, state=replace(the_book.state, capital=500_000.0))
    decision = build_risk_manager(cfg, tmp_path, tables=local_tables(margins)).evaluate(
        NEW, the_book, market(25000, PRICES, EXPIRY)
    )
    assert [r.split(":")[0] for r in decision.reasons] == ["paper_account"]


@pytest.mark.parametrize(("closed_now", "ok"), [(1_880_000.01, True), (1_880_000.0, False), (1_879_999.99, False)])
def test_the_rs_120000_brake_at_just_under_and_just_over(closed_now, ok):
    series = ((DAY - timedelta(days=30), START), (DAY - timedelta(days=1), closed_now))
    verdict = DrawdownBrake(_profile().drawdown_brake_rs).check(NEW, book(closed=series), None)
    assert verdict.ok is ok and verdict.numbers["brake_rs"] == 120_000


def _fill(fill_id, trade_id, side, price, day, strike=25000):
    when = datetime(day.year, day.month, day.day, 15, 15, tzinfo=IST)
    return Fill.priced(fill_id, trade_id, when, contract(strike, "CE", EXPIRY), Order(side, price, LOT, 0.0), CHARGES)


@pytest.fixture
def braked(tmp_path):
    """Book 1 on the Rs 20 lakh account, Rs 1,30,000 below its high after a closed loss on 1 Oct."""
    for name in BOOKS:
        with open_account_writer(name, tmp_path) as writer:
            writer.start(date(2026, 9, 1))
    with open_account_writer(BOOK1_RULES, tmp_path) as writer:
        writer.apply_fill(_fill("f1", "loser", SIDE_SELL, 100.0, date(2026, 9, 30)))
        writer.apply_fill(_fill("f2", "loser", SIDE_BUY, 2100.0, date(2026, 10, 1)))
    return tmp_path


def _brake(root):
    the_book = load_risk_book(root, BOOK1_RULES, market(25000, PRICES, EXPIRY), {})
    return DrawdownBrake(120_000).check(NEW, the_book, None)


def test_the_brake_lifts_only_by_the_owners_written_restart_row(braked):
    assert not _brake(braked).ok  # no written record: stays on, never lifted by time or by a new high of marks
    path = overrides_file(braked, BOOK1_RULES)
    owner_decision(braked, "Restart Book 1", day="2 Oct 2026")
    path.write_text(",".join(OVERRIDE_COLUMNS) + "\n2026-10-02,restart_brake,reviewed the loss,,Restart Book 1\n")
    with pytest.raises(RiskInputError, match="entered_by"):  # unsigned: the book cannot be read, so nothing trades
        _brake(braked)
    path.write_text(",".join(OVERRIDE_COLUMNS) + "\n2026-10-02,restart_brake,reviewed the loss,owner,Restart Book 1\n")
    assert _brake(braked).ok and _brake(braked).numbers["restarted_on"] == "2026-10-02"


def test_the_daily_stress_line_reports_every_scenario_below_the_sum_of_maximum_losses():
    line = build_stress_line(CONFIG)
    the_market = market(25000, PRICES, EXPIRY)
    cash = SimulatorTradeCosts(CHARGES).entry_cash_flow(NEW, the_market)
    held = open_trade("held", FLY, 200, short_fly(25000, 200), EXPIRY, cash, lots=1)
    result = line.line(book([held]), the_market)
    assert [r.scenario for r in result.rows] == [
        "nifty_down_5pct_vix_up_50pct", "nifty_down_5pct_vix_up_100pct", "nifty_down_10pct_vix_up_50pct",
        "nifty_down_10pct_vix_up_100pct", "nifty_up_5pct",
    ]  # fmt: skip
    assert result.max_loss_sum_rs > 0 and all(0 < r.loss_from_entry_rs <= result.max_loss_sum_rs for r in result.rows)
    assert result.record()["rows"][2]["scenario"] == "nifty_down_10pct_vix_up_50pct"
    empty = line.line(book(), the_market)
    assert empty.max_loss_sum_rs == 0 and all(r.loss_from_entry_rs == 0 for r in empty.rows)


def test_the_session_trades_are_every_trade_first_filled_today_with_each_state(braked):
    """Owner, 15 Oct 2026, "3 A": a trade opened and closed in the same session still counts; its largest maximum
    loss that day is its new risk. A trade first filled on an earlier day is not new risk, even if it trades today."""
    the_market = market(25000, PRICES, EXPIRY, day=DAY)
    with open_account_writer(BOOK1_RULES, braked) as writer:
        writer.apply_fill(_fill("e1", "older", SIDE_BUY, 70.0, DAY - timedelta(days=2), strike=25200))  # opened earlier
        writer.apply_fill(_fill("e2", "older", SIDE_BUY, 150.0, DAY))  # ... and traded again today: not new risk
        for i, (strike, kind, side) in enumerate(short_fly(25000, 200)):  # opened at 15:15 ...
            order = Order(SIDE_SELL if side < 0 else SIDE_BUY, PRICES[(strike, kind)], LOT, 0.0)
            when = datetime(DAY.year, DAY.month, DAY.day, 15, 15, tzinfo=IST)
            writer.apply_fill(Fill.priced(f"o{i}", "round_trip", when, contract(strike, kind, EXPIRY), order, CHARGES))
        for i, (strike, kind, side) in enumerate(short_fly(25000, 200)):  # ... and closed at 15:20
            order = Order(SIDE_BUY if side < 0 else SIDE_SELL, PRICES[(strike, kind)], LOT, 0.0)
            when = datetime(DAY.year, DAY.month, DAY.day, 15, 20, tzinfo=IST)
            writer.apply_fill(Fill.priced(f"c{i}", "round_trip", when, contract(strike, kind, EXPIRY), order, CHARGES))
    the_book = load_risk_book(braked, BOOK1_RULES, the_market, {"older": TradeTerms(FLY, 200, 1)})
    assert [t.trade_id for t in the_book.open_trades] == ["older"]
    assert [t.trade_id for t in the_book.session_trades] == ["round_trip"]
    (trade,) = the_book.session_trades
    assert len(trade.states) == 2 and trade.states[1][0] == {}  # held after 15:15, flat after 15:20
    from fno.risk.wiring import build_position_risks

    risks = build_position_risks(CONFIG, _profile())
    first = risks.held.max_loss(trade.states[0][0], trade.states[0][1], the_market)
    assert first > 0 and risks.of_session(trade, the_market) == pytest.approx(first)
    after = book_after_entry(the_book, NEW, the_market, SimulatorTradeCosts(CHARGES))
    assert [t.trade_id for t in after.session_trades] == ["round_trip", "new"]  # chosen earlier the same session
    assert book_from_json(book_to_json(after)) == after
    old_record = book_to_json(after)
    del old_record["session_trades"]  # a record written before C5
    assert book_from_json(old_record).session_trades is None  # then refused by the new-risk cap


@pytest.mark.parametrize("stray", ["max_open_trades", "paper_account_rs", "caps"])
def test_a_stray_key_under_risk_stops_start_up(stray, tmp_path):
    """Judge 105 minor 1: a leftover flat limit would look like a limit while nothing runs it."""
    cfg = copy.deepcopy(CONFIG)
    cfg["risk"][stray] = 3
    with pytest.raises(RiskSettingsError, match=stray):
        build_risk_manager(cfg, tmp_path)


def test_a_broken_manual_profile_stops_the_books_risk_manager_too(tmp_path):
    """Every profile is checked at start-up, so the Manual account's limits can never be wrong unnoticed."""
    cfg = copy.deepcopy(CONFIG)
    cfg["risk"]["profiles"]["manual"]["max_open_trades"] = 2.5
    with pytest.raises(RiskSettingsError, match="manual"):
        build_risk_manager(cfg, tmp_path)
