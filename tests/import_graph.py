"""One reading of a module's imports for the boundary tests: every `import x` and `from x import y` (relative ones
resolved against the file's package) as a full dotted module name."""

import ast
from pathlib import Path

from fno.config import ROOT


def full_imports(path: Path, package: str | None = None) -> set[str]:
    """`package`: the file's package when it is not under the repository (a test's planted file)."""
    package = package or ".".join(path.relative_to(ROOT).with_suffix("").parts[:-1])
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = package.rsplit(".", node.level - 1)[0] if node.level else ""
            module = ".".join(p for p in (base, node.module or "") if p)
            found |= {module} | {f"{module}.{alias.name}" for alias in node.names}  # `from fno import checks`
    return found


def refused(modules: set[str], prefixes: tuple[str, ...]) -> set[str]:
    """The modules equal to a refused name or inside a refused package."""
    return {m for m in modules if any(m == p or m.startswith(p + ".") for p in prefixes)}
