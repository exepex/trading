"""The gate for paper decisions on live features (story B7 criterion 3): a playbook strategy may reach status `paper`
only if every live feature it uses is validated under its frozen use rule. Story D1's playbook loader calls this; the
validation evidence is the committed report of each live feature (`python -m fno research validate-live`)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path


class LiveFeaturesNotValidated(ValueError):
    """The strategy uses a live feature without a passing validation report."""


def unvalidated(live_features: Sequence[str], validated: Mapping[str, bool]) -> list[str]:
    """The live features with no report or a report that does not pass."""
    return [name for name in live_features if not validated.get(name, False)]


def require_validated(strategy: str, live_features: Sequence[str], validated: Mapping[str, bool]) -> None:
    missing = unvalidated(live_features, validated)
    if missing:
        raise LiveFeaturesNotValidated(f"{strategy} cannot reach status paper: live features not validated: {missing}")


def validated_from_reports(folder: Path) -> dict[str, bool]:
    """Live feature name -> whether its committed validation report passes its use rule."""
    reports = (json.loads(path.read_text(encoding="utf-8")) for path in sorted(folder.glob("*.json")))
    return {report["live_feature"]: report["validated"] is True for report in reports}
