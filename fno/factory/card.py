"""The idea card's machine block (story R1): one fenced ```factory YAML block beside the card's human tables.

`read_card` checks the G0 fields; the G1-G3 inputs are read by their own gate when it runs (`inputs.py`), so a card
lacking them is refused there, by name. A card without exactly one valid block is refused before anything is
written.

Result-derived G1-G3 inputs may live in a sidecar beside the card (`<id>.inputs.md`, one ```factory-inputs block),
so a card frozen before its study ran stays byte for byte as frozen (EDGE2, judge 642 S1). The sidecar may hold only
those inputs, and never a field the card already has."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .constants import CARD_FENCE, CARD_INPUTS_SUFFIX
from .fields import CardError, Fields

_BLOCK = re.compile(rf"^```{CARD_FENCE}\n(.*?)^```$", re.MULTILINE | re.DOTALL)
_INPUTS_BLOCK = re.compile(rf"^```{CARD_FENCE}-inputs\n(.*?)^```$", re.MULTILINE | re.DOTALL)
G0_FIELDS = ("id", "experiment", "description", "question", "hypothesis", "measurement", "version", "trial")
SCREEN_FIELDS = ("gross", "tail", "cost")  # G1
SPEND_FIELDS = ("data_sets", "measures")  # G2
PLAN_FIELDS = ("sd_per_trade", "frequency_per_year", "pass_level")  # G3
REGISTRATION_FIELDS = ("playbook_name", "playbook_version", "minimum_useful_net")  # G4
FIELDS = (*G0_FIELDS, *SCREEN_FIELDS, *SPEND_FIELDS, *PLAN_FIELDS, *REGISTRATION_FIELDS)


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
    inputs: Fields | None = field(default=None, compare=False, repr=False)  # the block, for the G1-G3 readers


def read_card(root: Path, relative_path: str) -> IdeaCard:
    path = Path(root) / relative_path
    if not path.is_file():
        raise CardError(f"{relative_path}: no such card")
    block = _with_sidecar(_block(path.read_text(encoding="utf-8"), relative_path), path, relative_path)
    card = IdeaCard(
        idea_id=block.text("id"),
        version=block.count("version"),
        trial_id=str(block.count("trial")),
        experiment=block.slug("experiment"),
        description=block.text("description"),
        question=block.slug("question"),
        hypothesis=block.flag("hypothesis"),
        measurement=block.flag("measurement"),
        path=relative_path,
        inputs=block,
    )
    if card.idea_id != path.stem:
        raise CardError(f"{relative_path}: field 'id' is {card.idea_id!r}, the file name says {path.stem!r}")
    return card


def sidecar_path(relative_path: str) -> str:
    """Where a card's result-derived inputs live, whether or not the file exists."""
    path = Path(relative_path)
    return str(path.with_name(path.stem + CARD_INPUTS_SUFFIX))


def _with_sidecar(block: Fields, path: Path, where: str) -> Fields:
    sidecar = path.with_name(path.stem + CARD_INPUTS_SUFFIX)
    if not sidecar.is_file():
        return block
    found = _block(sidecar.read_text(encoding="utf-8"), f"{where} sidecar", _INPUTS_BLOCK)
    found.only((*SCREEN_FIELDS, *PLAN_FIELDS))
    repeated = sorted(set(found.values) & set(block.values))
    if repeated:
        raise CardError(f"{where}: field '{repeated[0]}' is in both the card and its sidecar")
    return Fields({**block.values, **found.values}, where).only(FIELDS)


def _block(text: str, where: str, pattern: re.Pattern = _BLOCK) -> Fields:
    blocks = pattern.findall(text)
    if len(blocks) != 1:
        raise CardError(f"{where}: needs exactly one ```{CARD_FENCE} block, found {len(blocks)}")
    try:
        values = yaml.safe_load(blocks[0])
    except yaml.YAMLError as bad:
        raise CardError(f"{where}: the ```{CARD_FENCE} block is not valid YAML ({bad})") from bad
    if not isinstance(values, dict):
        raise CardError(f"{where}: the ```{CARD_FENCE} block must be a mapping of fields")
    return Fields(values, where).only(FIELDS)
