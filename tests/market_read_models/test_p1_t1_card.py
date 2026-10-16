"""Story P1 addendum (orchestrator, 15 Oct 2026): T1's real daily card must fit the catalog's FnoCard, so the card's
engine (T1) and its screen (W3) cannot drift apart. T1 publishes a public delivery record per post
(`research/cards/deliveries/<YYYY>/<day>-<attempt>.json`, schema card_delivery/v1); the card itself stays in Drive.

- T1's first real delivery record (the TEST post to #fno-desk of 15 Oct 2026) builds a FnoCard that validates.
- Every committed delivery record validates the same way, and at least one must exist, so a moved folder fails here
  instead of passing on nothing. The folder and the 15:25 IST valid-until time come from T1's own constants.
What a delivery record does not hold (the forecast section's lines, the weather) is taken from the catalog's own empty
example, so this test checks the fields T1 publishes, not the rest."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from fno.constants import CARD_DELIVERIES_FOLDER, CARD_VALID_UNTIL
from fno.market_read_models.contract import PinnedContract
from fno.market_read_models.publication import canonical
from fno.market_read_models.wiring import CONTRACT_FOLDER
from fno.models import IST

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = PinnedContract(CONTRACT_FOLDER)
DELIVERIES = ROOT / CARD_DELIVERIES_FOLDER
FIRST_POST = DELIVERIES / "2026" / "2026-10-15-a1.json"  # T1's first real post (the TEST post of 15 Oct 2026)
DELIVERY_SCHEMA = "card_delivery/v1"
UTC_TIME = "%Y-%m-%dT%H:%M:%SZ"


def card_from_delivery(delivery: dict) -> dict:
    """The catalog's empty card with every field a delivery record holds taken from the record itself."""
    assert delivery["schema"] == DELIVERY_SCHEMA
    value = copy.deepcopy(CONTRACT.examples()["getFnoCard_india_none"]["value"])
    card, sent = value["payload"], datetime.fromisoformat(delivery["slack"]["server_time_utc"])
    valid_until = datetime.combine(datetime.fromisoformat(delivery["day"]).date(), CARD_VALID_UNTIL, tzinfo=IST)
    card |= {
        "session": delivery["day"], "status": delivery["status"], "reason": delivery["reason_code"],
        "test_post": delivery["test"], "missing": delivery["missing"], "previous_misses": delivery["previous_misses"],
        "valid_until": valid_until.astimezone(UTC).strftime(UTC_TIME),
        "footer": {"record_hashes": [{"path": r["path"], "sha256": r["sha256"]} for r in delivery["records_used"]]},
    }  # fmt: skip
    card["timing"] |= {
        "card_sent_at": sent.strftime(UTC_TIME),
        "delivery": "sent" if delivery["slack"]["sent"] else "not_sent",
    }
    value |= {"as_of": delivery["day"], "payload_sha256": hashlib.sha256(canonical(card)).hexdigest()}
    return value


def test_t1s_first_real_delivery_record_fits_the_catalogs_card():
    delivery = json.loads(FIRST_POST.read_text(encoding="utf-8"))
    value = card_from_delivery(delivery)
    CONTRACT.validate("FnoCardResponse", value)
    card = value["payload"]
    assert card["status"] == "NO TRADE" and card["reason"] == "no_approved_strategy" and card["test_post"] is True
    assert len(card["footer"]["record_hashes"]) == len(delivery["records_used"]) == 7


def test_a_delivery_record_with_a_reason_the_catalog_lacks_fails():
    delivery = json.loads(FIRST_POST.read_text(encoding="utf-8")) | {"reason_code": "new_reason"}
    with pytest.raises(Exception, match="payload/reason: breaks 'enum'") as broken:
        CONTRACT.validate("FnoCardResponse", card_from_delivery(delivery))
    assert "new_reason" not in str(broken.value)  # path and rule only, never the value (story P2, privacy rule 3)


def test_every_committed_delivery_record_fits_the_catalogs_card():
    records = sorted(DELIVERIES.rglob("*.json"))
    assert records, f"no delivery record under {CARD_DELIVERIES_FOLDER}: T1 moved its folder or stopped recording"
    for path in records:
        CONTRACT.validate("FnoCardResponse", card_from_delivery(json.loads(path.read_text(encoding="utf-8"))))
