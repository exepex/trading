"""Story G10 part 2, criterion 4: the 15:10 deadline on GitHub's receipt time, through the CommitmentTimes interface."""

from datetime import UTC, date, datetime

import pytest

from fno.health.model import EvidenceUnknown
from fno.models import IST
from fno.v4_pack.commitment import CommitmentTimeUnknown, GitHubCommitmentTimes, on_time
from fno.v4_pack.wiring import build_commitment_times

DAY = date(2026, 10, 22)


def test_received_at_1510_00_counts_and_1510_01_is_a_miss():
    assert on_time(datetime(2026, 10, 22, 15, 10, 0, tzinfo=IST), DAY)
    assert not on_time(datetime(2026, 10, 22, 15, 10, 1, tzinfo=IST), DAY)
    assert on_time(datetime(2026, 10, 22, 9, 40, 0, tzinfo=UTC), DAY)  # 15:10:00 IST, given in UTC
    assert not on_time(datetime(2026, 10, 21, 15, 9, 0, tzinfo=IST), date(2026, 10, 20))


class Evidence:
    def __init__(self, received=None, unknown=False):
        self.received, self.unknown, self.asked = received, unknown, []

    def file_pushed_at(self, path):
        return self._answer(("file", path))

    def row_pushed_at(self, path, text, session):
        return self._answer(("row", path, text, session))

    def _answer(self, asked):
        self.asked.append(asked)
        if self.unknown:
            raise EvidenceUnknown("push time unknown")
        return self.received


def test_the_adapter_reads_githubs_receipt_time_for_a_file_or_a_row():
    received = datetime(2026, 10, 22, 15, 2, tzinfo=IST)
    evidence = Evidence(received)
    times = GitHubCommitmentTimes(evidence)
    assert times.file_received_at("receipts/x") == received
    assert times.row_received_at("research/forecasts/v4/b/q.csv", "2026-10-22,0.3", DAY) == received
    assert evidence.asked == [("file", "receipts/x"), ("row", "research/forecasts/v4/b/q.csv", "2026-10-22,0.3", DAY)]


@pytest.mark.parametrize("evidence", [Evidence(unknown=True), Evidence(datetime(2026, 10, 22, 15, 2))])
def test_an_unknown_or_naive_receipt_time_is_never_guessed(evidence):
    with pytest.raises(CommitmentTimeUnknown):
        GitHubCommitmentTimes(evidence).file_received_at("receipts/x")


def test_the_composition_root_builds_the_github_adapter(tmp_path):
    assert isinstance(build_commitment_times(tmp_path, env={}), GitHubCommitmentTimes)
