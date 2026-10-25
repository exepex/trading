"""Book 3's composition root (stories F6 and F7) builds on the repository as it stands, and criterion 16's structural
half: proposals are registered only inside the decider's `decide`, which F1t calls only for a promoted answer (the
test through F1t's judging follows when F1t's code exists)."""

import ast
import hashlib
from pathlib import Path

from fno.book3 import decision_wiring
from fno.book3.decider import Book3Decider
from fno.book3.orders import Book3Orders
from fno.book3.shadow_reader import Book3ShadowReader
from fno.books.book1_exits import PlaybookExitRules
from fno.config import ROOT, load_app_config


def test_every_book3_part_builds_on_the_repository():
    cfg = load_app_config()
    assert isinstance(decision_wiring.build_book3_decider(cfg), Book3Decider)
    assert isinstance(decision_wiring.build_book3_orders(cfg), Book3Orders)
    assert isinstance(decision_wiring.build_book3_shadow_reader(cfg), Book3ShadowReader)
    assert isinstance(decision_wiring.build_book3_exit_rules(), PlaybookExitRules)


def test_the_prompt_is_hashed_from_its_file_and_the_playbook_is_read_for_rules_and_widths():
    prompt = (ROOT / decision_wiring.PROMPT_FILE).read_bytes()
    assert decision_wiring.prompt_sha256() == hashlib.sha256(prompt).hexdigest()
    assert "b0-monthly-sc-v1" in decision_wiring.playbook_rules().values()
    assert decision_wiring.playbook_widths(ROOT, "b0-monthly-sc", 1) == (300.0, 250.0, 200.0, 150.0, 100.0)
    assert decision_wiring.playbook_widths(ROOT, "no-such-version", 1) is None


def test_proposals_are_registered_only_inside_the_decider_s_decide():
    callers = []
    for path in sorted((Path(ROOT) / "fno").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for function in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            calls = [c for c in ast.walk(function) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)]
            if any(c.func.attr == "register_all" for c in calls):
                callers.append((path.relative_to(ROOT).as_posix(), function.name))
    assert callers == [("fno/book3/decider.py", "decide")]
