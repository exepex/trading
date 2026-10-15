"""One day's card, before it is issued (story T1): the session calendar decides whether there is a card, the previous
session's delivery decides what the card must say went wrong, and the builder and renderer make it."""

from __future__ import annotations

from datetime import date

from .card import CardBuilder, TradeCard
from .deliveries import DeliveryLog, misses
from .render import CardRenderer
from .session import SessionCheck


class DailyCard:
    def __init__(self, sessions: SessionCheck, builder: CardBuilder, renderer: CardRenderer, deliveries: DeliveryLog):
        self.sessions, self.builder, self.renderer, self.deliveries = sessions, builder, renderer, deliveries

    def prepare(self, day: date) -> tuple[TradeCard, str] | None:
        """The card and its text, or None on a day that is not an NSE session."""
        answer = self.sessions.answer(day)
        if not answer.is_session:
            return None
        previous = misses(self.deliveries, answer.previous) if answer.previous else ()
        card = self.builder.build(day, answer, previous)
        return card, self.renderer.render(card)
