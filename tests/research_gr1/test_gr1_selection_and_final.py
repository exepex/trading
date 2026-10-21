"""GR1 protocol sections 6, 9 and 10 on synthetic data: the calibration bands at their edges, the winner by paired
difference against C0, C8 not run for BANKNIFTY, an input gap over 5% not decided, C11's pair chosen on train only,
and the final decision (Holm, every check, "not shown at this sample size", C1/C2 "known before the study")."""

from datetime import date

from gr1study.evaluate import Numbers
from gr1study.final import NOT_SHARPER, NOT_SHOWN, SHARPER, decide, final_cell
from gr1study.selection import NOT_RUN_NO_DATA, bands_ok, select_cell, winner_of

from tests.research_gr1.gr1_fakes import context, rows, weekdays


def n(inside_90, inside_50):
    return Numbers(250, 0, inside_50, inside_90, 1.0, 2.0, 0.01, (), False)


def test_the_bands_hold_at_their_edges_only():
    assert bands_ok(n(0.87, 0.45)) and bands_ok(n(0.93, 0.55))
    assert not bands_ok(n(0.8699, 0.5)) and not bands_ok(n(0.9301, 0.5)) and not bands_ok(n(0.9, 0.4499))
    assert not bands_ok(n(0.9, 0.5501)) and not bands_ok(n(None, 0.5))


def periods(**kw):
    """A short train period keeps the suite fast; the rules do not depend on its length."""
    return rows(date(2022, 1, 1), date(2023, 12, 31), seed=1, **kw), rows(date(2024, 1, 1), date(2024, 12, 31),
                                                                       seed=2, **kw)  # fmt: skip


def test_a_too_wide_implied_gets_a_winner_with_a_negative_paired_difference():
    train, select = periods(implied_sd=0.01, true_sd=0.008)
    out = select_cell("NIFTY", train, select, context())
    winner = out["winner"]
    assert winner is not None and out["candidates"][winner]["select"]["mean_qs_difference_vs_c0"] < 0
    assert out["candidates"][winner]["eligible"] and not out["c0"]["select_bands_ok"]  # implied's 90% holds ~97%


def test_c8_is_not_run_for_banknifty_and_a_candidate_without_inputs_fails_with_no_rows():
    train, select = periods(underlying="BANKNIFTY")
    out = select_cell("BANKNIFTY", train, select, context())
    assert out["candidates"]["C8"]["status"] == NOT_RUN_NO_DATA
    assert out["candidates"]["C3"]["status"] == "failed"  # no VIX at all in this context


def vix_context(select_days, missing_share):
    days = weekdays(date(2022, 1, 1), date(2024, 12, 31))
    vix = {d: 10.0 + (i % 20) for i, d in enumerate(days)}
    for d in select_days[: int(len(select_days) * missing_share)]:
        vix.pop(d)
    return context(vix=vix, train_vix_terciles=(15.0, 22.0))


def test_an_input_gap_over_five_percent_in_2024_is_not_decided():
    train, select = periods()
    out = select_cell("NIFTY", train, select, vix_context([r.day for r in select], 0.06))
    assert out["candidates"]["C3"]["reason"].startswith("not decided:")
    ok = select_cell("NIFTY", train, select, vix_context([r.day for r in select], 0.04))
    assert not (ok["candidates"]["C3"]["reason"] or "").startswith("not decided:")


def test_c11s_pair_comes_from_train_only():
    days = weekdays(date(2023, 1, 1), date(2024, 12, 31))
    vix = {d: 10.0 + (i % 20) for i, d in enumerate(days)}
    ctx = context(vix=vix, train_vix_terciles=(15.0, 22.0), events={d: date(2018, 1, 1) for d in days[::9]})

    def sd(day):
        return 0.0004 * vix.get(day, 15.0)

    train = rows(date(2023, 1, 1), date(2023, 12, 31), seed=1, sd_of=sd)
    one = select_cell("NIFTY", train, rows(date(2024, 1, 1), date(2024, 12, 31), seed=2, sd_of=sd), ctx)
    other = select_cell("NIFTY", train, rows(date(2024, 1, 1), date(2024, 12, 31), seed=9, true_sd=0.02), ctx)
    c11 = [k for k in one["candidates"] if k.startswith("C11(")]
    assert c11 and c11 == [k for k in other["candidates"] if k.startswith("C11(")]


def chosen(winner="C1"):
    train, select = periods(implied_sd=0.01, true_sd=0.008)
    out = select_cell("NIFTY", train, select, context())
    return dict(out, winner=winner)


def test_the_final_decision_and_its_determinism():
    final_rows = rows(date(2025, 1, 1), date(2026, 10, 20), seed=3, implied_sd=0.01, true_sd=0.008)
    selection = chosen("C1")
    first = final_cell(("NIFTY", "N1"), selection, final_rows, context())
    assert first == final_cell(("NIFTY", "N1"), selection, final_rows, context())  # run 2 is deterministic
    decided = decide({"NIFTY/N1": first})["NIFTY/N1"]
    assert decided["verdict"] == SHARPER and decided["known_before_the_study"]
    no_winner = final_cell(("NIFTY", "N1"), dict(selection, winner=None), final_rows, context())
    assert no_winner["verdict"] == NOT_SHOWN


def test_holm_and_every_check_are_needed():
    base = {"winner": "C3", "p_value": 0.02, "tested": True, "mean_difference": -0.001,
            "checks": {"bands_ok": True, "crossed": False, "gap_ok": True, "narrower_90": True}}  # fmt: skip
    cells = {"a": dict(base), "b": dict(base, p_value=0.04)}
    assert {k: c["verdict"] for k, c in decide(cells).items()} == {"a": SHARPER, "b": SHARPER}  # Holm: 0.02, 0.04
    cells = {"a": dict(base, p_value=0.01), "b": dict(base, p_value=0.02), "c": dict(base, p_value=0.04)}
    assert {k: c["verdict"] for k, c in decide(cells).items()} == dict.fromkeys("abc", SHARPER)  # 1/3, 1/2, 1 of 5%
    cells = {"a": dict(base), "b": dict(base, p_value=0.03), "c": dict(base, p_value=0.04)}
    assert {k: c["verdict"] for k, c in decide(cells).items()} == dict.fromkeys("abc", NOT_SHARPER)  # 0.02 > 0.0167
    wider = dict(base, checks=dict(base["checks"], narrower_90=False))
    assert decide({"a": wider})["a"]["verdict"] == NOT_SHARPER
    assert decide({"a": dict(base, mean_difference=0.001)})["a"]["verdict"] == NOT_SHARPER
    assert decide({"a": dict(base, p_value=0.06)})["a"]["verdict"] == NOT_SHARPER
    out_of_band = dict(base, checks=dict(base["checks"], bands_ok=False))
    assert decide({"a": out_of_band})["a"]["verdict"] == NOT_SHARPER


def test_the_winner_is_the_most_negative_difference_and_never_a_worse_candidate():
    assert winner_of({"C3": -0.0002, "C5": -0.0005, "C7": 0.0001}) == "C5"
    assert winner_of({"C3": 0.0001, "C7": 0.0}) is None and winner_of({}) is None and winner_of({"C4": None}) is None
