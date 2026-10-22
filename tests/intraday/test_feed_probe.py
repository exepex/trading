"""Story A16h, criteria 3-5: each plan only inside its window and under its cap; every plan unsubscribes everything and
stops on a 429 or at its hard end time; the ramp stops at the first error; the alongside gate; coverage by class; the
summary holds no tick value and no secret."""

from datetime import date, datetime, timedelta

import pytest

from fno.intraday.feed_gate import alongside_gate, catch_up_gate
from fno.intraday.feed_probe import ENDED, PLANS, FeedProbe, ProbeRefused, summary
from fno.intraday.feed_ramp import CLOSED
from fno.intraday.feed_universe import FeedInstrument, universe
from fno.models import IST

DAY = date(2026, 10, 27)
SECRET, PRICE = "sk-secret-token", 24567.85
FEED_TYPES = {"subscribe_ltp": "ltp", "subscribe_index_value": "index_value", "subscribe_market_depth": "market_depth"}


class Clock:
    def __init__(self, hh, mm, ss=0):
        self.now = datetime(2026, 10, 27, hh, mm, ss, tzinfo=IST)

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += timedelta(seconds=seconds)


class RateLimited(Exception):
    code = 429

    def __str__(self):
        return f"429 for {SECRET}"


class Feed:
    def __init__(self, fail_on=None, fail_at=None):
        self.calls, self.callbacks, self.fail_on, self.fail_at, self.held = [], [], fail_on, fail_at, 0

    def _subscribe(self, name, items, callback):
        self.calls.append((name, len(items)))
        self.held += len(items)
        if self.fail_at is not None and self.held > self.fail_at:
            raise RuntimeError(SECRET)
        self.callbacks.append(callback)
        for item in items:
            callback({"feed_type": FEED_TYPES[name], "feed_key": item["exchange_token"]})
        return {"NSE": {"FNO": {item["exchange_token"]: True for item in items}}}

    def subscribe_ltp(self, items, callback):
        return self._subscribe("subscribe_ltp", items, callback)

    def subscribe_index_value(self, items, callback):
        return self._subscribe("subscribe_index_value", items, callback)

    def subscribe_market_depth(self, items, callback):
        return self._subscribe("subscribe_market_depth", items, callback)

    def get_ltp(self):
        if self.fail_on == "get_ltp":
            raise RateLimited()
        return {"NSE": {"FNO": {"1": {"tsInMillis": 1793079600000.0, "ltp": PRICE}}}}

    def get_index_value(self):
        return {}

    def __getattr__(self, name):
        if name.startswith("unsubscribe_"):
            return lambda items: self.calls.append((name, len(items)))
        raise AttributeError(name)


def options(n):
    return [FeedInstrument("option", "NIFTY", "NSE", "FNO", str(i), date(2026, 10, 27), 25000.0 + i, "CE", "monthly")
            for i in range(1, n + 1)]  # fmt: skip


def run(plan, clock, feed=None, instruments=None, minutes=None):
    feed = feed or Feed()
    outcome = FeedProbe(feed, clock, clock.sleep).run(PLANS[plan], instruments or options(10), DAY, minutes)
    return outcome, feed


@pytest.mark.parametrize(("plan", "early", "late"), [("coverage", (10, 19, 59), (10, 25, 1)),
                         ("alongside", (14, 29, 59), (14, 50, 1)), ("ramp", (15, 44, 59), (16, 0, 1)),
                         ("ramp-day", (10, 49, 59), (10, 51, 1))])  # fmt: skip
def test_each_plan_starts_only_in_its_window(plan, early, late):
    for moment in (early, late):
        with pytest.raises(ProbeRefused, match="may start only"):
            run(plan, Clock(*moment))


def test_alongside_holds_at_most_1000_instruments():
    with pytest.raises(ProbeRefused, match="at most 1000"):
        run("alongside", Clock(14, 45), instruments=options(1001))
    outcome, _ = run("alongside", Clock(14, 45), instruments=options(1000), minutes=1)
    assert outcome.accepted == 1000


def test_coverage_subscribes_ltp_and_depth_runs_to_its_hard_end_and_unsubscribes_everything():
    clock = Clock(10, 20)
    outcome, feed = run("coverage", clock)
    assert ("subscribe_ltp", 10) in feed.calls and ("subscribe_market_depth", 10) in feed.calls
    assert outcome.stop == ENDED and clock.now >= datetime(2026, 10, 27, 10, 40, tzinfo=IST)
    assert ("unsubscribe_ltp", 10) in feed.calls and ("unsubscribe_market_depth", 10) in feed.calls
    lines = "\n".join(outcome.lines)
    assert "option NIFTY monthly 2026-10-27 CE [ltp]: 10 of 10 ticked, 10 ticks" in lines
    assert "option NIFTY monthly 2026-10-27 CE [market_depth]: 10 of 10 ticked, 10 ticks" in lines


@pytest.mark.parametrize("plan", ["coverage", "alongside"])
def test_a_429_stops_at_once_unsubscribes_and_names_it_without_its_text(plan):
    clock = Clock(10, 20) if plan == "coverage" else Clock(14, 45)
    outcome, feed = run(plan, clock, Feed(fail_on="get_ltp"))
    assert outcome.stop == "rate limited (429): RateLimited" and ("unsubscribe_ltp", 10) in feed.calls
    assert clock.now < datetime(2026, 10, 27, 10, 21, tzinfo=IST) or plan == "alongside"
    text = "\n".join(summary(outcome))
    assert SECRET not in text and str(PRICE) not in text


def test_the_latency_line_uses_the_ticks_own_exchange_time():
    outcome, _ = run("coverage", Clock(10, 20), minutes=1)
    assert any(line.startswith("latency (receipt minus exchange time): median") for line in outcome.lines)


def ledger(**changes):
    clean = {"status": "good", "failures": "", "expected_contracts": "216", "recorded_contracts": "216"}
    return {mark: {"mark_ist": mark, **clean, **changes.get(mark, {})} for mark in ("10:30", "10:45")}


@pytest.mark.parametrize(("rows", "why"), [
    (ledger(), ""),
    (ledger(**{"10:30": {"status": "failed"}}), "10:30 mark is not clean (status failed)"),
    (ledger(**{"10:45": {"failures": "quote 429"}}), "10:45 mark is not clean (failures recorded)"),
    (ledger(**{"10:30": {"recorded_contracts": "200"}}), "10:30 mark is not clean (quotes missing)"),
    ({"10:30": ledger()["10:30"]}, "10:45 mark is not clean (no ledger row)"),
])  # fmt: skip
def test_the_alongside_gate_reads_a16s_1030_and_1045_marks(rows, why):
    found = alongside_gate(lambda day: list(rows.values()), DAY)
    assert found == ("" if not why else f"no alongside today: A16's {why}")


def test_the_universe_takes_index_values_three_futures_and_near_money_monthly_and_weekly_options():
    def row(kind, under, token, expiry="", strike=""):
        return {"instrument_type": kind, "trading_symbol": under if kind == "IDX" else token, "underlying_symbol": under
                if kind != "IDX" else "", "segment": "CASH" if kind == "IDX" else "FNO", "exchange": "NSE",
                "exchange_token": token, "expiry_date": expiry, "strike_price": strike}  # fmt: skip

    rows = [row("IDX", "NIFTY", "NIFTY")]
    rows += [row("FUT", "NIFTY", f"F{m}", f"2026-{m}-24") for m in (10, 11, 12)] + [
        row("FUT", "NIFTY", "F1", "2027-01-26")
    ]
    for expiry in ("2026-10-27", "2026-11-03", "2026-11-24"):
        rows += [
            row(t, "NIFTY", f"{expiry}{k}{t}", expiry, str(k)) for k in range(24800, 25300, 50) for t in ("CE", "PE")
        ]
    found = universe(rows, {"NIFTY": 25010.0}, date(2026, 10, 22), side=1)
    kinds = [(i.kind, i.expiry, i.strike) for i in found]
    assert ("index", None, None) in kinds and sum(k == "future" for k, *_ in kinds) == 3
    assert {s for k, e, s in kinds if k == "option"} == {24950.0, 25000.0, 25050.0}
    # 27 Oct is the October monthly, so NIFTY's weekly is the nearest non-monthly expiry, 3 Nov
    assert {e for k, e, s in kinds if k == "option"} == {date(2026, 10, 27), date(2026, 11, 3)}
    assert {i.feed_class() for i in found if i.kind == "option" and i.option_type == "CE"} == {
        "option NIFTY monthly 2026-10-27 CE",
        "option NIFTY weekly 2026-11-03 CE",
    }
    every = universe(rows, {"NIFTY": 25010.0}, date(2026, 10, 22), side=1, every_expiry=True)
    assert {i.expiry for i in every if i.kind == "option"} == {
        date(2026, 10, 27),
        date(2026, 11, 3),
        date(2026, 11, 24),
    }


def test_the_command_checks_the_gate_before_any_sign_in(monkeypatch, capsys):
    from argparse import Namespace

    from fno.intraday import feed_cli, feed_wiring

    monkeypatch.setattr(feed_wiring, "build_gate", lambda: lambda day: "no alongside today: A16's 10:30 mark ...")
    monkeypatch.setattr(feed_wiring, "build_feed_probe", lambda cfg: pytest.fail("signed in before the gate"))
    assert feed_cli.cmd_feed_probe(Namespace(plan="alongside", minutes=None, config=None)) == 1
    assert capsys.readouterr().out.startswith("no alongside today")


class CappedFeed(Feed):
    """Creates topics up to `cap` held at once; past it, `False` (not created); `refuse_all` raises on every call."""

    def __init__(self, cap=10_000, refuse_all=False, rate_limit_at=None):
        super().__init__()
        self.cap, self.refuse_all, self.rate_limit_at, self.tokens = cap, refuse_all, rate_limit_at, set()

    @property
    def holding(self):
        return len(self.tokens)

    def _subscribe(self, name, items, callback):
        self.calls.append((name, len(items)))
        if self.refuse_all:
            raise RuntimeError(SECRET)
        if self.rate_limit_at is not None and self.holding + len(items) > self.rate_limit_at:
            raise RateLimited()
        created = {}
        for item in items:
            created[item["exchange_token"]] = self.holding < self.cap
            if created[item["exchange_token"]]:
                self.tokens.add(item["exchange_token"])
        return {"NSE": {"FNO": created}}

    def __getattr__(self, name):
        if name.startswith("unsubscribe_"):

            def release(items):
                self.calls.append((name, len(items)))
                self.tokens -= {item["exchange_token"] for item in items}

            return release
        raise AttributeError(name)


def test_after_the_close_a_refusal_at_50_twice_means_a_closed_market():
    outcome, feed = run("ramp", Clock(15, 45), CappedFeed(refuse_all=True), options(3000))
    assert CLOSED in outcome.lines and outcome.reached == 0
    assert [c for c in feed.calls if c[0] == "subscribe_ltp"] == [("subscribe_ltp", 50), ("subscribe_ltp", 50)]
    assert SECRET not in "\n".join(summary(outcome))


def test_a_limit_at_450_is_found_by_halving_and_every_refused_batch_is_released():
    outcome, feed = run("ramp", Clock(15, 45), CappedFeed(cap=450), options(3000))
    line = next(line for line in outcome.lines if line.startswith("subscription limit:"))
    low, high = (int(word) for word in line.replace(",", "").split() if word.isdigit())
    assert low <= 450 < high and high - low <= 50 and outcome.reached == low
    assert feed.holding == 0  # everything released at the end


def test_between_marks_a_first_refusal_is_a_limit_not_a_closed_market():
    outcome, _ = run("ramp-day", Clock(10, 50), CappedFeed(refuse_all=True), options(3000))
    assert "subscription limit: 0 accepted, 50 refused" in outcome.lines and CLOSED not in outcome.lines


def test_a_429_in_the_ramp_stops_the_run_at_once():
    outcome, feed = run("ramp", Clock(15, 45), CappedFeed(rate_limit_at=600), options(3000))
    assert outcome.stop == "rate limited (429): RateLimited" and feed.holding == 0


def test_with_no_limit_the_ramp_reaches_3000():
    outcome, _ = run("ramp", Clock(15, 45), CappedFeed(), options(3000))
    assert "no limit up to 3000" in outcome.lines and outcome.reached == 3000


def test_the_ramp_stops_at_its_hard_end_time_and_never_waits_past_it(monkeypatch):
    monkeypatch.setattr("fno.intraday.feed_ramp.STEP_SECONDS", 120)  # the steps no longer fit in 10:50-10:58
    clock = Clock(10, 50)
    outcome, feed = run("ramp-day", clock, CappedFeed(), options(3000))
    assert clock.now == datetime(2026, 10, 27, 10, 58, tzinfo=IST) and outcome.reached < 3000
    assert outcome.stop == ENDED and feed.holding == 0


@pytest.mark.parametrize(("log", "why"), [
    (None, "no run log"),
    ({"steps": {}}, "no candles step"),
    ({"steps": {"candles": {"started_at": "2026-10-27T15:32:10+05:30"}}}, "the candles step has not finished"),
    ({"steps": {"candles": {"started_at": "x", "finished_at": "2026-10-27T15:33:17+05:30"}}}, ""),
])  # fmt: skip
def test_the_after_close_ramp_waits_for_a16bs_candle_catch_up(log, why):
    found = catch_up_gate(log, DAY)
    assert found == ("" if not why else f"no ramp today: A16b's candle catch-up is not recorded done in "
                     f"journal/runs/2026-10-27.json ({why})")  # fmt: skip


def test_the_ramp_command_checks_the_catch_up_before_any_sign_in(monkeypatch, capsys):
    from argparse import Namespace

    from fno.intraday import feed_cli, feed_wiring

    monkeypatch.setattr(feed_wiring, "build_catch_up_gate", lambda: lambda day: "no ramp today: ...")
    monkeypatch.setattr(feed_wiring, "build_feed_probe", lambda cfg: pytest.fail("signed in before the gate"))
    assert feed_cli.cmd_feed_probe(Namespace(plan="ramp", minutes=None, config=None)) == 1
    assert capsys.readouterr().out.startswith("no ramp today")
