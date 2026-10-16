"""A planned idea in a temporary repository, frozen and judged with fakes for the playbook and the shadow accounts
(story R1c)."""

from datetime import date, timedelta
from types import SimpleNamespace

from fno.factory.constants import DATA_SPEND_FILE
from fno.factory.gate_log import GateLog
from fno.factory.gate_order import GateOrder
from fno.factory.questions import Questions
from fno.factory.registration_freeze import FactoryFreeze
from fno.factory.staging import FactoryGit
from fno.factory.verdict import ShadowVerdicts
from fno.factory.wiring import build_gate_steps, build_registration, read_idea
from fno.playbook.fields import PlaybookError
from fno.research_engine.ledger import Ledger

from .helpers import BLOCK, INPUTS, REGISTER, commit, init_repo, write_card

DAY = date(2026, 10, 17)
QUESTION = "planted-question"
PLAN = INPUTS.replace("pass_level: 0.01", "pass_level: 0.05").replace("sd_per_trade: 3000", "sd_per_trade: 900")
SHADOW = "playbook_name: x1-sc\nplaybook_version: 1\nminimum_useful_net: 150\n"
WINNING = [1000.0] * 6 + [-100.0] * 5  # p = 0.0081: passes alone at 5%, never in a family of 20


class Versions:
    def __init__(self, measurements=()):
        self.measurements = set(measurements)

    def get(self, name, version):
        if name == "missing":
            raise PlaybookError(f"{name} v{version}", "no such playbook file")
        family = "measurement" if (name, version) in self.measurements else "premium"
        return SimpleNamespace(name=name, version=version, edge_family=family)


def after_freeze(nets, first=DAY + timedelta(days=1)):
    """Positions opened on successive days from `first`, as (opened_on, net)."""
    return [(first + timedelta(days=i), net) for i, net in enumerate(nets)]


class Results:
    """A shadow account's completed positions as (opened_on, net); a plain list of nets opens them after the freeze."""

    def __init__(self, nets=None):
        self.by_account = {a: v if v and isinstance(v[0], tuple) else after_freeze(v) for a, v in (nets or {}).items()}
        self.asked = []

    def nets(self, account, opened_after):
        self.asked.append((account, opened_after))
        return [net for day, net in self.by_account.get(account, []) if day > opened_after]


def planned_repo(root, extra=SHADOW, spent=False):
    init_repo(root)
    (root / DATA_SPEND_FILE).write_text(REGISTER)
    plan = PLAN.replace("Quotes | Groww | 2027", "Closes | NSE | 2019") if spent else PLAN
    write_card(root, BLOCK + plan + extra)
    build_registration(root).register(read_idea("X1", root), DAY)
    commit(root, "register X1")
    steps = build_gate_steps(root)
    for gate in ("screen", "spend", "plan"):
        getattr(steps, gate)(read_idea("X1", root), DAY)
        commit(root, gate)
    parts(root)[3].add(QUESTION, "a planted question", 0.05)
    commit(root, "question")
    return root


def parts(root):
    git = FactoryGit(root)
    return GateOrder(GateLog(root, git), git), Ledger(root, git), git, Questions(root, git)


def freezer(root, versions=None):
    order, ledger, _, questions = parts(root)
    return FactoryFreeze(order, ledger, questions, versions or Versions())


def verdicts(root, results):
    order, ledger, _, questions = parts(root)
    return ShadowVerdicts(order, ledger, questions, results)
