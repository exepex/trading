"""Builders for story F1t's tests: a repository holding the day's committed common pack and the books' decision
prompts, registered decision versions with a simple shape check, private packs with account figures, pointers, fake
answers, and a decider that writes a valid D3 run."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from pathlib import Path

from fno.ai_trading.answer import complete_answer, labels_of
from fno.ai_trading.paths import common_pack_path
from fno.ai_trading.pointer import DecisionPointer
from fno.ai_trading.ports import AcceptedDecision, AiBookDecider, DecidedRun, DecisionRefused
from fno.ai_trading.versions import DecisionRegistry, DecisionVersion
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.desk.common_pack import CommonPack
from fno.desk.pack_items import canonical_json, sha256_hex
from fno.desk.private_pack import PrivatePack
from fno.models import IST
from fno.playbook.decision_record import BODY, NULLABLE, THREE_BOOK
from fno.playbook.decision_store import DecisionStore
from tests.ai.fakes import git

DAY = date(2026, 10, 19)
MODEL = "claude-opus-5-5"
PROMPTS = {BOOK2_HYBRID: "agents/decision/book2_hybrid_test_v1.md", BOOK3_AI: "agents/decision/book3_ai_test_v1.md"}
FILL_PRICE, CASH, STRIKE = "1,23,456.75", "3,40,500", "25150"  # account figures; the strike is also public
COMMON_BODY = {"day": DAY.isoformat(), "kind": "common", "items": [{"name": "nifty_spot", "value": 25150.4},
               {"name": "strike_25150", "value": 25150}], "provenance": {}}  # fmt: skip
CARDS = {"input_sha256": "c" * 64, "role_set_version": "roles-v1",
         "roles": [{"unit_id": "analyst_volatility", "status": "valid", "card": {"view": "IV rich"}}]}  # fmt: skip


def at(hour: int, minute: int, second: int = 0, day: date = DAY) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, second, tzinfo=IST)


def shape_check(decision: dict) -> list[str]:
    """A book's own check, as F5 and F6 will write theirs: here only the action's closed set."""
    return [] if decision.get("action") in ("trade", "no_trade", "follow_rule") else ["decision.action is not allowed"]


def write_paths(book: str) -> tuple[str, ...]:
    return (f"journal/{book}/", "research/ledger.csv") if book == BOOK3_AI else (f"journal/{book}/",)


def version(root: Path, book: str = BOOK2_HYBRID, number: int = 1, model: str = MODEL) -> DecisionVersion:
    path = Path(root) / PROMPTS[book]
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {book} decision prompt, test version\nDecide.\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return DecisionVersion(book, number, PROMPTS[book], digest, model, shape_check, write_paths(book),
                           ("analyst_volatility",), "roles-v1")  # fmt: skip


def registry(root: Path, books=(BOOK2_HYBRID, BOOK3_AI)) -> DecisionRegistry:
    return DecisionRegistry([version(root, book) for book in books])


def private_body(book: str = BOOK2_HYBRID, day: date = DAY) -> dict:
    ledger = f"date,amount\n{day.isoformat()},{FILL_PRICE}\ncash,{CASH}\nstrike,{STRIKE}\n"
    files = [{"path": f"journal/{book}/cash_ledger.csv", "text": ledger},
             {"path": "playbook/b0-monthly-sc-v1.yaml", "text": "widths: [100, 200]\nlots: 1\n"}]  # fmt: skip
    for file in files:
        file["sha256"] = sha256_hex(file["text"].encode("utf-8"))
    return {"schema_version": 1, "kind": "book_private_pack", "book": book, "day": day.isoformat(), "files": files}


def common_pack(day: date = DAY) -> CommonPack:
    return CommonPack(day, dict(COMMON_BODY, day=day.isoformat()))


def make_repo(root: Path, day: date = DAY) -> Path:
    """A git repository with the day's committed common pack and the test prompts."""
    root = Path(root)
    path = root / common_pack_path(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(common_pack(day).data)
    registry(root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "desk@example.invalid")
    git(root, "config", "user.name", "desk")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "the day's common pack and prompts")
    return root


def pointer(root: Path, book: str = BOOK2_HYBRID, day: date = DAY, cards: dict | None = None) -> DecisionPointer:
    return DecisionPointer(book, day, version(root, book).label, common_pack(day).sha256, private_body(book, day),
                           CARDS if cards is None else cards, at(15, 10, day=day), at(15, 10, 10, day=day))  # fmt: skip


def draft(action: str = "trade", reason: str = "IV rich against the rule default", model: str = MODEL, **extra) -> dict:
    return {"decision": {"action": action, "reason": reason, **extra}, "model_reported": model}


def answer(root: Path, book: str = BOOK2_HYBRID, **kwargs) -> dict:
    return complete_answer(draft(**kwargs), labels_of(pointer(root, book)))


def record(book: str, run_id: str, accepted: AcceptedDecision, **changes) -> dict:
    """A valid D3 record of the decider's run (every three-book field the book must fill is filled)."""
    nullable = NULLABLE[book] | {"version_id", "judge", "owner_override", "forecasts"}
    fields = {key: None for key in BODY + THREE_BOOK}
    fields |= {key: "x" for key in THREE_BOOK if key not in nullable}
    fields |= {"schema_version": 1, "kind": "decision_record", "run_id": run_id, "opportunity_id": "no_trade",
               "mode": "book", "header": dict.fromkeys(("code_commit", "config_sha256", "inputs_sha256",
                                                         "registry_commit", "strategy_file_sha256"), "h"),
               "book": book, "common_pack_sha256": accepted.common_pack.sha256,
               "private_pack_sha256": accepted.private_pack.sha256, "model_served": accepted.model_reported,
               "session_id": accepted.session, "served": {"decision_version": accepted.version}}  # fmt: skip
    return fields | changes


class FakeDecider(AiBookDecider):
    """Writes one D3 run as a real decider would; `changes` spoils the record, `extra` writes more files, `refuse`
    or `fail` stops it after writing them (so a restore has something to undo)."""

    def __init__(self, root: Path, changes: dict | None = None, extra: dict | None = None, refuse: str = "",
                 fail: Exception | None = None, second_run: bool = False):  # fmt: skip
        self.root, self.changes, self.extra = Path(root), changes or {}, extra or {}
        self.refuse, self.fail, self.second_run, self.calls = refuse, fail, second_run, []

    def decide(self, accepted: AcceptedDecision) -> DecidedRun:
        self.calls.append(accepted)
        for name, text in self.extra.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            with (self.root / name).open("a", encoding="utf-8") as file:
                file.write(text)
        store = DecisionStore(self.root, accepted.book)
        run_id = store.next_run_id(accepted.day)
        run = store.write(accepted.day, run_id, None, [record(accepted.book, run_id, accepted, **self.changes)])
        if self.second_run:
            other = store.next_run_id(accepted.day)
            store.write(accepted.day, other, None, [record(accepted.book, other, accepted, **self.changes)])
        if self.refuse:
            raise DecisionRefused(self.refuse)
        if self.fail:
            raise self.fail
        return DecidedRun(run, tuple(self.root / name for name in self.extra))


def accepted(root: Path, book: str = BOOK2_HYBRID, decision: dict | None = None) -> AcceptedDecision:
    return AcceptedDecision(book, DAY, version(root, book).label, MODEL, MODEL, "https://example.invalid/session",
                            common_pack(), PrivatePack(book, DAY, private_body(book)),
                            decision or {"action": "trade", "reason": "r"}, CARDS, ("analyst_volatility",), "c1",
                            "c2")  # fmt: skip


def canonical(value) -> str:
    return sha256_hex(canonical_json(value))
