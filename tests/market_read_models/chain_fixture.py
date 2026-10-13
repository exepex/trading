"""NSE's real NIFTY chain inputs of 1 Jun to 12 Oct 2026 (story P9): the in-scope NIFTY rows of the daily F&O files
(UDiFF columns) and the NIFTY 50 and India VIX rows of the daily index files, cut from the archived files into
tests/fixtures/nse/chain/. Rebuilt as the per-day inputs the chain builder reads."""

import csv
import gzip
import io
from collections import defaultdict
from datetime import date
from functools import cache
from pathlib import Path

from fno.market_read_models.chain_session import ChainBuilder, ChainSession

FOLDER = Path(__file__).parents[1] / "fixtures" / "nse" / "chain"
DAY = date(2026, 10, 12)
RATE = 0.065  # config.yaml risk_free_rate
INDEX_HEADER = ["Index Name", "Closing Index Value", "Change(%)"]


def fo_rows() -> list[tuple[date, list[dict[str, str]]]]:
    by_day = defaultdict(list)
    with gzip.open(FOLDER / "nifty_fo_20260601_20261012.csv.gz", "rt", newline="") as handle:
        for row in csv.DictReader(handle):
            by_day[date.fromisoformat(row["TradDt"])].append(row)
    return sorted(by_day.items())


def index_files() -> list[tuple[date, str, bytes]]:
    by_day = defaultdict(list)
    with open(FOLDER / "index_20260601_20261012.csv", newline="") as handle:
        for row in csv.DictReader(handle):
            by_day[date.fromisoformat(row["date"])].append([row[k] for k in INDEX_HEADER])
    files = []
    for day, rows in sorted(by_day.items()):
        text = io.StringIO()
        csv.writer(text).writerows([INDEX_HEADER, *rows])
        files.append((day, f"ind_close_all_{day:%d%m%Y}.csv", text.getvalue().encode()))
    return files


@cache
def chain_of_12_october() -> ChainSession:
    return ChainBuilder(RATE).build(DAY, fo_rows(), index_files())
