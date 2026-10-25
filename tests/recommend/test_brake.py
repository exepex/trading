"""REC1c's first item (orchestrator's ruling on judge 654.1's open point): a version under its own drawdown brake or
daily stop is never eligible for real money; `decide` and the record's own contract both refuse it, and the line
names the brake."""

import json

import pytest

from fno.recommend.codec import decode, encode
from fno.recommend.constants import EvidenceRung, NoTradeReason, RealMoneyAnswer
from fno.recommend.contracts import RecordRefused
from fno.recommend.post import recommendation_line
from fno.recommend.store import Saved
from tests.recommend.builders import established_day
from tests.recommend.test_decide import V, decided

ELIGIBLE = RealMoneyAnswer.ELIGIBLE_FOR_YOUR_OWN_REVIEW


def test_a_braked_rung_3_rm1_eligible_version_is_do_not_trade():
    record = decided(EvidenceRung.ESTABLISHED, rm1_eligible={V}, braked={V})
    assert (record.real_money, record.eligible_version, record.braked_versions) == (
        RealMoneyAnswer.DO_NOT_TRADE_REAL_MONEY,
        None,
        (V,),
    )
    assert record.reason is NoTradeReason.BRAKE


def test_the_same_version_unbraked_is_eligible():
    assert decided(EvidenceRung.ESTABLISHED, rm1_eligible={V}).eligible_version == V


def test_the_contract_refuses_a_braked_eligible_version():
    with pytest.raises(RecordRefused, match="real-money"):
        established_day(braked_versions=("school:CS1@1",), real_money=ELIGIBLE, eligible_version="school:CS1@1")


def test_the_line_names_the_brake():
    line = recommendation_line(established_day(braked_versions=("school:CS1@1",)), Saved("p.json", "ab" * 32, "e" * 40))
    assert "Real money: DO NOT TRADE (under its own drawdown brake or daily stop: school:CS1@1)." in line


def test_braked_versions_are_sorted_unique_and_required():
    with pytest.raises(RecordRefused, match="braked versions"):
        established_day(braked_versions=("school:DB1@1", "school:CS1@1"))
    data = json.loads(encode(established_day()))
    del data["braked_versions"]
    with pytest.raises(RecordRefused, match="lacks braked_versions"):
        decode(json.dumps(data, sort_keys=True, separators=(",", ":")).encode())
