"""F9 protocol sections 3-7: entry at the close before the event, exit at the event day's close or the next, the
monthly expiry with at least 5 sessions left, the gap and the move, a fly closed at the exit closes, events used only
when announced before entry, control days away from events, the clustered p, the ordinary-day control and the
nomination."""

from datetime import date, timedelta

import pytest
from f9study import summary
from f9study.rows import FutureBar, MonthlyDay
from f9study.trades import NO_EXPIRY, run_setup, setup

from fno.config import load_app_config
from fno.research_data.panel_reader import OptionQuote

CHARGES = load_app_config()["charges"]
DAYS = [date(2024, 3, 1) + timedelta(days=i) for i in range(40) if (date(2024, 3, 1) + timedelta(days=i)).weekday() < 5]
NEAR, FAR = DAYS[8], DAYS[25]  # two monthly expiries
EVENT = DAYS[6]


def chain(day, expiry, forward=22000.0, tv=150.0):
    """A fixed strike grid around 22,000; intrinsic plus a time value falling with distance from the forward."""
    out = []
    for i in range(-30, 31):
        k = 22000.0 + 100 * i
        t = max(tv * 0.9 ** (abs(k - forward) / 100), 2.0)
        out += [OptionQuote(expiry, k, "CE", max(forward - k, 0) + t, 0.0, 5, 10),
                OptionQuote(expiry, k, "PE", max(k - forward, 0) + t, 0.0, 5, 10)]  # fmt: skip
    return out


def rows(entry_tv=150.0, exit_tv=100.0, exit_forward=22000.0, event_open=22050.0):
    found = {}
    for d in DAYS:
        tv, fwd = (exit_tv, exit_forward) if d >= EVENT else (entry_tv, 22000.0)
        options = chain(d, NEAR, fwd, tv) + chain(d, FAR, fwd, tv)
        opened = event_open if d == EVENT else fwd
        futures = (FutureBar(NEAR, opened, fwd), FutureBar(FAR, opened, fwd))
        found[d] = MonthlyDay(d, tuple(options), futures, {NEAR: 65, FAR: 65}, "udiff")
    return found


def test_entry_is_the_session_before_the_event_and_the_expiry_leaves_five_sessions():
    s = setup("NIFTY", EVENT, "E0", DAYS, rows())
    assert (s.entry, s.exit, s.status) == (DAYS[5], EVENT, "ok")
    assert s.expiry == FAR  # NEAR has only 2 sessions after the exit
    assert s.gap_pct == pytest.approx(50.0 / 22000.0)


def test_e1_exits_one_session_later():
    assert setup("NIFTY", EVENT, "E1", DAYS, rows()).exit == DAYS[7]


def test_an_event_on_a_non_session_day_uses_the_next_session():
    saturday = next(d for d in (DAYS[4] + timedelta(days=i) for i in range(1, 4)) if d.weekday() == 5)
    s = setup("NIFTY", saturday, "E0", DAYS, rows())
    assert s.entry < saturday < s.exit


def test_no_expiry_far_enough_is_counted():
    short = {d: MonthlyDay(r.day, r.options, (r.futures[0],), r.lots, r.source) for d, r in rows().items()}
    assert setup("NIFTY", EVENT, "E0", DAYS, short).status == NO_EXPIRY


def test_a_fly_closed_after_a_crush_with_no_move_earns_the_time_value_drop():
    data = rows(entry_tv=150.0, exit_tv=100.0)
    s = setup("NIFTY", EVENT, "E0", DAYS, data)
    t = run_setup("FLY", s, data, CHARGES, 1.0)
    assert t.status == "taken" and t.gross > 0
    assert t.pads == 2 * 4 * 1.0 * 65 and t.net == pytest.approx(t.gross - t.charges - t.pads)


def test_a_large_move_loses_and_stays_within_the_cap():
    data = rows(entry_tv=150.0, exit_tv=100.0, exit_forward=24000.0)
    s = setup("NIFTY", EVENT, "E0", DAYS, data)
    t = run_setup("FLY", s, data, CHARGES, 1.0)
    assert t.gross < 0 and -t.gross <= 10000.0


def test_events_count_only_when_announced_before_entry(tmp_path, monkeypatch):
    import study_f9

    path = tmp_path / "events.csv"
    path.write_text("date,type,announced_on,source_url,announcement_source_url\n"
                    f"{EVENT},budget,{DAYS[0]},x,y\n{DAYS[10]},rbi_policy,{DAYS[9]},x,y\n")  # fmt: skip
    monkeypatch.setattr(study_f9, "EVENTS", path)
    assert study_f9.events(DAYS) == {EVENT: "budget"}  # the second was announced on its own entry day


def test_control_days_keep_two_sessions_away_from_events():
    import study_f9

    controls = study_f9.control_days(DAYS, {EVENT: "budget"})
    assert not set(DAYS[4:9]) & set(controls) and DAYS[3] in controls and DAYS[9] in controls


def row(net, event, kind="rbi_policy", index="NIFTY", status="taken"):
    return {"net": net, "gross": net, "charges": 0.0, "pads": 0.0, "event": event, "kind": kind, "index": index,
            "status": status, "move_pct": 0.0}  # fmt: skip


def test_trades_of_one_event_form_one_cluster_and_few_events_give_p_one():
    rows_ = [row(10.0, "e1"), row(30.0, "e1", index="BANKNIFTY"), row(-20.0, "e2"), row(60.0, "e2", index="BANKNIFTY")]
    m, se, g = summary.clustered(rows_)
    assert (m, g) == (20.0, 2) and se == pytest.approx(0.0)
    assert summary.p_value(1.0, 1.0, 29) == 1.0


def test_an_incomplete_exit_is_kept_out_of_the_decided_mean():
    found = summary.decided([row(1.0, "a"), {**row(9.0, "b"), "incomplete": True}])
    assert [r["event"] for r in found] == ["a"]


def test_the_ordinary_day_control_samples_whole_days():
    control = [row(0.0, f"c{i}") for i in range(20)] + [row(100.0, "c0", index="BANKNIFTY")]
    p = summary.event_control_p(control, 1, 50.0)
    assert p == summary.event_control_p(control, 1, 50.0) and 0.0 < p < 0.2  # only day c0 reaches 50
    assert summary.event_control_p(control, 30, 1.0) is None


@pytest.mark.parametrize(("changes", "expected"),
                         [({}, True), ({"holm": False}, False), ({"p_event": 0.11}, False),
                          ({"mean_net_pad2": -1.0}, False), ({"mean_gross": 800.0}, False)])  # fmt: skip
def test_nomination_needs_all_four_conditions(changes, expected):
    r = {"holm": True, "p_event": 0.05, "mean_net_pad2": 1.0, "mean_gross": 900.0, **changes}
    assert summary.eligible(r) is expected


def test_the_code_hash_is_the_frozen_one():
    """Judge 668 m3: dropping an event row or editing the frozen code changes code_hash() and fails here."""
    import re

    import study_f9

    frozen = re.search(r"Study code SHA-256 .*\| `([0-9a-f]{64})` \|", (study_f9.HERE / "F9_FREEZE.md").read_text())
    assert frozen and study_f9.code_hash() == frozen.group(1)


def test_at_most_two_variants_are_nominated_lowest_p_first():
    """Judge 668 m4."""
    passing = {"holm": True, "p_event": 0.01, "mean_net_pad2": 10.0, "mean_gross": 900.0}
    rows = {f"V{i}": {**passing, "p": p} for i, p in enumerate((0.004, 0.001, 0.003, 0.002))}
    assert summary.nominated(rows) == ["V1", "V3"]
