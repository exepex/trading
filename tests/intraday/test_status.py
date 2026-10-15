"""Story A16 criteria 5 and 8: a snapshot's status, at and around every limit (120 s on time, 120 s source age,
5 s source ahead of the host), and the clock notes."""

from datetime import timedelta

import pytest

from fno.intraday.document import CallRecord, SnapshotDocument
from fno.intraday.status import (
    CHAIN_EMPTY,
    CONTRACTS_MISSING,
    INDEX_FAILED,
    INDEX_LATE,
    INDEX_REPEATED,
    INDEX_TIME_MISSING,
    INDEX_TIME_OLD,
    SOURCE_AHEAD_OF_HOST,
    SlotVerdict,
    index_check,
    verdict,
)
from tests.intraday.fakes import DAY, ist

MARK = ist(DAY, 10, 0)


def doc(sent=0.0, received=1.0, age=1.0, level=25000.0, contracts=(4, 4), failure="", chains=2):
    """A snapshot sent `sent` s after the mark, answered at `received` s, the source's time `age` s before that."""
    answered = MARK + timedelta(seconds=received)
    index = CallRecord("index", MARK + timedelta(seconds=sent), answered, {"last_price": level}, failure)
    quotes = [CallRecord("q", answered, answered, {}, "") for _ in range(contracts[1])]
    source_time = None if age is None else answered - timedelta(seconds=age)
    chain = [
        CallRecord(f"chain {n}", answered, answered, {}, "", {"contracts": contracts[0] // 2}) for n in range(chains)
    ]
    return SnapshotDocument("groww", "NIFTY", DAY, MARK, index, level, source_time, None, chain, quotes, {},
                            contracts[0])  # fmt: skip


@pytest.mark.parametrize(
    "kwargs, problem",
    [
        ({}, ""),
        ({"received": 120.0}, ""),  # answered exactly 120 s after the mark: on time
        ({"received": 120.001}, INDEX_LATE),
        ({"sent": -0.001}, INDEX_LATE),  # sent before the mark
        ({"age": 120.0}, ""),  # source time exactly 120 s old: fresh
        ({"age": 120.001}, INDEX_TIME_OLD),
        ({"age": None}, INDEX_TIME_MISSING),
        ({"level": None}, INDEX_FAILED),
        ({"level": 0.0}, INDEX_FAILED),
        ({"level": -1.0}, INDEX_FAILED),
        ({"failure": "GrowwAPIException"}, INDEX_FAILED),
    ],
)
def test_index_check_at_each_limit(kwargs, problem):
    check = index_check(doc(**kwargs), previous_level=24990.0)
    assert check.problem == problem and (check.level is None) == bool(problem)


def test_a_level_equal_to_the_previous_marks_is_stale_and_a_one_paisa_change_is_not():
    assert index_check(doc(level=25000.0), 25000.0).problem == INDEX_REPEATED
    assert index_check(doc(level=25000.01), 25000.0).problem == ""
    assert index_check(doc(level=25000.0), None).problem == ""  # 09:15, or the previous mark has no level


@pytest.mark.parametrize(
    "kwargs, status",
    [
        ({}, "good"),
        ({"contracts": (4, 3)}, "incomplete"),
        ({"contracts": (0, 0), "chains": 0}, "incomplete"),  # no chain at all: never good
        ({"contracts": (0, 0)}, "incomplete"),  # no contract in the band: an empty chain is never good
        ({"age": 121.0, "contracts": (4, 3)}, "stale"),  # the index decides first
        ({"received": 121.0}, "late"),
        ({"failure": "GrowwAPIException"}, "failed"),
    ],
)
def test_the_slot_status(kwargs, status):
    assert verdict(doc(**kwargs), 1.0).status == status


def test_the_named_reasons_are_kept():
    found = verdict(doc(contracts=(4, 3)), 1.0)
    assert found.failures == (CONTRACTS_MISSING,)


@pytest.mark.parametrize("ahead, noted", [(5.0, False), (5.001, True)])
def test_a_source_time_ahead_of_our_receive_time_is_noted_beyond_5_seconds(ahead, noted):
    found = verdict(doc(age=-ahead), 1.0)
    assert (SOURCE_AHEAD_OF_HOST in found.failures) == noted and found.status == "good"


def test_one_empty_chain_is_never_hidden_by_the_other():
    found = doc()
    found.chains[1].meta["contracts"] = 0
    assert verdict(found, 1.0) == SlotVerdict("incomplete", (CHAIN_EMPTY,))


def test_a_single_or_failed_chain_is_incomplete():
    assert verdict(doc(chains=1), 1.0).status == "incomplete"
    failed = doc()
    failed.chains[0].failure = "GrowwAPIException"
    assert CHAIN_EMPTY in verdict(failed, 1.0).failures


def test_failed_contract_quotes_are_counted_not_listed_and_notes_never_change_the_status():
    found = doc(contracts=(4, 2))
    found.failures = ["quote NIFTY26101925000CE", "quote NIFTY26101925050CE", "chain_parse 2026-10-27: ValueError"]
    assert verdict(found, 1.0).failures == (CONTRACTS_MISSING, "chain_parse 2026-10-27: ValueError", "quotes_failed:2")
    noted = doc()
    noted.notes = ["prepare sign_in: RuntimeError"]
    assert verdict(noted, 1.0) == SlotVerdict("good", ("prepare sign_in: RuntimeError",))
