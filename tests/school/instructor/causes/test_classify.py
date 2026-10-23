"""Part c's classifier end to end on a model-priced put spread (story MS-INS, criteria 6 and 9)."""

from fno.school.instructor.adapters import NotYetReplayable
from fno.school.instructor.attribution.attribute import attribute
from fno.school.instructor.causes.classify import Classifier
from fno.school.instructor.causes.evidence import Controls
from fno.school.instructor.contracts import Cause, Modifier
from fno.school.instructor.wiring import rules_sha256
from tests.school.instructor.builders import RULES
from tests.school.instructor.causes.paths import EXIT_DAY, spread_path
from tests.school.instructor.causes.test_evidence import builder


def test_a_losing_spread_is_classified_with_its_rules_and_closing_day():
    held = spread_path()
    found = Classifier(builder(), RULES).classify(held, attribute(held, 0.0, RULES), Controls(-1.0, -2.0))
    assert found.net < 0 and found.closed_on == EXIT_DAY and found.rules_sha256 == RULES
    assert found.modifier == Modifier.HARD_ROAD and found.corrects == ""
    assert Cause.EXIT_WHIPSAW in found.not_testable  # its expiry has not settled


def test_a_later_classification_names_the_one_it_replaces():
    held = spread_path()
    found = Classifier(builder(), RULES).classify(held, attribute(held, 0.0, RULES), None, corrects="ab" * 32)
    assert found.corrects == "ab" * 32 and found.modifier == Modifier.NOT_TESTABLE


def test_until_j_lands_cause_13_is_not_testable_and_the_rules_card_has_a_hash():
    held = spread_path()
    found = Classifier(builder(replay=NotYetReplayable()), RULES).classify(held, attribute(held, 0.0, RULES), None)
    assert Cause.RULE_BROKEN in found.not_testable and len(rules_sha256()) == 64
