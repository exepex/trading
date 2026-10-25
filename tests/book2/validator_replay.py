"""Book 2's C4 validator as a replay builds it (story F5): each stored pick's rule default and the recorded counts."""

from fno.book2.slots import terms_from_json
from fno.book2.validator import Book2TradeValidator
from fno.constants import BOOK2_HYBRID
from tests.book3.engine_builders import validator


def replay_validator(root, inputs):
    paired = {p["opportunity_id"]: terms_from_json(p["default"]) for p in inputs.selection}
    return Book2TradeValidator(validator(root, book=BOOK2_HYBRID), paired, inputs.replay_arguments()[5])
