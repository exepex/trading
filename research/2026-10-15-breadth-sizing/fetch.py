"""Read-only: copy the last N F&O bhavcopies (UDiFF, or the legacy format) from the shared Drive raw archive into a
scratch folder.

Needs the routine setup (`sh tools/routine_setup.sh`, for `google.auth`) and the Drive service-account settings. It
never writes to Drive and never calls NSE.

    python research/2026-10-15-breadth-sizing/fetch.py <scratch folder> <N> [udiff|legacy]
"""

import csv
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fno.storage.raw_source import NseDailyFoSource, NseLegacyFoSource  # noqa: E402
from fno.storage.wiring import build_drive_reader  # noqa: E402

MANIFESTS = ROOT / "research" / "data" / "manifests"
FORMATS = {"udiff": (NseDailyFoSource, "fo-bhavcopy.csv"), "legacy": (NseLegacyFoSource, "fo-bhavcopy-legacy.csv")}


def archived_days(manifest: str) -> list[date]:
    with (MANIFESTS / manifest).open() as f:
        return [date.fromisoformat(r["date"]) for r in csv.DictReader(f)]


def fetch(out: Path, count: int, kind: str = "udiff") -> None:
    source, manifest = FORMATS[kind]
    store, started, copied = build_drive_reader(), time.time(), 0
    for day in archived_days(manifest)[-count:]:
        target = out / f"{day}.zip"
        if target.exists():
            continue
        data = store.get(source.path_for(day))
        if data is None:
            print("missing", day)
            continue
        target.write_bytes(data)
        copied += 1
    print(f"fetched {copied} in {time.time() - started:.0f} s")


if __name__ == "__main__":
    fetch(Path(sys.argv[1]), int(sys.argv[2]), *sys.argv[3:4])
