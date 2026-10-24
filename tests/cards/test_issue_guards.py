"""Story T1f, criteria 3-5: after the post every stage of the issue is guarded on its own, so a posted card always
leaves its records or says plainly why not: a clock check that raises is unchecked by type, facts that cannot be
built become the minimal facts (still valid for the next card and for the dashboard's card), a Drive record that
cannot be built is a named miss, and a metadata write that raises anything prints the metadata to commit by hand."""

import json
from dataclasses import replace
from datetime import date, datetime

import pytest

from fno.cards import wiring
from fno.cards.card_clocks import CardClocks, ServerCardClocks
from fno.cards.deliveries import RepoDeliveryFiles, misses
from fno.cards.issue import CardIssuer
from fno.cards.posting import CardPoster, PostReceipt
from fno.cards.record_store import CardRecordStore, NoCardRecords
from fno.server_clock import ServerClock
from tests.cards.fakes import FakeRecords, Ticking, daily_card
from tests.cards.test_cli import run
from tests.market_read_models.test_p1_t1_card import CONTRACT, card_from_delivery

DAY = date(2026, 10, 15)
TS = "1792049889.000100"


class Sent(CardPoster):
    def __init__(self, receipt=None):
        self.receipt, self.posts = receipt or PostReceipt("alert sent to #fno-desk", TS, "C0C89E8QCCD"), []

    def post(self, text):
        self.posts.append(text)
        return self.receipt


class Saved(CardRecordStore):
    def __init__(self):
        self.saved = []

    def save(self, day, name, data):
        self.saved.append((name, json.loads(data)))
        return True, f"card record saved to Drive: {name}"


class Raising(ServerClock):
    name, resolution_seconds = "GitHub", 1.0

    def __init__(self, error):
        self.error = error

    def now(self):
        raise self.error


class RaisingLog(RepoDeliveryFiles):
    def __init__(self, root, records, error):
        super().__init__(root, records)
        self.error = error

    def write(self, day, metadata):
        raise self.error


def issued(tmp_path, servers=(), poster=None, store=None, log=None, card_change=None):
    records = FakeRecords()
    card, text = daily_card(records, tmp_path).prepare(DAY)
    card = card_change(card) if card_change else card
    poster, store, host = poster or Sent(), store or Saved(), Ticking()
    log = log or RepoDeliveryFiles(tmp_path, records)
    result = CardIssuer(poster, store, log, ServerCardClocks(servers, host), host, "c" * 40).issue(card, text)
    return result, poster, store, records


def delivery_file(tmp_path):
    (path,) = (tmp_path / "research" / "cards" / "deliveries" / "2026").glob("*.json")
    return path


@pytest.mark.parametrize("error", [OSError("down"), ValueError("bad date"), RuntimeError("refused")])
def test_a_clock_that_raises_anything_is_unchecked_by_type_and_the_records_are_still_written(tmp_path, error):
    result, poster, store, _ = issued(tmp_path, servers=(Raising(error),))
    stored = json.loads(delivery_file(tmp_path).read_text())
    github = [c for c in stored["clock"] if c["server"] == "GitHub"]
    assert github == [{"server": "GitHub", "checked": False, "skew_seconds": None, "warning": False,
                       "line": f"clock NOT CHECKED: host vs GitHub ({type(error).__name__})"}]  # fmt: skip
    assert (
        len(poster.posts) == 1 and store.saved and result.sent and not result.complete
    )  # a raise is a failure: exit 1


@pytest.mark.parametrize("error", [TypeError("not JSON"), PermissionError("read-only")])
def test_a_metadata_write_that_raises_anything_prints_the_metadata_and_fails(tmp_path, error):
    records = FakeRecords()
    result, _, store, _ = issued(tmp_path, log=RaisingLog(tmp_path, records, error))
    name = type(error).__name__
    assert result.lines[-1].startswith(f"delivery metadata NOT written ({name}); commit it by hand:")
    printed = json.loads(result.lines[-1].split("by hand:\n", 1)[1])
    assert printed["slack"]["ts"] == TS and printed["drive"]["saved"] and store.saved and not result.complete


def test_facts_that_cannot_be_built_leave_the_minimal_facts_in_both_records(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise KeyError("no such field")

    monkeypatch.setattr(CardIssuer, "_facts", broken)
    result, poster, store, records = issued(tmp_path)
    delivery = json.loads(delivery_file(tmp_path).read_text())
    ((_, record),) = store.saved
    assert delivery["failure"] == record["failure"] == "facts not built (KeyError)"
    assert delivery["slack"] == {"sent": True, "ts": TS, "channel": "C0C89E8QCCD", "outcome": "alert sent to #fno-desk",
                                 "server_time_utc": "2026-10-15T07:38:09.000100+00:00"}  # fmt: skip
    assert [c["server"] for c in delivery["clock"]] == ["Slack"]  # the checks already made are kept
    assert delivery["drive"]["saved"] and not result.complete and len(poster.posts) == 1
    CONTRACT.validate("FnoCardResponse", card_from_delivery(delivery))  # the dashboard can still show the day
    committed = FakeRecords(
        {delivery_file(tmp_path).relative_to(tmp_path).as_posix(): delivery_file(tmp_path).read_bytes()}
    )
    # the next card reads it without error, and names the kept Slack check's WARNING (the fake ts is 2 h off the host)
    assert misses(RepoDeliveryFiles(tmp_path, committed), DAY) == (
        "the 2026-10-15 card's clock check gave a WARNING (Slack)",
    )


def test_a_slack_time_that_cannot_be_read_is_a_failed_check_and_minimal_facts(tmp_path):
    result, _, _, _ = issued(tmp_path, poster=Sent(PostReceipt("alert sent to #fno-desk", "not-seconds", "C1")))
    delivery = json.loads(delivery_file(tmp_path).read_text())
    assert delivery["failure"] == "facts not built (ValueError)" and delivery["slack"]["server_time_utc"] is None
    assert delivery["clock"][0]["line"] == "clock NOT CHECKED: host vs Slack (ValueError)" and not result.complete


class BrokenClocks(CardClocks):
    def check(self, receipt, before, after):
        raise RuntimeError("a broken clock form")


def test_a_clock_form_that_raises_is_one_named_miss_and_the_records_are_still_written(tmp_path):
    records = FakeRecords()
    card, text = daily_card(records, tmp_path).prepare(DAY)
    store = Saved()
    result = CardIssuer(Sent(), store, RepoDeliveryFiles(tmp_path, records), BrokenClocks(), Ticking(), "c" * 40).issue(
        card, text
    )
    stored = json.loads(delivery_file(tmp_path).read_text())
    assert [c["line"] for c in stored["clock"]] == ["clock NOT CHECKED: host vs the clocks (RuntimeError)"]
    assert store.saved and not result.complete


class BrokenSection:
    title = "status"


def test_a_drive_record_that_cannot_be_built_is_a_named_miss_and_the_metadata_still_written(tmp_path):
    result, _, store, _ = issued(tmp_path, card_change=lambda card: replace(card, sections=(BrokenSection(),)))
    assert result.lines[-2] == "card record NOT saved to Drive: record not built (AttributeError)"
    delivery = json.loads(delivery_file(tmp_path).read_text())
    assert not delivery["drive"]["saved"] and not store.saved and not result.complete


def test_a_metadata_that_is_not_json_prints_the_minimal_facts_and_leaves_no_empty_file(tmp_path):
    """Self-review: the printed fallback stays readable by the next card and the dashboard (the minimal facts plus
    `drive`), and the real write, which fails on JSON, leaves no empty attempt file behind."""
    receipt = PostReceipt("alert sent to #fno-desk", TS, object())  # a channel that is not text: no JSON anywhere
    result, _, _, _ = issued(tmp_path, poster=Sent(receipt))
    assert result.lines[-1].startswith("delivery metadata NOT written (TypeError); commit it by hand:")
    assert result.lines[-2].endswith("record not built (TypeError)") and not result.complete
    printed = json.loads(result.lines[-1].split("by hand:\n", 1)[1])
    assert printed["failure"] == "metadata not JSON (TypeError)" and printed["slack"]["channel"] is None
    assert printed["slack"]["ts"] == TS and printed["drive"] == {"saved": False, "outcome": result.lines[-2]}
    CONTRACT.validate("FnoCardResponse", card_from_delivery(printed))
    assert list((tmp_path / "research" / "cards" / "deliveries").rglob("*.json")) == []  # no empty attempt


def test_a_slack_time_out_of_range_never_escapes(tmp_path):
    """Self-review: "1e20" passes Slack's answer check but overflows a date; it is a failed check, never a raise."""
    result, _, _, _ = issued(tmp_path, poster=Sent(PostReceipt("alert sent to #fno-desk", "1e20", "C1")))
    delivery = json.loads(delivery_file(tmp_path).read_text())
    assert delivery["slack"]["server_time_utc"] is None and delivery["failure"] == "facts not built (OverflowError)"
    assert not result.complete


def test_boundaries_no_server_an_unsent_post_and_no_drive(tmp_path):
    result, _, _, _ = issued(tmp_path, poster=Sent(PostReceipt("alert NOT sent: x")), store=NoCardRecords())
    delivery = json.loads(delivery_file(tmp_path).read_text())
    assert delivery["clock"] == [{"server": "Slack", "checked": False, "skew_seconds": None, "warning": False,
                                  "line": "clock NOT CHECKED: host vs Slack (not posted)"}]  # fmt: skip
    assert "failure" not in delivery and not result.sent and not result.complete  # T1's rule: not sent, not saved


def test_the_cli_prints_the_delivery_line_last_when_a_clock_raises(tmp_path, monkeypatch):
    from fno import models
    from fno.desk import wiring as desk_wiring

    monkeypatch.setattr(models, "now_ist", lambda: datetime(2026, 10, 15, 15, 8, tzinfo=models.IST))
    monkeypatch.setattr(desk_wiring, "download_private_records", lambda day=None: None)
    records = FakeRecords()
    host = Ticking()
    issuer = CardIssuer(Sent(), Saved(), RepoDeliveryFiles(tmp_path, records),
                        ServerCardClocks((Raising(RuntimeError("refused")),), host), host, "c" * 40)  # fmt: skip
    monkeypatch.setattr(wiring, "build_card_issuer", lambda: issuer)
    code, printed = run(DAY, post=True)
    assert code == 1 and printed.splitlines()[-1].startswith("delivery metadata written: research/cards/deliveries/")
