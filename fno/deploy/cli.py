"""`python deploy/desk.py deploy <command>`: the same commands on Windows, Linux and macOS."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..config import ROOT
from ..models import IST
from .desk_process import DeskProcess
from .git_sync import end_of_day_sync
from .jobs import desk_jobs
from .schedulers import scheduler_for_this_machine

ENTRY_SCRIPT = ROOT / "deploy" / "desk.py"
STATE_DIR = ROOT / "data" / "live" / "state"
LOG_DIR = ROOT / "logs"


def add_deploy_parser(subparsers) -> None:
    deploy = subparsers.add_parser("deploy", help="run the desk unattended on this machine (any OS)")
    actions = deploy.add_subparsers(dest="deploy_cmd", required=True)
    actions.add_parser("install", help="register the watchdog and end-of-day jobs, and start the desk")
    actions.add_parser("uninstall", help="remove the jobs and stop the desk")
    actions.add_parser("ensure-running", help="start the desk if it is not running (the watchdog job)")
    actions.add_parser("stop", help="stop the desk (the watchdog starts it again within minutes)")
    actions.add_parser("sync", help="save today's records to GitHub (the end-of-day job)")
    actions.add_parser("status", help="is the desk running, and which scheduler is used")
    deploy.set_defaults(func=run_deploy_command)


def run_deploy_command(args) -> int:
    now = datetime.now(IST)
    desk = DeskProcess(ROOT, STATE_DIR, LOG_DIR)
    scheduler = scheduler_for_this_machine()
    jobs = desk_jobs(Path(desk.python), ENTRY_SCRIPT)
    if args.deploy_cmd == "install":
        scheduler.install(jobs)
        print(f"Registered with {scheduler.name}: " + ", ".join(job.name for job in jobs))
        print(desk.ensure_running(now))
    elif args.deploy_cmd == "uninstall":
        scheduler.uninstall(jobs)
        print(f"Removed the jobs from {scheduler.name}. " + desk.stop())
    elif args.deploy_cmd == "ensure-running":
        print(desk.ensure_running(now))
    elif args.deploy_cmd == "stop":
        print(desk.stop())
    elif args.deploy_cmd == "sync":
        print(end_of_day_sync(ROOT, now.date()))
    elif args.deploy_cmd == "status":
        pid = desk.running_pid()
        print(f"Desk: {'running, pid ' + str(pid) if pid else 'not running'} · scheduler: {scheduler.name}")
        print(f"Logs: {LOG_DIR}")
    return 0
