"""The rung rule's card is frozen by its hash and the code's numbers are the card's (REC1a; the freeze in place of a
D6 row or a ledger trial, which do not fit a rule that decides nothing)."""

import hashlib
import re
from pathlib import Path

from fno.recommend import rungs

ROOT = Path(__file__).resolve().parents[2]
VALUE_ROW = re.compile(r"^\| (\w+) \| (\d+) \|$", re.MULTILINE)


def card() -> bytes:
    return (ROOT / rungs.RUNG_RULE_PATH).read_bytes()


def test_the_pinned_hash_is_the_card_s():
    assert hashlib.sha256(card()).hexdigest() == rungs.RUNG_RULE_SHA256


def test_the_code_s_numbers_are_the_card_s_values():
    values = {name: int(value) for name, value in VALUE_ROW.findall(card().decode("utf-8"))}
    assert values == {
        "watching_sessions": rungs.WATCHING_SESSIONS,
        "calibration_min_outcomes": rungs.CALIBRATION_MIN_OUTCOMES,
        "calibration_min_sessions": rungs.CALIBRATION_MIN_SESSIONS,
        "calibration_bins": rungs.CALIBRATION_BINS,
        "day_condition_step": rungs.DAY_CONDITION_STEP,
    }
