"""Stories G2 and G3: the committed history back-fill equals a fresh recomputation, every record follows the frozen
schema and names its method, version, the close proxy and the day's IV30 state, and Book 1 is the mean of its
baselines on every day.

The panel on `main` grows every evening (story A13, G1 v3), so the back-fill is checked against the panel it was built
from: its own days only, and its pack hash is the SHA-256 of the panel manifest at the commit that wrote it (ChatGPT
review 30 item 5). A day added to the panel later is not part of the back-fill and never changes one of its records."""

import csv
import gzip
import hashlib
import io
import math
import subprocess
from collections import defaultdict

import pytest

from fno.config import ROOT, load_app_config
from fno.forecast.backfill import BACKFILL_FILE, backfill_records
from fno.forecast.baseline_wiring import build_baselines, build_forecast_history
from fno.forecast.book1_method import method_label
from fno.forecast.comparisons import baselines_for
from fno.forecast.golden import GOLDEN_FILE, read_golden
from fno.forecast.record_files import read_records, records_gzip


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def backfill_pack_sha256() -> str:
    """The panel manifest's SHA-256 at the commit that last wrote the back-fill: the panel it was built from."""
    commit = _git("log", "-1", "--format=%H", "--", BACKFILL_FILE).decode().strip()
    return hashlib.sha256(_git("show", f"{commit}:research/data/nifty-panel/manifest.json")).hexdigest()


@pytest.fixture(scope="module")
def committed():
    return read_records(gzip.decompress((ROOT / BACKFILL_FILE).read_bytes()).decode("utf-8"))


@pytest.mark.usefixtures("full_history")
def test_the_committed_backfill_equals_a_fresh_recomputation(committed):
    history = build_forecast_history(load_app_config())
    last = max(r.date for r in committed)
    fresh = [r for r in backfill_records(history, build_baselines(history), backfill_pack_sha256()) if r.date <= last]
    # the records' CSV, not the gzip byte stream, which another zlib version may compress differently
    assert_same_records(gzip.decompress(records_gzip(fresh)), gzip.decompress((ROOT / BACKFILL_FILE).read_bytes()))


# The probabilities come from `math.erf` (fno/analytics.py `norm_cdf`), which CPython takes from the platform's C
# library. glibc 2.43 replaced erf with CORE-MATH's correctly rounded one, so its last bit differs from glibc 2.39's on
# about 1 call in 10: the committed back-fill (glibc 2.39) and a recomputation on Ubuntu 26.04 (glibc 2.43) differ by
# at most 2.2e-16 in a probability. That cannot be fixed in our code without changing the method, so every field is
# compared exactly except the probability, which may differ by at most 1e-12: far above libm noise, far below any
# real change (a changed input, rule or day moves a probability by orders of magnitude more).
LIBM_TOLERANCE = 1e-12


def same_probability(fresh: str, committed: str) -> bool:
    if fresh == "" or committed == "":
        return fresh == committed  # "no forecast" must stay "no forecast"
    return math.isclose(float(fresh), float(committed), rel_tol=0, abs_tol=LIBM_TOLERANCE)


def _rows(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8"))))


def assert_same_records(fresh: bytes, committed: bytes) -> None:
    new, old = _rows(fresh), _rows(committed)
    assert new[0] == old[0] and len(new) == len(old)  # same header, same number of records
    p = old[0].index("probability")
    for line, (a, b) in enumerate(zip(new[1:], old[1:]), start=2):
        assert a[:p] + a[p + 1 :] == b[:p] + b[p + 1 :], f"line {line}"
        assert same_probability(a[p], b[p]), f"line {line}: probability {a[p]} != {b[p]}"


COMMITTED = b"book,date,probability\nb,2026-10-12,0.4694583588320299\nb,2026-10-13,\n"


def test_the_record_comparison_allows_a_last_bit_libm_difference():
    assert_same_records(COMMITTED.replace(b"0.4694583588320299", b"0.46945835883202985"), COMMITTED)  # CI's glibc 2.43


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"0.4694583588320299", b"0.4694583598320299"),  # a probability 1e-9 away
        (b"2026-10-13,\n", b"2026-10-13,0.5\n"),  # "no forecast" became a forecast
        (b"2026-10-12", b"2026-10-14"),  # another field
        (b"b,2026-10-13,\n", b""),  # a record missing
    ],
)
def test_the_record_comparison_catches_every_real_change(old, new):
    with pytest.raises(AssertionError):
        assert_same_records(COMMITTED.replace(old, new), COMMITTED)


@pytest.mark.usefixtures("full_history")
def test_every_record_names_its_method_version_proxy_and_iv30_state(committed):
    golden = {r["date"]: r["iv30_flagged"] for r in read_golden((ROOT / GOLDEN_FILE).read_text(encoding="utf-8"))}
    state = {"true": "iv30:flagged", "false": "iv30:interpolated", "": "iv30:none"}
    pack = backfill_pack_sha256()
    for r in committed:
        assert "/close-proxy/" in r.method_or_version and r.pack_sha256 == pack
        assert r.method_or_version.endswith(state[golden[r.date.isoformat()]])
        if r.book == "book1_rules":
            assert r.method_or_version.startswith(method_label())
        else:
            assert r.method_or_version.startswith(f"{r.book}/v1/")
    assert len(committed) == 5 * 4 * len(golden)


def test_book1_is_the_mean_of_its_baselines_on_every_record(committed):
    by = defaultdict(dict)
    for r in committed:
        by[(r.date, r.question)][r.book] = r.probability
    for (_, question), values in by.items():
        available = [values[b] for b in baselines_for(question) if values[b] is not None]
        expected = sum(available) / len(available) if available else None
        assert (
            values["book1_rules"] == pytest.approx(expected) if expected is not None else values["book1_rules"] is None
        )
