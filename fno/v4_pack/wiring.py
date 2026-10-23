"""Composition root of protocol v4's pack (story G10 part 2): the verified Drive cache behind the released packs, and
GitHub's push receipts behind the 15:10 deadline."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from ..ai.receipts import GitHubActivityReceipts
from ..config import ROOT
from ..constants import ENV_GITHUB_TOKEN, GITHUB_REPOSITORY_VARIABLE
from ..health.evidence import Evidence, HealthHistory
from ..storage.data_wiring import DATA_AREA, build_drive_cache
from .commitment import CommitmentTimes, GitHubCommitmentTimes
from .release import ReleasedPacks


def build_released_packs(env: Mapping[str, str] = os.environ) -> ReleasedPacks:
    return ReleasedPacks(build_drive_cache(env), DATA_AREA)


def build_commitment_times(root: Path = ROOT, env: Mapping[str, str] = os.environ) -> CommitmentTimes:
    history = HealthHistory(Path(root))
    receipts = GitHubActivityReceipts(env.get(GITHUB_REPOSITORY_VARIABLE, ""), env.get(ENV_GITHUB_TOKEN, ""), history)
    return GitHubCommitmentTimes(Evidence(Path(root), history, receipts))
