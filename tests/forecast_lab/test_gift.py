"""FL1-1d-2: GIFT Nifty at 08:50 from A22b's own file, verified through O9's cache: its level and gap to the previous
official NIFTY close when A22 recorded one (ok or late); otherwise the edition names it itself; never in the evening."""

from datetime import date

from fno.forecast_lab.page.cues import AVAILABLE, NOT_AVAILABLE
from fno.forecast_lab.sections.gift import GiftSection

MON = date(2026, 10, 26)
HEADER = "date,gift_status,gift_reads,gift_seen_at,gift_source_time,gift_detail,gift_level,gift_contracts,gift_expiry\n"


class Report:
    def __init__(self, problems=()):
        self.problems = list(problems)


class Cache:
    def __init__(self, tmp_path, text=None, problems=()):
        self.root, self.text, self.problems, self.synced = tmp_path, text, problems, []

    def local(self, path):
        return self.root / path

    def sync(self, prefix):
        self.synced.append(prefix)
        if self.text is not None:  # with problems too: an older local copy may still be on disk
            (self.root / prefix).parent.mkdir(parents=True, exist_ok=True)
            (self.root / prefix).write_text(self.text, encoding="utf-8")
        return Report(self.problems)


def gift(cache):
    return GiftSection(cache, lambda day: 25000.0)


def test_a_recorded_level_is_shown_with_its_gap_to_the_previous_close(tmp_path):
    cache = Cache(tmp_path, HEADER + "2026-10-26,ok,1,08:40:05,08:40:01,,25125.5,1000,2026-10-29\n")
    view = gift(cache).read(MON, "morning")
    (cue,) = view.items
    assert (view.status, cue.value, cue.change, cue.as_of, cue.role) == (AVAILABLE, 25125.5, 0.502, MON, "context")
    assert cache.synced == ["data/preopen/gift/2026/10/2026-10-26.csv"]


def test_no_file_a_damaged_one_or_no_level_is_named_in_the_edition(tmp_path):
    for cache in (Cache(tmp_path / "a"), Cache(tmp_path / "b", HEADER, problems=["damaged"]),
                  Cache(tmp_path / "c", HEADER + "2026-10-26,failed,3,,,NSE refused,,,\n"),
                  Cache(tmp_path / "d", HEADER + "2026-10-26,failed,3,,,stale,25125.5,1,\n"),  # never shown
                  Cache(tmp_path / "e", HEADER + "2026-10-26,ok,1,,,,25125.5,1,\n", problems=["damaged"])):  # fmt: skip
        view = gift(cache).read(MON, "morning")
        assert view.status == NOT_AVAILABLE and view.items == () and view.why.startswith("GIFT Nifty: ")


def test_the_evening_does_not_show_a_pre_open_cue(tmp_path):
    assert gift(Cache(tmp_path)).read(MON, "evening").status == NOT_AVAILABLE
