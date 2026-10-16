"""The idea card's machine block (story R1, G0): one fenced ```factory YAML block beside the card's human tables.

A card without exactly one valid block is refused with the field named, before anything is written."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from .constants import CARD_FENCE

_BLOCK = re.compile(rf"^```{CARD_FENCE}\n(.*?)^```$", re.MULTILINE | re.DOTALL)
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_TEXT_FIELDS = ("id", "experiment", "description", "question")
_FLAG_FIELDS = ("hypothesis", "measurement")
_COUNT_FIELDS = ("version", "trial")
FIELDS = (*_TEXT_FIELDS, *_FLAG_FIELDS, *_COUNT_FIELDS)  # R1a: G0 only; R1b adds the G1-G3 inputs


class CardError(ValueError):
    """The card cannot be registered; the message names the card and the field."""


@dataclass(frozen=True)
class IdeaCard:
    idea_id: str
    version: int
    trial_id: str
    experiment: str
    description: str
    question: str
    hypothesis: bool
    measurement: bool
    path: str  # the card's path relative to the repository root


def read_card(root: Path, relative_path: str) -> IdeaCard:
    path = Path(root) / relative_path
    if not path.is_file():
        raise CardError(f"{relative_path}: no such card")
    block = _block(path.read_text(encoding="utf-8"), relative_path)
    card = IdeaCard(
        idea_id=_text(block, "id", relative_path),
        version=_count(block, "version", relative_path),
        trial_id=str(_count(block, "trial", relative_path)),
        experiment=_slug(block, "experiment", relative_path),
        description=_text(block, "description", relative_path),
        question=_slug(block, "question", relative_path),
        hypothesis=_flag(block, "hypothesis", relative_path),
        measurement=_flag(block, "measurement", relative_path),
        path=relative_path,
    )
    if card.idea_id != path.stem:
        raise CardError(f"{relative_path}: field 'id' is {card.idea_id!r}, the file name says {path.stem!r}")
    return card


def _block(text: str, where: str) -> dict:
    blocks = _BLOCK.findall(text)
    if len(blocks) != 1:
        raise CardError(f"{where}: needs exactly one ```{CARD_FENCE} block, found {len(blocks)}")
    try:
        block = yaml.safe_load(blocks[0])
    except yaml.YAMLError as bad:
        raise CardError(f"{where}: the ```{CARD_FENCE} block is not valid YAML ({bad})") from bad
    if not isinstance(block, dict):
        raise CardError(f"{where}: the ```{CARD_FENCE} block must be a mapping of fields")
    unknown = sorted(set(block) - set(FIELDS))
    if unknown:
        raise CardError(f"{where}: unknown field {unknown[0]!r}")
    return block


def _field(block: dict, name: str, where: str):
    if block.get(name) is None:
        raise CardError(f"{where}: field {name!r} is missing")
    return block[name]


def _text(block: dict, name: str, where: str) -> str:
    value = _field(block, name, where)
    if not isinstance(value, str) or not value.strip():
        raise CardError(f"{where}: field {name!r} must be non-empty text")
    return " ".join(value.split())


def _slug(block: dict, name: str, where: str) -> str:
    value = _text(block, name, where)
    if not _SLUG.match(value):
        raise CardError(f"{where}: field {name!r} must be lower-case letters, digits and hyphens")
    return value


def _flag(block: dict, name: str, where: str) -> bool:
    value = _field(block, name, where)
    if not isinstance(value, bool):
        raise CardError(f"{where}: field {name!r} must be yes or no")
    return value


def _count(block: dict, name: str, where: str) -> int:
    value = _field(block, name, where)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise CardError(f"{where}: field {name!r} must be a whole number of at least 1")
    return value
