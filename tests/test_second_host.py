"""Story A9c: the librarian's dated NSE files from a second host (`archives.nseindia.com`) only when the first is
unreachable, one try, the same bytes and store, each file logged; write times and A11's sweep stay on the first host."""

import csv
import hashlib
from datetime import UTC, date, datetime, timedelta

import pytest
import requests

from fno.http_pacing import HOST_SPACING_SECONDS, SourceCoolingOff
from fno.storage import wiring
from fno.storage.coverage import archive_range
from fno.storage.fallback_source import CsvProvenanceLog, FallbackSource
from fno.storage.host_check import DIFFERENT, INCOMPLETE, NEITHER, SAME, compare_hosts
from fno.storage.manifest_folder import FingerprintingStore, ManifestFolder
from fno.storage.raw_source import (
    PRIMARY_HOST,
    SECOND_HOST,
    NseIndexCloseSource,
    NseLegacyFoSource,
    PublishedFile,
    RawFileRefused,
    RawSourceCoolingOff,
    RawSourceUnavailable,
)
from fno.storage.raw_store import LocalFolderStore
from fno.storage.revision_source import RevisionCapturingSource
from fno.storage.revisions import RevisionArchive, RevisionIndex
from fno.storage.source_lists import LIBRARIAN_DATASETS
from fno.storage.wiring import DATED_SOURCES, RAW_SOURCES

DAY = date(2026, 10, 21)
PATH = NseIndexCloseSource.path_for(DAY)
FILE = b"Index Name,Closing Index Value\nNifty 50,22811.35\n"
LATER = b"Index Name,Closing Index Value\nNifty 50,22811.35\nNifty New,1.00\n"


class Answer:
    def __init__(self, status=200, content=b"", headers=None):
        self.status_code, self.content, self.headers = status, content, headers or {}


class Session:
    """Answers in order (an int status, bytes for a 200, or an exception), each request taking `cost` seconds."""

    def __init__(self, answers, clock=None, cost=0.0):
        self.answers, self.urls, self.clock, self.cost = list(answers), [], clock, cost

    def get(self, url, timeout=None):
        self.urls.append(url)
        if self.clock is not None:
            self.clock.now += timedelta(seconds=self.cost)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, bytes):
            return Answer(200, answer)
        return Answer(answer, headers={"Retry-After": "120"} if answer == 503 else {})

    head = get


class Untouchable:
    def get(self, url, timeout=None):
        raise AssertionError(f"the second host was asked: {url}")

    head = get


class Clock:
    def __init__(self):
        self.now = datetime(2026, 10, 22, 3, 0, tzinfo=UTC)

    def sleep(self, seconds):
        self.now += timedelta(seconds=seconds)


def _fallback(first, second, tmp_path, clock=None):
    sleep, now = (clock.sleep, lambda: clock.now) if clock else ((lambda s: None), (lambda: datetime.now(UTC)))
    primary = NseIndexCloseSource(first, sleep=sleep, clock=now)
    secondary = NseIndexCloseSource(second, sleep=sleep, clock=now, host=SECOND_HOST, retry_waits=())
    return FallbackSource(primary, secondary, CsvProvenanceLog(tmp_path / "second-host"))


def _provenance(tmp_path):
    file = tmp_path / "second-host" / "index-close.csv"
    return list(csv.DictReader(file.read_text().splitlines())) if file.is_file() else []


def test_an_unreachable_first_host_is_answered_by_the_second_with_the_same_bytes_and_logged(tmp_path):
    down = requests.ConnectionError("edge down")
    first, second = Session([down, down, down, down]), Session([FILE])
    source = _fallback(first, second, tmp_path)
    assert source.fetch(PATH) == FILE
    assert len(first.urls) == 4 and second.urls == [f"https://{SECOND_HOST}/content/indices/ind_close_all_21102026.csv"]
    [row] = _provenance(tmp_path)
    assert row["path"] == PATH and row["sha256"] == hashlib.sha256(FILE).hexdigest() and row["url"] == second.urls[0]
    assert row["size_bytes"] == str(len(FILE))


def test_a_first_host_answer_never_asks_the_second(tmp_path):
    source = _fallback(Session([FILE, 404]), Untouchable(), tmp_path)
    assert source.fetch(PATH) == FILE and source.fetch(PATH) is None  # served, then "not published": both final
    assert _provenance(tmp_path) == []


@pytest.mark.parametrize(
    ("answer", "error"), [(403, RawFileRefused), (SourceCoolingOff("nsearchives paused"), RawSourceCoolingOff)]
)
def test_a_refusal_or_a_cooling_off_is_never_taken_to_the_second_host(tmp_path, answer, error):
    with pytest.raises(error):
        _fallback(Session([answer]), Untouchable(), tmp_path).fetch(PATH)


def test_both_hosts_failing_is_one_error_naming_both(tmp_path):
    first, second = Session([503, 503, 503, 503]), Session([requests.ConnectionError("no route")])
    with pytest.raises(RawSourceUnavailable) as failed:
        _fallback(first, second, tmp_path).fetch(PATH)
    text = str(failed.value)
    assert "HTTP 503" in text and f"second host {SECOND_HOST}:" in text and "no route" in text
    assert failed.value.tries == 5 and _provenance(tmp_path) == []


def test_the_second_host_tries_once_and_the_worst_case_is_660_seconds(tmp_path):
    """Criterion 8: the primary at its slowest (4 x 60 s timeouts, 3 waits stretched to 120 s) plus one 60 s try."""
    clock = Clock()
    first, second = Session([503] * 4, clock, cost=60), Session([503], clock, cost=60)
    started = clock.now
    with pytest.raises(RawSourceUnavailable):
        _fallback(first, second, tmp_path, clock).fetch(PATH)
    assert (len(first.urls), len(second.urls)) == (4, 1)
    assert (clock.now - started).total_seconds() == 660


def test_the_second_host_is_paced_under_its_own_name():
    assert HOST_SPACING_SECONDS[SECOND_HOST] == HOST_SPACING_SECONDS[PRIMARY_HOST] == 1.0
    source = NseIndexCloseSource(Session([]), host=SECOND_HOST)
    assert requests.utils.urlparse(source.requested_url(PATH)).hostname == SECOND_HOST


def test_write_times_come_from_the_first_host_only(tmp_path):
    source = _fallback(Session([requests.ConnectionError("down")] * 4), Untouchable(), tmp_path)
    with pytest.raises(RawSourceUnavailable):
        source.last_written(PATH)  # the primary's failure stands: the second host's dates are never evidence
    first, second = Session([requests.ConnectionError("down")] * 4), Session([FILE])
    assert _fallback(first, second, tmp_path).fetch_published(PATH) == PublishedFile(FILE, None)


@pytest.mark.parametrize("source_type", [*LIBRARIAN_DATASETS.values(), NseLegacyFoSource])
def test_every_dataset_asks_the_same_path_on_either_host(source_type):
    path = source_type.path_for(DAY)
    default, second = source_type(Session([])), source_type(Session([]), host=SECOND_HOST)
    assert default.requested_url(path) == source_type.url_for(path)
    assert default.requested_url(path).startswith(f"https://{PRIMARY_HOST}/")
    assert second.requested_url(path) == source_type.url_for(path).replace(PRIMARY_HOST, SECOND_HOST, 1)


def test_a_second_host_file_is_stored_once_with_the_usual_manifest_row_and_its_provenance(tmp_path):
    manifests = ManifestFolder(tmp_path / "manifests")
    store = FingerprintingStore(LocalFolderStore(tmp_path / "drive"), manifests, RAW_SOURCES)
    source = _fallback(Session([requests.ConnectionError("down")] * 4), Session([FILE]), tmp_path)
    store.put(PATH, source.fetch(PATH))
    store.put(PATH, FILE)  # a later primary fetch of the same bytes: nothing changes
    [row] = manifests.read(NseIndexCloseSource)
    assert row.url.startswith(f"https://{PRIMARY_HOST}/") and row.sha256 == _provenance(tmp_path)[0]["sha256"]


def test_a_differing_later_primary_copy_is_an_a11_revision_and_the_first_copy_s_host_is_on_record(tmp_path):
    raw, revisions = LocalFolderStore(tmp_path / "raw"), LocalFolderStore(tmp_path / "revisions")
    manifests = ManifestFolder(tmp_path / "manifests")
    store = FingerprintingStore(raw, manifests, RAW_SOURCES)
    store.put(PATH, _fallback(Session([requests.ConnectionError("down")] * 4), Session([FILE]), tmp_path).fetch(PATH))
    index = RevisionIndex(tmp_path / "manifests" / "revisions", DATED_SOURCES)
    archive = RevisionArchive(raw, revisions, index, manifests, lambda: datetime(2026, 10, 22, 18, 0, tzinfo=UTC))
    sweep = RevisionCapturingSource(NseIndexCloseSource(Session([LATER]), sleep=lambda s: None), archive)
    assert sweep.fetch(PATH) == LATER and len(archive.stored) == 1 and raw.get(PATH) == FILE
    assert _provenance(tmp_path)[0]["url"].startswith(f"https://{SECOND_HOST}/")


def test_the_librarian_and_library_get_the_fallback_and_every_other_user_one_host(monkeypatch):
    monkeypatch.setattr(wiring, "build_owner_drive_store", lambda: LocalFolderStore("/nonexistent"))
    librarian = wiring.build_librarian("index-close")
    assert isinstance(librarian.source, FallbackSource) and librarian.source.secondary.retry_waits == ()
    assert isinstance(wiring.build_nse_fo_library().source, FallbackSource)
    single = wiring.build_nse_source(NseIndexCloseSource)
    assert single.host == PRIMARY_HOST and not isinstance(single, FallbackSource)
    capturing = wiring.build_revision_capturing_source(NseIndexCloseSource, archive=None)
    assert isinstance(capturing.source, NseIndexCloseSource) and capturing.source.host == PRIMARY_HOST
    end = date(2026, 10, 21)
    assert archive_range(librarian.source, None, end) == archive_range(NseIndexCloseSource, None, end)


class Built:
    def __init__(self, by_host):
        self.by_host = by_host

    def __call__(self, source_type, host, retry_waits):
        return NseIndexCloseSource(Session([self.by_host[host]]), sleep=lambda s: None, host=host, retry_waits=())


@pytest.mark.parametrize(
    ("first", "second", "verdict", "code"),
    [(FILE, FILE, SAME, 0), (404, 404, NEITHER, 0), (FILE, LATER, DIFFERENT, 1),
     (FILE, requests.ConnectionError("x"), INCOMPLETE, 1), (FILE, 404, DIFFERENT, 1)],
)  # fmt: skip
def test_the_hosts_check_passes_only_on_same_or_neither(first, second, verdict, code):
    lines = []
    result = compare_hosts([NseIndexCloseSource], DAY, Built({PRIMARY_HOST: first, SECOND_HOST: second}), lines.append)
    assert result == code and lines[0].endswith(f"-> {verdict}")
