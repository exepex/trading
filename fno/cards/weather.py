"""The card's weather section (story T1 v1). The weather model (story M1) is not built and response 94's v0 rule lives
only in a research study, so v1 says the weather is not scored. It never shows a colour it did not score."""

from __future__ import annotations

from datetime import date

from .sections import CardSection, WeatherSource

NOT_SCORED = "Weather: not yet scored (M1 pending)"
WHY = "No weather model is built yet; the card shows no colour until M1 scores one."


class PendingWeather(WeatherSource):
    def weather(self, day: date) -> CardSection:
        return CardSection("weather", (NOT_SCORED, WHY), missing=("weather model (story M1) not built",))
