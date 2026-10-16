"""The G1-G3 inputs (story R1b, judge 261): required when their gate runs, refused by name, never defaulted."""

import re

import pytest

from fno.factory.card import read_card
from fno.factory.fields import CardError
from fno.factory.inputs import plan_inputs, screen_inputs, spend_inputs

from .helpers import BLOCK, write_card

MEASURED = """gross: {kind: measured, mean: 978, sd: 2667, n: 33, source: response 92}
tail: {probability: 0.0, loss: 0, in_gross: yes}
cost: {measured: 824, source: response 92}
"""


def card(tmp_path, extra):
    return read_card(tmp_path, write_card(tmp_path, BLOCK + extra))


def test_a_full_screen_input_reads(tmp_path):
    inputs = screen_inputs(card(tmp_path, MEASURED), {})
    assert (inputs.gross.mean, inputs.gross.n, inputs.cost.rupees(), inputs.tail.in_gross) == (978, 33, 824, True)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("gross: {kind: measured, mean: 978, sd: 2667, n: 33, source: response 92}\n", "", "'gross' is missing"),
        ("cost: {measured: 824, source: response 92}\n", "", "'cost' is missing"),
        ("tail: {probability: 0.0, loss: 0, in_gross: yes}\n", "", "'tail' is missing"),
        ("sd: 2667, ", "", "'gross.sd' is missing"),
        ("n: 33", "n: 1", "'gross.n' must be at least 2"),
        ("kind: measured", "kind: hunch", "'gross.kind' must be one of"),
        ("in_gross: yes", "in_gross: maybe", "'tail.in_gross' must be yes or no"),
        ("probability: 0.0", "probability: 1.5", "'tail.probability' must be a probability"),
        ("{measured: 824, source: response 92}", "{source: response 92}", "'cost.measured' or 'legs' must be given"),
        ("source: response 92}\ntail", "pad: 2}\ntail", "unknown field 'gross.pad'"),
    ],
)
def test_a_missing_or_bad_screen_input_is_named(tmp_path, old, new, message):
    with pytest.raises(CardError, match=message):
        screen_inputs(card(tmp_path, MEASURED.replace(old, new)), {})


def test_no_stated_edge_needs_no_cost_or_tail(tmp_path):
    inputs = screen_inputs(card(tmp_path, "gross: {kind: none, source: studies disagree}\n"), {})
    assert inputs.cost is None and inputs.tail is None


@pytest.mark.parametrize(
    ("leg", "message"),
    [("{side: sell, units: 65, entry: 120, exit: 40, settlement: 0, pad: 1, pad_source: A4}", "'cost.legs[0].exit' or"),
     ("{side: short, units: 65, entry: 120, exit: 40, pad: 1, pad_source: A4}", "'cost.legs[0].side' must be one of"),
     ("{side: sell, units: 65, entry: 120, exit: 40, pad: 1}", "'cost.legs[0].pad_source' is missing")],
)  # fmt: skip
def test_a_bad_leg_is_named(tmp_path, leg, message):
    extra = MEASURED.replace("{measured: 824, source: response 92}", f"{{legs: [{leg}]}}")
    with pytest.raises(CardError, match=re.escape(message)):
        screen_inputs(card(tmp_path, extra), {})


def test_spend_and_plan_inputs_are_named_when_missing(tmp_path):
    bare = card(tmp_path, "")
    with pytest.raises(CardError, match="'data_sets' is missing"):
        spend_inputs(bare)
    with pytest.raises(CardError, match="'sd_per_trade' is missing"):
        plan_inputs(bare)
    with pytest.raises(CardError, match="one-sided level between 0 and 0.5"):
        plan_inputs(card(tmp_path, "sd_per_trade: 3000\nfrequency_per_year: 12\npass_level: 0.5\n"))
