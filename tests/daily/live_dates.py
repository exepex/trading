"""The app's config with every O1 step's `daily.live_from` cleared: the input of each "not live" test, so the rule is
tested on its own and never on whatever the repository's config holds today (phase 1 goes live on 22 Oct 2026)."""

from __future__ import annotations

from fno.config import load_app_config


def without_live_dates(cfg: dict | None = None) -> dict:
    cfg = cfg or load_app_config()
    cleared = dict.fromkeys(cfg.get("daily", {}).get("live_from", {}) or {})
    return {**cfg, "daily": {**cfg.get("daily", {}), "live_from": cleared}}
