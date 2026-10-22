"""Mutation proof of the EDGE1 tests (before the freeze): plants each bug below (edit, test, restore) and checks the
synthetic tests fail. `python research/edge1/mutation_proof.py`; restores every file even when a run fails."""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = HERE / "edge1study"
ROOT = HERE.parents[1]
M = [
    ("runner.py", "{d: q for d, q in panel.options.items() if d <= last}", "dict(panel.options)", "seal leaks options"),
    (
        "runner.py",
        "tuple(s for s in panel.sessions if s.day <= last)",
        "tuple(s for s in panel.sessions if s.day <= date(last.year, last.month + 1, last.day))",
        "seal loosened for sessions",
    ),  # fmt: skip
    ("inputs.py", "[r for r in found if r.day <= through]", "list(found)", "rows not sealed at load"),
    ("trade.py", "STOP_MULTIPLE, TARGET_SHARE = 3.0, 0.5", "STOP_MULTIPLE, TARGET_SHARE = 2.0, 0.5", "SL2 at 2x"),
    ("trade.py", "STOP_MULTIPLE, TARGET_SHARE = 3.0, 0.5", "STOP_MULTIPLE, TARGET_SHARE = 3.0, 0.4", "TP at 40%"),
    (
        "trade.py",
        "if not _all_traded(prices) or not _possible(",
        "if not _possible(",
        "trigger fires on an untraded leg",
    ),  # fmt: skip
    (
        "trade.py",
        "return all(p.price is not None and not p.on_settlement for p in prices)",
        "return all(p.price is not None for p in prices)",
        "settlement proxy counts as traded",
    ),  # fmt: skip
    (
        "trade.py",
        "_terms_on(terms, exit_day, charges_on)",
        "_terms_on(terms, cycle.entry_day, charges_on)",
        "exit charged at the entry date's STT",
    ),  # fmt: skip
    ("trade.py", "gross - charges - entry_pads)", "gross - charges - 2 * entry_pads)", "an exit pad at settlement"),
    ("stats.py", "means - observed >= observed", "means >= observed", "p not re-centred"),
    ("stats.py", "BLOCK, RESAMPLES, ALPHA = 2,", "BLOCK, RESAMPLES, ALPHA = 1,", "block of 1"),
    ("stats.py", "MIN_TESTED, MIN_RUN1 = 30, 20", "MIN_TESTED, MIN_RUN1 = 20, 20", "test floor 20"),
    ("stats.py", "MIN_TESTED, MIN_RUN1 = 30, 20", "MIN_TESTED, MIN_RUN1 = 30, 5", "G1 floor 5"),
    ("stats.py", "holm([p_values[n] for n in names], ALPHA)", "[p_values[n] < ALPHA for n in names]", "no Holm"),
    ("stats.py", 'r["holm"] and r["mean_net_pad2"] > 0 and', 'r["holm"] and', "nomination without the Rs 2 pad"),
    ("stats.py", "[:limit]", "", "more than two nominated"),
    ("stats.py", "if t.taken and not t.incomplete_exit]", "if t.taken]", "incomplete exits in the decided mean"),
    (
        "runs.py",
        'if chosen["tradeable"] and not chosen.get("g1", {}).get("passed"):',
        "if False:",
        "run 2 tests G1 failures",
    ),  # fmt: skip
    ("runs.py", 'tested[name] = row["p"]', 'tested[name] = row["p"] if False else 0.0', "p ignored by Holm"),
    ("stt_history.py", "(date(2023, 4, 1), 0.0625, 0.125)", "(date(2023, 3, 1), 0.0625, 0.125)", "STT date moved"),
    ("stt_history.py", "(date(2024, 10, 1), 0.1, 0.125)", "(date(2024, 10, 1), 0.1, 0.15)", "exercise STT early"),
    ("day_files.py", "if board > 0:\n            lots.setdefault(expiry, board)\n", "", "board lot ignored"),
    ("day_files.py", "q.expiry in monthly", "True", "weekly options kept"),
    ("lots.py", "(date(2023, 7, 1), 15,", "(date(2023, 8, 1), 15,", "lot change a month late"),
    ("lots.py", "dict(r.lots) if r.source == UDIFF else", "dict(r.lots) if True else", "derived lot used as the lot"),
    ("expiries.py", "if key not in last or day > last[key][0]:", "if key not in last:", "first date kept, not last"),
    ("expiries.py", "if q.expiry in moved else q", "if True else q", "weeklies relabelled too"),
    (
        "trade.py",
        "if not _all_traded(prices) or not _possible(legs, [p.price for p in prices]):",
        "if not _all_traded(prices):",
        "a trigger fires on an impossible mark",
    ),  # fmt: skip
    ("trade.py", "incomplete = impossible or any(", "incomplete = any(", "an impossible exit in the decided mean"),
    ("margin.py", "if span.created >= datetime.combine", "if span.created > datetime.combine", "09:00 file allowed"),
    ("margin.py", "if hashlib.sha256(data).hexdigest() != sha256[day]:", "if False:", "no first-copy check"),
    (
        "guard.py",
        'if (root / final).exists() or git(root, "log", "--all", "--format=%H", "--", final).strip():',
        "if (root / final).exists():",
        "a deleted final.json allows a second look",
    ),  # fmt: skip
    ("report.py", "if t.incomplete_exit]", "if False]", "incomplete exits not counted"),
    ("structures.py", "SC3: ShortCondor(0.03)", "SC3: ShortCondor(0.02)", "SC3 is SC2"),
]


def main() -> int:
    env = {k: v for k, v in os.environ.items() if k != "FNO_SLACK_BOT_TOKEN"} | {"PYTHONDONTWRITEBYTECODE": "1"}
    failures = 0
    for name, old, new, label in M:
        path = S / name
        text = path.read_text()
        if text.count(old) != 1:
            print(f"NOT PLANTED ({text.count(old)} matches): {label}")
            failures += 1
            continue
        path.write_text(text.replace(old, new))
        try:
            command = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", "tests/research_edge1"]
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=env)
            caught = run.returncode != 0
            print(("caught   " if caught else "SURVIVED ") + label)
            failures += not caught
        finally:
            path.write_text(text)
    planted = len(M)
    print(f"{planted - failures} of {planted} planted bugs caught")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
