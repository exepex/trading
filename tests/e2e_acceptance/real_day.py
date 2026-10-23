"""Story O11's recorded day: NSE's real 3 pm NIFTY chain of 16 Oct 2026 (the only quote rows committed to this public
repository; Groww's stay in Drive, story A4b), the committed closes, events, calendar, margins and stress factor, in a
temporary repository folder. Three outside services are replaced at their composition-root seams, nothing else:
Drive's quote store (a local folder), NSE's archive of daily F&O files (one file of the real contracts), and the
playbook's git approval evidence (one approved test version: no strategy is approved yet, so a real one cannot be)."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
from datetime import date, datetime, time
from pathlib import Path

from fno.composition import open_account_writer
from fno.config import ROOT
from fno.constants import BOOKS
from fno.desk import wiring as desk_wiring
from fno.models import IST
from fno.playbook import wiring as playbook_wiring
from fno.quotes.recorder import DATASET
from fno.scorecard import wiring as scorecard_wiring
from fno.storage import data_wiring
from fno.storage import wiring as storage_wiring
from fno.storage.raw_store import LocalFolderStore
from fno.storage.table_source import FileTable
from tests.book1.builders import book1_doc
from tests.checks.validity_sources import NseFiles, nse_file
from tests.decisions.builders import snapshot

DAY = date(2026, 10, 16)
# A14's margins rows up to the day, frozen from the table before it moved to Drive (O9b step 2, 23 Oct 2026)
MARGINS = Path(__file__).parent / "fixtures" / "margins_to_2026-10-16.csv"
NSE_FILE_DAY = date(2026, 10, 15)  # the session before: C4 reads its F&O file for listings and lot sizes
ACCOUNTS_START = date(2026, 10, 1)
SNAPSHOT_ID = "nifty_20261016_145500"
SOURCE = ROOT / "research" / "data" / "quotes" / "nse" / "derivatives" / "quote-snapshots" / "2026" / "10"
QUOTES = Path("research") / "data" / "quotes"  # the repository's quote folder, as E6 and S2 read it
LISTED_EXPIRIES = ("2026-10-20", "2026-10-27", "2026-11-23", "2026-12-29")  # NSE's monthlies on 16 Oct plus a weekly
LISTED_STRIKES = range(21_000, 25_050, 50)
ENTRY_WINDOW_DAYS = 38  # 16 Oct is the first session within 38 days of the 23 Nov expiry: the version's entry day


def restated(row: dict) -> dict:
    """NSE's contract ID (`OPTIDXNIFTY23-11-2026CE21950.00`) in the exchange-symbol form Groww's rows carry, so C5's
    bucket map reads the underlying `NIFTY` (prices, sizes and times unchanged)."""
    expiry = date.fromisoformat(row["expiry"])
    return {**row, "contract_id": f"NIFTY{expiry:%y%m%d}{float(row['strike']):g}{row['type']}"}


def real_rows() -> list[dict]:
    with open(SOURCE / f"{SNAPSHOT_ID}.csv", newline="", encoding="utf-8") as file:
        return [restated(row) for row in csv.DictReader(file)]


def csv_bytes(rows: list[dict]) -> bytes:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def write_capture(root: Path) -> None:
    """The 14:55 capture as A4 would have filed it: rows, sidecar (its CSV hash updated) and canonical marker."""
    folder = root / QUOTES / DATASET / "2026" / "10"
    folder.mkdir(parents=True)
    data = csv_bytes(real_rows())
    meta = json.loads((SOURCE / f"{SNAPSHOT_ID}.meta.json").read_text(encoding="utf-8"))
    (folder / f"{SNAPSHOT_ID}.csv").write_bytes(data)
    (folder / f"{SNAPSHOT_ID}.meta.json").write_text(json.dumps({**meta, "csv_sha256": _sha(data)}, indent=1))
    shutil.copy(SOURCE / "nifty_20261016.canonical", folder / "nifty_20261016.canonical")


def approved_playbook():
    version = book1_doc()
    version["structure"]["expiry"]["max_days"] = ENTRY_WINDOW_DAYS
    return snapshot(version)


class FixedLoader:
    """D1's loader port over the approved test version (E6 also reads its registry rows)."""

    def __init__(self, playbook):
        self.playbook = playbook
        self.registry = self

    def load(self):
        return self.playbook.playbook()

    def rows(self):
        return self.load().rows


def build_repository(root: Path) -> None:
    write_capture(root)
    shutil.copytree(ROOT / "research" / "data" / "margins", root / "research" / "data" / "margins")
    for book in BOOKS:
        with open_account_writer(book, root) as writer:
            writer.start(ACCOUNTS_START)


def replace_outside_services(monkeypatch, root: Path, playbook, listed: bool = True) -> None:
    """Each seam in its home module and in every module that imported it by name at load time; `listed=False`: NSE's
    F&O file of the day before is missing."""
    listing = NseFiles({NSE_FILE_DAY: nse_file(expiries=LISTED_EXPIRIES, strikes=LISTED_STRIKES)} if listed else {})
    for module in (storage_wiring, desk_wiring):
        monkeypatch.setattr(module, "build_quote_store", lambda *args, **kwargs: quote_store(root))
        monkeypatch.setattr(module, "build_nse_fo_library", lambda *args, **kwargs: listing)
    for module in (playbook_wiring, scorecard_wiring):
        monkeypatch.setattr(module, "build_playbook_loader", lambda *args, **kwargs: FixedLoader(playbook))
    monkeypatch.setattr(data_wiring, "build_data_table", lambda name, env=None: FileTable(MARGINS))  # C2's and C4's


def quote_store(root: Path) -> LocalFolderStore:
    return LocalFolderStore(root / QUOTES)


def at(hour: int, minute: int, second: int = 0) -> datetime:
    return datetime.combine(DAY, time(hour, minute, second), IST)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
