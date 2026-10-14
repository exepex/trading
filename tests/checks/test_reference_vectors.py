"""Story C4: the independent maximum loss equals twelve hand computations to Rs 0.01 (their arithmetic is in
`reference_vectors.md`, the numbers in `reference_vectors.json`)."""

import json
from pathlib import Path

import pytest

from fno.checks.validity_money import ProposedLeg, max_loss

VECTORS = json.loads((Path(__file__).parent / "reference_vectors.json").read_text(encoding="utf-8"))


def test_there_are_at_least_ten_vectors_across_the_three_structures():
    titles = " ".join(v["title"] for v in VECTORS)
    assert len(VECTORS) >= 10 and all(name in titles for name in ("Short iron fly", "Short condor", "Long iron fly"))


@pytest.mark.parametrize("vector", VECTORS, ids=lambda v: v["id"])
def test_the_independent_max_loss_equals_the_hand_computation(vector):
    legs = [ProposedLeg(leg["strike"], leg["kind"], leg["side"], leg["price"]) for leg in vector["legs"]]
    assert abs(max_loss(legs, vector["units"], vector["charges"]).total - vector["expected_rs"]) < 0.01
