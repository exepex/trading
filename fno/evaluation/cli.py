"""`python -m fno evaluation check|freeze|order` (story S1).
- `check` runs the completeness check; `--decided` also requires every item decided by the owner.
- `freeze` writes the freeze record and registers the protocol in the ledger; commit both at once.
- `order` checks that the freeze precedes each book's first counted decision.
- `verify` checks that the latest freeze's files and settings are unchanged (a suite test runs it).
None of them computes a result or places an order."""

from __future__ import annotations

from datetime import date

from ..constants import BOOKS

EXIT_FAILED = 2


def add_evaluation_parser(subparsers) -> None:
    evaluation = subparsers.add_parser("evaluation", help="the evaluation protocol of the three books (story S1)")
    actions = evaluation.add_subparsers(dest="evaluation_cmd", required=True)
    check = actions.add_parser("check", help="completeness check of research/evaluation/PROTOCOL.md")
    check.add_argument("--decided", action="store_true", help="also require every item decided by the owner")
    actions.add_parser("freeze", help="freeze the decided protocol (commit the record and the ledger at once)")
    actions.add_parser("verify", help="the latest freeze's files and settings are unchanged")
    order = actions.add_parser("order", help="the freeze precedes each book's first counted decision")
    order.add_argument("--version", type=int, default=1)
    order.add_argument("--common-start", type=date.fromisoformat, help="without it every decision counts")
    evaluation.set_defaults(func=cmd_evaluation)


def _check(decided: bool) -> int:
    from ..config import ROOT
    from .completeness import completeness_problems, undecided_items
    from .protocol import PROTOCOL_FILE, parse_protocol

    text = (ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")
    protocol = parse_protocol(text)
    problems = completeness_problems(text, protocol)
    undecided = undecided_items(protocol) if decided else []
    for problem in problems:
        print(f"incomplete: {problem}")
    if undecided:
        print(f"not decided by the owner ({len(undecided)}): {', '.join(undecided)}")
    if problems or undecided:
        return EXIT_FAILED
    print(f"{PROTOCOL_FILE} version {protocol.version}: complete" + (" and decided" if decided else ""))
    return 0


def _freeze() -> int:
    from .freeze import FreezeRefused, freeze_path
    from .wiring import build_freezer

    try:
        record = build_freezer().freeze(date.today())
    except FreezeRefused as refused:
        print(f"not frozen: {refused}")
        return EXIT_FAILED
    print(f"wrote {freeze_path(record.version)} ({len(record.hashes)} targets) and its ledger row: commit both now")
    return 0


def _order(version: int, common_start: date | None) -> int:
    from ..config import ROOT
    from .order import first_counted_decision, order_problems
    from .wiring import build_protocol_git

    git = build_protocol_git()
    firsts = [first_counted_decision(ROOT, git, book, common_start) for book in BOOKS]
    problems = order_problems(git, version, [f for f in firsts if f is not None])
    for problem in problems:
        print(f"out of order: {problem}")
    if not problems:
        print(f"v{version}: the freeze precedes every counted decision ({sum(f is not None for f in firsts)} books)")
    return EXIT_FAILED if problems else 0


def _verify() -> int:
    from ..config import ROOT
    from .order import verify

    problems = verify(ROOT)
    for problem in problems:
        print(f"changed: {problem}")
    if not problems:
        print("the latest freeze's files and settings are unchanged (or nothing is frozen yet)")
    return EXIT_FAILED if problems else 0


def cmd_evaluation(args) -> int:
    if args.evaluation_cmd == "check":
        return _check(args.decided)
    if args.evaluation_cmd == "verify":
        return _verify()
    if args.evaluation_cmd == "freeze":
        return _freeze()
    return _order(args.version, args.common_start)
