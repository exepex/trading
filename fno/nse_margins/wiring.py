"""Composition root of story A14: the daily NSE margin job. The only place that picks its concrete parts: Drive's raw
area (the first archived `i1` file, A9; A11 keeps later versions apart), NSE's exposure rule for index options, B2's
structures (STR1's included) and research widths, the entry window's near edge, the margins table named in
`config.yaml` (a receipt-backed Drive series since O9b step 2) and #fno-desk. Story A14c's stress-factor run is wired
here too: the same archive and calculator, A9's manifest, the factor file from `config.yaml`, its evidence folder and
Drive for its evidence CSV (O9b step 2)."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from ..composition import build_alert_sender, build_tradable_structures
from ..config import ROOT
from ..constants import NIFTY_SYMBOL, STRUCTURES_BOUGHT_ONLY
from ..models import now_ist
from ..research_data.expiries import DAYS_TO_EXPIRY
from ..research_engine.cycle_costs import WIDTHS
from ..research_engine.cycles import TradingDays
from ..risk.settings import count_setting
from ..storage import wiring as storage
from ..storage.data_wiring import build_data_store, build_drive_cache
from ..storage.moving import move_into
from ..storage.raw_source import NseSpanBodSource
from ..storage.raw_store import AreaStore, RawFileStore
from ..storage.receipted_rows import ReceiptedRowLog, ReceiptedSnapshots
from ..storage.table_source import ReceiptedTable
from .broker_approvals import BrokerApprovals
from .calculator import NseIndexOptionExposure, SpanMarginCalculator
from .held_rise import HeldRiseTracker
from .job import DayFile, NseMarginJob, due_session
from .margin_log import MarginLog
from .prefetch import per_thread
from .rows import MarginRowBuilder
from .stress_log import StressFactorFile
from .stress_run import StressFactorRun, StressSources

DRIVE_SETTINGS_MISSING = f"set {', '.join(storage.OWNER_UPLOAD_SETTINGS)} to read the archived SPAN files in Drive"
STRESS_EVIDENCE = "research/data/margins/stress"  # one run's file list and Markdown (its CSV is in Drive, O9b)
MARGINS_WRITER, STRESS_WRITER = "nse-margins", "stress-factor"  # O9b step 2: the jobs writing Drive's data area
EVIDENCE_SERIES = "margins/stress-evidence/{day}"  # one run day's evidence CSV, a receipted snapshot
MARGINS_FILE = "research/data/margins/margins.csv"  # the repository copy, read only by `margins move` (O9b step 2)
EVIDENCE_CSV = "stress_evidence_*.csv"  # under STRESS_EVIDENCE: each run day's evidence CSV, moved by `margins move`


def archived_span_file(raw: RawFileStore) -> DayFile:
    """A day's beginning-of-day SPAN file as first archived in Drive (never fetched from NSE here)."""
    return lambda day: (NseSpanBodSource.filename_for(day), raw.get(NseSpanBodSource.path_for(day)))


def build_row_builder(cfg: dict) -> MarginRowBuilder:
    """Every tradable structure at every research width (LC and LP also at 0, the ATM strike), one NIFTY lot
    (`lot_sizes`), first monthly expiry 30+ days out."""
    calculator = SpanMarginCalculator(NseIndexOptionExposure(), cfg["lot_sizes"][NIFTY_SYMBOL])
    atm = dict.fromkeys(STRUCTURES_BOUGHT_ONLY, (0.0,))
    return MarginRowBuilder(build_tradable_structures(), WIDTHS, calculator, DAYS_TO_EXPIRY[0], atm)


def build_margin_log(cfg: dict, env=os.environ) -> MarginLog:
    """A14's margins table as a receipt-backed Drive series (O9b step 2), read and appended by this run."""
    table = cfg["risk"]["margins"]["table"]
    log = ReceiptedRowLog(build_data_store(MARGINS_WRITER, env=env), build_drive_cache(env), table)
    return MarginLog(ReceiptedTable(lambda: log, table), log)


def build_evidence_saver(env=os.environ):
    """A14c's evidence CSV of a run day into Drive with its receipt; the same bytes again write nothing (a rerun)."""

    def save(day: date, data: bytes) -> None:
        store, cache = build_data_store(STRESS_WRITER, env=env), build_drive_cache(env)
        series = ReceiptedSnapshots(store, cache, EVIDENCE_SERIES.format(day=day))
        if series.latest_bytes() != data:
            series.write_bytes(data)

    return save


def build_trading_days():
    return TradingDays(storage.build_session_calendar()).is_trading_day


def build_drive_span_files(env=os.environ) -> DayFile:
    drive = storage.build_owner_drive(env)
    if drive is None:
        raise RuntimeError(DRIVE_SETTINGS_MISSING)
    return archived_span_file(AreaStore(drive, storage.RAW_AREA))


def build_stress_factor_run(cfg: dict, run_day: date | None = None, env=os.environ, day_file: DayFile | None = None,
                            root: Path = ROOT) -> StressFactorRun:  # fmt: skip
    """Story A14c's run on Drive's archived files (or `day_file`), A9's manifest and the factor file in config; each
    download thread has its own Drive session (`risk.stressed_margin.recompute_workers` threads)."""
    builder, is_trading_day = build_row_builder(cfg), build_trading_days()
    stressed = cfg["risk"]["stressed_margin"]
    workers = count_setting(stressed, "recompute_workers", ".stressed_margin")
    tracker = lambda: HeldRiseTracker(builder.structures, builder.widths_for, builder.calculator, is_trading_day)  # noqa: E731
    manifest = lambda: {f.day: f.sha256 for f in storage.build_manifest_folder().read(NseSpanBodSource)}  # noqa: E731
    day_file = day_file or per_thread(lambda: build_drive_span_files(env))
    sources = StressSources(day_file, manifest, is_trading_day, tracker, workers=workers)
    factor_file = StressFactorFile(root / stressed["factor_file"])
    return StressFactorRun(
        sources,
        factor_file,
        root / STRESS_EVIDENCE,
        build_evidence_saver(env),
        build_alert_sender(),
        run_day or now_ist().date(),
    )


def build_nse_margin_job(cfg: dict, env=os.environ, day_file: DayFile | None = None) -> NseMarginJob:
    """Story A14's job on Drive's archived files, or on `day_file` (a local check of downloaded files)."""
    day_file = day_file or build_drive_span_files(env)
    check = BrokerApprovals.from_margins_block(cfg["risk"]["margins"])
    return NseMarginJob(day_file, build_row_builder(cfg), build_margin_log(cfg, env), build_trading_days(), check,
                        build_alert_sender(), now_ist)  # fmt: skip


def due_day() -> date:
    """The first session from today on (the librarian's last day in the scheduled morning job)."""
    return due_session(now_ist(), build_trading_days())


def move_margins_to_drive(cfg: dict, root: Path = ROOT, env=os.environ) -> list[str]:
    """O9b step 2: the committed margins table and each evidence CSV into their Drive series, each read back equal (a
    file grown since an earlier move is caught up)."""
    table = cfg["risk"]["margins"]["table"]
    lines = [move_into(ReceiptedRowLog(build_data_store(MARGINS_WRITER, env=env), build_drive_cache(env), table),
                       (root / MARGINS_FILE).read_bytes(), MARGINS_FILE)]  # fmt: skip
    for path in sorted((root / STRESS_EVIDENCE).glob(EVIDENCE_CSV)):
        day = path.stem.removeprefix("stress_evidence_")
        series = ReceiptedSnapshots(build_data_store(STRESS_WRITER, env=env), build_drive_cache(env),
                                    EVIDENCE_SERIES.format(day=day))  # fmt: skip
        lines.append(move_into(series, path.read_bytes(), path.name, exact=True))  # its factor row names the SHA
    return lines
