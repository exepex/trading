"""`python -m fno news kick` (story A19, scope 7): run by `news-capture-kick.yml` on its crons and when a
news-capture run completes. It prints its decision; a stopped restart is one row in O10's log and one alert."""

from __future__ import annotations

import os

from .kick import DISPATCH, STOPPED, decide

DECIDED = "kick: {action}: {reason}"
NOT_STARTED = "kick: news-capture NOT started: {problem}"


def add_kick_parser(actions) -> None:
    kick = actions.add_parser("kick", help="start news-capture when none is alive (cron or a completed run)")
    kick.set_defaults(func=cmd_kick)


def cmd_kick(args, out=print, parts=None) -> int:
    from .github_runs import GitHubError, read_event
    from .names import RESTART_STOPPED

    parts = parts or _real_parts()
    runs, episodes = parts["runs"], parts["episodes"]
    event = parts.get("event", read_event(os.environ.get("GITHUB_EVENT_PATH")))
    try:
        completed = runs.completed(event) if "workflow_run" in event else None
        decision = decide(parts["clock"](), parts["window"], parts["bridge"], runs.active_count(), completed)
        out(DECIDED.format(action=decision.action, reason=decision.reason))
        if decision.action == STOPPED:
            episodes.event(RESTART_STOPPED, RESTART_STOPPED, f"Omenix F&O news: {decision.reason} ({completed.url})")
            out(parts["committer"].commit("news capture: restart stopped"))
        elif decision.action == DISPATCH:
            runs.dispatch()
    except GitHubError as problem:
        out(NOT_STARTED.format(problem=problem))
        return 1
    return 0


def _real_parts() -> dict:
    from .wiring import build_committer, build_episodes, build_settings, build_window, build_workflow_runs, now_utc

    settings = build_settings()
    return {"runs": build_workflow_runs(), "episodes": build_episodes(), "window": build_window(settings),
            "bridge": settings.overnight_bridge, "committer": build_committer(), "clock": now_utc}  # fmt: skip
