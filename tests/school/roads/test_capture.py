"""The capture reader (story 3.5): what it verifies, what it keeps, and what it refuses to turn into a closure."""

import json

import pytest

from fno.quotes.drive_only_store import RawQuoteHashMismatch, RawQuoteMissing, RawQuoteStoreUnavailable
from fno.school.constants import ClosureReason, OptionKind, RoadCode
from fno.school.roads.capture import CaptureProblem, CaptureReader
from fno.storage.raw_store import RawFileStore
from tests.school.roads.capture_builder import MONTHLIES, SESSION, SPOT, DictStore, Plant, road

BANK = road(RoadCode.BANKNIFTY_MONTHLY)


class CountingStore(DictStore):
    def __init__(self):
        super().__init__()
        self.reads = 0

    def get(self, path):
        self.reads += 1
        return super().get(path)


class RaisingStore(RawFileStore):
    name = "raising"

    def __init__(self, error):
        self.error = error

    def get(self, path):
        if path.endswith(".csv"):
            raise self.error
        return planted.files.get(path)

    def put(self, path, data):
        raise AssertionError("the reader never writes")


planted = DictStore()


def reader_over(store):
    return CaptureReader({BANK.dataset: store})


def test_a_good_capture_is_read_into_a_snapshot_with_the_sidecars_hash_and_spot():
    store = DictStore()
    plant = Plant(BANK).write(store)
    capture = reader_over(store).read(BANK, SESSION)
    snapshot = capture.snapshot()
    assert (snapshot.road, snapshot.session, snapshot.snapshot_id) == (BANK.code, SESSION, plant.snapshot_id)
    assert snapshot.expiries == MONTHLIES and snapshot.spot == SPOT and len(snapshot.quotes) == 32
    assert snapshot.sha256 == capture.sha256 and len(capture.sha256) == 64
    quote = next(q for k, q in snapshot.quotes.items() if k.strike == 1000.0 and k.kind is OptionKind.PUT)
    assert quote.valid and quote.two_sided and quote.bid < quote.ask and quote.bid_qty == 1000


def test_a_good_capture_is_fetched_once_however_often_it_is_asked_for():
    store = CountingStore()
    Plant(BANK).write(store)
    reader = reader_over(store)
    first = reader.read(BANK, SESSION)
    reads = store.reads
    assert reader.read(BANK, SESSION) is first and store.reads == reads


def test_a_fault_is_remembered_too():
    store = CountingStore()
    Plant(BANK, tamper=True).write(store)
    reader = reader_over(store)
    with pytest.raises(CaptureProblem):
        reader.read(BANK, SESSION)
    reads = store.reads
    with pytest.raises(CaptureProblem) as raised:
        reader.read(BANK, SESSION)
    assert raised.value.reason is ClosureReason.HASH_MISMATCH and store.reads == reads


def test_a_missing_capture_is_asked_for_again_because_it_may_still_be_recorded():
    store = DictStore()
    reader = reader_over(store)
    with pytest.raises(CaptureProblem) as raised:
        reader.read(BANK, SESSION)
    assert raised.value.reason is ClosureReason.CAPTURE_MISSING
    Plant(BANK).write(store)
    assert reader.read(BANK, SESSION).snapshot_id


def test_the_snapshot_hands_out_a_read_only_view_of_the_quotes():
    store = DictStore()
    Plant(BANK).write(store)
    snapshot = reader_over(store).read(BANK, SESSION).snapshot()
    with pytest.raises(TypeError):
        snapshot.quotes[next(iter(snapshot.quotes))] = None


@pytest.mark.parametrize("change", [{"underlying": "NIFTY"}, {"snapshot_id": "banknifty_other"}], ids=["road", "id"])
def test_a_sidecar_that_is_another_captures_is_refused(change):
    store = DictStore()
    plant = Plant(BANK).write(store)
    from fno.quotes.recorder import QuoteSnapshotRecorder

    path = QuoteSnapshotRecorder.path(SESSION, f"{plant.snapshot_id}.meta.json", BANK.dataset)
    store.files[path] = json.dumps({**json.loads(store.files[path]), **change}).encode()
    with pytest.raises(CaptureProblem) as raised:
        reader_over(store).read(BANK, SESSION)
    assert raised.value.reason is ClosureReason.CAPTURE_INCOMPLETE


@pytest.mark.parametrize("column,cell", [("strike", ""), ("strike", "inf"), ("strike", "x"), ("expiry", "2026-13-45"),
                                          ("bid", "nan"), ("type", "XX")])  # fmt: skip
def test_a_row_that_cannot_be_read_is_an_incomplete_capture_never_a_crash(column, cell):
    store = DictStore()
    Plant(BANK, change_rows=[lambda rows: rows[0].update({column: cell})]).write(store)
    with pytest.raises(CaptureProblem) as raised:
        reader_over(store).read(BANK, SESSION)
    assert raised.value.reason is ClosureReason.CAPTURE_INCOMPLETE


def test_the_stores_own_hash_refusal_and_missing_file_become_their_closure_reasons():
    Plant(BANK).write(planted)
    for error, reason in ((RawQuoteHashMismatch("x"), ClosureReason.HASH_MISMATCH),
                          (RawQuoteMissing("x"), ClosureReason.CAPTURE_MISSING)):  # fmt: skip
        with pytest.raises(CaptureProblem) as raised:
            reader_over(RaisingStore(error)).read(BANK, SESSION)
        assert raised.value.reason is reason


def test_a_store_that_is_down_is_an_error_never_a_closure():
    Plant(BANK).write(planted)
    with pytest.raises(RawQuoteStoreUnavailable):
        reader_over(RaisingStore(RawQuoteStoreUnavailable("no Drive"))).read(BANK, SESSION)


def test_rows_naming_an_expiry_the_sidecar_does_not_are_an_expiry_mismatch():
    store = DictStore()
    plant = Plant(BANK).write(store)
    import json

    from fno.quotes.recorder import QuoteSnapshotRecorder

    sidecar = QuoteSnapshotRecorder.path(SESSION, f"{plant.snapshot_id}.meta.json", BANK.dataset)
    meta = json.loads(store.files[sidecar])
    meta["expiries"] = meta["expiries"][:1]
    store.files[sidecar] = json.dumps(meta).encode()
    with pytest.raises(CaptureProblem) as raised:
        reader_over(store).read(BANK, SESSION)
    assert raised.value.reason is ClosureReason.EXPIRY_MISMATCH


@pytest.mark.parametrize("garbage", [b"not json", b'{"complete": true}', b"[]"], ids=["text", "keys missing", "list"])
def test_a_sidecar_that_cannot_be_read_is_incomplete_never_a_crash(garbage):
    store = DictStore()
    plant = Plant(BANK).write(store)
    from fno.quotes.recorder import QuoteSnapshotRecorder

    store.files[QuoteSnapshotRecorder.path(SESSION, f"{plant.snapshot_id}.meta.json", BANK.dataset)] = garbage
    with pytest.raises(CaptureProblem) as raised:
        reader_over(store).read(BANK, SESSION)
    assert raised.value.reason is ClosureReason.CAPTURE_INCOMPLETE


def test_strike_step_is_the_most_common_gap_of_the_nearest_expiry():
    store = DictStore()
    Plant(BANK).write(store)
    assert reader_over(store).read(BANK, SESSION).strike_step() == 100.0
