"""Story T1: the card reads committed bytes only (criterion 5, on a real git repository), the issuance witnesses
(criterion 6) and the composition root's choices (criteria 11-13)."""

import subprocess
from datetime import UTC, date, datetime

from fno.ai.receipts import PushReceipts, ReceiptUnknown
from fno.cards import wiring
from fno.cards.committed import GitHeadRecords
from fno.cards.deliveries import RepoDeliveryFiles
from fno.cards.posting import NoCardPoster, SlackCardPoster
from fno.cards.record_store import DriveCardRecords, NoCardRecords
from fno.cards.witness import IssuanceWitness
from fno.constants import ENV_FNO_SLACK_BOT_TOKEN
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
    (tmp_path / "a" / "y.csv").write_bytes(b"untracked\n")
    records = GitHeadRecords(tmp_path)
    assert records.read("a/x.csv") == b"committed\n"
    assert records.read("a/y.csv") is None and records.names("a") == ["x.csv"]
    assert records.names("missing") == [] and len(records.code_commit()) == 40


class History:
    def __init__(self, commit):
        self.commit = commit

    def first_commit_adding(self, path):
        return self.commit


class Receipts(PushReceipts):
    def __init__(self, at=None):
        self.at = at

    def received_at(self, commit):
        if self.at is None:
            raise ReceiptUnknown("HTTP 401 from GitHub's activity log")
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
    assert line.endswith("GitHub push receipt unknown (not committed)")
    (line,) = IssuanceWitness(log, History("d" * 40), Receipts()).lines(date(2026, 10, 15))
    assert line.endswith("unknown (HTTP 401 from GitHub's activity log)")
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
