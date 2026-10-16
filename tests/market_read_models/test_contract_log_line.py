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


def test_no_fno_screen_schema_is_a_map_so_no_data_key_can_reach_a_logged_path():
    """A map's keys are data and would appear in a violation's path; the F&O screens' schemas have none (judge 218)."""
    from fno.market_read_models.wiring import build_pinned_contract

    def maps(node, where):
        if isinstance(node, dict):
            if "patternProperties" in node or isinstance(node.get("additionalProperties"), dict):
                yield where
            for key, child in node.items():
                yield from maps(child, f"{where}/{key}")
        elif isinstance(node, list):
            for i, child in enumerate(node):
                yield from maps(child, f"{where}/{i}")

    schemas = build_pinned_contract().schemas
    fno = {name: schema for name, schema in schemas.items() if name.startswith("Fno")}
    # FnoPicks' baskets are keyed by basket id, but FnoPicksBlock refuses to build while any strategy is approved
    # and publishes {} otherwise (P10), so no key exists to reach a path; a picks builder must revisit this
    known = {"FnoPicks/properties/baskets"}
    assert fno and [m for name, schema in fno.items() for m in maps(schema, name)] == sorted(known)


def test_the_picks_page_publishes_no_basket_key():
    from fno.market_read_models.home_blocks import FnoPicksBlock
    from tests.market_read_models.test_market_contract_and_run import example_rows

    assert FnoPicksBlock().build(example_rows())["baskets"] == {}
