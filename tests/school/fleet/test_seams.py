"""Story MS-P1j's two seams for the simulator (orchestrator, 23 Oct 2026): the replay dashcam's encoding is the one
method a practice dashcam overrides, and the pilot's decoder still reads its labelled lines; `books_on` is the one
construction of the accounts and the ticket ledger, filled through the port it is given."""

import gzip
import json
from types import SimpleNamespace

from fno.config import ROOT, load_config
from fno.school import fleet_wiring
from fno.school.constants import SLOT_1500, RecordKind
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.slot_file import decode_slot_file, encode_slot_file
from fno.school.fleet.replay_store import ReplayDashcam
from fno.school.fleet_wiring import FleetStores, books_on
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import closed_record

LABEL = "practice (simulator)"
CFG = load_config(ROOT / "config.yaml")


class LabelledDashcam(ReplayDashcam):
    def encode(self, records):
        lines = gzip.decompress(encode_slot_file(records)).splitlines()
        return gzip.compress(b"".join(json.dumps({**json.loads(line), "label": LABEL}).encode() + b"\n"
                                      for line in lines), mtime=0)  # fmt: skip


def test_a_subclass_changes_only_the_encoding_and_the_pilot_s_decoder_reads_its_labelled_lines(tmp_path):
    clock, records = FixedClock(b.SLOT_AT), (closed_record(),)
    labelled = LabelledDashcam(tmp_path, clock)
    seal = labelled.seal(b.SESSION, SLOT_1500, RecordKind.DECISIONS, records)
    data = (tmp_path / seal.path).read_bytes()
    assert all(json.loads(line)["label"] == LABEL for line in gzip.decompress(data).splitlines())
    assert decode_slot_file(data) == records == ReplayDashcam(tmp_path, clock).read(seal)
    assert labelled.seal(b.SESSION, SLOT_1500, RecordKind.DECISIONS, records) == seal, "write-once is the base's"


def test_books_on_builds_the_accounts_and_tickets_under_the_home_with_the_given_fill_port(tmp_path):
    fills = SimpleNamespace()
    books = books_on(CFG, FleetStores(tmp_path, None, None, None, FixedClock(b.SLOT_AT)), fills)
    assert books.fills is fills and books.tickets.fills is fills
    assert books.accounts.root.is_relative_to(tmp_path) and books.ticket_entries.root.is_relative_to(tmp_path)
    assert books.accounts is books.account_entries and books.ticket_entries is books.tickets.ledger.store


def test_fleet_on_builds_its_books_through_books_on(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(fleet_wiring, "books_on", lambda *a, **k: seen.append(a) or SimpleNamespace())
    for name in ("build_road_services", "build_quality_gate", "build_margin", "build_capture_1515",
                 "build_school_drivers", "build_fill_port"):  # fmt: skip
        monkeypatch.setattr(
            fleet_wiring,
            name,
            lambda *a, **k: SimpleNamespace(catalogue=None, snapshots=None, listing=None, for_session=None),
        )
    fleet_wiring.fleet_on(CFG, FleetStores(tmp_path, None, None, None, FixedClock(b.SLOT_AT)))
    assert len(seen) == 1


def test_read_decodes_through_the_subclass_s_own_decode(tmp_path):
    class Counting(ReplayDashcam):
        decoded = 0

        def decode(self, data):
            Counting.decoded += 1
            return super().decode(data)

    cam = Counting(tmp_path, FixedClock(b.SLOT_AT))
    cam.read(cam.seal(b.SESSION, SLOT_1500, RecordKind.DECISIONS, (closed_record(),)))
    assert Counting.decoded == 1
