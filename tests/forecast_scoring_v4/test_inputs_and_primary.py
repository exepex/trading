"""G7's agreed file layout read through `ForecastFiles`, and V1's one-way switch to intraday HAR (story G8)."""

from datetime import date

from fno.constants import V1_RV_1S, V4_BASELINE_HAR_DAILY, V4_BASELINE_HAR_INTRADAY, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.inputs import ForecastFiles, ForecastValue, V4ForecastSource
from fno.forecast_scoring.v4.primary import primary_values

HEADER = "day,value,status,label,forecaster_version,kind\n"


def test_the_agreed_layout_is_read_and_any_status_but_ok_is_no_forecast(tmp_path):
    folder = tmp_path / "base_rate"
    folder.mkdir()
    (folder / f"{V6_BIG_MOVE_5S}.csv").write_text(
        HEADER + "2025-01-02,0.1376,ok,backfill_exploratory,1,baseline\n"
        "2025-01-03,,not_eligible,backfill_exploratory,1,baseline\n2025-01-06,0.14,ok,live,1,baseline\n"
    )
    files = ForecastFiles(tmp_path)
    assert files.forecasters(V6_BIG_MOVE_5S) == ["base_rate"] and files.forecasters(V1_RV_1S) == []
    assert files.values(V6_BIG_MOVE_5S, "base_rate") == {
        date(2025, 1, 2): ForecastValue(0.1376, False),
        date(2025, 1, 3): ForecastValue(None, False),
        date(2025, 1, 6): ForecastValue(0.14, True),
    }
    assert files.values(V6_BIG_MOVE_5S, "nobody") == {}


class Fixed(V4ForecastSource):
    def __init__(self, series):
        self.series = series

    def forecasters(self, question):
        return sorted(self.series)

    def values(self, question, forecaster):
        return self.series.get(forecaster, {})


def test_v1_uses_daily_har_until_intraday_har_is_eligible_then_never_again():
    d = [date(2026, 11, day) for day in (2, 3, 4, 5)]
    daily = {day: ForecastValue(1e-4, True) for day in d}
    intraday = {d[2]: ForecastValue(2e-4, True), d[3]: ForecastValue(None, True)}
    chosen = primary_values(V1_RV_1S, Fixed({V4_BASELINE_HAR_DAILY: daily, V4_BASELINE_HAR_INTRADAY: intraday}))
    assert [chosen[day].value for day in d] == [1e-4, 1e-4, 2e-4, None]  # day 4: daily HAR never stands in again
