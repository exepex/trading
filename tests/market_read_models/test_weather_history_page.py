"""Story P2a (screen W3a): the `weather_history` page (contract 2.8.0), every session's colour and label from M1's
records, re-counted here straight from the record files. Colour and label only (owner, 16 Oct 2026; judge 217)."""

import json
from collections import Counter
from datetime import date

from fno.market_read_models.blocks import SessionRows
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.weather_history_block import FnoWeatherHistoryBlock
from fno.market_read_models.wiring import build_pinned_contract, build_weather_inputs
from fno.weather.wiring import WEATHER_FOLDER

REAL_DAY = date(2026, 10, 14)


def history(day: date) -> dict:
    rows = SessionRows(day, [], [], [], [], weather=build_weather_inputs().on(day))
    builder = PublicationBuilder([FnoWeatherHistoryBlock()], build_pinned_contract(), "c" * 40)
    return builder.build(rows).records["weather_history"]["payload"]


def test_every_committed_record_up_to_the_day_is_a_row_oldest_first_and_the_counts_are_the_files_own():
    page = history(REAL_DAY)
    files = [json.loads(f.read_text()) for f in sorted(WEATHER_FOLDER.glob("*/*.json"))]
    files = [r for r in files if r["day"] <= REAL_DAY.isoformat()]
    assert [s["session"] for s in page["sessions"]] == [r["day"] for r in files]
    colours, labels = Counter(r["colour"] for r in files), Counter(r["label"] for r in files)
    assert page["counts"] == {"green": colours["GREEN"], "amber": colours["AMBER"], "red": colours["RED"],
                              "not_scored": colours["not scored"], "live": labels["live"],
                              "backfill": labels["backfill_exploratory"]}  # fmt: skip
    assert page["counts"]["backfill"] == len(files) == 2409 and page["counts"]["live"] == 0


def test_a_row_carries_only_its_session_colour_and_label():
    page = history(REAL_DAY)
    assert {tuple(sorted(row)) for row in page["sessions"]} == {("colour", "label", "session")}
    text = json.dumps(page)
    assert not any(word in text for word in ("reaches", "us_move", "p_big", "base_rate", "probabilit", "value"))


def test_a_day_before_the_first_record_publishes_the_empty_history():
    page = history(date(2017, 1, 2))
    assert page == {"sessions": [], "counts": dict.fromkeys(("green", "amber", "red", "not_scored", "live",
                                                              "backfill"), 0)}  # fmt: skip
