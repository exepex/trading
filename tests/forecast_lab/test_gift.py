"""FL1-1d-2: GIFT Nifty at 08:50 from A22b's own file, read by its own receipt and verified on real O9 parts
(FL1-1e): its level and gap to the previous official NIFTY close when A22 recorded one (ok or late); otherwise the
edition names it itself; never in the evening."""

from datetime import date

from fno.forecast_lab.page.cues import AVAILABLE, NOT_AVAILABLE
from fno.forecast_lab.sections.gift import GiftSection

from .drive_files import DriveFiles

MON = date(2026, 10, 26)
HEADER = "date,gift_status,gift_reads,gift_seen_at,gift_source_time,gift_detail,gift_level,gift_contracts,gift_expiry\n"


GIFT = "data/preopen/gift/2026/10/2026-10-26.csv"


def files(tmp_path, text=None, damaged=False):
    parts = DriveFiles(tmp_path)
    if text is not None:
        parts.put(GIFT, text.encode())
    if damaged:
        parts.damage(GIFT)
    return parts.files


def gift(verified):
    return GiftSection(verified, lambda day: 25000.0)


def test_a_recorded_level_is_shown_with_its_gap_to_the_previous_close(tmp_path):
    view = gift(files(tmp_path, HEADER + "2026-10-26,ok,1,08:40:05,08:40:01,,25125.5,1000,2026-10-29\n")).read(
        MON, "morning"
    )
    (cue,) = view.items
    assert (view.status, cue.value, cue.change, cue.as_of, cue.role) == (AVAILABLE, 25125.5, 0.502, MON, "context")


def test_no_file_a_damaged_one_or_no_level_is_named_in_the_edition(tmp_path):
    for verified in (files(tmp_path / "a"), files(tmp_path / "b", HEADER),
                     files(tmp_path / "c", HEADER + "2026-10-26,failed,3,,,NSE refused,,,\n"),
                     files(tmp_path / "d", HEADER + "2026-10-26,failed,3,,,stale,25125.5,1,\n"),  # never shown
                     files(tmp_path / "e", HEADER + "2026-10-26,ok,1,,,,25125.5,1,\n", damaged=True)):  # fmt: skip
        view = gift(verified).read(MON, "morning")
        assert view.status == NOT_AVAILABLE and view.items == () and view.why.startswith("GIFT Nifty: ")


def test_the_evening_does_not_show_a_pre_open_cue(tmp_path):
    assert gift(files(tmp_path)).read(MON, "evening").status == NOT_AVAILABLE
