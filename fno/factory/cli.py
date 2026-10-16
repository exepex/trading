"""`python -m fno factory register | backfill | status | report` (story R1a). Research records only: nothing here
runs a test, opens an account or places an order."""

from __future__ import annotations

from datetime import date

from .constants import DEFAULT_ALPHA

EXIT_REFUSED = 2


def add_factory_parser(subparsers) -> None:
    factory = subparsers.add_parser("factory", help="the strategy factory: register idea cards, show the trial count")
    actions = factory.add_subparsers(dest="factory_cmd", required=True)
    register = actions.add_parser("register", help="G0: write the card's ledger row and its gate-log row (commit them)")
    register.add_argument("idea_id")
    register.add_argument("--on", type=date.fromisoformat, default=None, help="registration date (default: today)")
    backfill = actions.add_parser("backfill", help="the `idea` row of a card registered by hand before R1's code")
    backfill.add_argument("idea_id")
    status = actions.add_parser("status", help="one idea's trial k of K and its last gate")
    status.add_argument("idea_id")
    report = actions.add_parser("report", help="every idea's trial k of K and last gate, and expected false passes")
    report.add_argument("--alpha", type=float, default=DEFAULT_ALPHA, help="one-sided pass level (default 0.01)")
    factory.set_defaults(func=cmd_factory)


def cmd_factory(args) -> int:
    from .card import CardError
    from .gate_log import GateLogError
    from .registration import RegistrationError

    try:
        lines = _COMMANDS[args.factory_cmd](args)
    except (CardError, GateLogError, RegistrationError) as refused:
        print(f"refused: {refused}")
        return EXIT_REFUSED
    print("\n".join(lines))
    return 0


def _register(args) -> list[str]:
    from .wiring import build_registration, read_idea

    files = build_registration().register(read_idea(args.idea_id), args.on or date.today())
    return [f"registered: {args.idea_id} (G0 idea); commit together: {' '.join(files)}"]


def _backfill(args) -> list[str]:
    from .wiring import build_registration, read_idea

    files = build_registration().backfill(read_idea(args.idea_id))
    return [f"back-filled: {args.idea_id} (G0 idea); commit together: {' '.join(files)}"]


def _status(args) -> list[str]:
    from .status import idea_line
    from .wiring import build_gate_log, build_trial_count, read_idea

    card, gates = read_idea(args.idea_id), build_gate_log()
    gates.require_append_only()
    return [idea_line(card, build_trial_count(), gates.last(card.trial_id))]


def _report(args) -> list[str]:
    from .status import false_pass_line, idea_line
    from .wiring import build_gate_log, build_trial_count, read_all_ideas

    cards, gates, count = read_all_ideas(), build_gate_log(), build_trial_count()
    gates.require_append_only()
    passes = count.false_passes(args.alpha, (card.trial_id for card in cards if card.measurement))
    return [false_pass_line(count, passes), *(idea_line(card, count, gates.last(card.trial_id)) for card in cards)]


_COMMANDS = {"register": _register, "backfill": _backfill, "status": _status, "report": _report}
