"""Story receipts-reach: the health evidence keeps the receipt's kind of answer, so a seal can tell "no push" and "the
log no longer reaches it" (answers) from a failed read; the health check still sees each as `unknown`."""

import pytest

from fno.ai.receipts import ReceiptNotFound, ReceiptOutsideLog, ReceiptUnavailable
from fno.health.evidence import Evidence
from fno.health.model import EvidenceNotCommitted, EvidenceNotPushed, EvidenceOutsideLog, EvidenceUnknown


class History:
    def __init__(self, commit):
        self.commit = commit

    def first_commit_adding(self, path):
        return self.commit


class Receipts:
    def __init__(self, error):
        self.error = error

    def received_at(self, commit):
        raise self.error


@pytest.mark.parametrize(("error", "kind"), [(ReceiptNotFound("no push"), EvidenceNotPushed),
                                             (ReceiptOutsideLog("log ends"), EvidenceOutsideLog),
                                             (ReceiptUnavailable("HTTP 502"), EvidenceUnknown)])  # fmt: skip
def test_each_receipt_answer_keeps_its_kind(tmp_path, error, kind):
    with pytest.raises(kind) as raised:
        Evidence(tmp_path, History("c1"), Receipts(error)).file_pushed_at("receipts/x.sha256")
    assert type(raised.value) is kind  # a failed read is a plain unknown, never an answer


def test_no_commit_adding_the_file_is_its_own_answer(tmp_path):
    with pytest.raises(EvidenceNotCommitted, match="no commit adding it"):
        Evidence(tmp_path, History(None), Receipts(None)).file_pushed_at("receipts/x.sha256")
