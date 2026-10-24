"""Story REH1i: a guard test reads every call in a file, not the first match. A file that hands one builder to its
rehearsal choice and leaves another unwrapped (the v4 collector's receipts, found by G11's builder) passed a single
regex search; it fails here."""

from __future__ import annotations

import ast


def unwrapped(text: str, built: str, wrapper: str) -> list[int]:
    """The line of every call of `built` that is not the first argument of a call of `wrapper`."""
    tree = ast.parse(text)
    handed = {id(call.args[0]) for call in _calls(tree, wrapper) if call.args}
    return sorted(call.lineno for call in _calls(tree, built) if id(call) not in handed)


def calls(text: str, built: str) -> int:
    return len(_calls(ast.parse(text), built))


def _calls(tree: ast.AST, name: str) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call) and _name(node.func) == name]


def _name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    return func.attr if isinstance(func, ast.Attribute) else None
