"""S1 items 8 and 11 (judge 194 criterion 11; ChatGPT review 124): S1's role-value text states F9a's cost label and
denominator, and the freeze hashes every role-value module and the review dates, so an edit of the code or the text
alone fails before a freeze."""

from fno.config import ROOT
from fno.evaluation.freeze import frozen_targets
from fno.evaluation.protocol import PROTOCOL_FILE, parse_protocol
from fno.role_value.cost import COST_LABEL


def text() -> str:
    return (ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")


def test_the_cost_wording_is_f9a_s_declared_split():
    value = parse_protocol(text()).items["role_value_minimum_sample"].value
    assert COST_LABEL.startswith("conservative cost allocation") and '"conservative cost allocation"' in value
    for words in ("the same dates as the tested net", "split equally across the units consulted that day",
                  "rounded down to the paisa", "unknown, never zero", "shown apart as the operating cost"):  # fmt: skip
        assert words in value, words


def test_every_role_value_module_and_the_review_dates_are_hashed():
    modules = {f"fno/role_value/{p.name}" for p in (ROOT / "fno/role_value").glob("*.py")
               if p.name not in {"__init__.py", "cli.py"}}  # fmt: skip
    assert modules | {"fno/evaluation/review_dates.py"} <= set(frozen_targets(text()))
