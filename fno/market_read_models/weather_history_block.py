"""The weather's history page (story P2a, screen W3a; contract `FnoWeatherHistory` 2.8.0, page `weather_history`): every
session's colour and label from M1's records, oldest first, and the counts by colour and label.

Colour and label only (owner, 16 Oct 2026; judge 217): no input value, no `reaches` colour, no US cue, and no chances
of a big move or usual chances, which beside about 2,400 colours would give the colour rule's floors back."""

from __future__ import annotations

from ..forecast_v4_rules.records import BACKFILL, LIVE
from ..weather.constants import WeatherColour
from .blocks import BlockBuilder, SessionRows
from .weather_parts import colour_of

COUNTED = {"green": WeatherColour.GREEN, "amber": WeatherColour.AMBER, "red": WeatherColour.RED}


class FnoWeatherHistoryBlock(BlockBuilder):
    page_key, served_schema = "weather_history", "FnoWeatherHistoryResponse"

    def build(self, rows: SessionRows) -> dict:
        return weather_history(rows.weather.history)


def weather_history(records: list[dict]) -> dict:
    sessions = [{"session": r["day"], "colour": colour_of(r), "label": r["label"]} for r in records]
    colours = [s["colour"] for s in sessions]
    labels = [s["label"] for s in sessions]
    counts = {name: colours.count(colour) for name, colour in COUNTED.items()}
    counts |= {"not_scored": colours.count(None), "live": labels.count(LIVE), "backfill": labels.count(BACKFILL)}
    return {"sessions": sessions, "counts": counts}
