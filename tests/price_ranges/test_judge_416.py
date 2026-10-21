"""Judge 416's findings, each with its test: an earlier failure still fails a day with no chain (should-fix 1); a
back-fill never carries the live label, an issue not built or an unknown label is refused before any row (should-fix
2); and the rules the first tests left empty: a tie with P(up) away from 0.5, a comparison under 40 paired days, the
90% band's lower edge, a day with no next session, and hist750's P(up) counting only rises."""

from datetime import date, datetime, timedelta

import pytest

from fno.forecast_v4_rules.series import DayValue
from fno.models import IST
from fno.price_ranges.backfill import RangeBackfill
from fno.price_ranges.build import CAPTURE, CLOSE
from fno.price_ranges.forecasters import HistoricalRange
from fno.price_ranges.records import RecordRefused
from fno.price_ranges.scores import comparisons, group_scores, resolved
from fno.price_ranges.sealing import SealCheck
from tests.price_distribution.builders import DAY, Chains, chain_day, drive_store
from tests.price_ranges.builders import CALENDAR, builder, closes
from tests.price_ranges.test_forecasters import inputs
from tests.price_ranges.test_issuer import issuer
from tests.price_ranges.test_sealing_and_scores import record, row


def test_an_earlier_failure_fails_a_day_with_no_chain_anywhere(tmp_path):
    built, drive, _ = issuer(tmp_path, chains={})

    def broken(day):
        raise OSError("Drive unreachable")

    built.before = broken
    code, lines = built.issue(DAY)
    assert code == 1 and any("close tables or seals not updated (OSError)" in line for line in lines)
    assert lines[-1].startswith("nothing written: NIFTY: no canonical") and not drive.files


def test_a_day_with_no_chain_and_no_earlier_failure_is_still_refused(tmp_path):
    code, lines = issuer(tmp_path, chains={})[0].issue(DAY)
    assert code == 0 and len(lines) == 2 and lines[-1].startswith("nothing written:")


@pytest.mark.parametrize(("label", "basis"), [("live", CAPTURE), ("backfill_eod", CAPTURE), ("backfill_3pm", CLOSE)])
def test_a_back_fill_takes_only_its_own_label_and_basis(tmp_path, label, basis):
    store, drive, _ = drive_store(tmp_path)
    run = RangeBackfill(Chains({("NIFTY", DAY): chain_day()}), builder(), lambda u: closes(), store, CALENDAR, None)
    with pytest.raises(ValueError, match="a back-fill is labelled"):
        run.run(label, basis, ("NIFTY",), DAY, DAY)
    assert not drive.files


@pytest.mark.parametrize(("issue", "label"), [("1600", "live"), ("0915", "live"), ("1545", "backfill")])
def test_an_issue_not_built_or_an_unknown_label_is_refused_before_any_row(issue, label):
    with pytest.raises(RecordRefused, match="not built or label"):
        builder().build("NIFTY", DAY, issue, chain_day(), closes(), CAPTURE, label, None)


def test_a_close_equal_to_s_ref_is_not_up_whatever_p_up_says():
    (group,) = group_scores(resolved([(record(rows=[row(p_up=0.8)]), True)], lambda u, d: 100.0)[0])
    assert group["brier_up"] == pytest.approx(0.64)  # (0.8 - 0)^2; counted as up it would be 0.04


@pytest.mark.parametrize(("n", "tested"), [(39, False), (40, True)])
def test_under_40_paired_days_a_comparison_is_not_tested(n, tested):
    days = [(date(2025, 1, 1) + timedelta(days=i)).isoformat() for i in range(n)]
    scored = resolved([(record(d, rows=[row(), row("rv20", shift=0.004)]), True) for d in days], lambda u, d: 100.5)
    first = next(c for c in comparisons(scored[0]) if c["second"] == "rv20")
    assert (first["n"], first["tested"]) == (n, tested)


def test_an_outcome_between_q05_and_q25_is_inside_90_and_outside_50():
    (group,) = group_scores(resolved([(record(), True)], lambda u, d: 98.5)[0])  # -1.5%: between -2% and -1%
    assert (group["inside_50"], group["inside_90"]) == (0.0, 1.0)


def test_with_no_next_session_on_the_calendar_a_pushed_record_is_late():
    pushed = datetime(2026, 12, 31, 16, 0, tzinfo=IST)
    seal = SealCheck(lambda path: pushed, CALENDAR).seal("receipts/x.sha256", date(2026, 12, 31))
    assert seal.late and seal.deadline is None and seal.sealed_at == pushed


def test_hist750_counts_only_rises_as_up_never_a_flat_return():
    wiggle = closes(last=DAY - timedelta(days=1), n=751)
    flat = [c if i % 10 else DayValue(c.day, wiggle[i - 1].value) for i, c in enumerate(wiggle)]  # 1 in 10 unchanged
    out = HistoricalRange().forecast(inputs(tuple(flat)), 1)
    returns = [b.value / a.value for a, b in zip(flat[-750:], flat[-749:], strict=False)]
    assert sum(r == 1 for r in returns) > 70
    assert out.p_up == pytest.approx(sum(r > 1 for r in returns) / len(returns))
