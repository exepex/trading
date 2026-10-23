"""Story C2 end to end: the risk manager as the app wires it (config.yaml `risk`, B2's cost model), its decision record,
and failing closed on unusable inputs."""

import csv
from datetime import date, timedelta

import pytest

from fno.config import ROOT, load_app_config
from fno.risk.manager import RiskManager
from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.verdict import RiskRule
from fno.risk.wiring import build_risk_manager
from tests.margin_tables import local_tables
from tests.stress_factor_files import HEADER, factor_file

from .builders import DAY, FLY, book, market, open_trade, proposal, short_fly

EXPIRY = DAY + timedelta(days=14)
PRICES = {(25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0}
RULES = [  # the books' profile, in config.yaml order
    "inputs",
    "paper_account",
    "max_loss_per_trade",
    "bucket_cap",
    "open_risk_cap",
    "new_risk_per_day",
    "drawdown_brake",
    "margin_room",
]


def _manager(tmp_path, **books) -> RiskManager:
    margins = tmp_path / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,40000,0,0,test calculator,2026-10-12\n")
    stressed = {"factor_file": str(factor_file(1.5, date(2026, 10, 12)))}  # the day before the decision
    profiles = {"books": books}
    overrides = {"risk": {"stressed_margin": stressed, "profiles": profiles}}
    return build_risk_manager(load_app_config(overrides=overrides), tmp_path, tables=local_tables(margins))


def _evaluate(manager, lots=1, the_book=None):
    new = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY, lots=lots)
    return manager.evaluate(new, the_book or book(), market(25000, PRICES, EXPIRY))


def _verdict(decision, rule):
    return next(v for v in decision.verdicts if v.rule == rule)


def test_inside_every_limit_the_trade_may_open_and_every_rule_reports(tmp_path):
    decision = _evaluate(_manager(tmp_path))
    assert decision.ok, decision.reasons
    assert [v.rule for v in decision.verdicts] == RULES
    record = decision.record()
    assert record["stressed_margin"] == {
        "method": "multiplier",
        "stresses": "scan and exposure (owner, 15 Oct 2026; story C2c)",
        "factor_file": "k1.5_2026-10-12_applied.csv",
    }
    used = _verdict(decision, "margin_room").numbers["stress_factor_row"]  # story C2d: the row used on the day
    assert (used["factor"], used["as_of"], used["status"], used["evidence_sha256"]) == (
        "1.5",
        "2026-10-12",
        "applied",
        "",
    )
    assert record["day"] == "2026-10-13" and record["book"] == "book1_rules"


def test_outside_the_per_trade_limit_the_trade_is_refused_with_reason_and_numbers(tmp_path):
    decision = _evaluate(_manager(tmp_path), lots=4)
    assert not decision.ok
    loss = next(v for v in decision.verdicts if v.rule == "max_loss_per_trade")
    assert not loss.ok and loss.numbers["max_loss_rs"] > 10000 and "above the limit Rs 10,000.00" in loss.reason


def test_borderline_the_limit_equal_to_the_maximum_loss_passes_and_a_paisa_less_refuses(tmp_path):
    loss = _verdict(_evaluate(_manager(tmp_path)), "max_loss_per_trade").numbers["max_loss_rs"]
    assert _verdict(_evaluate(_manager(tmp_path, max_loss_per_trade_rs=loss)), "max_loss_per_trade").ok
    assert not _verdict(_evaluate(_manager(tmp_path, max_loss_per_trade_rs=loss - 0.01)), "max_loss_per_trade").ok


def test_the_repository_settings_refuse_every_trade_until_margin_rows_are_entered():
    decision = _evaluate(build_risk_manager(load_app_config()))
    margin = next(v for v in decision.verdicts if v.rule == "margin_room")
    assert not decision.ok and not margin.ok and "input not usable" in margin.reason


SEED_ONLY = HEADER + '2026-10-14,1.45,,,applied,"owner seed: response 77, decision 14 Oct",,\n'


def _factor_on(tmp_path, day, factor_path):
    """A decision on `day` with `factor_path` as the factor file and a fresh margin row (A14 writes them daily)."""
    margins = tmp_path / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + f"\nSF,200,40000,0,0,test calculator,{day}\n")
    overrides = {"risk": {"stressed_margin": {"factor_file": str(factor_path)}}}
    manager = build_risk_manager(load_app_config(overrides=overrides), tmp_path, tables=local_tables(margins))
    new = proposal("new", FLY, 200, short_fly(25000, 200), day + timedelta(days=14))
    decision = manager.evaluate(new, book(), market(25000, PRICES, day + timedelta(days=14), day=day))
    return decision, next(v for v in decision.verdicts if v.rule == "margin_room")


def _seed_only(tmp_path):
    """The owner's seed alone (1.45 as_of 14 Oct, 30 days): the age rule's fixture; A14c's rows never move it."""
    path = tmp_path / "seed_only.csv"
    path.write_text(SEED_ONLY, encoding="utf-8")
    return path


@pytest.mark.parametrize("day", [date(2026, 10, 15), date(2026, 11, 13)])  # from the day after the seed (as_of < d)
def test_the_owner_s_factor_lets_a_valid_trade_open_through_its_30th_day(tmp_path, day):
    decision, margin = _factor_on(tmp_path, day, _seed_only(tmp_path))
    assert decision.ok, decision.reasons
    used = margin.numbers["stress_factor_row"]
    assert used["factor"] == "1.45" and used["as_of"] == "2026-10-14"


def test_from_the_31st_day_every_trade_is_refused_until_the_factor_is_renewed(tmp_path):
    decision, margin = _factor_on(tmp_path, date(2026, 11, 14), _seed_only(tmp_path))
    assert not decision.ok and "stressed margin multiplier of 2026-10-14 is not valid on 2026-11-14" in margin.reason


def test_the_repository_s_file_is_read_by_its_own_rule(tmp_path):
    """Config names the real file, and C2 uses its latest row dated strictly before the day, whatever A14c has added
    (append-only, so the seed stays in force on 15 Oct, the day after it, forever)."""
    path = ROOT / load_app_config()["risk"]["stressed_margin"]["factor_file"]
    all_rows = list(csv.DictReader(path.open(encoding="utf-8")))
    latest = max(date.fromisoformat(r["as_of"]) for r in all_rows)
    for day in (date(2026, 10, 15), latest + timedelta(days=1)):  # the seed's next day, the latest row's next day
        before = [r for r in all_rows if date.fromisoformat(r["as_of"]) < day]
        _, margin = _factor_on(tmp_path, day, path)
        used = margin.numbers["stress_factor_row"]
        assert (used["as_of"], used["factor"]) == (before[-1]["as_of"], before[-1]["factor"])


@pytest.mark.parametrize(
    ("profile", "priced"),
    [("books", {"bucket_cap", "open_risk_cap"}), ("manual", {"stress_loss", "exposure_limit"})],
)
def test_a_missing_quote_fails_closed_in_every_rule_that_needs_it(tmp_path, profile, priced):
    held = open_trade("held", FLY, 200, short_fly(24000, 200), EXPIRY, 0.0)  # no quotes for its contracts
    manager = _manager(tmp_path)
    if profile == "manual":
        manager = build_risk_manager(load_app_config(), tmp_path, profile)
    decision = _evaluate(manager, the_book=book([held]))
    refused = {v.rule for v in decision.verdicts if not v.ok}
    assert priced <= refused and not decision.ok  # margin room needs no quote of it
    assert all("no quote" in v.reason for v in decision.verdicts if v.rule in priced)


def test_a_stale_mark_cannot_price_a_new_trade(tmp_path):
    new = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)
    stale = market(25000, PRICES, EXPIRY, stale=frozenset({(25000, "CE")}))
    decision = _manager(tmp_path).evaluate(new, book(), stale)
    assert not decision.ok and "stale" in _verdict(decision, "max_loss_per_trade").reason


def test_a_proposal_reusing_an_open_trade_id_is_refused(tmp_path):
    held = open_trade("new", FLY, 200, short_fly(25000, 200), EXPIRY, 0.0)
    assert not _evaluate(_manager(tmp_path), the_book=book([held])).verdicts[0].ok


def test_a_bug_in_a_rule_is_not_swallowed():
    class Broken(RiskRule):
        name = "broken"

        def check(self, proposal, book, market):
            raise KeyError("bug")

    with pytest.raises(KeyError):
        _evaluate(RiskManager([Broken()], {}))


def test_a_malformed_factor_file_refuses_the_trade_by_name(tmp_path):
    """Story C2d (self-review): a short row once escaped RiskManager.evaluate as a TypeError."""
    bad = tmp_path / "stress_factor.csv"
    bad.write_text(HEADER + "2026-10-12,1.45\n", encoding="utf-8")
    margins = tmp_path / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,40000,0,0,test calculator,2026-10-12\n")
    overrides = {"risk": {"stressed_margin": {"factor_file": str(bad)}}}
    decision = _evaluate(
        build_risk_manager(load_app_config(overrides=overrides), tmp_path, tables=local_tables(margins))
    )
    margin = _verdict(decision, "margin_room")
    assert not decision.ok and "stress_factor.csv row 2" in margin.reason
