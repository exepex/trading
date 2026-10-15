"""Story D3b criterion 6: scoreboard B lists the runs the desk saw but did not collect, corrections included, apart
(`uncollected_runs`), and its scored figures are the same with or without them."""

import json

from fno.constants import BOOK1_RULES, BOOKS
from fno.desk.run_log import RUNS_FOLDER

from .test_whole_system import START, build, history

FIXES = [{"corrects": {"run_id": f"{START}-r1", "opportunity_id": "o"}, "reason": "lot size"}]
CORRECTION = {"run_id": f"{START}-r2", "commit": "c9", "committed_at": f"{START}T15:08:00+05:30", "corrections": FIXES}


def with_others(root, others):
    path = root / "journal" / RUNS_FOLDER / f"{START.isoformat()}.json"
    body = json.loads(path.read_text())
    body["steps"]["decisions"]["result"][BOOK1_RULES]["others"] = others
    path.write_text(json.dumps(body))


def test_a_correction_is_listed_apart_and_changes_no_scored_figure(tmp_path):
    root = history(tmp_path)
    before = build(root)
    assert before["uncollected_runs"] == {book: [] for book in BOOKS}
    with_others(root, [CORRECTION])
    after = build(root)
    assert after["uncollected_runs"][BOOK1_RULES] == [{"day": START.isoformat(), **CORRECTION}]
    assert after["books"] == before["books"] and after["common_start"] == before["common_start"]
