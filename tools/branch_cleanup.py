"""Story GB1: delete remote branches, by one of two rules. Dry run unless `--apply`. Never deletes `main`.

    python tools/branch_cleanup.py --mode inventory     # the committed docs/branch_inventory.csv, rows marked delete
    python tools/branch_cleanup.py --mode merged        # the standing rule: merged 24 h ago, week-old rehearsals

Both modes re-check every branch against GitHub right now before deleting it: the head must be the one the plan was
made from (inventory mode: the CSV's `sha`), and no keep-list line, register row or open pull request may name it.
Exit 1 when a deletion failed. Deleting needs `GH_TOKEN` and `GITHUB_REPOSITORY` (the workflow's own token).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from branch_git import KEEP_LIST, REGISTER, delete_remote_branch, open_pr_heads, read_branches, remote_heads
from branch_inventory import INVENTORY
from branch_rules import DELETE, Branch, Evidence, ongoing_decision, parse_keep_list, protection, register_branches

Plan = list[tuple[str, str, str, bool]]  # (branch, expected head sha, reason, merged into main)


def evidence(open_prs: frozenset[str]) -> Evidence:
    return Evidence(
        keep_list=parse_keep_list(KEEP_LIST.read_text(encoding="utf-8")),
        register=register_branches(REGISTER.read_text(encoding="utf-8")),
        open_prs=open_prs,
    )


def inventory_plan(path: Path) -> Plan:
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    names = [row["branch"] for row in rows]
    if len(set(names)) != len(names):
        raise SystemExit(f"{path.name}: a branch is listed twice")
    return [(r["branch"], r["sha"], r["reason"], r["merged"] == "yes") for r in rows if r["decision"] == DELETE]


def merged_plan(held: Evidence, now: datetime) -> Plan:
    decided = [(b, *ongoing_decision(b, held, now)) for b in read_branches()]
    return [(b.name, b.sha, why, b.merged) for b, action, why in decided if action == DELETE]


def refusal(name: str, expected: str, merged: bool, held: Evidence, head: str | None) -> str | None:
    """Why this branch must not be deleted now; None when it may go."""
    stub = Branch(name, expected, datetime.min.replace(tzinfo=UTC), merged, 0)
    if protection(stub, held):
        return protection(stub, held)
    if head is None:
        return "already gone"
    if head != expected:
        return f"head moved: planned {expected[:10]}, now {head[:10]}"
    return None


def run(plan: Plan, held: Evidence, apply: bool, delete: Callable[[str], None], heads: dict[str, str]) -> int:
    failed = 0
    for name, sha, reason, merged in plan:
        why_not = refusal(name, sha, merged, held, heads.get(name))
        if why_not:
            print(f"SKIP   {name}: {why_not}")
            continue
        if not apply:
            print(f"WOULD DELETE {name} {sha[:10]}: {reason}")
            continue
        try:
            delete(name)
            print(f"DELETED {name} {sha[:10]}: {reason}")
        except RuntimeError as error:
            failed += 1
            print(f"FAILED {name}: {error}")
    print(f"{'applied' if apply else 'dry run'}: {len(plan)} planned, {failed} failed")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("inventory", "merged"), required=True)
    parser.add_argument("--inventory", type=Path, default=INVENTORY)
    parser.add_argument("--apply", action="store_true", help="delete for real (default: print what would go)")
    parser.add_argument("--open-prs", type=Path, required=True, help="file with one open pull request head per line")
    args = parser.parse_args(argv)
    held = evidence(open_pr_heads(args.open_prs.read_text(encoding="utf-8")))
    now = datetime.now(UTC)
    plan = inventory_plan(args.inventory) if args.mode == "inventory" else merged_plan(held, now)
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if args.apply and not repo:
        raise SystemExit("--apply needs GITHUB_REPOSITORY (the workflow sets it)")
    return run(plan, held, args.apply, lambda name: delete_remote_branch(repo, name), remote_heads())


if __name__ == "__main__":
    sys.exit(main())
