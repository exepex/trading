"""Judge 651 should-fix 1: the decider's hard time limit. It interrupts a slow block, sets nothing for None, stops at
once for no time left, puts the previous alarm handler back, and the promoter then restores every write path and
marks the promotion timed out (`test_promote.py`; the collector records `late`, never `refused`)."""

import signal
import threading
import time

import pytest

from fno.ai_trading.time_limit import DecisionTimedOut, time_limit


def test_a_slow_block_is_interrupted_at_its_limit():
    started = time.monotonic()
    with pytest.raises(DecisionTimedOut, match="within 0.2 s"), time_limit(0.2):
        time.sleep(5)
    assert time.monotonic() - started < 2


def test_no_limit_and_a_fast_block_run_to_the_end_and_the_old_handler_comes_back():
    before = signal.getsignal(signal.SIGALRM)
    with time_limit(None):
        time.sleep(0.01)
    with time_limit(5):
        time.sleep(0.01)
    assert signal.getsignal(signal.SIGALRM) == before and signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)


@pytest.mark.parametrize("seconds", [0, -3.5])
def test_no_time_left_stops_before_the_block_runs(seconds):
    ran = []
    with pytest.raises(DecisionTimedOut), time_limit(seconds):
        ran.append(1)
    assert ran == []


def test_outside_the_main_thread_no_alarm_is_set():
    seen = []
    worker = threading.Thread(target=lambda: seen.append(_run_in_limit()))
    worker.start()
    worker.join()
    assert seen == ["ran"]


def _run_in_limit():
    with time_limit(0.01):
        time.sleep(0.05)
    return "ran"


def test_a_decider_s_own_except_exception_cannot_swallow_the_stop():
    """Judge 651.1: the stop is a BaseException, so Book 3's proposal guards (`except Exception`) never hide it."""
    with pytest.raises(DecisionTimedOut), time_limit(0.2):
        try:  # noqa: SIM105 - written as deciders write their guards
            time.sleep(5)
        except Exception:  # noqa: BLE001 - what a decider's own guard does
            pass
        time.sleep(5)  # never reached: the stop went through the guard


def test_the_old_handler_comes_back_after_a_stop_too():
    before = signal.getsignal(signal.SIGALRM)
    with pytest.raises(DecisionTimedOut), time_limit(0.05):
        time.sleep(1)
    assert signal.getsignal(signal.SIGALRM) == before and signal.getitimer(signal.ITIMER_REAL) == (0.0, 0.0)
