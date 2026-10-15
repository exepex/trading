"""Story A9b, criterion 2: an NSE source never lets `requests.HTTPError` out, so no code catches one around a source
read: a test that reads the code (every function in fno/ and research/ that calls `fetch`, `fetch_published` or
`last_written`)."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
READS = {"fetch", "fetch_published", "last_written"}


def _calls_a_read(function: ast.AST) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in READS
        for node in ast.walk(function)
    )


def _catches_http_error(function: ast.AST) -> bool:
    return any(
        isinstance(node, ast.ExceptHandler) and node.type is not None and "HTTPError" in ast.unparse(node.type)
        for node in ast.walk(function)
    )


def offenders(paths) -> list[str]:
    found = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            function = isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            if function and _calls_a_read(node) and _catches_http_error(node):
                found.append(f"{path.name}:{node.lineno} {node.name}")
    return found


def test_no_function_reading_a_source_catches_http_error():
    paths = [*ROOT.joinpath("fno").rglob("*.py"), *ROOT.joinpath("research").rglob("*.py")]
    assert len(paths) > 300 and offenders(paths) == []


def test_the_check_finds_a_planted_catch_and_passes_a_proper_one(tmp_path):
    planted, proper = tmp_path / "planted.py", tmp_path / "proper.py"
    body = "def read(source, path):\n    try:\n        return source.fetch(path)\n    except {}:\n        return None\n"
    planted.write_text(body.format("(RawSourceUnavailable, requests.HTTPError)"))
    proper.write_text(body.format("RawSourceUnavailable"))
    assert offenders([planted, proper]) == ["planted.py:1 read"]
