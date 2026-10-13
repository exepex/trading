"""`python -m fno research run <experiment> --period discovery|challenge` (story B3): runs a registered experiment's
period and writes research/<experiment>/results_<period>.json and .md. The decisive period (the challenge) runs only
with its frozen protocol and then records the first run in the ledger (commit it with the results)."""

from __future__ import annotations

from ..constants import PERIOD_CHALLENGE, PERIOD_DISCOVERY
from .experiment_1 import EXPERIMENT_1

EXPERIMENTS = {EXPERIMENT_1.folder: EXPERIMENT_1}


def add_research_parser(subparsers) -> None:
    research = subparsers.add_parser("research", help="run a registered experiment's period (story B3)")
    actions = research.add_subparsers(dest="research_cmd", required=True)
    run = actions.add_parser("run", help="run every policy and control of one period and write its results")
    run.add_argument("experiment", choices=sorted(EXPERIMENTS))
    run.add_argument("--period", required=True, choices=[PERIOD_DISCOVERY, PERIOD_CHALLENGE])
    research.set_defaults(func=cmd_research)


def cmd_research(args) -> int:
    from ..composition import build_experiment_runner, build_ledger
    from ..config import ROOT, load_app_config
    from .ledger import NotRegistered
    from .results_file import write_results
    from .trial_guard import ProtocolNotFrozen

    experiment = EXPERIMENTS[args.experiment]
    try:
        document = build_experiment_runner(load_app_config(args.config)).run(experiment, args.period)
    except (NotRegistered, ProtocolNotFrozen) as refusal:
        print(f"refused: {refusal}")
        return 2
    paths = write_results(ROOT / "research" / experiment.folder, document)
    print("wrote " + " and ".join(str(p.relative_to(ROOT)) for p in paths))
    if experiment.period(args.period).decisive:
        ledger = build_ledger()
        for trial_id in experiment.trial_ids:
            ledger.mark_run(trial_id)
        print("first run recorded in research/ledger.csv: commit it with the results")
    return 0
