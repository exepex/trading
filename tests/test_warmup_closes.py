"""Story A10: warm-up closes before the panel (index closes only), read by the panel reader as closes-only sessions,
so F1 and F2 exist from the first 2019 decision day; no 2017-18 option or future row reaches experiment code."""

import csv
import json
import math
from datetime import date
from statistics import median

import pytest

from fno.composition import build_cycles, build_features, load_research_data
from fno.config import ROOT, load_app_config
from fno.constants import INDEX_INDIA_VIX, INDEX_NIFTY_50, SESSION_MUHURAT
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.nifty_panel import DailyFiles, PanelBuildError
from fno.research_data.panel_reader import SessionClose, read_nifty_panel
from fno.research_data.panel_store import MANIFEST_FILE, WARMUP_FILE
from fno.research_data.warmup_closes import build_warmup_rows, write_warmup_closes
from fno.research_engine.close_series import realised_vol_points
from fno.research_engine.cycles import cycle_rows
from fno.research_engine.features import DecisionContext
from fno.research_engine.volatility_features import atm_strike
from fno.storage.raw_source import NseIndexCloseSource
from fno.storage.wiring import PANEL_FOLDER, build_session_calendar

SOURCE_URL = "https://nsearchives.nseindia.com/content/circulars/FAOP36476.pdf"
CALENDAR = CsvSessionCalendar(
    f"date,kind,description,source_url\n2018-12-25,holiday,Christmas,{SOURCE_URL}\n"
    f"2019-03-04,holiday,Mahashivratri,{SOURCE_URL}\n"
)
FIRST_DECISION_DAY = date(2019, 1, 2)  # the story's "first 2019 decision day"
FIRST_CYCLE_DAY = date(2019, 1, 14)  # B2's first monthly cycle decision of 2019 (expiry 28 Feb 2019)


def closes_file(nifty="10862.55", vix="15.54") -> bytes:
    return f"Index Name,Closing Index Value\n{INDEX_NIFTY_50},{nifty}\n{INDEX_INDIA_VIX},{vix}\nNifty Bank,1\n".encode()


def index_files(files: dict[date, bytes]) -> DailyFiles:
    return DailyFiles(
        "index-close",
        NseIndexCloseSource.dataset,
        None,
        None,
        lambda day: (NseIndexCloseSource.filename_for(day), files.get(day)),
    )


def test_one_row_per_session_with_both_closes_and_the_file_it_came_from(tmp_path):
    days = [date(2018, 12, d) for d in (24, 26, 27, 28, 31)]  # the 25th is a holiday
    rows = build_warmup_rows(index_files({d: closes_file() for d in days}), CALENDAR, days[0], days[-1])
    assert [r[0] for r in rows] == [d.isoformat() for d in days]
    assert rows[0][1:5] == ("regular", 10862.55, 15.54, "ind_close_all_24122018.csv") and len(rows[0][5]) == 64
    path = write_warmup_closes(tmp_path, rows)
    assert (
        path.name == WARMUP_FILE
        and path.read_text().splitlines()[0] == "date,session,underlying,vix,index_file,index_sha256"
    )


def test_a_session_without_its_file_or_a_close_fails_the_whole_build():
    files = {date(2018, 12, 24): closes_file(), date(2018, 12, 26): b"Index Name,Closing Index Value\nNifty 50,1\n"}
    with pytest.raises(PanelBuildError) as failed:
        build_warmup_rows(index_files(files), CALENDAR, date(2018, 12, 24), date(2018, 12, 27))
    assert [p[:10] for p in failed.value.problems] == ["2018-12-26", "2018-12-27"]


def small_panel(folder, warmup_rows):
    manifest = {"days": {"2019-01-01": {"status": "ok", "session": "regular"}}}
    (folder / MANIFEST_FILE).write_text(json.dumps(manifest))
    write_warmup_closes(folder, warmup_rows)


def test_the_reader_puts_closes_only_warmup_sessions_before_the_panel(tmp_path):
    rows = [
        ("2018-12-31", "regular", 10862.55, 15.54, "f", "0" * 64),
        ("2019-01-01", "regular", 1.0, 1.0, "f", "0" * 64),
    ]
    small_panel(tmp_path, rows)
    panel = read_nifty_panel(tmp_path)
    assert panel.sessions[0] == SessionClose(date(2018, 12, 31), "regular", 10862.55, 15.54)
    assert [s.day for s in panel.sessions] == [date(2018, 12, 31), date(2019, 1, 1)]  # never one on or after the start
    assert not panel.options and not panel.futures
    assert read_nifty_panel(tmp_path, years=[2020]).sessions == ()  # warm-up only before the panel's first year


# Real data: the committed panel (A3) and warm-up file (A10).

WARMUP = PANEL_FOLDER / WARMUP_FILE


@pytest.fixture(scope="module")
def year_2019():
    return load_research_data(years=[2019], keep=cycle_rows)


@pytest.fixture(scope="module")
def features():
    return build_features(load_app_config(str(ROOT / "config.yaml")))


def test_the_warmup_file_covers_every_2017_and_2018_session_with_index_closes_only():
    rows = list(csv.DictReader(WARMUP.read_text().splitlines()))
    sessions = build_session_calendar().sessions(date(2017, 1, 1), date(2018, 12, 31))
    assert [date.fromisoformat(r["date"]) for r in rows] == sessions
    assert all(r["index_file"].startswith("ind_close_all_") for r in rows)  # never an F&O file


def test_no_2017_or_2018_option_or_future_row_reaches_experiment_code(year_2019):
    panel = year_2019.panel
    assert panel.sessions[0].day == date(2017, 1, 2)
    assert min(panel.options) >= date(2019, 1, 1) and min(panel.futures) >= date(2019, 1, 1)
    assert build_cycles(panel)[0].decision_day == FIRST_CYCLE_DAY  # warm-up days never become decision days


def daily_closes(panel, through: date, value) -> list[float]:
    """Hand-made series: the warm-up file's rows, then the panel's 2019 sessions, muhurat sessions left out."""
    warm = [float(r[value]) for r in csv.DictReader(WARMUP.read_text().splitlines()) if r["session"] != SESSION_MUHURAT]
    later = [getattr(s, "underlying" if value == "underlying" else "vix") for s in panel.sessions]
    later = [v for s, v in zip(panel.sessions, later) if date(2019, 1, 1) <= s.day <= through]
    return warm + later


@pytest.mark.parametrize("day, expiry", [(FIRST_DECISION_DAY, date(2019, 1, 31)), (FIRST_CYCLE_DAY, date(2019, 2, 28))])
def test_f2_equals_the_hand_calculation_from_the_raw_closes(year_2019, features, day, expiry):
    closes = daily_closes(year_2019.panel, day, "vix")
    expected = closes[-1] > median(closes[-251:-1])  # today against the previous 250 valid closes
    assert features[1].value(year_2019, day, DecisionContext(expiry, day, day)) is expected


def test_f1_on_2_jan_2019_exists_and_its_realised_part_equals_the_hand_calculation(year_2019, features):
    day, expiry = FIRST_DECISION_DAY, date(2019, 1, 31)  # both ATM legs traded that day
    closes = daily_closes(year_2019.panel, day, "underlying")[-21:]
    returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
    realised = math.sqrt(sum(r * r for r in returns) / 20 * 252) * 100
    implied = features[0].atm_implied_vol_points(year_2019, day, expiry, closes[-1])
    value = features[0].value(year_2019, day, DecisionContext(expiry, day, day))
    assert implied is not None and value == pytest.approx(implied - realised, abs=1e-9)


def test_f1_on_the_first_cycle_day_is_none_only_because_its_atm_put_did_not_trade(year_2019, features):
    day, expiry = FIRST_CYCLE_DAY, date(2019, 2, 28)
    quotes = year_2019.panel.options_on(day, expiry)
    put = next(
        q
        for q in quotes
        if q.strike == atm_strike(quotes, year_2019.panel.session_on(day).underlying) and q.kind == "PE"
    )
    assert put.volume == 0  # NSE: the 10750 put of 28 Feb 2019 had no trade on 14 Jan 2019
    assert features[0].value(year_2019, day, DecisionContext(expiry, day, day)) is None
    assert realised_vol_points(daily_closes(year_2019.panel, day, "underlying"), 20) is not None  # history is there
