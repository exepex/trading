"""Story T1: issuing the card (criteria 6, 7, 9, 11, 13): Slack's ts as issuance time, Drive-only card records,
non-sensitive delivery metadata, failures printed and named on the next card, the clock check."""

import json
from datetime import date, timedelta

import requests

from fno.cards.deliveries import RepoDeliveryFiles
from fno.cards.issue import CardIssuer
from fno.cards.posting import NoCardPoster, SlackCardPoster
from fno.cards.record_store import DriveCardRecords, NoCardRecords
from fno.constants import FNO_DESK_CHANNEL_ID
from fno.models import IST
from tests.cards.fakes import HOST, TOKEN, FakeDrive, FakeRecords, FakeSlack, FixedClock, Ticking, daily_card, slack_ok

DAY = date(2026, 10, 15)


def issue(tmp_path, poster, store, clocks=(), files=None, test=False):
    records = FakeRecords(files)
    card, text = daily_card(records, tmp_path).prepare(DAY)
    issuer = CardIssuer(poster, store, RepoDeliveryFiles(tmp_path, records), clocks, Ticking(), "c" * 40)
    return card, text, issuer.issue(card, text, test=test)


def written(tmp_path, attempt=1):
    path = tmp_path / "research" / "cards" / "deliveries" / "2026" / f"2026-10-15-a{attempt}.json"
    return path, json.loads(path.read_text())


def test_a_posted_card_stores_slacks_ts_as_issuance_time_and_its_full_record_in_drive_only(tmp_path):
    slack, drive = FakeSlack(slack_ok()), FakeDrive()
    card, text, result = issue(tmp_path, SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack), DriveCardRecords(drive))
    assert result.sent and result.saved and result.lines[0] == "alert sent to #fno-desk"
    assert slack.calls[0]["json"] == {"channel": FNO_DESK_CHANNEL_ID, "text": text}
    ((drive_path, data),) = drive.files.items()
    assert drive_path == f"2026/10/2026-10-15_{slack_ok()['ts'].replace('.', '')}.json"
    record = json.loads(data)
    assert record["text"] == text and record["slack"]["ts"] == slack_ok()["ts"]
    assert record["slack"]["server_time_utc"] == HOST.isoformat()  # stored in UTC with its offset
    path, delivery = written(tmp_path)
    assert delivery["slack"] == record["slack"] and delivery["card_sha256"] == record["card_sha256"]
    assert delivery["records_used"] == [{"path": r.path, "sha256": r.sha256} for r in card.used]
    assert delivery["host_clock"]["before_utc"].endswith("+00:00")
    assert delivery["drive"] == {"saved": True, "outcome": f"card record saved to Drive: {drive_path}"}


def test_the_repository_metadata_holds_no_card_text_and_no_secret(tmp_path):
    _, text, _ = issue(
        tmp_path, SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, FakeSlack(slack_ok())), DriveCardRecords(FakeDrive())
    )
    path, delivery = written(tmp_path)
    stored = path.read_text()
    body = [line for line in text.splitlines() if line.strip() and not line.startswith("  research/")]
    assert "text" not in delivery and "sections" not in delivery
    assert not [line for line in body if line in stored and len(line) > 20]
    assert TOKEN not in stored


def test_slack_down_is_retried_once_printed_stored_and_still_saved_to_drive(tmp_path):
    slack, drive = FakeSlack({"ok": False, "error": "ratelimited"}), FakeDrive()
    poster = SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack, sleep=lambda s: None)
    _, _, result = issue(tmp_path, poster, DriveCardRecords(drive))
    assert len(slack.calls) == 2 and not result.sent
    assert result.lines[0] == "alert NOT sent: ratelimited after 2 attempts"
    assert result.lines[1] == "clock NOT CHECKED: host vs Slack (not posted)"
    _, delivery = written(tmp_path)
    assert delivery["slack"]["sent"] is False and delivery["slack"]["ts"] is None
    ((name, data),) = drive.files.items()
    assert "unsent-" in name and json.loads(data)["slack"]["sent"] is False


def test_a_connect_timeout_then_success_posts_once_more(tmp_path):
    slack = FakeSlack(requests.ConnectTimeout("never connected"), slack_ok())
    poster = SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack, sleep=lambda s: None)
    _, _, result = issue(tmp_path, poster, NoCardRecords())
    assert result.sent and len(slack.calls) == 2


def test_no_token_and_no_drive_print_what_was_not_done_and_never_a_secret(tmp_path):
    _, _, result = issue(tmp_path, NoCardPoster(), NoCardRecords())
    assert result.lines[0] == "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"
    assert "card record NOT saved to Drive: the owner's Drive settings (FNO_GDRIVE_*) are not set" in result.lines
    assert not result.sent and not result.saved
    _, delivery = written(tmp_path)
    assert delivery["drive"]["saved"] is False


def test_drive_down_does_not_stop_the_post_and_is_named_by_error_type_only(tmp_path):
    drive = FakeDrive(requests.ConnectionError("https://oauth2.example/token?refresh=secret"))
    _, _, result = issue(
        tmp_path, SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, FakeSlack(slack_ok())), DriveCardRecords(drive)
    )
    assert result.sent and not result.saved
    assert "card record NOT saved to Drive: ConnectionError" in result.lines
    assert "secret" not in "\n".join(result.lines) and "secret" not in written(tmp_path)[0].read_text()


def test_the_next_card_names_the_previous_sessions_misses(tmp_path):
    issue(tmp_path, NoCardPoster(), NoCardRecords())
    path, _ = written(tmp_path)
    committed = FakeRecords()
    committed.files[path.relative_to(tmp_path).as_posix()] = path.read_bytes()
    _, text = daily_card(committed, tmp_path).prepare(date(2026, 10, 16))
    assert "Previous card: the 2026-10-15 card was NOT sent (alert NOT sent: FNO_SLACK_BOT_TOKEN is not set)" in text
    assert "Previous card: the 2026-10-15 card record was NOT saved to Drive" in text
    _, text = daily_card(FakeRecords(), tmp_path).prepare(date(2026, 10, 16))
    assert "Previous card: no card on record for 2026-10-15" in text  # an uncommitted delivery is not counted


def test_attempts_are_never_overwritten(tmp_path):
    issue(tmp_path, NoCardPoster(), NoCardRecords())
    first = written(tmp_path)[0].read_bytes()
    issue(tmp_path, NoCardPoster(), NoCardRecords())
    assert written(tmp_path)[0].read_bytes() == first and written(tmp_path, attempt=2)[0].is_file()


def test_a_server_clock_off_by_more_than_five_seconds_is_a_warning_printed_and_stored(tmp_path):
    clocks = [FixedClock("GitHub", HOST + timedelta(seconds=10)), FixedClock("Other", None)]
    _, _, result = issue(
        tmp_path, SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, FakeSlack(slack_ok())), NoCardRecords(), clocks
    )
    assert "clock: host vs Slack within 0.0 s" in result.lines
    assert any(line.startswith("clock WARNING: host vs GitHub off by 10.0 s") for line in result.lines)
    assert "clock NOT CHECKED: host vs Other (ConnectionError)" in result.lines
    _, delivery = written(tmp_path)
    assert [c["warning"] for c in delivery["clock"]] == [False, True, False]
    assert delivery["clock"][2]["line"] == "clock NOT CHECKED: host vs Other (ConnectionError)"
    assert [c["checked"] for c in delivery["clock"]] == [True, True, False]  # a named failure, never a bare null
    committed = FakeRecords()
    committed.files["research/cards/deliveries/2026/2026-10-15-a1.json"] = written(tmp_path)[0].read_bytes()
    _, next_text = daily_card(committed, tmp_path).prepare(date(2026, 10, 16))
    assert "Previous card: the 2026-10-15 card's clock NOT CHECKED: host vs Other (ConnectionError)" in next_text


def test_slack_ts_far_from_the_host_clock_is_a_warning(tmp_path):
    slack = FakeSlack(slack_ok(HOST - timedelta(seconds=30)))
    _, _, result = issue(tmp_path, SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack), NoCardRecords())
    assert result.lines[1].startswith("clock WARNING: host vs Slack off by 30.0 s")


def test_a_test_post_is_marked_on_its_first_line_and_records_and_never_counts_as_the_card(tmp_path):
    slack, drive = FakeSlack(slack_ok()), FakeDrive()
    _, text, result = issue(
        tmp_path, SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack), DriveCardRecords(drive), test=True
    )
    posted = slack.calls[0]["json"]["text"]
    assert posted.startswith("TEST — PAPER ONLY:") and posted.endswith(text) and result.sent
    ((name, data),) = drive.files.items()
    assert name.endswith("_test.json") and json.loads(data)["test"] is True
    path, delivery = written(tmp_path)
    assert delivery["test"] is True and delivery["slack"]["ts"] == slack_ok()["ts"]
    committed = FakeRecords()
    committed.files[path.relative_to(tmp_path).as_posix()] = path.read_bytes()
    _, next_text = daily_card(committed, tmp_path).prepare(date(2026, 10, 16))
    assert "Previous card: no card on record for 2026-10-15" in next_text


def test_times_are_stored_in_utc_even_when_the_host_clock_is_in_ist(tmp_path):
    records = FakeRecords()
    card, text = daily_card(records, tmp_path).prepare(DAY)
    host = Ticking(HOST.astimezone(IST))
    issuer = CardIssuer(NoCardPoster(), NoCardRecords(), RepoDeliveryFiles(tmp_path, records), (), host, "c" * 40)
    issuer.issue(card, text)
    _, delivery = written(tmp_path)
    assert delivery["host_clock"]["before_utc"].startswith("2026-10-15T09:38:00")
    assert delivery["host_clock"]["before_utc"].endswith("+00:00")


def test_a_failure_that_may_have_posted_or_is_a_refusal_is_never_retried(tmp_path):
    cases = (
        (
            requests.ReadTimeout("lost answer"),
            f"ReadTimeout; Slack may still have posted it (check channel {FNO_DESK_CHANNEL_ID}); not retried",
        ),
        (
            requests.ConnectionError("dropped after sending"),
            f"ConnectionError; Slack may still have posted it (check channel {FNO_DESK_CHANNEL_ID}); not retried",
        ),
        ({"ok": False, "error": "channel_not_found"}, "channel_not_found"),
    )
    for answer, reason in cases:
        slack = FakeSlack(answer)
        receipt = SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack, sleep=lambda s: None).post("card")
        assert len(slack.calls) == 1 and not receipt.sent and receipt.outcome == f"alert NOT sent: {reason}"


def test_an_accepted_post_without_a_readable_ts_is_said_and_not_posted_again():
    for body in ({"ok": True}, {"ok": True, "ts": "not-a-number"}):
        slack = FakeSlack(body)
        receipt = SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack, sleep=lambda s: None).post("card")
        assert len(slack.calls) == 1 and receipt.ts is None
        assert "accepted the post but gave no readable ts" in receipt.outcome


def test_a_non_dict_slack_answer_never_raises(tmp_path):
    for body in ([], "html", None):
        slack = FakeSlack(body)
        receipt = SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack, sleep=lambda s: None).post("card")
        assert receipt.outcome.startswith("alert NOT sent: unexpected answer") and len(slack.calls) == 1


class FailingLog(RepoDeliveryFiles):
    def write(self, day, metadata):
        raise OSError("disk full")


def test_a_failed_metadata_write_keeps_every_line_and_prints_the_metadata(tmp_path):
    records = FakeRecords()
    card, text = daily_card(records, tmp_path).prepare(DAY)
    poster = SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, FakeSlack(slack_ok()))
    issuer = CardIssuer(poster, NoCardRecords(), FailingLog(tmp_path, records), (), Ticking(), "c" * 40)
    result = issuer.issue(card, text)
    assert result.lines[0] == "alert sent to #fno-desk" and not result.saved
    assert result.lines[-1].startswith("delivery metadata NOT written (OSError); commit it by hand:")
    assert slack_ok()["ts"] in result.lines[-1] and text not in result.lines[-1]


def test_attempt_numbers_count_committed_attempts_from_another_checkout(tmp_path):
    committed = FakeRecords()
    committed.files["research/cards/deliveries/2026/2026-10-15-a1.json"] = b"{}"
    path = RepoDeliveryFiles(tmp_path, committed).write(DAY, {"x": 1})
    assert path.endswith("2026-10-15-a2.json")


def test_a_corrupt_earlier_delivery_record_is_named_and_never_stops_the_card(tmp_path):
    for bad in (b"{not json", b'{"slack": {"sent": true}}', b"[]"):
        committed = FakeRecords()
        committed.files["research/cards/deliveries/2026/2026-10-15-a1.json"] = bad
        prepared = daily_card(committed, tmp_path).prepare(date(2026, 10, 16))
        assert prepared is not None
        assert "Previous card: the 2026-10-15 card's delivery record could not be read (" in prepared[1]


def test_the_next_card_names_an_unchecked_github_clock_even_without_any_warning(tmp_path):
    """Judge 101 SF4: the routine's GitHub clock is often not checked; the next card must say so."""
    _, _, result = issue(
        tmp_path, SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, FakeSlack(slack_ok())), NoCardRecords(),
        [FixedClock("GitHub", None)],
    )  # fmt: skip
    path, delivery = written(tmp_path)
    assert [c["warning"] for c in delivery["clock"]] == [False, False]  # no WARNING anywhere: only "not checked"
    committed = FakeRecords()
    committed.files[path.relative_to(tmp_path).as_posix()] = path.read_bytes()
    _, next_text = daily_card(committed, tmp_path).prepare(date(2026, 10, 16))
    assert "Previous card: the 2026-10-15 card's clock NOT CHECKED: host vs GitHub (ConnectionError)" in next_text


def test_the_next_card_names_a_clock_warning(tmp_path):
    """Judge A addendum: the WARNING line in misses() had no test of its own (its mutation survived)."""
    issue(tmp_path, SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, FakeSlack(slack_ok())), NoCardRecords(),
          [FixedClock("GitHub", HOST + timedelta(seconds=10))])  # fmt: skip
    path, _ = written(tmp_path)
    committed = FakeRecords()
    committed.files[path.relative_to(tmp_path).as_posix()] = path.read_bytes()
    _, next_text = daily_card(committed, tmp_path).prepare(date(2026, 10, 16))
    assert "Previous card: the 2026-10-15 card's clock check gave a WARNING (GitHub)" in next_text


def test_a_connection_error_is_never_retried_even_when_a_retry_would_succeed():
    """Judge A addendum: with a success queued behind it, a retry would post; it must not (may have posted already)."""
    slack = FakeSlack(requests.ConnectionError("dropped after sending"), slack_ok())
    receipt = SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack, sleep=lambda s: None).post("card")
    assert len(slack.calls) == 1 and not receipt.sent
    assert (
        receipt.outcome
        == f"alert NOT sent: ConnectionError; Slack may still have posted it (check channel {FNO_DESK_CHANNEL_ID}); "
        "not retried"
    )


def test_a_may_have_posted_failure_names_the_poster_s_own_channel_not_fno_desk():
    """Orchestrator, 21 Oct: the same poster sends to another channel (FL1's #fno-forecast); its warning must say where
    to look, never #fno-desk."""
    other = "C0OTHERCHAN"
    receipt = SlackCardPoster(TOKEN, other, FakeSlack(requests.ReadTimeout("lost")), sleep=lambda s: None).post("x")
    assert f"check channel {other}" in receipt.outcome and "fno-desk" not in receipt.outcome
