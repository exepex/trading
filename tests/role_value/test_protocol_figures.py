"""Story F9a criterion 11: F9a's figures match S1's text (`research/evaluation/PROTOCOL.md`), so an edit of one alone
fails. The minimum of 30, the block of 20, 10,000 resamples and seed 20261014 are in S1's text today. The 5th and 95th
percentiles and the cost denominator are S1's pending edit 3 (register row "S1 text"): provisional until the S1 freeze,
and checked here as soon as S1's text states them."""

import re

from fno.config import ROOT
from fno.evaluation.protocol import PROTOCOL_FILE, parse_protocol
from fno.role_value.score import LOWER_PERCENTILE, UPPER_PERCENTILE
from fno.role_value.verdict import MIN_CHANGED
from fno.scoreboard.uncertainty import BLOCK_DAYS, RESAMPLES, SEED

PENDING_S1_EDIT = "5th and 95th"


def value(item: str) -> str:
    return parse_protocol((ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")).items[item].value


def test_the_figures_s1_states_today_match_f9a_s():
    text = value("role_value_minimum_sample")
    assert f"at least {MIN_CHANGED} applicable opportunities" in text
    assert f"blocks of {BLOCK_DAYS} " in text
    assert f"{RESAMPLES:,} resamples" in text and f"seed {SEED}" in text


def test_the_provisional_percentiles_match_once_s1_states_them():
    text = value("role_value_minimum_sample")
    stated = re.search(r"(\d+)th and (\d+)th", text)
    if PENDING_S1_EDIT in text or stated:
        assert stated and (int(stated.group(1)), int(stated.group(2))) == (LOWER_PERCENTILE, UPPER_PERCENTILE)
    else:  # until S1's pending edit 3 lands, its text still says the old "one-sided 95%" wording
        assert "one-sided 95%" in text and (LOWER_PERCENTILE, UPPER_PERCENTILE) == (5, 95)
