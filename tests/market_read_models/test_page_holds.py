"""Story P11, the per-page hold: a held page is the previous publication's row byte for byte (or no row), every other
page publishes, one alert line and the run status name the rule, a held copy that no longer matches the pin gets no
row, and `page_holds` names each held page from its first held session (criteria 1-7, 9 and 10)."""

import json
from dataclasses import replace
from datetime import date

from fno.market_read_models.blocks import BlockBuilder
from fno.market_read_models.page_holds import PageHeld, PageHoldsBlock, page_holds_payload
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.run_status import LocalRunStatus
from fno.market_read_models.weather_block import FnoWeatherBlock
from fno.market_read_models.wiring import build_market_blocks

from .test_market_contract_and_run import CONTRACT, Rows, example_rows, run

RULE = "A planted rule broke in this test"
ROW = ("as_of", "cutoff", "built_at", "source_commit", "payload_sha256", "payload", "market", "product")


class HeldWeather(FnoWeatherBlock):
    def build(self, rows):
        raise PageHeld(RULE)


class FreePageHolds(PageHoldsBlock):
    served_schema = None  # FnoPageHolds is not pinned yet: its shape is tested here, its schema once pinned


def builder(clock: str, hold: bool = False, holds_page: BlockBuilder | None = None) -> PublicationBuilder:
    blocks = [HeldWeather() if hold and isinstance(b, FnoWeatherBlock) else b for b in build_market_blocks()]
    return PublicationBuilder(blocks, CONTRACT, "c" * 40, clock=lambda: clock, holds_page=holds_page)


def publish(tmp_path, clock, hold=False, holds_page=None):
    """A publish of the session the clock names (12 Oct or a later session), from the same example rows."""
    day = date.fromisoformat(clock[:10])
    rows = replace(example_rows(), day=day)
    market, alerts, publisher = run(tmp_path, Rows(rows), builder(clock, hold, holds_page))
    code, lines = market.run(day)
    return code, lines, alerts, publisher.current()


def test_a_held_page_is_its_previous_row_byte_for_byte_and_every_other_page_publishes(tmp_path):
    _, _, _, before = publish(tmp_path, "2026-10-12T12:30:00Z")
    code, lines, alerts, after = publish(tmp_path, "2026-10-13T12:30:00Z", hold=True)
    assert code == 0 and set(after) == set(before)  # read back passed, every page there
    assert {k: after["weather"][k] for k in ROW} == {k: before["weather"][k] for k in ROW}
    assert after["weather"]["publication_id"] != before["weather"]["publication_id"]
    assert after["session"]["built_at"] == "2026-10-13T12:30:00Z"  # every other page is built anew
    assert alerts.sent == [f"2026-10-13: weather held back: {RULE}"]
    status = LocalRunStatus(tmp_path, "fno").rows()[-1]
    assert (status["result"], status["reason_code"], status["reason"]) == ("published", None, alerts.sent[0])


def test_with_no_earlier_page_the_held_page_is_absent_and_the_rest_publish(tmp_path):
    code, _, alerts, after = publish(tmp_path, "2026-10-13T12:30:00Z", hold=True)
    assert code == 0 and "weather" not in after and "session" in after and len(alerts.sent) == 1


def test_a_second_run_of_the_day_with_the_same_hold_adds_nothing(tmp_path):
    publish(tmp_path, "2026-10-12T12:30:00Z")
    _, first, _, after = publish(tmp_path, "2026-10-13T12:30:00Z", hold=True)
    _, second, _, again = publish(tmp_path, "2026-10-13T12:30:00Z", hold=True)
    assert after["weather"]["publication_id"] == again["weather"]["publication_id"]
    assert second[0].endswith("(0 rows added)")


def test_a_held_copy_that_no_longer_matches_the_pin_gets_no_row_and_the_line_says_why(tmp_path):
    publish(tmp_path, "2026-10-12T12:30:00Z")
    pointer = json.loads((tmp_path / "current.json").read_text())["publication_id"]
    stored = tmp_path / "publications" / pointer / "weather.json"
    row = json.loads(stored.read_text())
    stored.write_text(json.dumps(row | {"payload": row["payload"] | {"planted_field": 1}}))  # an older contract's shape
    code, _, alerts, after = publish(tmp_path, "2026-10-13T12:30:00Z", hold=True)
    assert code == 0 and "weather" not in after and "session" in after
    assert alerts.sent == [f"2026-10-13: weather held back: {RULE}; its previous page no longer matches contract "
                           f"{CONTRACT.version}, so it is not published"]  # fmt: skip


def test_page_holds_names_each_held_page_from_its_first_held_session_and_is_never_held(tmp_path):
    publish(tmp_path, "2026-10-12T12:30:00Z", holds_page=FreePageHolds())
    publish(tmp_path, "2026-10-13T12:30:00Z", hold=True, holds_page=FreePageHolds())
    _, _, _, held = publish(tmp_path, "2026-10-14T12:30:00Z", hold=True, holds_page=FreePageHolds())
    assert held["page_holds"]["payload"] == {
        "holds": [{"page_key": "weather", "since": "2026-10-13", "reason": RULE, "shows": "previous_page"}]
    }
    _, _, _, lifted = publish(tmp_path, "2026-10-15T12:30:00Z", holds_page=FreePageHolds())
    assert lifted["page_holds"]["payload"] == {"holds": []}
    assert "page_holds" not in {b.page_key for b in build_market_blocks()}  # built by the publication, never a block


def test_since_resets_when_a_hold_lifts_and_returns():
    first = page_holds_payload({"weather": RULE}, set(), None, date(2026, 10, 12))
    kept = page_holds_payload({"weather": RULE}, set(), first, date(2026, 10, 13))
    lifted = page_holds_payload({}, set(), kept, date(2026, 10, 14))
    back = page_holds_payload({"weather": RULE}, set(), lifted, date(2026, 10, 15))
    assert [p["holds"][0]["since"] for p in (first, kept, back)] == ["2026-10-12", "2026-10-12", "2026-10-15"]


def test_every_hold_reason_in_the_code_is_a_fixed_sentence_with_no_digit():
    """Contract 2.13.0 refuses a digit in a reason (its probe plants "Rs 10,500"); a reason is shown on screen."""
    import re

    from fno.market_read_models import home_blocks

    holds = CONTRACT.schemas.get("FnoPageHolds")  # 2.13.0's pattern once pinned; until then the same rule
    pattern = holds and holds["properties"]["holds"]["items"]["properties"]["reason"].get("pattern")
    for reason in (home_blocks.OPEN_TRADE_RISK, home_blocks.APPROVED_PICKS, RULE):
        assert re.fullmatch(pattern or "^[^0-9]*$", reason) and "{" not in reason, reason


def test_a_held_page_with_no_row_is_listed_as_showing_nothing(tmp_path):
    _, _, _, held = publish(tmp_path, "2026-10-13T12:30:00Z", hold=True, holds_page=FreePageHolds())
    assert "weather" not in held and held["page_holds"]["payload"]["holds"][0]["shows"] == "nothing"
