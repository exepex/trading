"""REH1g round 2 (judges 572 and 574): a file is dated only by the row its own writer committed, at that commit's
committer time. A revision log's or a filings list's `path` row never moves a file's time; an author date older than
the commit never counts; of two rows for one file the earlier commit counts; a dataset is matched by its whole folder
name."""

from datetime import UTC, date, datetime

import fno.rehearsal.manifest_rows as manifest_rows
from fno.rehearsal.manifest_rows import MANIFESTS, ManifestRows

from .test_manifest_rows import INDEX_CLOSE, SP500, git, publish, record

A9_COMMIT = datetime(2026, 10, 16, 19, 1, 48, tzinfo=UTC)  # the 16 Oct close's row, in `record`


def commit_file(repo, relative, text, when, authored=None):
    file = repo / relative
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", relative, when=when, authored=authored)
    publish(repo)


def test_a_revision_row_committed_after_the_a9_row_does_not_change_the_file_s_time(tmp_path):
    repo, _ = record(tmp_path)
    revision = (
        "date,path,sha256,size_bytes\n2026-10-18,nse/indices/index-close/2026/10/ind_close_all_16102026.csv,ff,1\n"
    )
    commit_file(repo, MANIFESTS / "revisions" / "index-close.csv", revision, "2026-10-18T10:00:00+00:00")
    assert ManifestRows(repo).seen_at(INDEX_CLOSE) == A9_COMMIT


def test_a_filings_list_row_naming_a_cue_path_does_not_date_it(tmp_path):
    repo, _ = record(tmp_path)
    listed = f"symbol,path\nX,{SP500.removeprefix('raw/')}\n"
    commit_file(repo, MANIFESTS / "filings" / "outside-layout.csv", listed, "2026-10-22T00:00:00+00:00")
    assert ManifestRows(repo).seen_at(SP500) == datetime(2026, 10, 23, 0, 42, 24, tzinfo=UTC)  # the cue log's row


def test_the_time_is_the_committer_time_not_an_older_author_time(tmp_path):
    repo, _ = record(tmp_path)
    row = "2026-10-23T08:50:34+05:30,yahoo/preopen/2026/10/23/085034_kospi_5m.json,u,,ab,1\n"
    log = "fetched_at,path,url,form,sha256,size_bytes\n" + row
    commit_file(repo, MANIFESTS / "global-cues" / "kospi_preopen.csv", log, "2026-10-23T03:23:35+00:00",
                authored="2026-10-23T03:20:00+00:00")  # fmt: skip
    seen = ManifestRows(repo).seen_at("raw/yahoo/preopen/2026/10/23/085034_kospi_5m.json")
    assert seen == datetime(2026, 10, 23, 3, 23, 35, tzinfo=UTC)


def test_of_two_rows_for_one_file_the_earlier_commit_counts(tmp_path):
    repo, _ = record(tmp_path)
    again = (
        f"fetched_at,path,url,form,sha256,size_bytes\n2026-10-23T06:06:20+05:30,{SP500.removeprefix('raw/')},u,,cd,1\n"
    )
    commit_file(repo, MANIFESTS / "global-cues" / "sp500_again.csv", again, "2026-10-24T00:00:00+00:00")
    assert ManifestRows(repo).seen_at(SP500) == datetime(2026, 10, 23, 0, 42, 24, tzinfo=UTC)


def test_a_dataset_is_matched_by_its_whole_folder_name_whatever_the_source_order(monkeypatch):
    """`nse/flows/fii-dii-cash` is a prefix of `nse/flows/fii-dii-cash-by-session`: the folder's `/` decides."""
    monkeypatch.setattr(manifest_rows, "RAW_SOURCES", tuple(reversed(manifest_rows.RAW_SOURCES)))
    key = manifest_rows._a9_key("nse/flows/fii-dii-cash-by-session/2026/10/23/fii-dii-cash.json")
    assert key == ("fii-dii-cash-by-session", date(2026, 10, 23), "https://www.nseindia.com/api/fiidiiTradeReact")
    monkeypatch.setattr(manifest_rows, "RAW_SOURCES", tuple(reversed(manifest_rows.RAW_SOURCES)))
    assert manifest_rows._a9_key("nse/flows/fii-dii-cash/2026/10/13/fii-dii-cash.json")[0] == "fii-dii-cash"
