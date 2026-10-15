"""Story A9b, criterion 2: an NSE source never lets `requests.HTTPError` (or any other `requests` error, or the pacer's
`SourceCoolingOff`) out, so no code catches one around a source read: a test that reads the code (every function in
fno/ and research/ that calls `fetch`, `fetch_published` or `last_written`).

It resolves a module-level tuple of exceptions named in an `except` (e.g. A12's `LIST_ERRORS`). Limits, stated plainly
(judge 119 addendum 1): it does not follow an imported alias of an exception or of such a tuple, a tuple built in a
function, a method alias of a read (`get = source.fetch`), an `except Exception` or a bare `except`, or a catch one
call up from the function that reads (e.g. a caller of `_filing`). Those stay with review; the policy tests show no
such error leaves a source in the first place."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
READS = {"fetch", "fetch_published", "last_written"}
NEVER_RAISED = {"HTTPError", "RequestException", "SourceCoolingOff"}


def _calls_a_read(function: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in READS
        for node in ast.walk(function)
    )


def _names(expression: ast.AST) -> set[str]:
    """The exception names an expression lists (`requests.HTTPError` gives `HTTPError`)."""
    return {
        n.id if isinstance(n, ast.Name) else n.attr
        for n in ast.walk(expression)
        if isinstance(n, ast.Name | ast.Attribute)
    }


def _tuple_constants(tree: ast.Module) -> dict[str, set[str]]:
    """Module-level `NAME = (ExcA, ExcB, ...)`: the names each tuple lists."""
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = _names(node.value)
    return found


def _caught(handler: ast.ExceptHandler, constants: dict[str, set[str]]) -> set[str]:
    listed = _names(handler.type)
    return listed.union(*(constants.get(name, set()) for name in listed))


def offenders(paths) -> list[str]:
    found = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        constants = _tuple_constants(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _calls_a_read(node)):
                continue
            handlers = [h for h in ast.walk(node) if isinstance(h, ast.ExceptHandler) and h.type is not None]
            if any(_caught(h, constants) & NEVER_RAISED for h in handlers):
                found.append(f"{path.name}:{node.lineno} {node.name}")
    return found


def test_no_function_reading_a_source_catches_http_error():
    paths = [*ROOT.joinpath("fno").rglob("*.py"), *ROOT.joinpath("research").rglob("*.py")]
    assert len(paths) > 300 and offenders(paths) == []


def test_the_check_finds_a_planted_catch_also_through_a_tuple_and_passes_a_proper_one(tmp_path):
    body = "def read(source, path):\n    try:\n        return source.fetch(path)\n    except {}:\n        return None\n"
    files = {
        "planted.py": body.format("(RawSourceUnavailable, requests.HTTPError)"),
        "tuple.py": "ERRORS = (requests.RequestException, ValueError)\n\n\n" + body.format("ERRORS"),
        "proper.py": "ERRORS = (RawSourceUnavailable, ValueError)\n\n\n" + body.format("ERRORS"),
        "cooling.py": body.format("RawSourceCoolingOff"),  # a source's own error, not the pacer's
    }
    for name, text in files.items():
        (tmp_path / name).write_text(text)
    assert offenders(sorted(tmp_path.iterdir())) == ["planted.py:1 read", "tuple.py:4 read"]
