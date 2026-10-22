"""Composition root of story MS-P1m, the market school's margins per trade: A9's Drive archive of beginning-of-day
SPAN files and its manifest, A14's exposure rule and C2's factor file from `config.yaml`. Drive is reached on first use,
so building it needs no settings (the school builds its fleet before any session is checked)."""

from __future__ import annotations

import os
from datetime import date

from ..config import ROOT
from ..risk.inputs import RiskInputError
from ..risk.settings import risk_settings
from ..risk.stress_factor import FactorRow, factor_in_force
from ..storage import wiring as storage
from ..storage.raw_source import NseSpanBodSource
from .calculator import NseIndexOptionExposure
from .road_margin import ArchivedSpanMargin, ArchivedSpanSource
from .wiring import build_drive_span_files

NO_FACTOR_FILE = "school margin: risk.stressed_margin.factor_file is not set"


def build_road_margin(cfg: dict, env=os.environ) -> ArchivedSpanMargin:
    stressed = risk_settings(cfg, ROOT).stressed_margin

    def factor(day: date) -> FactorRow:
        if stressed.factor_file is None:
            raise RiskInputError(NO_FACTOR_FILE)
        return factor_in_force(stressed.factor_file, day, stressed.max_age_days)

    def manifest() -> dict[date, str]:
        return {f.day: f.sha256 for f in storage.build_manifest_folder().read(NseSpanBodSource)}

    def day_file(day: date) -> tuple[str, bytes | None]:  # one Drive session per call: the margin keeps each day's file
        return build_drive_span_files(env)(day)

    return ArchivedSpanMargin(ArchivedSpanSource(day_file, manifest, NseIndexOptionExposure(), factor))
