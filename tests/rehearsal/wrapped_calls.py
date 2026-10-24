"""Story REH1i: a guard test reads every use of a builder in a file, not the first text match. A file that hands one
builder to its rehearsal choice and leaves another bare (G11's branch, the v4 collector's receipts) passed a single
regex search; it fails here. Any reference to the builder counts (a call, an alias, `partial`, `map`, a subclass's
base, an import that renames it), so only "called straight inside the choice" passes. Limits, said plainly: a name
built from a string (`getattr(m, "...")`) is not seen, and the choice is matched by its name."""

from __future__ import annotations

import ast


def unwrapped(text: str, built: str, wrapper: str) -> list[int]:
    """The line of every use of `built` other than as the called function of a wrapper's first argument."""
    tree = ast.parse(text)
    handed = {
        id(call.args[0].func) for call in _calls(tree, wrapper) if call.args and isinstance(call.args[0], ast.Call)
    }
    used = [node.lineno for node in ast.walk(tree) if _names(node, built) and id(node) not in handed]
    renamed = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
               and any(alias.name == built and alias.asname not in (None, built) for alias in node.names)]  # fmt: skip
    return sorted(used + renamed)


def calls(text: str, built: str) -> int:
    """How many uses of `built` the file has (calls and other references)."""
    return sum(1 for node in ast.walk(ast.parse(text)) if _names(node, built))


def _calls(tree: ast.AST, name: str) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call) and _names(node.func, name)]


def _names(node: ast.AST, name: str) -> bool:
    return (isinstance(node, ast.Name) and node.id == name) or (isinstance(node, ast.Attribute) and node.attr == name)
