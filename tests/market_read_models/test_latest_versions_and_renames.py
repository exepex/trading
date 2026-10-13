"""Story P6, judge 49: publishing reads NSE's latest version of each file (A11's revisions), a renamed stock keeps its
history under the old symbol (NSE's symbol-change file: TATAMOTORS became TMPV, HEG became HEGAM), and a 52-week
figure is null, never computed over a shorter window, when a corporate action without a price cut that window."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from fno.config import load_app_config
from fno.market_read_models import wiring as market_wiring
from fno.market_read_models.corporate_actions import adjusted, read_corporate_actions
from fno.market_read_models.index_rows import index_rows
from fno.market_read_models.nse_files import EquityBar, read_index_figures
from fno.market_read_models.stock_rows import stock_row
from fno.market_read_models.symbol_changes import SymbolChange, joined, read_symbol_changes
from fno.storage.manifest_folder import Fingerprint, ManifestFolder
from fno.storage.raw_source import NseIndexCloseSource, PublishedFile
from fno.storage.raw_store import LocalFolderStore
from fno.storage.revisions import RevisionArchive, RevisionIndex
from fno.storage.snapshot_source import EquityListSource
from fno.storage.versioned_store import VersionedRawStore
from fno.storage.wiring import RAW_SOURCES

from .test_corporate_actions import nse_list

FIXTURES = Path(__file__).parents[1] / "fixtures" / "nse" / "revisions"
OCT_12 = date(2026, 10, 12)
PATH = NseIndexCloseSource.path_for(OCT_12)
ADDED_IN_THE_REWRITE = ("Nifty Capital Goods", "Nifty Telecommunications")  # NSE, 23:20 IST on 12 Oct 2026


def latest_reader(tmp_path) -> VersionedRawStore:
    """The raw archive with NSE's first 12 Oct index file and its rewrite kept as a revision (A11)."""
    raw, revisions = LocalFolderStore(tmp_path / "raw"), LocalFolderStore(tmp_path / "revisions")
    manifests, index = ManifestFolder(tmp_path / "manifests"), RevisionIndex(tmp_path / "revisions.csv", RAW_SOURCES)
    first = (FIXTURES / "ind_close_all_12102026.first.csv").read_bytes()
    raw.put(PATH, first)
    manifests.record(NseIndexCloseSource, Fingerprint.of(NseIndexCloseSource, PATH, first))
    archive = RevisionArchive(raw, revisions, index, manifests, lambda: datetime(2026, 10, 13, tzinfo=UTC))
    rewritten = (FIXTURES / "ind_close_all_12102026.rewritten.csv").read_bytes()
    archive.capture(PATH, PublishedFile(rewritten, datetime(2026, 10, 12, 17, 50, 10, tzinfo=UTC)))
    raw.put(EquityListSource.path_for(OCT_12), b"SYMBOL,NAME OF COMPANY\n")  # a reference list: never revised
    return VersionedRawStore(raw, revisions, index, as_of=None)


def sector_names(data: bytes) -> set[str]:
    return {row["name"] for row in index_rows([(OCT_12, read_index_figures(data, PATH))])}


def test_the_sectors_come_from_nses_latest_version_of_the_index_file(tmp_path):
    reader = latest_reader(tmp_path)
    assert set(ADDED_IN_THE_REWRITE) <= sector_names(reader.get(PATH))
    assert not set(ADDED_IN_THE_REWRITE) & sector_names(reader.raw.get(PATH))  # the first version lacks both
    assert reader.get(EquityListSource.path_for(OCT_12)) == b"SYMBOL,NAME OF COMPANY\n"  # no index: the raw copy


def test_publishing_is_wired_to_the_latest_reader(monkeypatch):
    calls = []
    monkeypatch.setattr(market_wiring, "build_versioned_reader", lambda *args: calls.append(args) or "latest")
    assert market_wiring.build_session_rows_builder(load_app_config()).store == "latest" and calls == [()]


def test_nses_symbol_change_file_is_read_with_its_padded_header():
    text = (
        "NAME OF THE COMPANY, OLD SYMBOL ,NEW SYMBOL,EFFECTIVE DATE\nTata Motors,TATAMOTORS,TMPV,24-OCT-2025\n,X,Y,\n"
    )
    assert read_symbol_changes(text.encode(), "symbolchange.csv") == [
        SymbolChange("TATAMOTORS", "TMPV", date(2025, 10, 24))
    ]


def tmpv_series():
    """NSE's closes (judge 42 addendum 3): TATAMOTORS until 23 Oct 2025, its demerger ex-date 14 Oct (previous close
    660.75, open 400.00), TMPV from 24 Oct; NSE lists the demerger under TMPV."""
    days = [date(2025, 10, 7) + timedelta(days=i) for i in range(251)]
    ex, renamed = 5, 13

    def bar(i, d):
        close = 700.0 if i < ex else 400.0 if i < 250 else 284.45
        return EquityBar(
            d, "TATAMOTORS" if i < renamed else "TMPV", "EQ", close, close, close, 1, 400.0 if i == ex else None
        )

    bars = [bar(i, d) for i, d in enumerate(days)]
    bars[ex - 1] = EquityBar(days[ex - 1], "TATAMOTORS", "EQ", 660.75, 700.0, 660.75, 1)
    series = {"TATAMOTORS": bars[:renamed], "TMPV": bars[renamed:]}
    actions = read_corporate_actions(nse_list(("TMPV", f"{days[ex]:%d-%b-%Y}", "Demerger")), "list.json")
    return series, actions, SymbolChange("TATAMOTORS", "TMPV", days[renamed])


def test_tmpv_keeps_its_tatamotors_sessions_and_its_demerger_uses_the_ex_date_open():
    series, actions, change = tmpv_series()
    before = stock_row(adjusted(series["TMPV"], actions), "TMPV", "", None, [])
    assert before["y1"] is None and before["h"] == 400.0  # 238 sessions: no year, a high over part of it
    joined_series, joined_actions = joined(series, actions, [change])
    assert set(joined_series) == {"TMPV"} and len(joined_series["TMPV"]) == 251
    row = stock_row(adjusted(joined_series["TMPV"], joined_actions), "TMPV", "", None, [])
    assert row["y1"] == round((284.45 / round(700.0 / (660.75 / 400.0), 2) - 1) * 100, 2)  # factor 1.6519
    assert row["h"] == round(700.0 / (660.75 / 400.0), 2)  # the pre-demerger high on today's basis


def test_a_rename_applies_old_symbol_actions_and_chains_in_date_order():
    day = date(2025, 1, 1)
    bars = {s: [EquityBar(day + timedelta(days=i), s, "EQ", 1.0, 1.0, 1.0, 1)] for i, s in enumerate(("A", "B", "C"))}
    actions = read_corporate_actions(nse_list(("A", f"{day:%d-%b-%Y}", "Bonus 1:1")), "list.json")
    changes = [SymbolChange("B", "C", day + timedelta(days=2)), SymbolChange("A", "B", day + timedelta(days=1))]
    series, moved = joined(bars, actions, changes)
    assert [b.symbol for b in series["C"]] == ["C", "C", "C"] and [a.symbol for a in moved] == ["C"]


def test_a_cut_window_has_no_52_week_high_low_or_volume_average_but_a_later_listing_keeps_them():
    days = [date(2025, 10, 7) + timedelta(days=i) for i in range(251)]
    bars = [EquityBar(d, "P", "EQ", 100.0 + i % 7, 110.0, 90.0 + i % 3, 10) for i, d in enumerate(days)]
    cut = adjusted(bars, read_corporate_actions(nse_list(("P", f"{days[240]:%d-%b-%Y}", "Demerger")), "list.json"))
    assert len(cut) == 11
    row = stock_row(cut, "P", "", None, [], cut=True)
    assert (row["y1"], row["h"], row["l"], row["va"]) == (None, None, None, None) and row["d1"] is not None
    listed_late = stock_row(bars[-11:], "P", "", None, [])  # every session there is: its 52-week range is complete
    assert (listed_late["h"], listed_late["l"]) == (110.0, 90.0) and listed_late["va"] == 10.0
