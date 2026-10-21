"""FL1-1c: G13b's score rows as the page's history, each with the band it scored; for one method, horizon and target
day a live row wins over the 3 pm back-fill, which wins over the end-of-day back-fill (nothing counts twice)."""

from dataclasses import dataclass
from datetime import date

from fno.forecast_lab.g13b_history import G13bHistory

ROW = {"forecaster": "implied", "horizon": "N1", "q05": 980.0, "q25": 995.0, "q50": 1000.0, "q75": 1005.0,
       "q95": 1020.0}  # fmt: skip


OLD, NEW = "a" * 64, "b" * 64


def record(label, day, scale=1.0, method=NEW):
    return {"label": label, "underlying": "NIFTY", "day": day, "issue": "1545", "method_sha256": method,
            "rows": [{**ROW, "q95": 1020.0 * scale}]}  # fmt: skip


def score(label, issue, target, close=1001.0, method=NEW):
    return {"label": label, "method_sha256": method, "underlying": "NIFTY", "issue": "1545", "forecaster": "implied",
            "horizon": "N1", "issue_day": issue, "target_day": target, "outcome_close": close,
            "quantile_score": 0.01, "inside_25_75": True, "inside_05_95": True}  # fmt: skip


@dataclass
class Sealed:
    record: dict


class Forecasts:
    def live(self):
        return [Sealed(record("live", "2026-10-22", 1.01))]

    def backfill(self):
        return [record("backfill_eod", "2026-10-21"), record("backfill_eod", "2026-10-22"),
                record("backfill_3pm", "2026-10-22", 1.02)]  # fmt: skip


class Scores:
    def rows(self, underlying, live_only=False):
        return [score("backfill_eod", "2026-10-21", "2026-10-22"), score("backfill_eod", "2026-10-22", "2026-10-23"),
                score("backfill_3pm", "2026-10-22", "2026-10-23"), score("live", "2026-10-22", "2026-10-23", 1002.0),
                score("backfill_eod", "2026-10-20", "2026-10-21")]  # fmt: skip


def test_live_wins_over_3pm_over_eod_and_each_row_carries_the_band_it_scored():
    points = G13bHistory(Forecasts(), Scores()).points("NIFTY")
    by_target = {p.target_day: p for p in points}
    assert len(points) == 3  # one row per target day
    live = by_target[date(2026, 10, 23)]
    assert (live.live, live.close, live.band.q95, live.error_points) == (True, 1002.0, 1020.0 * 1.01, 0.01 * 1002.0)
    assert by_target[date(2026, 10, 22)].band.q95 == 1020.0 and not by_target[date(2026, 10, 22)].live
    assert by_target[date(2026, 10, 21)].band is None  # its record is not on file: no band, never a made-up one


class TwoVersions:
    """The back-fill was made by the old method; today's live record by the new one, with a different band."""

    def __init__(self, live_method=NEW):
        self.live_method = live_method

    def live(self):
        return [Sealed(record("live", "2026-10-22", 1.01, self.live_method))]

    def backfill(self):
        return [record("backfill_3pm", "2026-10-21", 1.5, OLD), record("backfill_3pm", "2026-10-22", 1.5, OLD)]

    def rows(self, underlying, live_only=False):
        return [score("backfill_3pm", "2026-10-21", "2026-10-22", method=OLD),
                score("backfill_3pm", "2026-10-22", "2026-10-23", method=OLD),
                score("live", "2026-10-22", "2026-10-23", 1002.0, method=self.live_method)]  # fmt: skip


def test_only_the_current_method_version_counts_and_bands_never_cross_versions():
    versions = TwoVersions()
    points = G13bHistory(versions, versions).points("NIFTY")
    assert [(p.target_day, p.live, p.band.q95) for p in points] == [(date(2026, 10, 23), True, 1020.0 * 1.01)]


def test_a_live_score_of_another_version_is_never_paired_with_this_versions_band():
    versions = TwoVersions(live_method=OLD)  # live by the old method too: every row is the old version's
    points = G13bHistory(versions, versions).points("NIFTY")
    assert [(p.target_day, p.live, p.band.q95) for p in points] == [
        (date(2026, 10, 22), False, 1020.0 * 1.5), (date(2026, 10, 23), True, 1020.0 * 1.01)]  # fmt: skip


class Rebuilt:
    """The same back-fill day built by both versions (a re-run after a method change), the old one read last."""

    def live(self):
        return [Sealed(record("live", "2026-10-23", 1.0, NEW))]

    def backfill(self):
        return [record("backfill_3pm", "2026-10-22", 1.01, NEW), record("backfill_3pm", "2026-10-22", 1.5, OLD)]

    def rows(self, underlying, live_only=False):
        return [score("backfill_3pm", "2026-10-22", "2026-10-23", method=NEW)]


def test_a_rebuilt_day_pairs_the_score_with_its_own_versions_band():
    points = G13bHistory(Rebuilt(), Rebuilt()).points("NIFTY")
    assert [p.band.q95 for p in points] == [1020.0 * 1.01]
