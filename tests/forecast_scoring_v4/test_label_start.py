"""Story G10, D2 revised (orchestrator's rule-8 finding, 24 Oct): the day labels start at the pack's live date
(`daily.live_from.v4_pack`), never at the forecasts' (`forecasts_v4`). A live forecast day before the pack was live has
no label and its rows stay in; a pack-live day with no release record is `system_late` once passed, pending on its own
date; the release's catch-up starts at the same date."""

from datetime import date

import pytest

from fno.constants import V4_DAY_A, V4_DAY_SYSTEM_LATE
from fno.forecast_scoring.v4 import wiring
from fno.forecast_scoring.v4.days import DayLabel, LateDaysOut, LiveDayLabels
from fno.forecast_scoring.v4.inputs import ForecastValue, Outcome
from tests.forecast_scoring_v4.test_release_days import Records, weekdays

FORECASTS, FRI, PACK, TUE = date(2026, 10, 22), date(2026, 10, 23), date(2026, 10, 26), date(2026, 10, 27)


def config(v4_pack=PACK):
    return {"daily": {"live_from": {"forecasts_v4": FORECASTS.isoformat(),
                                    "v4_pack": v4_pack.isoformat() if v4_pack else None}}}  # fmt: skip


def test_the_labels_start_at_the_pack_s_live_date():
    assert wiring.label_start(config()) == PACK
    assert wiring.label_start(config(v4_pack=None)) is None  # the pack not live: no label at all


@pytest.fixture
def labels_on(monkeypatch):
    """`build_day_labels` with no release record in Drive, a weekday calendar and `config()`'s dates."""
    monkeypatch.setattr(wiring, "build_drive_records", lambda folder: None)
    monkeypatch.setattr(wiring, "ReleasedDays", lambda records: Records({}))
    monkeypatch.setattr(wiring, "_is_session", lambda: lambda day: day.weekday() < 5)
    monkeypatch.setattr("fno.config.load_config", config)
    return wiring.build_day_labels


def test_pre_pack_live_days_have_no_label_and_a_passed_pack_day_without_a_record_is_late(labels_on):
    labels = labels_on(TUE)
    assert {d: label.label for d, label in labels.labels().items()} == {PACK: V4_DAY_SYSTEM_LATE}
    assert labels.pending() == 1  # Tuesday itself, no record yet


def test_the_pack_s_first_day_is_pending_on_its_own_date_and_nothing_before_it_is_labelled(labels_on):
    labels = labels_on(PACK)
    assert labels.labels() == {} and labels.pending() == 1


class Rows:
    def forecasters(self, question):
        return ["rule"]

    def values(self, question, forecaster):
        return {d: ForecastValue(0.5, True) for d in (FORECASTS, FRI, PACK)}

    def outcomes(self, question):
        return dict.fromkeys((FORECASTS, FRI, PACK), Outcome(1.0))


def test_the_rows_of_pre_pack_live_days_stay_in_and_only_the_late_pack_day_is_out():
    days = LiveDayLabels(Records({}), weekdays, wiring.label_start(config()), TUE)
    kept = LateDaysOut(Rows(), Rows(), days)
    assert set(kept.values("q", "rule")) == set(kept.outcomes("q")) == {FORECASTS, FRI}


def test_a_stored_record_before_the_live_date_is_ignored_and_none_counts_while_the_pack_is_not_live():
    """Judge 613: a record dated before the pack's live date (a rehearsal's, say) never labels a day."""
    stored = {FRI: DayLabel(FRI, V4_DAY_SYSTEM_LATE, "", None), PACK: DayLabel(PACK, V4_DAY_A, "a" * 64, None)}
    labels = LiveDayLabels(Records(stored), weekdays, PACK, TUE)
    assert {d: label.label for d, label in labels.labels().items()} == {PACK: V4_DAY_A}
    assert LiveDayLabels(Records(stored), weekdays, PACK, PACK).labels() == {PACK: stored[PACK]}  # the boundary day
    assert LiveDayLabels(Records(stored), weekdays, None, TUE).labels() == {}
