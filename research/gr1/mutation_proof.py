"""Mutation proof of the GR1 tests (protocol section 12, step 2): plants each bug below (edit, test, restore) and
checks the synthetic tests fail. `python research/gr1/mutation_proof.py`; restores every file even when a run fails."""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = HERE / "gr1study"
ROOT = HERE.parents[1]
M = [
    ("periods.py", "or (final_open and period == FINAL)", "or period == FINAL", "seal broken: final rows in run 1"),
    ("rows.py", "sealed(dated, final_open)", "sealed(dated, True)", "rows not sealed at load"),
    ("scaling.py", "return tuple(m + s * (q - m)", "return tuple(s * q", "the centre moves"),
    ("scaling.py", "return 2 / len(LEVELS) * sum(", "return 1 / len(LEVELS) * sum(", "QS weight"),
    (
        "scaling.py",
        "return quantiles[band[0]] <= outcome <= quantiles[band[1]]",
        "return quantiles[band[0]] < outcome < quantiles[band[1]]",
        "coverage edges",
    ),  # fmt: skip
    (
        "fit.py",
        "    if any(abs(t) >= BOUND for t in theta):\n        return Fit(tuple(theta), FAILED_EDGE)\n",
        "",
        "no grid-edge failure",
    ),  # fmt: skip
    ("fit.py", "        if crosses(quantiles):\n            return math.inf\n", "", "crossings allowed in the fit"),
    ("candidates.py", "if announced < row.day", "if announced <= row.day", "event announced on the issue day"),
    ("candidates.py", "any(row.day < d <= row.target_day", "any(row.day <= d <= row.target_day", "horizon edge"),
    (
        "selection.py",
        "BAND_90, BAND_50 = (0.87, 0.93), (0.45, 0.55)",
        "BAND_90, BAND_50 = (0.85, 0.95), (0.45, 0.55)",
        "wider band",
    ),  # fmt: skip
    ("selection.py", "GAP_LIMIT = 0.05", "GAP_LIMIT = 0.10", "gap limit 10%"),
    ("selection.py", "if d is not None and d < 0}", "if d is not None}", "a worse candidate can win"),
    (
        "final.py",
        'significant = dict(zip(tested, holm_significant([cells[k]["p_value"] for k in tested]), strict=True))',
        'significant = {k: cells[k]["p_value"] < 0.05 for k in tested}',
        "no Holm",
    ),  # fmt: skip
    ("final.py", 'and checks["gap_ok"] and checks["narrower_90"])', 'and checks["gap_ok"])', "width not required"),
    (
        "guard.py",
        'if (root / final).exists() or git(root, "log", "--all", "--format=%H", "--", final).strip():',
        "if (root / final).exists():",
        "a deleted final.json allows a second look",
    ),  # fmt: skip
    (
        "cues.py",
        "row = value_for(usable, india_day, cutoff, False, source.available_at)",
        'row = max([r for r in usable if r["value_date"] <= india_day.isoformat()], key=lambda r: r["value_date"], '
        "default=None)",
        "raw value_date instead of A17's rule",
    ),  # fmt: skip
    ("cues.py", "return OPEN_CUTOFF if cue in DAY_BEFORE_CUES else cutoff", "return cutoff", "USD/INR of the day"),
    (
        "n0.py",
        "m, root = n1.quantiles[MEDIAN], math.sqrt(REMAINING_SHARE)",
        "m, root = n1.quantiles[MEDIAN], REMAINING_SHARE",
        "variance share as a scale",
    ),  # fmt: skip
    (
        "n0.py",
        "outcome = n1.outcome + math.log(n1.s_ref / open_)",
        "outcome = n1.outcome",
        "outcome not moved to 09:15",
    ),
    ("cues.py", 'if r["value_date"] not in held', "", "FBIL overrides RBI's own rate"),
    (
        "selection.py",
        'entry["reason"] = _train_gap(fitted_on) or _ineligible(sel)',
        'entry["reason"] = _ineligible(sel)',
        "no train gap rule",
    ),
    (
        "selection.py",
        "return [r for r in train if candidate.train_from is None or r.day >= candidate.train_from]",
        "return list(train)",
        "C8's 2020 start ignored",
    ),
    (
        "evaluate.py",
        "tuple(s - b for s, b in zip(scores, base, strict=True))",
        "tuple(b - s for s, b in zip(scores, base, strict=True))",
        "difference sign",
    ),  # fmt: skip
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
            run = subprocess.run([sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
                                  "tests/research_gr1"], cwd=ROOT, capture_output=True, text=True, env=env)  # fmt: skip
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
