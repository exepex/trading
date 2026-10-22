"""The live issue's exit contract, criterion 4 (the seal and late flag are G13b's, with G13d's 15:30 deadline), and
the readers FL1 and the dashboard use."""

import json
from datetime import date, datetime

from fno.models import IST
from fno.premium_ranges.constants import ISSUE
from fno.premium_ranges.folders import SCORES, live_path, seal_path
from fno.premium_ranges.issuer import HAND_RUN, NO_G13, NOT_LIVE, NOT_TRADING, PremiumIssuer
from fno.premium_ranges.reader import PremiumRanges, PremiumScores
from fno.premium_ranges.wiring import same_day_close
from fno.price_distribution.folders import live_path as g13_live_path
from fno.price_ranges.sealing import SealCheck

from .builders import contract, expiry, g13_record

D, NEXT = date(2026, 10, 16), date(2026, 10, 19)


class FakeStore:
    def __init__(self, files=None):
        self.files = dict(files or {})

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        self.files[path] = data


class Calendar:
    def session_kind(self, day):
        return "regular" if day.weekday() < 5 else None

    def next_session(self, day):
        return NEXT


def issuer(store, live_from=D, now=datetime(2026, 10, 16, 15, 20, tzinfo=IST)) -> PremiumIssuer:
    return PremiumIssuer(store, Calendar(), ("NIFTY",), live_from, lambda: now, "m" * 64)


def with_g13() -> FakeStore:
    record = g13_record(D, [expiry(date(2026, 10, 27), 11, [contract(23000.0, "CE", 150.0)])])
    return FakeStore({g13_live_path("NIFTY", D): json.dumps(record).encode()})


def test_refusals_write_nothing():
    store = with_g13()
    assert issuer(store).issue(D, live=False) == (0, [HAND_RUN])
    assert issuer(store, live_from=None).issue(D) == (0, [NOT_LIVE.format(day=D, live_from=None)])
    saturday = date(2026, 10, 17)
    assert issuer(store, now=datetime(2026, 10, 17, 15, 20, tzinfo=IST)).issue(saturday) == (0, [NOT_TRADING])
    assert len(store.files) == 1


def test_an_issue_is_written_once_and_a_rerun_keeps_it():
    store = with_g13()
    code, lines = issuer(store).issue(D)
    stored = store.files[live_path("NIFTY", D, ISSUE)]
    assert code == 0 and lines[-1] == "issued" and json.loads(stored)["rows"][0]["strike"] == 23000.0
    assert issuer(store, now=datetime(2026, 10, 16, 15, 25, tzinfo=IST)).issue(D) == (0, ["NIFTY: already issued",
                                                                                          "issued"])  # fmt: skip
    assert store.files[live_path("NIFTY", D, ISSUE)] == stored


def test_no_g13_record_is_a_problem_and_no_file():
    store = FakeStore()
    code, lines = issuer(store).issue(D)
    assert code == 1 and NO_G13.format(underlying="NIFTY", day=D) in lines and store.files == {}


def test_the_seal_deadline_is_1530_on_the_issue_day():
    on_time, late = datetime(2026, 10, 16, 15, 29, tzinfo=IST), datetime(2026, 10, 16, 15, 31, tzinfo=IST)
    assert same_day_close(Calendar(), D) == datetime(2026, 10, 16, 15, 30, tzinfo=IST)
    assert not SealCheck(lambda path: on_time, Calendar(), same_day_close).seal("r", D).late
    assert SealCheck(lambda path: late, Calendar(), same_day_close).seal("r", D).late
    assert (
        SealCheck(lambda path: (_ for _ in ()).throw(OSError("no log")), Calendar(), same_day_close).seal("r", D).late
    )


def test_premium_ranges_reader_gives_the_rule_quantiles_and_the_stored_seal(tmp_path):
    store = with_g13()
    issuer(store).issue(D)
    target = tmp_path / live_path("NIFTY", D, ISSUE)
    target.parent.mkdir(parents=True)
    target.write_bytes(store.files[live_path("NIFTY", D, ISSUE)])
    (found,) = PremiumRanges(tmp_path).for_day("NIFTY", D)
    assert (found.next_session, found.strike, found.side, found.mid, found.late) == (NEXT, 23000.0, "CE", 150.0, None)
    assert list(found.quantiles) == sorted(found.quantiles)
    seal = tmp_path / seal_path("NIFTY", D, ISSUE)
    seal.parent.mkdir(parents=True)
    seal.write_text(json.dumps({"sealed_at": "2026-10-16T15:24:00+05:30", "late": False}))
    assert PremiumRanges(tmp_path).for_day("NIFTY", D)[0].late is False
    assert PremiumRanges(tmp_path).for_day("NIFTY", NEXT) == []


def test_premium_scores_reader_takes_the_latest_report(tmp_path):
    folder = tmp_path / SCORES
    folder.mkdir(parents=True)
    for name, sessions in (("2026-10-20T160000_a", 1), ("2026-10-21T160000_b", 2)):
        (folder / f"{name}.json").write_text(json.dumps({"underlyings": {"NIFTY": {"sessions": sessions}}}))
    assert PremiumScores(tmp_path).latest("NIFTY") == {"sessions": 2}
    assert PremiumScores(tmp_path).latest("BANKNIFTY") is None
    assert PremiumScores(tmp_path / "none").latest("NIFTY") is None
