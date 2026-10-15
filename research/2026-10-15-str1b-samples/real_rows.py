"""Story STR1b: NSE's real margin rows of 14 Oct 2026 for every tradable structure and width, made by the app's own A14
row builder from NSE's beginning-of-day SPAN file `nsccl.20261014.i1.zip` (SHA-256 d85b883a...e8b5b, judges 77 and
106). The file is NSE's public archive (https://nsearchives.nseindia.com/archives/nsccl/span/), not committed (9.5 MB).
Run: python research/2026-10-15-str1b-samples/real_rows.py <path to the zip> \
    > tests/risk/fixtures/margins_2026-10-14.csv"""

import csv
import hashlib
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fno.config import load_app_config  # noqa: E402
from fno.nse_margins.span_file import read_span_file  # noqa: E402
from fno.nse_margins.wiring import build_row_builder  # noqa: E402
from fno.risk.margins import MARGIN_COLUMNS  # noqa: E402

DAY = date(2026, 10, 14)
SHA256 = "d85b883ae4ca6015261a1ae126d8a3ed87a0a882c86932f2af842879270e8b5b"

if __name__ == "__main__":
    data = Path(sys.argv[1]).read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise SystemExit("not NSE's 14 Oct 2026 i1 file (SHA-256 differs)")
    found = build_row_builder(load_app_config()).rows(read_span_file(data, "nsccl.20261014.i1.zip"), SHA256, DAY)
    writer = csv.DictWriter(sys.stdout, fieldnames=MARGIN_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(row.as_csv() for row in found.rows)
    for reason in found.skipped:
        print(f"skipped: {reason}", file=sys.stderr)
