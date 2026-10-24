"""Story G7b completion, part b2 (criteria 6, 9-11 live, 13): the adapter from G10's released pack, V4's and V5's
history from their stored records, and yardstick A's intraday window points."""

import hashlib
import json
from datetime import UTC, date, datetime, time, timedelta

import pytest

from fno.forecast_v4.settlement import V5Outcome
from fno.forecast_v4_rules.implied import HorizonRv, IvPoint
from fno.forecast_v4_rules.intraday_series import intraday_horizon_rv
from fno.forecast_v4_rules.option_history import (
    OptionHistory,
    outcome_bytes,
    outcome_from_bytes,
    outcome_path,
    terms_from_bytes,
)
from fno.forecast_v4_rules.option_terms import OptionTerms, Void
from fno.forecast_v4_rules.pack_adapter import future_quote, pack_inputs
from fno.forecast_v4_rules.pack_capture import terms_bytes
from fno.forecast_v4_rules.series import SessionRv
from fno.models import IST
from fno.v4_pack.model import FutureQuote, Iv30, Level, Pack, VixLevel
from fno.v4_pack.release import ReleaseRecord
from tests.forecast_v4_rules.option_fixtures import LISTED, MONTHLY, WEEKLY, D, chain

SEEN = datetime.combine(D, time(14, 31), IST)
SHA = "a" * 64
TERMS = OptionTerms(D, WEEKLY, 26000.0, 26080.0, 200.0, 150.0, 0.138, 0.138, 5, 7)


def pack(future: FutureQuote, v4_expiry=WEEKLY) -> Pack:
    return Pack(D, "A", "groww", "groww", "capture", SEEN, Level(26010.0, SEEN), future, VixLevel(14.0, SEEN, None),
                tuple(chain(WEEKLY, 26080.0, 0.14)), Iv30(15.5, False, (MONTHLY,), "g1", SEEN), v4_expiry)  # fmt: skip


def test_the_adapter_keeps_the_release_apart_converts_iv30_and_reads_the_future_trade():
    future = FutureQuote(MONTHLY, 26080.0, 26075.0, 26085.0, SEEN, None, 1200, SEEN)
    release = ReleaseRecord(D, "A", "v4/packs/2026/2026-10-27.json", SHA, SEEN)
    inputs = pack_inputs(release, pack(future), b"pack bytes", LISTED)
    assert (inputs.release_label, inputs.release_sha256) == ("A", SHA)
    assert inputs.pack_sha256 == hashlib.sha256(b"pack bytes").hexdigest()  # the bytes read, apart from the release
    assert inputs.iv30 == IvPoint(0.155, False) and inputs.v4_expiry == WEEKLY and inputs.future_expiry == MONTHLY
    assert inputs.future.traded_flag is True and inputs.future.last_trade_time is None
    assert future_quote(FutureQuote(MONTHLY, 1.0, None, None, SEEN)) is None  # the quote failed: V5 voids itself
    assert future_quote(FutureQuote(MONTHLY, 1.0, 1.0, 2.0, SEEN, None, 0, SEEN)).traded_flag is False


def test_a_system_late_release_gives_inputs_with_its_label_and_no_pack():
    late = pack_inputs(ReleaseRecord(D, "system_late", "", "", None), None, b"", None)
    assert (late.release_label, late.release_sha256, late.pack_sha256, late.iv30) == ("system_late", "", "", None)


def test_terms_and_outcomes_round_trip_through_their_stored_bytes():
    assert terms_from_bytes(terms_bytes(TERMS, SHA)) == TERMS
    void = Void(D, "no_v4_expiry")
    assert terms_from_bytes(terms_bytes(void, SHA)) == void
    outcome = V5Outcome(MONTHLY, True, 26500.0, "nse/fo/x.csv", "f" * 64, datetime(2026, 11, 23, 19, 0, tzinfo=UTC))
    assert outcome_from_bytes(outcome_bytes(D, outcome)) == (D, outcome)
    assert outcome_path(D) == "v4/outcomes/v5/2026/2026-10-27.json"
    assert json.loads(outcome_bytes(D, outcome))["day"] == "2026-10-27"


SESSIONS = [D + timedelta(n) for n in range(10) if (D + timedelta(n)).weekday() < 5]


def rows(values):
    return [SessionRv(d, v, datetime.combine(d, time(20), IST)) for d, v in zip(SESSIONS[1:], values)]


def test_history_gives_v4_outcomes_void_terms_and_v5_outcomes_and_their_base_inputs():
    v5_outcome = V5Outcome(MONTHLY, True, 26500.0, "x", "f" * 64, datetime(2026, 11, 23, 19, 0, tzinfo=UTC))
    later = D + timedelta(days=1)
    history = OptionHistory({D: TERMS, later: Void(later, "spread")}, {D: TERMS, later: TERMS}, {D: v5_outcome},
                            rows([6e-05, 8e-05, 7e-05, 9e-05, 7e-05]), SESSIONS)  # fmt: skip
    v4 = history.v4()
    assert v4[D].value is False and v4[later].value is None  # v4_golden.json's "no"; void terms void at once
    assert history.v5()[D].value is True and history.v5()[D].resolved_on == date(2026, 11, 24)  # IST date of 19:00 UTC
    v4_base, v5_base = history.base_outcomes()
    assert [o.day for o in v4_base] == [D] and [o.day for o in v5_base] == [D]
    assert history.pending_v5() == [TERMS]  # `later`'s V5 terms have no outcome yet


def test_empty_history_has_no_outcomes():
    empty = OptionHistory({}, {}, {}, [], SESSIONS)
    assert empty.v4() == {} and empty.v5() == {} and empty.base_outcomes() == ([], []) and empty.pending_v5() == []


def test_yardstick_as_window_points_need_every_session_of_the_horizon_non_void():
    rv = {SESSIONS[1]: 1e-5, SESSIONS[2]: 2e-5, SESSIONS[3]: None, SESSIONS[4]: 3e-5, SESSIONS[5]: 4e-5}
    points = intraday_horizon_rv(rv, SESSIONS, 1)
    assert points[SESSIONS[0]] == HorizonRv(1e-5, SESSIONS[1]) and SESSIONS[2] not in points  # its next is void
    assert points[SESSIONS[3]] == HorizonRv(3e-5, SESSIONS[4]) and SESSIONS[5] not in points  # no row ahead
    two = intraday_horizon_rv(rv, SESSIONS, 2)
    assert two[SESSIONS[0]].value == pytest.approx(3e-5) and SESSIONS[1] not in two and SESSIONS[2] not in two
    assert intraday_horizon_rv({}, SESSIONS, 1) == {}


class Args:
    forecast_v4_cmd = "capture-pack"


def run_cli(monkeypatch, capsys, build=None, capture=None):
    import fno.forecast_v4_rules.pack_capture as pack_capture
    import fno.forecast_v4_rules.pack_wiring as pack_wiring
    from fno.forecast_v4_rules.cli import cmd_forecast_v4

    monkeypatch.setattr(pack_wiring, "build_pack_capture", build)
    monkeypatch.setattr(pack_wiring, "run_followups", lambda day, eod, put: ["proxy drift: 1 day(s) paired"])
    if capture is not None:
        monkeypatch.setattr(pack_capture, "capture_pack", capture)
    code = cmd_forecast_v4(Args())
    return code, capsys.readouterr().out


def built(label="A"):
    from fno.forecast_v4_rules.pack_adapter import pack_inputs

    release = ReleaseRecord(D, label, "", SHA if label == "A" else "", None)
    future = FutureQuote(MONTHLY, 26080.0, 26075.0, 26085.0, SEEN, None, 1200, SEEN)
    inputs = pack_inputs(release, pack(future) if label == "A" else None, b"x", LISTED)
    from fno.forecast_v4_rules.pack_wiring import PackCapture

    return lambda day: PackCapture(None, inputs, None, None, {}, ["V5 2026-10-27: outcome written"])


def test_the_cli_refuses_without_a_release_record_and_o1_reads_it_as_nothing_written(monkeypatch, capsys):
    from fno.forecast_v4_rules.pack_wiring import PackCapture

    def missing(day):  # judge 598 SF1: the refit ratios and V5 are settled before the release is read
        return PackCapture(None, None, None, None, {}, ["premium ratio close_proxy v1 for 2026-10: 0.6"],
                           "no release record")  # fmt: skip

    code, out = run_cli(monkeypatch, capsys, missing)
    assert code == 0 and "nothing written: no release record" in out and "premium ratio close_proxy" in out
    assert "proxy drift" not in out  # no release: the follow-ups wait for a released day


def test_the_cli_on_a_system_late_day_is_no_refusal(monkeypatch, capsys):
    code, out = run_cli(monkeypatch, capsys, built("system_late"))
    assert code == 0 and "no pack today (system_late)" in out and "nothing written:" not in out
    assert out.index("V5 2026-10-27: outcome written") < out.index("no pack today")  # V5 settled before the rows
    assert "proxy drift: 1 day(s) paired" in out  # the follow-ups run whatever the day's rows did


def test_the_cli_fails_on_a_changed_row_and_refuses_past_the_deadline(monkeypatch, capsys):
    from fno.forecast_v4_rules.pack_capture import CaptureRefused, ChangedRow
    from fno.storage.raw_store import RawFileConflict

    def changed(*args):
        raise ChangedRow("v4/x.json: a different row is already written for this day")

    def late(*args):
        raise CaptureRefused("15:10:00 IST is at or after the 15:10 deadline")

    assert run_cli(monkeypatch, capsys, built(), changed)[0] == 1

    def in_drive(*args):
        raise RawFileConflict("v4/x.json is already in Drive with other bytes")

    code, out = run_cli(monkeypatch, capsys, built(), in_drive)  # a row in Drive whose receipt is gone (review 8)
    assert code == 1 and "stopped:" in out
    code, out = run_cli(monkeypatch, capsys, built(), late)
    assert code == 0 and "nothing written:" in out
    code, out = run_cli(monkeypatch, capsys, built(), lambda *args: ["a", "b"])
    assert code == 0 and "2 files written or already the same" in out


def test_pending_v5_outcomes_are_written_once_resolved_refused_printed_and_unresolved_waiting():
    from fno.forecast_v4_rules.option_outcomes import Refused
    from fno.forecast_v4_rules.pack_followups import resolve_pending_v5

    later, latest = D + timedelta(days=1), D + timedelta(days=2)
    from dataclasses import replace

    history = OptionHistory({}, {d: replace(TERMS, day=d) for d in (D, later, latest)}, {}, [], SESSIONS)
    outcome = V5Outcome(MONTHLY, False, 27000.0, "x", "f" * 64, datetime(2026, 11, 23, 19, 0, tzinfo=UTC))
    answers = {D: outcome, later: Refused(later, "first seen before the close"), latest: None}
    written = {}
    lines, found = resolve_pending_v5(history, lambda terms: answers[terms.day], written.__setitem__)
    assert found == {D: outcome} and history.with_v5_outcomes(found).pending_v5() == [
        replace(TERMS, day=later),
        replace(TERMS, day=latest),
    ]
    assert list(written) == [outcome_path(D)] and outcome_from_bytes(written[outcome_path(D)]) == (D, outcome)
    assert any("refused" in line and "2026-10-28" in line for line in lines) and len(lines) == 2


def test_drift_pairs_wait_for_the_eod_chain_and_are_written_once():
    from fno.forecast_v4_rules.pack_followups import drift_pair, drift_path, write_drift_pairs

    later = D + timedelta(days=1)
    packs = {D: IvPoint(0.15, False), later: IvPoint(0.16, False)}
    written = {}
    days = write_drift_pairs(packs, {D: IvPoint(0.14, False)}, set(), written.__setitem__)
    assert days == [D] and drift_pair(written[drift_path(D)]) == (D, 0.15, 0.14)  # `later` waits for its EOD chain
    assert write_drift_pairs(packs, {D: IvPoint(0.14, False)}, {D}, written.__setitem__) == []
    write_drift_pairs({later: IvPoint(0.16, True)}, {later: IvPoint(0.14, False)}, set(), written.__setitem__)
    assert drift_pair(written[drift_path(later)]) == (later, None, 0.14)  # a flagged pack IV30 is no value
