"""T1's card in a rehearsal starts with the label (story REH1), chosen by `build_card_poster`."""

from __future__ import annotations

import os
from collections.abc import Mapping

from ..cards.posting import CardPoster
from .mode import labelled, rehearsal


class LabelledCardPoster(CardPoster):
    def __init__(self, inner: CardPoster, label: str):
        self.inner, self.label = inner, label

    def post(self, text: str):
        return self.inner.post(labelled(self.label, text))


def rehearsed_card_poster(poster: CardPoster, env: Mapping[str, str] = os.environ) -> CardPoster:
    mode = rehearsal(env)
    return poster if mode is None else LabelledCardPoster(poster, mode.label)
