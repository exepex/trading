"""Story A16c: one server-clock module (`fno/server_clock.py`) for T1 and A16, with no copy or shim left behind (DRY;
judge 108 addendum 3 should-fix 2 and its follow-up)."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_t1_and_a16_import_the_one_server_clock_module_and_no_copy_exists():
    assert not (ROOT / "fno" / "cards" / "clock.py").exists()
    users = {}
    for module in (
        "fno/cards/issue.py",
        "fno/cards/wiring.py",
        "fno/intraday/clock.py",
        "fno/intraday/clock_wiring.py",
    ):
        tree = ast.parse((ROOT / module).read_text(encoding="utf-8"))
        users[module] = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert all("server_clock" in modules for modules in users.values()), users
    defined = [p.relative_to(ROOT).as_posix() for p in (ROOT / "fno").rglob("*.py")
               if "class HttpDateClock" in p.read_text(encoding="utf-8")]  # fmt: skip
    assert defined == ["fno/server_clock.py"]
