"""Broken-code proof (quality rule 4): each planted bug in `mutations.json` must make its named test fail.

    python research/2026-10-15-r2-stock-options-results/mutation_proof.py    (from the repository root)

Each file is restored after its run. No bytecode is written (a stale .pyc would hide a mutation), and only pytest's
exit code 1 (a failing test) counts as caught; any other code (no such test, a crash) is reported.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PYTEST = [sys.executable, "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"]


def main() -> int:
    mutations = json.loads((HERE / "mutations.json").read_text())
    caught = 0
    for m in mutations:
        path = HERE / "r2study" / m["file"]
        text = path.read_text()
        if text.count(m["old"]) != 1:
            print(f"NOT APPLIED {m['file']}: {m['old'][:60]!r}")
            continue
        path.write_text(text.replace(m["old"], m["new"]))
        try:
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            run = subprocess.run([*PYTEST, f"tests/research/{m['test']}"], cwd=ROOT, capture_output=True, env=env)
        finally:
            path.write_text(text)
        caught += run.returncode == 1
        verdict = {0: "MISSED", 1: "caught"}.get(run.returncode, f"ERROR {run.returncode}")
        print(f"{verdict} {m['file']}: {m['old'][:60]!r} -> {m['test'].split('::')[1][:60]}")
    print(f"{caught} of {len(mutations)} mutations caught")
    return 0 if caught == len(mutations) else 1


if __name__ == "__main__":
    raise SystemExit(main())
