"""Composition root of protocol v4's pack (story G10 part 2): the day's release run (A4e's v4 capture, G1 v2's live IV30
rule, O9's data store), the verified Drive cache behind the released packs, and GitHub's push receipts behind the
15:10 deadline."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from datetime import date, timedelta
from pathlib import Path

from ..ai.receipts import GitHubActivityReceipts
from ..config import ROOT
from ..constants import ENV_GITHUB_TOKEN, GITHUB_REPOSITORY_VARIABLE
from ..health.evidence import Evidence, HealthHistory
from ..storage.data_wiring import DATA_AREA, build_data_store, build_drive_cache
from .commitment import CommitmentTimes, GitHubCommitmentTimes
from .release import ReleasedPacks
from .release_run import ReleaseRun

V4_CAPTURE_WINDOW = "v4"  # A4e's named window in config.yaml (quotes.windows.v4)
RELEASE_WRITER = "v4-release"
IV30_METHOD = "g1_v2_live_atm_iv30"
IV30_METHOD_FILES = ("research_engine/live_features.py", "forecast/iv30.py")  # G1 v2's live ATM rule and interpolation


def iv30_method() -> str:
    """The IV30 method's name and the SHA-256 of its files' bytes, carried in every pack."""
    package = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256(b"".join((package / name).read_bytes() for name in IV30_METHOD_FILES)).hexdigest()
    return f"{IV30_METHOD}/sha256:{digest}"


def build_release_run(cfg: dict, env: Mapping[str, str] = os.environ) -> ReleaseRun:
    from ..daily.wiring import live_dates
    from ..forecast_v4.sessions import is_scored_session
    from ..models import now_ist
    from ..quotes.recorder import DATASET
    from ..quotes.window import named_window
    from ..research_engine.implied_vol import Black76
    from ..research_engine.live_features import LiveAtmIvMinusRealised
    from ..storage.quote_wiring import build_drive_only_quote_store
    from ..storage.wiring import QUOTES_FOLDER, build_session_calendar
    from .builder import PackBuilder
    from .capture import StoredV4Capture

    dataset = named_window(cfg, V4_CAPTURE_WINDOW).dataset(DATASET)
    capture = StoredV4Capture(build_drive_only_quote_store(QUOTES_FOLDER, env, dataset=dataset), dataset)
    rule = LiveAtmIvMinusRealised(None, cfg["risk_free_rate"], Black76())
    calendar, store = build_session_calendar(), build_data_store(RELEASE_WRITER, env=env)

    def sessions(first: date, last: date) -> list[date]:
        days = (first + timedelta(days=n) for n in range((last - first).days + 1))
        return [day for day in days if is_scored_session(calendar, day)]

    builder, live_from = PackBuilder(rule, iv30_method(), now_ist), live_dates(cfg)["forecasts_v4"]
    in_drive = lambda path: store.drive.get(path) is not None  # noqa: E731
    return ReleaseRun(store, in_drive, capture, builder, sessions, live_from, now_ist)


def build_released_packs(env: Mapping[str, str] = os.environ) -> ReleasedPacks:
    return ReleasedPacks(build_drive_cache(env), DATA_AREA)


def build_commitment_times(root: Path = ROOT, env: Mapping[str, str] = os.environ) -> CommitmentTimes:
    history = HealthHistory(Path(root))
    receipts = GitHubActivityReceipts(env.get(GITHUB_REPOSITORY_VARIABLE, ""), env.get(ENV_GITHUB_TOKEN, ""), history)
    return GitHubCommitmentTimes(Evidence(Path(root), history, receipts))
