"""G13b criterion 10: the live 15:45 issue and O1's exit contract (G13's): not live, a hand run and a closed day
write nothing; a recorded issue is never rebuilt and its stored problems count again; an unreadable chain writes no
file; a chain never captured is a `missing` record; problems exit 1; nothing captured anywhere is refused."""

import json
from datetime import date, datetime, timedelta

from fno.models import IST
from fno.price_distribution.sources import ChainUnavailable
from fno.price_ranges.folders import live_path
from fno.price_ranges.issuer import HAND_RUN, NOT_TRADING, RangeIssuer
from tests.price_distribution.builders import DAY, Chains, chain_day, drive_store
from tests.price_ranges.builders import CALENDAR, builder, closes

NOW = datetime(2026, 10, 16, 15, 45, tzinfo=IST)
BOTH = {("NIFTY", DAY): chain_day(), ("BANKNIFTY", DAY): chain_day(underlying="BANKNIFTY", spot=51_000.0)}


def issuer(tmp_path, chains=None, live_from=DAY, now=NOW, history=None):
    store, drive, receipts = drive_store(tmp_path)
    found = closes() if history is None else history
    source = Chains(BOTH if chains is None else chains)
    built = RangeIssuer(source, builder(), lambda u: found, store, CALENDAR, ("NIFTY", "BANKNIFTY"), live_from,
                        lambda: now, lambda day: ["BANKNIFTY closes: x"])  # fmt: skip
    return built, drive, receipts


def path(underlying):
    return f"data/{live_path(underlying, DAY, '1545')}"


def test_a_good_day_writes_one_live_record_per_underlying_with_receipts(tmp_path):
    built, drive, receipts = issuer(tmp_path)
    code, lines = built.issue(DAY)
    assert (code, lines[0], lines[-1]) == (0, "BANKNIFTY closes: x", "issued")
    for underlying in ("NIFTY", "BANKNIFTY"):
        record = json.loads(drive.files[path(underlying)])
        assert record["label"] == "live" and record["issued_at"] == NOW.isoformat() and receipts.read(path(underlying))


def test_not_live_a_hand_run_not_today_and_a_closed_day_write_nothing(tmp_path):
    assert issuer(tmp_path / "a")[0].issue(DAY, live=False) == (0, [HAND_RUN])
    assert issuer(tmp_path / "b", live_from=None)[0].issue(DAY)[1][0].startswith("nothing written: not live")
    assert issuer(tmp_path / "c", live_from=DAY + timedelta(days=1))[0].issue(DAY)[0] == 0
    earlier = issuer(tmp_path / "d", live_from=DAY - timedelta(days=5))[0].issue(DAY - timedelta(days=1))
    assert earlier[1][0].startswith("nothing written: 2026-10-15 is not today")
    holiday = datetime(2026, 10, 20, 15, 45, tzinfo=IST)
    assert issuer(tmp_path / "e", now=holiday)[0].issue(date(2026, 10, 20)) == (0, [NOT_TRADING])


def test_a_missing_chain_is_recorded_missing_and_fails_the_step(tmp_path):
    built, drive, _ = issuer(tmp_path, chains={("NIFTY", DAY): chain_day()})
    code, lines = built.issue(DAY)
    assert code == 1 and lines[-1] == "written with problems: BANKNIFTY no canonical 3 pm chain"
    assert json.loads(drive.files[path("BANKNIFTY")])["status"] == "missing"


def test_an_unreadable_chain_writes_no_file_and_a_rerun_issues_it(tmp_path):
    down = {**BOTH, ("BANKNIFTY", DAY): ChainUnavailable("groww raw quote file unreadable: x")}
    built, drive, _ = issuer(tmp_path, chains=down)
    code, lines = built.issue(DAY)
    assert (
        code == 1
        and "BANKNIFTY groww raw quote file unreadable: x" in lines[-1]
        and path("BANKNIFTY") not in drive.files
    )
    built.chains = Chains(BOTH)
    assert built.issue(DAY)[1][-3:] == ["NIFTY: already issued", "BANKNIFTY: issued (0 problems)", "issued"]


def test_a_rerun_of_a_problem_day_still_fails_with_its_stored_problems(tmp_path):
    built, drive, _ = issuer(tmp_path, history=closes(last=DAY - timedelta(days=4)))  # stale closes
    first, _ = built.issue(DAY)
    files = dict(drive.files)
    code, lines = built.issue(DAY)
    assert (first, code) == (1, 1) and drive.files == files and lines[1].startswith("NIFTY: already issued with")


def test_nothing_captured_anywhere_is_refused_and_writes_nothing(tmp_path):
    built, drive, _ = issuer(tmp_path, chains={})
    code, lines = built.issue(DAY)
    assert code == 0 and lines[-1].startswith("nothing written: NIFTY: no canonical") and not drive.files
