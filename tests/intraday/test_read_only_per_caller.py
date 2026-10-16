"""ReadOnlyGroww with one allow-list per caller (A14c part 2, agreed with A16's builder on 16 Oct 2026): the recorder
keeps its default list; any caller's list refuses every other name at getattr; and no list may hold an order call,
which the constructor refuses by name."""

import pytest

from fno.intraday.read_only import ALLOWED, ReadOnlyGroww, ReadOnlyViolation
from tests.intraday.test_read_only_and_fallback import sdk_names

ORDER_CALLS = ("place_order", "modify_order", "cancel_order", "create_smart_order", "modify_smart_order",
               "cancel_smart_order")  # fmt: skip
MARGIN_ONLY = frozenset({"get_order_margin_details", "SEGMENT_FNO"})


class Sdk:
    def __getattr__(self, name):
        return name  # every name exists on the fake: only the wrapper can refuse


def test_a_caller_s_list_lets_only_its_names_through():
    client = ReadOnlyGroww(Sdk, MARGIN_ONLY)
    assert client.get_order_margin_details == "get_order_margin_details" and client.SEGMENT_FNO == "SEGMENT_FNO"
    for name in (*ORDER_CALLS, "get_quote", "get_positions_for_user", "get_available_margin_details"):
        with pytest.raises(ReadOnlyViolation, match=f"{name} is not a read call this client may use"):
            getattr(client, name)


@pytest.mark.parametrize("order_call", ORDER_CALLS)
def test_no_list_may_hold_an_order_call(order_call):
    with pytest.raises(ReadOnlyViolation, match=f"only public reads and constants, not: {order_call}"):
        ReadOnlyGroww(Sdk, MARGIN_ONLY | {order_call})


@pytest.mark.parametrize(
    "name", ["session", "_request", "get_access_token", "generate_socket_token", "Place_order", "exit_position",
             "get_session_info", "__class__", "get_Quote"],
)  # fmt: skip
def test_judge_356_s_names_are_refused_by_the_positive_rule(name):
    """Only `get_<lower_snake>` reads and UPPER_CASE constants pass; private, token, session and other names do not."""
    with pytest.raises(ReadOnlyViolation, match=f"only public reads and constants, not: {name}"):
        ReadOnlyGroww(Sdk, MARGIN_ONLY | {name})


def test_every_name_of_the_real_sdk_class_is_sorted_by_the_rule():
    """dir() of growwapi.GrowwAPI, private names included (A16's 1.5.0 list when the SDK is absent): each name either
    passes as a read or constant or is refused, and no order, private or token name passes."""
    try:
        from growwapi import GrowwAPI

        names = set(dir(GrowwAPI))
    except ImportError:
        names = set(sdk_names()) | {"_request_post", "_build_headers", "__init__"}
    passed = set()
    for name in names:
        try:
            ReadOnlyGroww(Sdk, frozenset({name}))
            passed.add(name)
        except ReadOnlyViolation:
            pass
    assert passed and all(n.startswith("get_") or n.isupper() for n in passed)
    assert not passed & set(ORDER_CALLS) and not any(n.startswith("_") or "token" in n for n in passed)


def test_the_recorder_keeps_its_list_by_default():
    client = ReadOnlyGroww(Sdk)
    assert all(getattr(client, name) == name for name in ALLOWED)
    with pytest.raises(ReadOnlyViolation):
        getattr(client, "get_order_margin_details")  # noqa: B009 - the access itself is what is tested


def test_no_sdk_order_call_ever_passes():
    """The SDK's public names (the installed one, else A16's 1.5.0 list): every order call is refused."""
    refused = set()
    for name in sdk_names():
        try:
            ReadOnlyGroww(Sdk, frozenset({name}))
        except ReadOnlyViolation:
            refused.add(name)
    assert set(ORDER_CALLS) <= refused
