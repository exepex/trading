"""Story P2a (screen W3a): the `weather_history` page (contract 2.10.0), every session's colour, label and chances from
M1's records, re-counted here straight from the record files. The chances are back in 2.9 (owner, 16 Oct 2026: the
levels stay public)."""

import json
from collections import Counter
from datetime import date

from fno.market_read_models.blocks import SessionRows
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.weather_history_block import FnoWeatherHistoryBlock
from fno.market_read_models.wiring import build_pinned_contract, build_weather_inputs
from fno.weather.wiring import WEATHER_FOLDER

REAL_DAY = date(2026, 10, 14)
Q1, Q5 = "v6_abs_move_2pct_next_session", "v6_abs_move_2pct_within_5_sessions"


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


def test_a_row_carries_its_colour_label_and_the_records_own_chances_and_nothing_of_the_inputs():
    page = history(REAL_DAY)
    files = {r["day"]: r for r in map(lambda f: json.loads(f.read_text()), WEATHER_FOLDER.glob("*/*.json"))}
    keys = ("base_rate_1d", "base_rate_5d", "colour", "label", "p_big_1d", "p_big_5d", "session")
    assert {tuple(sorted(row)) for row in page["sessions"]} == {keys}
    for row in page["sessions"]:
        probabilities = files[row["session"]]["probabilities"]
        for field, key, question in (("p_big_1d", "weather_vix_v1", Q1), ("p_big_5d", "weather_vix_v1", Q5),
                                     ("base_rate_1d", "base_rate", Q1), ("base_rate_5d", "base_rate", Q5)):  # fmt: skip
            entry = probabilities[key][question]
            assert row[field] == (entry["value"] if entry["status"] == "ok" else None)
    assert not any(word in json.dumps(page) for word in ("reaches", "us_move", "v0_inputs", "drivers"))


def test_a_day_before_the_first_record_publishes_the_empty_history():
    page = history(date(2017, 1, 2))
    assert page == {"sessions": [], "counts": dict.fromkeys(("green", "amber", "red", "not_scored", "live",
                                                              "backfill"), 0)}  # fmt: skip
