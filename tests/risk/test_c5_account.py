"""Story C5 criteria 8-12: the settings are the owner's and checked at start-up, the Rs 1.2 lakh brake lifts only by a
written owner record, the daily stress line, the day each trade opened, and no Rs 5 lakh setting used silently."""

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
from fno.constants import BOOK1_RULES, BOOKS, SIDE_BUY, SIDE_SELL
from fno.models import IST
from fno.playbook.book_effects import book_after_entry
from fno.playbook.decision_codec import book_from_json, book_to_json
from fno.risk.book_view import load_risk_book
from fno.risk.cap_settings import cap_settings
from fno.risk.drawdown import DrawdownBrake
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.overrides import OVERRIDE_COLUMNS, overrides_file
from fno.risk.settings import RiskSettingsError, risk_settings
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.risk.wiring import build_risk_manager, build_stress_line

from .builders import CHARGES, DAY, FLY, LOT, START, book, contract, market, open_trade, proposal, short_fly

CONFIG = load_app_config()
EXPIRY = DAY + timedelta(days=14)
PRICES = {(25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0}
NEW = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)


def test_the_repository_holds_the_owners_numbers_and_no_rs_5_lakh_account_or_brake():
    caps, risk = cap_settings(CONFIG), risk_settings(CONFIG, ROOT)
    assert (caps.paper_account_rs, risk.max_loss_per_trade_rs, risk.drawdown_brake_rs) == (2_000_000, 10_000, 120_000)
    assert (caps.bucket_cap_rs, caps.open_risk_cap_rs, caps.new_risk_per_day_rs) == (30_000, 150_000, 50_000)


@pytest.mark.parametrize(
    "path",
    [
        ("risk", "paper_account_rs"),
        ("risk", "caps"),
        ("risk", "caps", "bucket_cap_rs"),
        ("risk", "caps", "open_risk_cap_rs"),
        ("risk", "caps", "new_risk_per_day_rs"),
        ("risk", "caps", "bucket_sides"),
        ("risk", "stress_line"),
    ],
)
def test_a_missing_c5_setting_is_an_error_never_a_default(path):
    cfg = copy.deepcopy(CONFIG)
    block = cfg
    for key in path[:-1]:
        block = block[key]
    del block[path[-1]]
    with pytest.raises(RiskSettingsError, match=path[-1]):
        cap_settings(cfg)


@pytest.mark.parametrize(
    ("key", "value", "problem"),
    [
        ("bucket_sides", {"SF": "sideways"}, "sides must be one of"),
        ("bucket_cap_rs", 0, "positive"),
        ("open_risk_cap_rs", 2_000_001, "larger than the paper account"),
    ],
)
def test_a_malformed_c5_setting_is_an_error(key, value, problem):
    cfg = copy.deepcopy(CONFIG)
    cfg["risk"]["caps"][key] = value
    with pytest.raises(RiskSettingsError, match=problem):
        cap_settings(cfg)


def test_no_rs_5_lakh_account_size_or_old_brake_is_left_in_the_code():
    """The account size comes only from `risk.paper_account_rs`: the writer has no default, and no module holds the
    old Rs 5 lakh or the old Rs 30,000 brake as a number."""
    assert "starting_cash" in inspect.signature(AccountWriter).parameters
    assert inspect.signature(AccountWriter).parameters["starting_cash"].default is inspect.Parameter.empty
    old = re.compile(r"\b(500_?000|5,00,000)\b|Rs 5 lakh paper account|STARTING_CASH_RS")
    hits = [
        f"{path.relative_to(ROOT)}:{n}"
        for path in sorted((ROOT / "fno").rglob("*.py"))
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if old.search(line)
    ]
    assert hits == []


def test_the_rs_5_lakh_limits_not_rescaled_are_marked_in_the_settings_never_silent():
    """max_open_trades, max_stress_loss_rs and the exposure limits have no Rs 20 lakh value from the owner yet: the
    settings file says so next to them (response 105, question 1)."""
    text = (ROOT / "config.yaml").read_text(encoding="utf-8")
    for key in ("max_open_trades:", "max_stress_loss_rs:", "exposure:"):
        before = text[: text.index("\n", text.index(key))].splitlines()[-5:]
        assert any("NOT rescaled" in line for line in before), key


def test_the_repository_books_opened_on_rs_5_lakh_are_refused_by_the_wired_manager(tmp_path):
    margins = tmp_path / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,40000,0,0,test calculator,2026-10-12\n")
    stressed = {"multiplier": 1.5, "source": "test factor", "as_of": "2026-10-13"}
    cfg = load_app_config(overrides={"risk": {"margins": {"file": str(margins)}, "stressed_margin": stressed}})
    the_book = book()
    the_book = replace(the_book, state=replace(the_book.state, starting_cash=500_000.0))
    decision = build_risk_manager(cfg, tmp_path).evaluate(NEW, the_book, market(25000, PRICES, EXPIRY))
    assert [r.split(":")[0] for r in decision.reasons] == ["paper_account"]


@pytest.mark.parametrize(("closed_now", "ok"), [(1_880_000.01, True), (1_880_000.0, False), (1_879_999.99, False)])
def test_the_rs_120000_brake_at_just_under_and_just_over(closed_now, ok):
    series = ((DAY - timedelta(days=30), START), (DAY - timedelta(days=1), closed_now))
    verdict = DrawdownBrake(risk_settings(CONFIG, ROOT).drawdown_brake_rs).check(NEW, book(closed=series), None)
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
    path.write_text(",".join(OVERRIDE_COLUMNS) + "\n2026-10-02,restart_brake,reviewed the loss,\n")
    with pytest.raises(RiskInputError, match="entered_by"):  # unsigned: the book cannot be read, so nothing trades
        _brake(braked)
    path.write_text(",".join(OVERRIDE_COLUMNS) + "\n2026-10-02,restart_brake,reviewed the loss,owner\n")
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


def test_each_open_trade_knows_the_day_it_opened_in_every_view(braked):
    the_market = market(25000, PRICES, EXPIRY)
    with open_account_writer(BOOK1_RULES, braked) as writer:
        writer.apply_fill(_fill("o1", "held", SIDE_BUY, 150.0, date(2026, 10, 9)))
    held = load_risk_book(braked, BOOK1_RULES, the_market, {"held": TradeTerms(FLY, 200, 1)})
    assert held.open_trades[0].opened_on == date(2026, 10, 9)  # from the ledger's first fill
    after = book_after_entry(held, NEW, the_market, SimulatorTradeCosts(CHARGES))
    assert after.open_trades[-1].opened_on == DAY  # chosen earlier the same session: new risk today
    assert book_from_json(book_to_json(after)) == after
    old_record = book_to_json(after)
    del old_record["open_trades"][0]["opened_on"]  # a record written before C5
    assert book_from_json(old_record).open_trades[0].opened_on is None  # then refused by the new-risk cap
