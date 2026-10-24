"""The practice report says which spread buckets are still short of the sessions they need (MS-SIM, DRY1 P-e4; judge
556): never a count above 30, and the legs in no bucket are said plainly."""

from datetime import timedelta

import pytest

from fno.school.constants import RoadCode
from fno.school.execution import practice_wiring
from fno.school.fakes import FakeSettlementSource
from fno.school.simulator.constants import PRACTICE_LABEL
from fno.school.simulator.practice.render import render
from fno.school.simulator.practice.report import PracticeReport, RoadDayCoverage
from fno.school.simulator.spreads.model import SpreadModel
from tests.school.simulator.practice import test_fleet as tf
from tests.school.simulator.practice.test_runner import ONE_SESSION, runner
from tests.school.simulator.source import builders as sb


@pytest.fixture(autouse=True)
def archive_stubbed(monkeypatch):
    monkeypatch.setattr(practice_wiring, "build_settlement_source", lambda: FakeSettlementSource({}))


def cut_model(sessions_of) -> SpreadModel:
    """The full model with each bucket cut or extended to `sessions_of(bucket)` recorded sessions."""
    full = tf.parts().spreads
    out = {}
    for bucket, days in full.by_session.items():
        wanted, kept = sessions_of(bucket), dict(days)
        first = min(kept)
        kept.update({first - timedelta(days=i): 0.01 for i in range(1, 60)})  # more days than any bucket needs
        out[bucket] = dict(sorted(kept.items(), reverse=True)[:wanted])
    return SpreadModel(out)


def test_a_run_with_too_few_recorded_sessions_names_the_short_buckets_with_their_counts(tmp_path):
    """Dry run 1 (23 Oct): 0 of 39,422 legs priced looked like a silent zero. It is the 30-session rule at work."""
    report = runner(tmp_path, tf.parts(spreads=cut_model(lambda bucket: 8))).run(ONE_SESSION)
    insufficient = sum(c.insufficient for c in report.coverage)
    legs = sum(c.legs for c in report.coverage)
    text = render(report)
    assert insufficient and set(report.short_buckets.values()) == {8}
    expected = (f"{PRACTICE_LABEL} | not enough sessions yet: {len(report.short_buckets)} spread buckets are short of "
                f"the 30 recorded sessions a bucket needs (shortest 8, longest 8), so {insufficient} of {legs} legs "
                "read 'insufficient spread data' and are not priced")  # fmt: skip
    assert expected in text
    assert any(t.endswith(", 8 of 30 sessions") for t in text if "insufficient spread data: " in t)


def test_with_unequal_buckets_only_the_short_ones_are_named_and_no_count_exceeds_30(tmp_path):
    """Judge 556: a best-bucket count printed "35 of the 30" when another bucket was short."""
    from fno.school.simulator.spreads.bucket import DaysToExpiry

    def sessions(bucket):
        return {DaysToExpiry.WEEK: 8, DaysToExpiry.MONTH: 12}.get(bucket.dte, 35)

    report = runner(tmp_path, tf.parts(spreads=cut_model(sessions))).run(ONE_SESSION)
    text = "\n".join(render(report))
    assert set(report.short_buckets.values()) == {8, 12}  # the 35-session buckets priced their legs, so none is named
    assert "shortest 8, longest 12" in text and "of 30 sessions" in text
    assert not any(f"{n} of 30 sessions" in text for n in range(30, 99)) and "35" not in text


def test_the_summary_counts_only_buckets_with_legs_that_could_not_be_priced(tmp_path):
    report = runner(tmp_path, tf.parts(spreads=cut_model(lambda bucket: 35))).run(ONE_SESSION)
    assert not report.short_buckets
    assert "not enough sessions yet" not in "\n".join(render(report))


def test_the_line_is_absent_when_every_leg_could_be_priced():
    report = PracticeReport(sb.SESSION, sb.SESSION, ())
    report.coverage.append(RoadDayCoverage(sb.SESSION, RoadCode.NIFTY_MONTHLY, 10, 10, 0, 0, 0, 0))
    assert not any("not enough sessions yet" in text for text in render(report))


def report_with(insufficient_legs: int, short: dict[str, int]) -> PracticeReport:
    report = PracticeReport(sb.SESSION, sb.SESSION, (), short_buckets=short)
    report.coverage.append(
        RoadDayCoverage(sb.SESSION, RoadCode.NIFTY_MONTHLY, 20, 20 - insufficient_legs, 0, 0, 0, insufficient_legs)
    )
    return report


def test_insufficient_legs_in_no_bucket_are_said_plainly_and_never_raise():
    """Judge 556 addendum: legs of an expired contract belong to no bucket, so there is no session count to name."""
    text = render(report_with(3, {}))
    assert f"{PRACTICE_LABEL} | 3 of 20 legs read 'insufficient spread data' and are not priced" in text
    assert not any("spread buckets are short" in line for line in text)


def test_the_bucket_count_is_the_short_buckets_not_every_bucket_with_legs():
    report = report_with(5, {"NIFTY, a": 8, "NIFTY, b": 12})
    report.insufficient_buckets.update({"NIFTY, a": 2, "NIFTY, b": 1, "None": 2})  # two legs belong to no bucket
    text = "\n".join(render(report))
    assert "2 spread buckets are short" in text and "shortest 8, longest 12" in text
    assert "5 of 20 legs read" in text
