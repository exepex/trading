"""S1 item 15 (owner, 16 Oct 2026; judge 229): the freeze hashes the code that computes a scored figure. Starting at
the scoring modules of `fno/scoreboard`, every fno module imported by a hashed module is either hashed itself or
exempted below with a one-line reason; an exempted module's own imports are not followed. A new import of an
unhashed computation fails here, so a figure cannot change after the freeze while `verify` stays silent."""

import ast
from pathlib import Path

from fno.config import ROOT
from fno.evaluation.freeze import frozen_targets
from fno.evaluation.protocol import PROTOCOL_FILE

DATA_SHAPES = {  # names, constants and record shapes: no figure is computed in them
    "fno/constants.py": "names and enum values; each number scoring takes from it is pinned (test_frozen_numbers)",
    "fno/budget/constants.py": "the budget's purpose names (no numbers)",
    "fno/models.py": "the clock and plain value types",
    "fno/books/fills.py": "the Fill row shape",
    "fno/factory/constants.py": (
        "gate names, outcomes, file paths and the figures pattern, each value Test B reads pinned "
        "(test_factory_constants_pinned); its numbers serve G1-G3, which Test B never reads"
    ),
    "fno/desk/trade_counts.py": "version_key only: parses a strategy-version tag",
    "fno/desk/pack_items.py": "available_time only: parses an ISO time into IST",
    "fno/desk/execution.py": "fill_id only: an identifier string",
    "fno/playbook/decision_record.py": "the D3 record's field names and the no-trade ID",
    "fno/playbook/decision_validity.py": "the C4 'blocked' reason prefix",
    "fno/playbook/opportunities.py": "the book and shadow mode names",
    "fno/playbook/schema.py": "the playbook file's field schema",
    "fno/research_data/panel_reader.py": "the FutureQuote row shape",
    "fno/research_engine/experiments.py": "the StatisticsTerms shape that statistics.py reads",
    "fno/scorecard/strategy_record.py": "the scorecard's record shapes",
}
READERS = {  # read committed or archived files as they are; the files themselves are the evidence
    "fno/books/account.py": "reads a book's paper account rows",
    "fno/budget/usage_ledger.py": "reads F8's committed AI usage rows",
    "fno/checks/validity_failures.py": "reads C4's append-only failure log",
    "fno/books/paths.py": "journal file paths",
    "fno/factory/append_only.py": "reads the gate log's committed rows and refuses an edited history",
    "fno/books/versions.py": "reads the strategy-version registry",
    "fno/desk/pack_store.py": "reads E2's common packs",
    "fno/playbook/lifecycle.py": "D1's status writer: applies the pause the hashed rule decided",
    "fno/playbook/loader.py": "reads the committed playbook files",
    "fno/desk/records.py": "reads the journal's fill and trade rows",
    "fno/desk/run_log.py": "reads E3's run logs",
    "fno/playbook/decision_store.py": "reads D3's committed decision records",
    "fno/research_data/calendar.py": "reads NSE's committed session calendar",
    "fno/research_engine/ledger.py": "the research ledger's rows, which the freezer registers into",
    "fno/quotes/recorder.py": "the quote archive's dataset name and file paths only",
    "fno/storage/raw_library.py": "the raw data archive",
    "fno/storage/raw_source.py": "the raw data sources' names and addresses",
    "fno/storage/raw_store.py": "the raw data store",
}
WIRING = {  # composition and settings: the settings that decide figures are hashed as config sections
    "fno/alerts/sender.py": "sends the #fno-desk line; decides nothing",
    "fno/scorecard/measurement_alerts.py": "measurement versions' alert wording; decides nothing",
    "fno/budget/wiring.py": "composition root",
    "fno/composition.py": "composition root",
    "fno/config.py": "loads config.yaml; its scoring sections are hashed",
    "fno/desk/wiring.py": "composition root",
    "fno/factory/wiring.py": "composition root",
    "fno/storage/wiring.py": "composition root",
}
EXEMPT = {**DATA_SHAPES, **READERS, **WIRING}
NOT_SCORING = {"__init__.py", "cli.py"}
SCORING_PACKAGES = ("fno/scoreboard", "fno/role_value")  # S2, S3 and S6; F9 (judge 235)


def module_file(module: str) -> str | None:
    path = Path(*module.split("."))
    for candidate in (path.with_suffix(".py"), path / "__init__.py"):
        if (ROOT / candidate).is_file():
            return candidate.as_posix()
    return None


def imported(path: str) -> set[str]:
    """The fno module files `path` imports a name from (package markers left out)."""
    tree, package, found = ast.parse((ROOT / path).read_text(encoding="utf-8")), Path(path).parent.parts, set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = list(package[: len(package) - node.level + 1] if node.level else ())
            module = ".".join(base + (node.module.split(".") if node.module else []))
            found |= {module_file(f"{module}.{a.name}") or module_file(module) for a in node.names}
        elif isinstance(node, ast.Import):
            found |= {module_file(a.name) for a in node.names}
    return {f for f in found if f and f.startswith("fno/") and not f.endswith("__init__.py")}


def unaccounted(hashed: set[str]) -> dict[str, set[str]]:
    """Walked from the scoring packages and from every hashed module, so a hashed rule's own imports are covered too."""
    start = {f"{package}/{p.name}" for package in SCORING_PACKAGES for p in (ROOT / package).glob("*.py")
             if p.name not in NOT_SCORING} | {h for h in hashed if h.endswith(".py")}  # fmt: skip
    seen, todo, missing = set(), list(start), {}
    while todo:
        current = todo.pop()
        if current in seen:
            continue
        seen.add(current)
        for target in imported(current):
            if target in hashed:
                todo.append(target)
            elif target not in EXEMPT:
                missing.setdefault(target, set()).add(current)
    return missing


def hashed_files() -> set[str]:
    return set(frozen_targets((ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")))


def test_every_module_the_scoring_reaches_is_hashed_or_exempted_with_a_reason():
    assert unaccounted(hashed_files()) == {}


def test_every_exemption_is_still_needed_and_not_also_hashed():
    """An exemption nothing reaches any more, or one that is also hashed, is a stale line: removed, never kept."""
    hashed = hashed_files()
    reached = set().union(*(imported(h) for h in hashed if h.endswith(".py")))
    assert set(EXEMPT) & hashed == set() and set(EXEMPT) - reached == set()
    assert all(reason.strip() for reason in EXEMPT.values())


def test_dropping_a_computation_module_from_the_list_is_caught():
    missing = unaccounted(hashed_files() - {"fno/desk/pricing.py"})
    assert set(missing) == {"fno/desk/pricing.py"}
    assert "fno/scoreboard/standard_unit.py" in missing["fno/desk/pricing.py"]
