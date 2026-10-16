"""LM1 criterion 5: the same condition on the same position alerts once an hour, a market-wide one once an hour for
the desk (or once per step), and the 11th DANGER of a session starts the summary at most every 30 minutes."""

from __future__ import annotations

from fno.monitor.limits import SUMMARY_KEY, AlertLimits, SentAlert
from fno.monitor.model import DANGER, DESK, HOURLY, ONCE, POSITION, WARNING, Condition

from .fixtures import at, settings

LIMITS = AlertLimits(settings())


def condition(key="loss_used:danger:T1", severity=DANGER, repeat=HOURLY, scope=POSITION) -> Condition:
    return Condition(key.split(":")[0], severity, scope, key, repeat, "facts", "T1")


def sent(key, hhmm, severity=DANGER) -> SentAlert:
    return SentAlert(key, severity, at(hhmm))


def test_an_hourly_condition_waits_a_full_hour():
    history = [sent("loss_used:danger:T1", "10:00")]
    assert LIMITS.decide([condition()], history, at("10:45")).send == ()
    assert LIMITS.decide([condition()], history, at("11:00")).send == (condition(),)


def test_a_once_condition_alerts_once_a_session():
    once = condition("big_move:below:1.50", repeat=ONCE, scope=DESK)
    history = [sent(once.key, "09:30")]
    decision = LIMITS.decide([once], history, at("15:00"))
    assert (decision.send, decision.held) == ((), (once,))


def test_each_position_and_each_level_has_its_own_key():
    two = [condition("loss_used:danger:T1"), condition("loss_used:danger:T2")]
    assert len(LIMITS.decide(two, [sent("loss_used:warning:T1", "10:15", WARNING)], at("10:30")).send) == 2


def test_the_11th_danger_starts_the_summary_and_the_next_waits_30_minutes():
    history = [sent(f"short_strike_near:T{n}:24500", "10:00") for n in range(10)]
    decision = LIMITS.decide([condition("loss_used:danger:T99")], history, at("10:15"))
    assert decision.send == () and decision.summary.key == SUMMARY_KEY
    assert "1 more DANGER" in decision.summary.facts
    history.append(sent(SUMMARY_KEY, "10:15"))
    later = LIMITS.decide([condition("loss_used:danger:T98")], history, at("10:30"))
    assert later.summary is None and len(later.held) == 1
    assert LIMITS.decide([condition("loss_used:danger:T98")], history, at("10:45")).summary is not None


def test_warnings_are_never_folded_into_the_danger_summary():
    history = [sent(f"short_strike_near:T{n}:24500", "10:00") for n in range(10)]
    warning = condition("loss_used:warning:T5", severity=WARNING)
    assert LIMITS.decide([warning], history, at("10:15")).send == (warning,)


def test_the_tenth_danger_still_goes_out_alone():
    history = [sent(f"short_strike_near:T{n}:24500", "10:00") for n in range(9)]
    decision = LIMITS.decide([condition("a:1"), condition("b:2")], history, at("10:15"))
    assert [c.key for c in decision.send] == ["a:1"] and decision.summary is not None
