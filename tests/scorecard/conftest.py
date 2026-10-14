"""Story E6 fixtures: started books and one shadow account, a playbook with two approved versions and one shadow
candidate, and a scorecard run wired like the app (the evidence-in-git checks are D1's and are left out here)."""

from datetime import date

import pytest
from playbook.builders import DOCUMENT, document, write

from fno.books.account import PaperAccount
from fno.books.paths import shadow_account
from fno.composition import open_account_writer
from fno.constants import BOOKS, PlaybookStatus
from fno.desk.records import DeskRecords
from fno.playbook.lifecycle import StatusChanger
from fno.playbook.loader import PlaybookLoader, registry_path
from fno.playbook.registry import Registry, RegistryRow
from fno.playbook.schema import parse_strategy
from fno.scorecard.pauses import AutoPauser
from fno.scorecard.run import ScorecardRun

from .history import CHARGES

START = date(2026, 10, 14)
REVIEW = date(2027, 1, 20)
PLAN = {
    "expected_range": {"low": -500, "high": 800}, "unit": "Rs net per completed position",
    "review_dates": [REVIEW], "pause_rules": ["one trade loses Rs 10,000"], "catastrophic_loss_rs": 10000,
}  # fmt: skip
SHADOW = shadow_account("cand-c-v1")
ACCOUNTS = (*BOOKS, SHADOW)


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


class NoGit:
    def head(self):
        raise AssertionError("a pause never needs the evidence commit")


def version(folder, name, status, plan=None, **changes):
    doc = document(name=name, evaluation_plan=plan or PLAN, **changes)
    path = write(folder, doc)
    if status == PlaybookStatus.PAPER:
        strategy = parse_strategy(doc)
        row = RegistryRow(name, 1, strategy.parameters_sha256, status, START, "owner", "abcdef1")
        Registry(registry_path(folder)).append(row)
        path.write_text(path.read_text().replace("status: research", "status: paper"))


@pytest.fixture
def root(tmp_path):
    for account in ACCOUNTS:
        with open_account_writer(account, tmp_path) as writer:
            writer.start(START)
    folder = tmp_path / "playbook"
    version(folder, "fly-a", PlaybookStatus.PAPER)
    version(folder, "fly-b", PlaybookStatus.PAPER, entry_conditions=[DOCUMENT["entry_conditions"][1]])  # F3 only
    version(folder, "cand-c", PlaybookStatus.RESEARCH)
    return tmp_path


@pytest.fixture
def alerts():
    return Alerts()


def loader(root, checks=()):
    folder = root / "playbook"
    return PlaybookLoader(folder, Registry(registry_path(folder)), checks)


@pytest.fixture
def make_run(root, alerts):
    def make(checks=()):
        pauser = AutoPauser(StatusChanger(loader(root, checks), NoGit()), alerts)
        records = lambda name: DeskRecords(PaperAccount(root, name))  # noqa: E731
        return ScorecardRun(lambda: ACCOUNTS, records, loader(root, checks), pauser, CHARGES)

    return make
