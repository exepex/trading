"""G13's paths in Drive's `data` area and its receipts in the checkout (section 5); O1's step commits only these."""

from __future__ import annotations

from datetime import date

ROOT = "price_distribution/v1"
LIVE, BACKFILL, SCORES = f"{ROOT}/live", f"{ROOT}/backfill", f"{ROOT}/scores"
DATA_AREA = "data"  # O9's area (`fno/storage/data_wiring.py`)


def live_path(underlying: str, day: date) -> str:
    return f"{LIVE}/{day:%Y}/{day:%m}/{underlying.lower()}_{day.isoformat()}.json"


def backfill_path(label: str, method_sha256: str, underlying: str, first: date, last: date) -> str:
    return f"{BACKFILL}/{label}_{method_sha256[:8]}/{underlying.lower()}_{first.isoformat()}_{last.isoformat()}.json.gz"


def scores_path(day: date, digest: str) -> str:
    return f"{SCORES}/{day.isoformat()}_{digest[:12]}.json"


def receipt_pathspecs() -> tuple[str, ...]:
    """The receipts of G13's Drive files only (as M1's `record_folders()`), never a shared folder."""
    return (f"receipts/{DATA_AREA}/{ROOT}/",)
