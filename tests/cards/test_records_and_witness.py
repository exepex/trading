"""Story T1: the card reads committed bytes only (criterion 5, on a real git repository), the issuance witnesses
(criterion 6) and the composition root's choices (criteria 11-13)."""

import subprocess
from datetime import UTC, date, datetime, timedelta

import pytest

from fno.ai.receipts import PushReceipts, ReceiptAccessDenied, ReceiptUnknown
from fno.cards import wiring
from fno.cards.committed import GitHeadRecords
from fno.cards.deliveries import RepoDeliveryFiles
from fno.cards.posting import NoCardPoster, SlackCardPoster
from fno.cards.record_store import DriveCardRecords, NoCardRecords
from fno.cards.witness import IssuanceWitness
from fno.constants import ENV_FNO_SLACK_BOT_TOKEN
from fno.server_clock import HttpDateClock, ServerTimeUnknown, check_server, skew_check
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS
from tests.cards.fakes import TOKEN, FakeDrive, FakeRecords

DELIVERY = "research/cards/deliveries/2026/2026-10-15-a1.json"
SENT = b'{"slack": {"sent": true, "ts": "1760521080.000100", "server_time_utc": "2026-10-15T09:38:00.000100+00:00"}}'


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def test_an_edited_or_untracked_working_tree_file_is_never_read(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.csv").write_bytes(b"committed\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "x")
    (tmp_path / "a" / "x.csv").write_bytes(b"edited\n")
    (tmp_path / "a" / "z.csv").write_bytes(b"staged only\n")
    git(tmp_path, "add", "a/z.csv")  # staged, not committed: the index must never reach a card (judge 101 SF3)
    (tmp_path / "a" / "y.csv").write_bytes(b"untracked\n")
    records = GitHeadRecords(tmp_path)
    assert records.read("a/x.csv") == b"committed\n"
    assert records.read("a/y.csv") is None and records.names("a") == ["x.csv"]
    assert records.read("a/z.csv") is None
    (tmp_path / "a" / "x.csv").write_bytes(b"staged edit\n")
    git(tmp_path, "add", "a/x.csv")
    assert records.read("a/x.csv") == b"committed\n"
    assert records.names("missing") == [] and len(records.code_commit()) == 40


class History:
    def __init__(self, commit):
        self.commit = commit

    def first_commit_adding(self, path):
        return self.commit


class Receipts(PushReceipts):
    def __init__(self, at=None, error=None):
        self.at, self.error = at, error

    def received_at(self, commit):
        if self.error is not None:
            raise self.error
        if self.at is None:
            raise ReceiptUnknown(f"no push of {commit[:10]} in GitHub's activity log of main")
        return self.at


def test_the_witness_prints_slacks_time_beside_githubs_push_receipt(tmp_path):
    log = RepoDeliveryFiles(tmp_path, FakeRecords({DELIVERY: SENT}))
    pushed = datetime(2026, 10, 15, 9, 39, 30, tzinfo=UTC)
    (line,) = IssuanceWitness(log, History("d" * 40), Receipts(pushed)).lines(date(2026, 10, 15))
    assert line == (
        f"{DELIVERY}: Slack 2026-10-15 15:08:00 IST (ts 1760521080.000100); "
        "GitHub push receipt 2026-10-15 15:09:30 IST (commit dddddddddd)"
    )
    (line,) = IssuanceWitness(log, History(None), Receipts(pushed)).lines(date(2026, 10, 15))
    assert line.endswith("GitHub push receipt none yet (the delivery file is not committed)")
    (line,) = IssuanceWitness(log, History("d" * 40), Receipts()).lines(date(2026, 10, 15))
    assert line.endswith("none yet (no push of dddddddddd in GitHub's activity log of main)")
    refused = Receipts(error=ReceiptAccessDenied("access refused: HTTP 403 from GitHub's activity log"))
    (line,) = IssuanceWitness(log, History("d" * 40), refused).lines(date(2026, 10, 15))
    assert line.endswith(
        "GitHub push receipt NOT READABLE: access refused: HTTP 403 from GitHub's activity log "
        "(an access problem, not a missing receipt)"
    )
    assert IssuanceWitness(log, History(None), Receipts()).lines(date(2026, 10, 16)) == [
        "no committed card delivery for 2026-10-16"
    ]


def test_the_composition_root_sends_only_with_the_token_and_saves_only_with_the_owners_drive(monkeypatch):
    assert isinstance(wiring.build_card_poster({}), NoCardPoster)
    assert isinstance(wiring.build_card_poster({ENV_FNO_SLACK_BOT_TOKEN: TOKEN}), SlackCardPoster)
    store = wiring.build_card_records({})
    assert isinstance(store, NoCardRecords) and "FNO_GDRIVE_" in store.reason
    full = {name: "x" for name in OWNER_UPLOAD_SETTINGS}
    monkeypatch.setattr(wiring.storage, "build_owner_drive", lambda env: FakeDrive())
    assert isinstance(wiring.build_card_records(full), DriveCardRecords)

    def refused(env):
        raise RuntimeError("refresh token secret-value rejected")

    monkeypatch.setattr(wiring.storage, "build_owner_drive", refused)
    store = wiring.build_card_records(full)
    assert store.reason == "Drive sign-in failed (RuntimeError)" and "secret" not in store.reason


def test_the_witness_never_crashes_on_a_record_without_slack_facts(tmp_path):
    log = RepoDeliveryFiles(tmp_path, FakeRecords({DELIVERY: b"{}"}))
    (line,) = IssuanceWitness(log, History(None), Receipts()).lines(date(2026, 10, 15))
    assert "Slack not posted (no Slack outcome recorded)" in line


class Answer:
    def __init__(self, date_header, status=200):
        self.headers = {"Date": date_header} if date_header else {}
        self.status_code = status


def test_githubs_date_header_is_read_as_utc_and_a_missing_one_is_unknown():
    clock = HttpDateClock(
        "GitHub", "https://example.invalid", head=lambda url, timeout: Answer("Thu, 15 Oct 2026 09:38:00 -0000")
    )
    assert clock.now() == datetime(2026, 10, 15, 9, 38, tzinfo=UTC)
    proxy_answer = HttpDateClock("GitHub", "https://example.invalid", head=lambda url, timeout: Answer(None, 400))
    with pytest.raises(ServerTimeUnknown, match=r"^HTTP 400 from GitHub, no Date header"):
        proxy_answer.now()  # what the cloud proxy gave on the live test post (root path, HTTP 400, no headers)
    no_date = HttpDateClock("GitHub", "https://example.invalid", head=lambda url, timeout: Answer(None, 200))
    with pytest.raises(ServerTimeUnknown, match=r"^HTTP 200 from GitHub with no Date header$"):
        no_date.now()


def test_an_error_answer_carrying_a_date_is_never_trusted_as_githubs_time():
    """Judge 101 SF1: a proxy's 403 with its own current Date must not read as "within skew"."""
    for status in (403, 400, 500):
        clock = HttpDateClock(
            "GitHub",
            "https://example.invalid",
            head=lambda url, timeout, s=status: Answer("Thu, 15 Oct 2026 09:38:00 GMT", s),
        )
        with pytest.raises(
            ServerTimeUnknown, match=f"^HTTP {status} from GitHub, a Date header: an error answer's time"
        ):
            clock.now()
        check = check_server(clock, lambda: datetime(2026, 10, 15, 9, 38, tzinfo=UTC))
        assert check.skew_seconds is None and check.stored()["checked"] is False
    redirect = HttpDateClock(
        "GitHub", "https://example.invalid", head=lambda url, timeout: Answer("Thu, 15 Oct 2026 09:38:00 GMT", 301)
    )
    assert redirect.now() == datetime(2026, 10, 15, 9, 38, tzinfo=UTC)


@pytest.mark.parametrize(
    ("offset", "resolution", "warning"),
    [
        (-5.0, 0.0, False), (-5.1, 0.0, True), (5.0, 0.0, False), (5.1, 0.0, True),  # early and late, exact clock
        (-6.0, 1.0, False), (-6.1, 1.0, True), (6.0, 1.0, False), (6.1, 1.0, True),  # with GitHub's 1 s resolution
    ],
)  # fmt: skip
def test_the_five_second_boundary_on_both_sides(offset, resolution, warning):
    """Judge 101 SF2: at 5.0 s beyond the host's window (after resolution) no WARNING; at 5.1 s a WARNING."""
    before = datetime(2026, 10, 15, 9, 38, tzinfo=UTC)
    after = before + timedelta(seconds=0.5)
    server = (before if offset < 0 else after) + timedelta(seconds=offset)
    check = skew_check("GitHub", server, before, after, resolution)
    assert check.warning is warning and check.line.startswith("clock WARNING" if warning else "clock: host vs GitHub")


def test_githubs_clock_is_asked_on_the_repository_path(monkeypatch):
    issuer = wiring.build_card_issuer({})
    (github,) = issuer.clocks.servers
    assert github.url == "https://api.github.com/repos/exepex/trading"
    issuer = wiring.build_card_issuer({"GITHUB_REPOSITORY": "someone/fork"})
    assert issuer.clocks.servers[0].url == "https://api.github.com/repos/someone/fork"
