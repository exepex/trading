"""Story D3b criterion 4 (decision 60): one run order. Every reader that takes a day's runs from `DecisionStore.runs`
hands them straight to `ordered_runs`; no reader orders run folders by itself (by name, `sorted` or `reversed`)."""

import ast

from fno.config import ROOT

OWNERS = {"fno/playbook/decision_store.py"}  # the store itself: listing, the next run ID, the duplicate check


def day_run_calls(tree: ast.AST):
    """Each `<x>.runs(<day>)` call (one argument: a day's runs) with the call it sits in, if any."""
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in ast.walk(tree):
        attr = node.func.attr if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) else None
        if attr == "runs" and len(node.args) == 1:
            yield node, parents.get(node)


def test_every_reader_of_a_day_s_runs_orders_them_with_the_shared_function():
    found, wrong = [], []
    for path in sorted((ROOT / "fno").rglob("*.py")):
        name = path.relative_to(ROOT).as_posix()
        if name in OWNERS:
            continue
        for call, parent in day_run_calls(ast.parse(path.read_text(encoding="utf-8"))):
            found.append(name)
            caller = parent.func.id if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name) else None
            if caller != "ordered_runs":
                wrong.append(f"{name}:{call.lineno}")
    assert wrong == []
    assert sorted(set(found)) == ["fno/desk/committed_decisions.py", "fno/evaluation/order.py"]


def test_the_check_catches_a_reader_that_sorts_by_itself():
    tree = ast.parse("for run in reversed(store.runs(day)): pass\nrows = ordered_runs(root, store.runs(day), git)")
    callers = [p.func.id if isinstance(p, ast.Call) else None for _, p in day_run_calls(tree)]
    assert callers == ["reversed", "ordered_runs"]
