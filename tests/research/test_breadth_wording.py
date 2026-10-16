"""Response 230 (ChatGPT review 133): every BR1 chart, table and export carries the exploratory disclaimer, the BR1
text names dependence as the leading supported explanation, and no family is ever marked PASS or "beats baseline"."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DISCLAIMER = (
    "Exploratory estimate; interval is descriptive and its coverage is not validated for these dependent market days. "
    "Not evidence of forecast skill, trading profit or real-money eligibility."
)
EXPLANATION = "dependence is the leading supported explanation, with skew and tails contributing"
TABLES = (
    "research/breadth/README.md",
    "research/breadth/PROTOCOL.md",
    "research/breadth/studies/results/DIAGNOSTICS.md",
    "reviews/claude/response_198_br1-test-candidates.md",
)
TEXTS = (*sorted(str(p.relative_to(ROOT)) for p in (ROOT / "research/breadth").rglob("*.md")), TABLES[-1])


def flat(path: str) -> str:
    return " ".join((ROOT / path).read_text(encoding="utf-8").split()).replace("> ", "")


@pytest.mark.parametrize("path", TABLES)
def test_every_br1_table_carries_the_disclaimer(path):
    assert DISCLAIMER in flat(path)


@pytest.mark.parametrize("path", TABLES[:3])
def test_the_br1_text_names_dependence_as_the_leading_explanation(path):
    assert EXPLANATION in flat(path)


@pytest.mark.parametrize("path", TEXTS)
def test_no_family_is_marked_pass_or_beats_baseline(path):
    text = flat(path)
    assert not re.search(r"\bPASS\b", text) and "beats baseline" not in text
