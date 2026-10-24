"""The builder's self-review findings (story MS-P0b Claims, round 1), each as a test that fails on the old code."""

import threading
from datetime import datetime, time

import pytest

from fno.models import IST
from fno.school.probes.constants import Source
from fno.school.probes.dry_run import MadeUpResponse
from fno.school.probes.groww_timeout import BoundedCall, GrowwCallHung

from .fakes import SESSION, GrowwError, GrowwRateLimitedStub, Rig


class GrowwAPITimeoutException(Exception):
    pass


@pytest.mark.parametrize("error", [GrowwAPITimeoutException(), GrowwError("503"), GrowwError("401")])
def test_a_sign_in_that_fails_in_any_way_is_tried_once_for_the_whole_run(tmp_path, error):
    rig = Rig(tmp_path)
    tries = []

    class SignsInEachTime:
        def __getattr__(self, name):
            tries.append(name)
            raise error

    rig.tools.groww.client = SignsInEachTime()
    rig.run()
    assert len(tries) == 1
    assert rig.counts().stops[Source.GROWW].endswith(f"sign-in failed: {type(error).__name__}")


def test_a_groww_stop_is_pushed_before_nse_runs_so_a_rerun_never_asks_groww_again(tmp_path):
    rig = Rig(tmp_path, groww_faults={8: GrowwRateLimitedStub("429")}, nse_faults={3: KeyboardInterrupt()})
    with pytest.raises(KeyboardInterrupt):
        rig.run()
    assert rig.publisher.calls[-1] == f"{SESSION} groww stopped"
    again = Rig(tmp_path)
    again.run()
    assert again.groww.calls == 0


@pytest.mark.parametrize(("call", "answer"), [(7, {}), (7, {"status": "FAILURE"}), (1, {"expiries": []})])
def test_a_groww_answer_without_its_expected_fields_stops_groww(tmp_path, call, answer):
    rig = Rig(tmp_path)
    original = {"get_quote": rig.groww.get_quote, "get_expiries": rig.groww.get_expiries}

    def odd(name):
        def answer_or_call(**kw):
            if rig.groww.calls + 1 == call:
                rig.groww.calls += 1
                return answer
            return original[name](**kw)

        return answer_or_call

    rig.groww.get_quote, rig.groww.get_expiries = odd("get_quote"), odd("get_expiries")
    rig.run()
    assert rig.counts().stops[Source.GROWW].endswith("answer is not the expected JSON")
    assert rig.groww.calls == call


def test_an_nse_answer_with_no_futures_listed_stops_nse(tmp_path):
    rig = Rig(tmp_path, nse_faults={2: MadeUpResponse({"stocks": []})})
    rig.run()
    assert rig.counts().stops[Source.NSE].endswith("answer is not the expected JSON") and rig.nse.calls == 2


def test_an_unreadable_chain_stops_its_source_cleanly_and_the_run_goes_on(tmp_path):
    rig = Rig(tmp_path)
    chain = rig.groww.get_option_chain

    def bad_strike(**kw):
        answer = chain(**kw)
        answer["strikes"]["n/a"] = answer["strikes"].popitem()[1]
        return answer

    rig.groww.get_option_chain = bad_strike
    code, lines = rig.run()
    assert rig.counts().stops[Source.GROWW].endswith("answer is not the expected JSON")
    assert rig.alerts.sent and rig.nse.calls == 44 and code == 1


@pytest.mark.parametrize("bad", ["n/a", None, 7])
def test_an_unreadable_nse_future_stops_nse_cleanly(tmp_path, bad):
    entry = {"metadata": {"instrumentType": "Stock Futures", "expiryDate": "24-Nov-2026", "lastPrice": bad}}
    if bad is None:
        entry = "not a dict"
    rig = Rig(tmp_path, nse_faults={2: MadeUpResponse({"stocks": [entry]})})
    rig.run()
    stop = rig.counts().stops.get(Source.NSE, "")
    assert stop.endswith("answer is not the expected JSON") or bad == 7  # 7 is a number: read as a price


def test_a_hung_groww_call_stops_after_the_timeout_and_is_never_called_twice():
    release, calls = threading.Event(), []

    def hangs():
        calls.append(1)
        release.wait(5)

    bounded = BoundedCall(timeout_seconds=0.05)
    with pytest.raises(GrowwCallHung):
        bounded.run(hangs)
    with pytest.raises(GrowwCallHung):
        bounded.run(hangs)
    release.set()
    assert calls == [1]


def test_an_answer_inside_the_timeout_is_returned():
    assert BoundedCall(timeout_seconds=1).run(lambda: {"ok": 1}) == {"ok": 1}


def test_no_request_starts_after_the_hard_stop_even_after_a_pace_wait(tmp_path):
    from fno.school.probes.answers import RawAnswer
    from fno.school.probes.caller import PacedCaller
    from fno.school.probes.dry_run import JumpingClock
    from fno.school.probes.pace import StudyPace

    clock = JumpingClock(SESSION, time(10, 2))
    deadline = datetime.combine(SESSION, time(10, 2, 1), IST)
    caller = PacedCaller(StudyPace(3.0, clock.timer, clock.sleep), 10, deadline, clock.wall, clock.timer,
                         clock.sleep, False)  # fmt: skip
    ok = RawAnswer(status=200, payload={}, shape_ok=True)
    assert caller.call("future", lambda: ok) is ok
    assert caller.call("future", lambda: ok) is None and caller.sent == 1


def test_a_failed_expiry_lookup_is_tried_again_next_slot(tmp_path):
    rig = Rig(tmp_path, groww_faults={1: GrowwError("503"), 2: GrowwError("503")})  # NIFTY's lookup, twice
    rig.run()
    first, second = rig.counts().slots["10:07"][Source.GROWW], rig.counts().slots["11:37"][Source.GROWW]
    assert second.reserved == 51  # the plain budget plus NIFTY's lookup
    assert first.quality["missing"] >= 1 and second.quality.get("missing", 0) == 0


def test_groww_rows_carry_no_source_time(tmp_path):
    import gzip
    import json

    rig = Rig(tmp_path)
    rig.run()
    raw = gzip.decompress(rig.store.files["school/p0b/groww/2026-10-29/1007.jsonl.gz"]).decode().splitlines()
    rows = [json.loads(line)["row"] for line in raw if '"row"' in line[:8]]
    assert rows and all(row["source_time"] is None for row in rows)
    assert all("stale" not in row["quality"] for row in rows)
