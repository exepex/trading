"""Story E5 criterion 2: no AI call is reachable from Book 1's code path. Statically, nothing Book 1's modules import
(their lazy imports included, followed through every `fno` module) is an AI module or an AI SDK; the market-data
providers it reaches through the composition root (Groww, NSE) are data, not models. At run time, every AI module and
SDK is replaced by a fake that fails on any use, and Book 1 still decides and orders."""

import sys
import types
from datetime import date, datetime, time
from pathlib import Path

from fno.books.book1_orders import ReplayedOrders
from fno.constants import BOOK1_RULES
from fno.models import IST
from fno.playbook.decision_store import DecisionStore
from tests.decisions.builders import SAME_CODE, doc, snapshot

from .builders import book1, clock_at, priced_evaluator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from check_imports import imported_modules  # noqa: E402

BOOK1_MODULES = ("book1", "book1_cli", "book1_exits", "book1_inputs", "book1_market", "book1_orders", "book1_wiring")
AI_MODULES = ("fno.ai",)
AI_SDKS = ("anthropic", "openai", "google.generativeai", "mistralai", "cohere", "ollama")
DAY = date(2026, 10, 13)


def _path(module: str) -> Path | None:
    base = ROOT.joinpath(*module.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def closure(start) -> set[str]:
    """Every module reachable by import from `start`: fno modules followed, others kept as leaves."""
    seen, todo = set(), list(start)
    while todo:
        module = todo.pop()
        if module in seen:
            continue
        seen.add(module)
        path = _path(module) if module.startswith("fno") else None
        if path is not None:
            todo += [m for m in imported_modules(path, ROOT) if not m.startswith("fno") or _path(m)]
    return seen


def test_nothing_book1_imports_is_an_ai_module_or_sdk():
    reached = closure(f"fno.books.{name}" for name in BOOK1_MODULES)
    assert "fno.books.book1" in reached and "fno.playbook.evaluate" in reached  # the walk follows real imports
    ai = [m for m in reached if any(m == n or m.startswith(f"{n}.") for n in AI_MODULES + AI_SDKS)]
    assert ai == []


class Trap(types.ModuleType):
    def __getattr__(self, name):
        raise AssertionError(f"Book 1 reached an AI module: {self.__name__}.{name}")


def test_book1_decides_orders_and_names_exits_with_every_ai_module_a_failing_fake(tmp_path, monkeypatch):
    for name in [m for m in sys.modules if m.startswith(AI_MODULES)] + list(AI_MODULES) + list(AI_SDKS):
        monkeypatch.setitem(sys.modules, name, Trap(name))
    decider, _ = book1(tmp_path, snapshot(doc("sc-a")), clock_at(datetime.combine(DAY, time(15), IST)))
    assert decider.decide(DAY).startswith(f"Book 1 {DAY}: decided")
    [run] = DecisionStore(tmp_path, BOOK1_RULES).runs(DAY)
    orders = ReplayedOrders(priced_evaluator(), SAME_CODE).orders(
        BOOK1_RULES, run, datetime.combine(DAY, time(15), IST)
    )
    assert orders and all(o.book == BOOK1_RULES for o in orders)
