"""Read-only: copy the last N UDiFF F&O bhavcopies from the shared Drive raw archive into a scratch folder.

Needs the routine setup (`sh tools/routine_setup.sh`, for `google.auth`) and the Drive service-account settings. It
never writes to Drive and never calls NSE.

    python research/2026-10-15-breadth-sizing/fetch.py <scratch folder> <N>
"""

import csv
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fno.storage.raw_source import NseDailyFoSource  # noqa: E402
from fno.storage.wiring import build_drive_reader  # noqa: E402

MANIFEST = ROOT / "research" / "data" / "manifests" / "fo-bhavcopy.csv"


def archived_days() -> list[date]:
    with MANIFEST.open() as f:
        return [date.fromisoformat(r["date"]) for r in csv.DictReader(f)]


def fetch(out: Path, count: int) -> None:
    store, started, copied = build_drive_reader(), time.time(), 0
    for day in archived_days()[-count:]:
        target = out / f"{day}.zip"
        if target.exists():
            continue
        data = store.get(NseDailyFoSource.path_for(day))
        if data is None:
            print("missing", day)
            continue
        target.write_bytes(data)
        copied += 1
    print(f"fetched {copied} in {time.time() - started:.0f} s")


if __name__ == "__main__":
    fetch(Path(sys.argv[1]), int(sys.argv[2]))
