"""Configuration loading with defaults merged from config.yaml."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "config.yaml"


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


PROFILE_KEY = "profile"
PROFILES_KEY = "profiles"


def load_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict:
    """config.yaml, then the active profile's overrides (e.g. `paper` or `live`), then any explicit overrides."""
    path = Path(path) if path else DEFAULT_CONFIG_PATH
    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    profiles = cfg.pop(PROFILES_KEY, {}) or {}
    active = (overrides or {}).get(PROFILE_KEY) or cfg.get(PROFILE_KEY)
    if active and active not in profiles:
        raise ValueError(f"Unknown profile '{active}'. Known: {', '.join(sorted(profiles)) or 'none'}")
    if active:
        cfg = _merge(cfg, profiles[active])
    return _merge(cfg, overrides or {})
