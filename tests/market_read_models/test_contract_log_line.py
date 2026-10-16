"""Story P2, privacy rule 3 (criterion 3 of every F&O page): a validation failure names the field path and the rule it
breaks, never the failing value, because the message reaches the public Actions log."""

import pytest

from fno.market_read_models.contract import ContractBroken
from tests.market_read_models.test_p1_data_catalog import payload_of, validated

PLANTED = 987654.321


def test_a_value_out_of_range_is_named_by_path_and_rule_without_the_value():
    value = payload_of("getFnoWeather_india_red")
    value["payload"]["p_big_1d"] = PLANTED  # the schema's maximum is 1
    with pytest.raises(ContractBroken) as broken:
        validated("getFnoWeather", value)
    message = str(broken.value)
    assert "payload/p_big_1d: breaks 'maximum'" in message
    assert str(PLANTED) not in message and "987654" not in message


def test_a_wrong_enum_value_is_named_by_path_and_rule_without_the_value():
    value = payload_of("getFnoWeather_india_red")
    value["payload"]["colour"] = "PURPLE-PLANTED"
    with pytest.raises(ContractBroken) as broken:
        validated("getFnoWeather", value)
    assert "payload/colour: breaks" in str(broken.value) and "PLANTED" not in str(broken.value)
