"""The review's sources from MS-P1j's record (story MS-INS, part e follow-up): the unfilled entries from MS-P1j's
root, and f's three counts from the counts file each session's run commits."""

from datetime import date

from fno.config import load_app_config
from fno.school.constants import SLOT_1500, RoadCode
from fno.school.contracts.tickets import OpportunityCounts
from fno.school.fleet.counts_file import opportunity_path, opportunity_text
from fno.school.instructor import review_wiring

DAY = date(2026, 11, 4)


def test_the_review_reads_ms_p1j_unfilled_entries_and_the_committed_three_counts(monkeypatch, tmp_path):
    built = []
    unfilled = object()
    monkeypatch.setattr(review_wiring, "build_dashcam", lambda: object())
    monkeypatch.setattr(review_wiring, "build_unfilled_entries", lambda cfg, root: built.append(root) or unfilled)
    counts = OpportunityCounts(DAY, RoadCode.BANKNIFTY_MONTHLY, "CS1@1", 2, 1, 1)
    file = tmp_path / opportunity_path(DAY, SLOT_1500)
    file.parent.mkdir(parents=True)
    file.write_text(opportunity_text((counts,)))
    sources = review_wiring.build_review_sources(load_app_config(), tmp_path)
    assert sources.unfilled is unfilled and built == [tmp_path]
    assert sources.counts.counts(DAY) == (counts,)
    assert sources.counts.counts(date(2026, 11, 5)) == ()  # no counts file committed: none


def test_the_commands_entry_point_gives_the_review_its_sources(monkeypatch):
    from fno.school.instructor import __main__ as entry

    given = []
    monkeypatch.setattr(entry, "run", lambda argv, config, wiring, sources: given.append(sources) or [])
    assert entry.main(["--review", "2026-11-02", "2026-11-04"]) == 0
    assert given == [review_wiring.build_review_sources]
