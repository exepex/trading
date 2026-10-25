"""Story GB1: write the branch inventory, one row per remote branch with its decision and the reason.

    python tools/branch_inventory.py --open-prs open_prs.txt     # one head branch per line; writes the CSV

The CSV is what `branch_cleanup.py --mode inventory` deletes from, and only rows marked `delete` whose head still
matches `sha`. Run it on a fresh `git fetch origin` of every branch.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from branch_git import KEEP_LIST, REGISTER, ROOT, open_pr_heads, read_branches
from branch_rules import RECENT, Evidence, inventory_decision, mentioned, parse_keep_list, register_branches

INVENTORY = ROOT / "docs" / "branch_inventory.csv"
COLUMNS = ["branch", "sha", "last_commit_utc", "merged", "commits_not_on_main", "decision", "reason"]
WRITTEN_DIRS = ("reviews", "conversations", "docs")  # files here that were written lately name the branches in use


def recent_text(now: datetime) -> str:
    since = (now - RECENT).isoformat()
    log = subprocess.run(
        ["git", "log", "origin/main", f"--since={since}", "--name-only", "--format=", "--", *WRITTEN_DIRS],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()  # fmt: skip
    skipped = {INVENTORY.relative_to(ROOT).as_posix(), REGISTER.relative_to(ROOT).as_posix()}
    files = {ROOT / name for name in log if name not in skipped}
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files if path.is_file())


def build(open_prs: frozenset[str], now: datetime) -> list[list[str]]:
    branches = read_branches(with_code=True)
    text = recent_text(now)
    evidence = Evidence(
        keep_list=parse_keep_list(KEEP_LIST.read_text(encoding="utf-8")),
        register=register_branches(REGISTER.read_text(encoding="utf-8")),
        open_prs=open_prs,
        recent_mentions=mentioned([b.name for b in branches], text),
    )
    rows = []
    for branch in sorted(branches, key=lambda b: b.name):
        decision, reason = inventory_decision(branch, evidence, now)
        stamp = branch.tip_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        rows.append(
            [branch.name, branch.sha, stamp, "yes" if branch.merged else "no", str(branch.ahead), decision, reason]
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open-prs", type=Path, required=True, help="file with one open pull request head per line")
    parser.add_argument("--now", help="UTC time to judge by, ISO (default: now)")
    args = parser.parse_args(argv)
    now = datetime.fromisoformat(args.now).astimezone(UTC) if args.now else datetime.now(UTC)
    rows = build(open_pr_heads(args.open_prs.read_text(encoding="utf-8")), now.replace(microsecond=0))
    with INVENTORY.open("w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    counts = {d: sum(1 for r in rows if r[5] == d) for d in ("delete", "keep", "keep-unsure")}
    print(f"{len(rows)} branches: {counts} (as of {now:%Y-%m-%d %H:%M} UTC; window {timedelta(hours=48)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
