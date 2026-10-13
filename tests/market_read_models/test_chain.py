"""Story P9: the NIFTY option chain blocks for screen 32, built from NSE's real F&O and index files of 1 Jun to 12 Oct
2026 (tests/fixtures/nse/chain/), equal W13's examples field by field; the rules behind them (scope, contract codes,
IV only when traded and within 1%-200%, coverage) hold on their own."""

from datetime import date

from fno.market_read_models.blocks import SessionRows
from fno.market_read_models.chain_expiries import FoRow, contract_code, in_scope, monthly_expiries
from fno.market_read_models.chain_history import covered_change, covered_middle
from fno.market_read_models.chain_math import bounded_iv
from fno.market_read_models.chain_route import strikes_view
from fno.market_read_models.contract import PinnedContract
from fno.market_read_models.contract_examples import compare
from fno.market_read_models.wiring import CONTRACT_FOLDER, build_market_blocks

from .chain_fixture import DAY, RATE, chain_of_12_october

EXAMPLES = PinnedContract(CONTRACT_FOLDER).examples()
CHAIN_EXAMPLES = {name: e for name, e in EXAMPLES.items() if name.startswith(("getChain", "getContractHistory"))}


def chain_pages() -> dict[str, dict]:
    rows = SessionRows(DAY, [], [], [], [], chain_of_12_october())
    chain_blocks = [b for b in build_market_blocks() if b.page_key.startswith(("chain", "contract"))]
    return {key: payload for b in chain_blocks for key, payload in b.pages(rows).items()}


def test_every_published_chain_block_equals_w13s_example_of_12_october():
    found = compare(chain_pages(), CHAIN_EXAMPLES)
    assert sorted(found) == sorted(n for n in CHAIN_EXAMPLES if n != "getChainHistory_india_short")  # 9 examples
    assert {name: diffs for name, diffs in found.items() if diffs} == {}


def test_the_pages_one_per_expiry_and_one_per_contract():
    pages = chain_pages()
    expiries = [e["expiry"] for e in chain_of_12_october().expiries]
    assert len(expiries) == 7 and sum(k.startswith("chain_rows:") for k in pages) == 7  # W13: one page per expiry
    assert sum(k.startswith("chain_contract:") for k in pages) == len(chain_of_12_october().contracts) == 1246
    stored = pages["chain_rows:2026-10-27"]
    assert stored["strikes"] == "all" and len(stored["rows"]) == 89  # every strike within 10%, stored once
    near = strikes_view(stored, "near", 22363.35, 22350.0)["rows"]
    assert len(near) == 21 and near[10]["strike"] == 22350.0  # the route: 10 strikes each side of the ATM strike


def test_the_short_history_example_is_our_series_cut_to_its_last_30_sessions():
    history, short = chain_of_12_october().history, CHAIN_EXAMPLES["getChainHistory_india_short"]["value"]["payload"]
    nifty, vix = history["nifty"][-30:], history["vix"][-30:]
    assert short["dates"] == history["dates"][-30:] and short["nifty"] == nifty
    coverage = {"nifty": {k: covered_change(nifty, n) for k, n in {"d5": 5, "m1": 21, "m3": 63}.items()},
                "vix_middle_3m": covered_middle(vix, 63)}  # fmt: skip
    assert coverage == short["coverage"] and coverage["nifty"]["m3"] == {
        "days_in_period": 63, "days": 29, "complete": False, "value": None,
    }  # fmt: skip


def test_contract_codes_name_monthly_and_weekly_expiries_as_nse_does():
    assert contract_code(date(2026, 10, 27), 22400.0, "CE", monthly=True) == "NIFTY26OCT22400CE"
    assert contract_code(date(2026, 10, 13), 22400.0, "PE", monthly=False) == "NIFTY26O1322400PE"
    assert contract_code(date(2026, 12, 1), 21000.0, "CE", monthly=False) == "NIFTY26D0121000CE"


def row(expiry: date, strike: float, kind: str = "CE") -> FoRow:
    return FoRow(DAY, expiry, strike, kind, 100.0, 90.0, 10, 1, 5, 22363.35, 65)


def test_the_scope_is_the_next_three_calendar_months_within_10_percent():
    rows = [row(date(2026, 10, 12), 22400), row(date(2026, 12, 29), 22400), row(date(2027, 1, 26), 22400),
            row(date(2026, 10, 27), 24700), row(date(2026, 10, 27), 0, "FUT")]  # fmt: skip
    kept = in_scope(rows, DAY, 22363.35)
    assert [(r.expiry, r.strike) for r in kept] == [(date(2026, 12, 29), 22400), (date(2026, 10, 27), 0)]
    assert monthly_expiries([row(date(2026, 10, 20), 1), row(date(2026, 10, 27), 1)]) == {date(2026, 10, 27)}


def test_iv_only_within_1_and_200_percent_and_only_for_a_traded_leg():
    years = 15 / 365
    assert round(bounded_iv(151.4 / 2, 22363.35, 22350, years, RATE, "CE") * 100, 1) > 0
    assert bounded_iv(2000.0, 22363.35, 20000, years, RATE, "CE") is None  # under intrinsic: below the price at 1%
    assert bounded_iv(5000.0, 22363.35, 22350, years, RATE, "CE") is None  # above the price at 200%
    weekly = next(e for e in chain_of_12_october().expiries if e["expiry"] == "2026-10-13")
    untraded = next(r["CE"] for r in weekly["rows"] if r["CE"]["volume"] == 0)
    assert (untraded["iv"], untraded["greeks"], untraded["chance"]) == (None, None, None)


def test_a_spot_exactly_between_two_strikes_takes_the_lower_as_atm():
    """Judge 60's plant (a tie to the higher strike) must fail: W13's rule is "a tie to the lower"."""
    from fno.market_read_models.chain_expiries import summary

    def leg(close):
        return {"close": close, "oi": 10, "oi_chg": 1, "iv": 15.0}

    strikes = [{"strike": k, "CE": leg(100.0), "PE": leg(90.0)} for k in (22300.0, 22350.0, 22400.0, 22450.0)]
    assert summary(strikes, 22375.0)["atm"] == 22350.0  # 25 points from both 22350 and 22400
    assert summary(strikes, 22376.0)["atm"] == 22400.0  # no tie: the nearer one
