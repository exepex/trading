"""REC1c's evening run: the waiting days, one write-once check file per day and evening with its receipt, a #fno-desk
line only when a day becomes final, a day that cannot be read alerted without stopping the others, and nothing left
to check said in one line."""

import hashlib
from dataclasses import dataclass, field
from datetime import timedelta

from fno.recommend.check import FoundOutcome, OutcomeLookup
from fno.recommend.check_run import CheckPorts, CheckRun
from fno.recommend.codec import encode
from fno.recommend.store import record_path
from fno.recommend.write_once import WriteOnce
from fno.storage.receipt_publisher import PushedReceipt
from tests.recommend.builders import DAY, MADE_AT, candidate, evidence_of, no_trade
from tests.recommend.fakes import FakeData, RecordingAlerts

CS1 = "school:CS1@1"
SESSIONS = [DAY + timedelta(days=k) for k in range(0, 30) if (DAY + timedelta(days=k)).weekday() < 5]


@dataclass
class ReceiptingPublisher:
    """Commits a receipt file under the repository's receipts folder, as the real publisher's commit does."""

    data: FakeData
    receipts: object
    pushed: dict = field(default_factory=dict)

    def publish(self, drive_path: str, what: str) -> PushedReceipt:
        digest = hashlib.sha256(self.data.files[drive_path.removeprefix("data/")]).hexdigest()
        file = self.receipts / f"{drive_path.removeprefix('data/')}.sha256"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(digest)
        self.pushed[drive_path] = PushedReceipt("f" * 40, MADE_AT, digest)
        return self.pushed[drive_path]

    def published(self, drive_path: str):
        return self.pushed.get(drive_path)


class Outcomes(OutcomeLookup):
    def __init__(self, found):
        self.found = found

    def outcome(self, cand, session, until):
        return self.found.get(cand.version)

    def ticket(self, cand, session):
        return False


def harness(tmp_path, found=None, record=None):
    data, alerts = FakeData(), RecordingAlerts()
    publisher = ReceiptingPublisher(data, tmp_path)
    keeper = WriteOnce(data, publisher)
    if record is not None:
        keeper.keep(record_path(record.session), encode(record), lambda b: None, "planted recommendation")
    ports = CheckPorts(tmp_path, lambda path: data.files[path], lambda a, b: [d for d in SESSIONS if a <= d <= b],
                       lambda: Outcomes(found or {}))  # fmt: skip
    return CheckRun(ports, keeper, alerts, lambda: MADE_AT + timedelta(days=1)), data, alerts


def traded_day():
    return no_trade(versions=(evidence_of(CS1),), candidates=(candidate(CS1, traded=True),))


def test_nothing_recorded_says_so(tmp_path):
    run, _, alerts = harness(tmp_path)
    result = run.run(SESSIONS[3])
    assert result.ok and result.lines == (f"recommender check {SESSIONS[3]}: no recorded day waits for a check",)
    assert alerts.lines == []


def test_an_open_trade_is_checked_again_each_evening_without_a_line(tmp_path):
    run, data, alerts = harness(tmp_path, record=traded_day())
    assert run.run(SESSIONS[1]).lines == (f"recommender check {DAY}: not_known_yet, 1 position(s) still open",)
    run.run(SESSIONS[2])
    assert alerts.lines == [] and sorted(p for p in data.files if ".check." in p) == [
        f"recommend/2026/11/{DAY}.check.{SESSIONS[1]}.json",
        f"recommend/2026/11/{DAY}.check.{SESSIONS[2]}.json",
    ]


def test_a_day_that_becomes_final_gets_one_line_and_is_never_checked_again(tmp_path):
    run, data, alerts = harness(tmp_path, {CS1: FoundOutcome(-1500.0, False)}, record=traded_day())
    run.run(SESSIONS[4])
    assert len(alerts.lines) == 1 and alerts.lines[0].startswith(
        f"PAPER ONLY. Recommender check for {DAY:%d %b %Y}: complete."
    )
    assert "abstaining saved Rs 1,500.00" in alerts.lines[0]
    assert run.run(SESSIONS[5]).lines == (f"recommender check {SESSIONS[5]}: no recorded day waits for a check",)


def test_an_unreadable_day_is_alerted_and_fails_the_step(tmp_path):
    run, data, alerts = harness(tmp_path, record=traded_day())
    data.files[record_path(DAY)] = b"damaged"
    result = run.run(SESSIONS[1])
    assert not result.ok and alerts.lines[0].startswith(f"recommender check NOT made for {DAY}: ")


def test_a_rerun_the_same_evening_writes_nothing_new(tmp_path):
    run, data, alerts = harness(tmp_path, record=traded_day())
    run.run(SESSIONS[1])
    before = dict(data.files)
    run.run(SESSIONS[1])
    assert data.files == before


def test_days_older_than_60_sessions_are_left(tmp_path):
    long = [DAY + timedelta(days=k) for k in range(0, 120) if (DAY + timedelta(days=k)).weekday() < 5]
    run, data, alerts = harness(tmp_path, record=traded_day())
    run.ports = CheckPorts(run.ports.receipts, run.ports.read, lambda a, b: [d for d in long if a <= d <= b],
                           run.ports.lookup)  # fmt: skip
    run.run(long[58])  # the 59th session: still open, checked again
    final = run.run(long[59])  # the 60th: the last check, final and alerted (judge 658 S3)
    assert alerts.lines[-1].startswith(f"PAPER ONLY. Recommender check for {DAY:%d %b %Y}: data check failed.")
    assert "never closed in 60 sessions" in alerts.lines[-1] and final.ok
    assert run.run(long[60]).lines == (f"recommender check {long[60]}: no recorded day waits for a check",)


def test_a_day_unreadable_at_its_last_check_is_written_final_and_alerted(tmp_path):
    long = [DAY + timedelta(days=k) for k in range(0, 120) if (DAY + timedelta(days=k)).weekday() < 5]
    run, data, alerts = harness(tmp_path, record=traded_day())
    run.ports = CheckPorts(run.ports.receipts, run.ports.read, lambda a, b: [d for d in long if a <= d <= b],
                           run.ports.lookup)  # fmt: skip
    data.files[record_path(DAY)] = b"damaged"
    assert not run.run(long[59]).ok
    assert any(".check." in p for p in data.files) and alerts.lines[0].startswith(
        f"recommender check NOT made for {DAY}"
    )
    assert run.run(long[60]).ok


def test_a_stale_seal_on_one_day_never_stops_the_others(tmp_path):
    """Self-review 1 (blocking): the real reader raises StaleSeal; that day is alerted, the next day still checked."""
    from fno.school.contracts.seal import StaleSeal

    run, data, alerts = harness(tmp_path, {CS1: FoundOutcome(10.0, False)}, record=traded_day())
    second = no_trade(session=SESSIONS[1], made_at=MADE_AT + timedelta(days=1),
                      evidence_cutoff=MADE_AT + timedelta(days=1), versions=(evidence_of(CS1),),
                      candidates=(candidate(CS1, traded=True),))  # fmt: skip
    run.keeper.keep(record_path(second.session), encode(second), lambda b: None, "second day")
    real = run.ports.read

    def read(path):
        if path == record_path(DAY):
            raise StaleSeal("hash differs")
        return real(path)

    run.ports = CheckPorts(run.ports.receipts, read, run.ports.sessions, run.ports.lookup)
    result = run.run(SESSIONS[3])
    assert not result.ok and alerts.lines[0].startswith(f"recommender check NOT made for {DAY}: ")
    assert any(line.startswith(f"PAPER ONLY. Recommender check for {SESSIONS[1]:%d %b %Y}") for line in alerts.lines)


def test_a_damaged_check_file_is_that_day_s_problem(tmp_path):
    run, data, alerts = harness(tmp_path, record=traded_day())
    run.run(SESSIONS[1])
    data.files[f"recommend/2026/11/{DAY}.check.{SESSIONS[1]}.json"] = b"{broken"
    result = run.run(SESSIONS[2])
    assert not result.ok and "does not read" in alerts.lines[-1]
