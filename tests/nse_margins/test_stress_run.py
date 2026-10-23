"""Story A14c criteria 3 and 5-10 on planted files: coverage by date, the guardrails, the first-archived and
point-in-time checks, incremental equals full, deterministic evidence, and one #fno-desk line per run.

A held SF 100 at scale 1 has a whole margin of 53,950 a lot; a scale-20 day lifts it to 91,000 (rise 1.68674,
computed 1.7) and a scale-8 day to 67,600 (rise 1.25301, computed 1.3), against the owner's seed of 1.45."""

import time
from datetime import date

import pytest

from fno.nse_margins.stress_log import StressFactorFile
from fno.nse_margins.stress_run import StressFactorRun, StressSources
from tests.stress_factor_files import HEADER

from .stress_days import FIRST, day_bytes, day_file, manifest, planted, sf_tracker, weekday
from .test_job import Alerts

SEED = '2026-10-14,1.45,,,applied,"owner seed: response 77, decision 14 Oct",,\n'
RUN_DAY, THROUGH = date(2026, 11, 5), date(2026, 11, 4)
SPIKE = date(2026, 10, 7)


def local_csv(folder):
    """The evidence CSV beside the other two files (the wiring's goes to Drive with a receipt, O9b step 2)."""

    def save(day, data: bytes) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"stress_evidence_{day}.csv").write_bytes(data)

    return save


def run(
    tmp_path,
    files,
    run_day=RUN_DAY,
    archived=None,
    approved=None,
    full=False,
    rows=SEED,
    workers=1,
    read=None,
    tracker=sf_tracker,
    is_trading_day=weekday,
):
    tmp_path.mkdir(parents=True, exist_ok=True)
    factor = tmp_path / "stress_factor.csv"
    if not factor.exists():
        factor.write_text(HEADER + rows, encoding="utf-8")
    alerts, printed = Alerts(), []
    sources = StressSources(read or day_file(files), lambda: archived if archived is not None else manifest(files),
                            is_trading_day, tracker, FIRST, workers)  # fmt: skip
    evidence = tmp_path / "evidence"
    code = StressFactorRun(sources, StressFactorFile(factor), evidence, local_csv(evidence), alerts, run_day,
                           printed.append).run(full, approved)  # fmt: skip
    return code, factor.read_text(encoding="utf-8").splitlines()[-1].split(","), alerts.sent


def test_a_rise_is_applied_at_once_with_its_evidence(tmp_path):
    code, row, sent = run(tmp_path, planted(THROUGH, {SPIKE: 20.0}))
    assert code == 0 and row[:5] == ["2026-11-05", "1.7", "1.7", "1.686747", "applied"]
    assert row[6] == "2026-11-04" and len(row[7]) == 64
    assert (
        len(sent) == 1 and "applied 1.7" in sent[0] and "was 1.45" in sent[0] and "SF 100 entered 2026-10-01" in sent[0]
    )
    evidence = (tmp_path / "evidence" / "stress_evidence_2026-11-05.md").read_text(encoding="utf-8")
    assert "1.686747" in evidence and "Factor in force: 1.7 (applied)" in evidence


def test_any_fall_is_held_and_the_owner_is_asked(tmp_path):
    code, row, sent = run(tmp_path, planted(THROUGH, {SPIKE: 8.0}))
    assert code == 0 and row[:5] == ["2026-11-05", "1.45", "1.3", "1.253012", "held"]
    assert "held 1.45 (computed 1.3" in sent[0] and "waits for the owner" in sent[0]


def test_an_owner_approved_fall_is_applied_and_names_the_decision(tmp_path):
    code, row, sent = run(tmp_path, planted(THROUGH, {SPIKE: 8.0}), approved="da0f769d")
    assert code == 0 and row[1:5] == ["1.3", "1.3", "1.253012", "applied"] and "DESK_DECISIONS da0f769d" in sent[0]


@pytest.mark.parametrize(
    ("change", "said"),
    [
        (lambda m: {**{d: s for d, s in m.items() if d != date(2026, 10, 15)}, date(2026, 10, 17): "x"}, "2026-10-15"),
        (lambda m: {d: s for d, s in m.items() if d != THROUGH}, "2026-11-04"),
    ],
    ids=["same count, a date swapped", "latest session missing"],
)
def test_coverage_is_checked_by_date_and_a_gap_writes_nothing(tmp_path, change, said):
    files = planted(THROUGH)
    code, row, sent = run(tmp_path, files, archived=change(manifest(files)))
    assert code == 1 and row[0] == "2026-10-14" and "nothing written" in sent[0] and said in sent[0]


def test_a_file_that_is_not_the_first_archived_copy_writes_nothing(tmp_path):
    files = planted(THROUGH)
    archived = manifest(files) | {date(2026, 10, 5): "0" * 64}
    code, row, sent = run(tmp_path, files, archived=archived)
    assert code == 1 and row[0] == "2026-10-14" and "differs from its manifest SHA-256" in sent[0]


def test_a_file_written_at_or_after_9_on_its_day_writes_nothing(tmp_path):
    files = planted(THROUGH) | {date(2026, 10, 6): day_bytes(date(2026, 10, 6), 1.0, created="202610060900")}
    code, row, sent = run(tmp_path, files)
    assert code == 1 and row[0] == "2026-10-14" and "not before 09:00" in sent[0]


@pytest.mark.parametrize("spike", [date(2026, 10, 7), date(2026, 11, 20)], ids=["peak in run 1", "peak in run 2"])
def test_incremental_equals_full(tmp_path, spike):
    files = planted(date(2026, 12, 8), {spike: 20.0})
    run(tmp_path / "steps", files, run_day=RUN_DAY)  # the seed forces run 1 to be full
    _, incremental, _ = run(tmp_path / "steps", files, run_day=date(2026, 12, 9))
    _, full, _ = run(tmp_path / "once", files, run_day=date(2026, 12, 9))
    assert incremental[1:5] == full[1:5] and incremental[6] == full[6] == "2026-12-08"
    assert incremental[3] == "1.686747"


def test_a_second_run_on_the_same_files_writes_byte_identical_evidence(tmp_path):
    files = planted(THROUGH, {SPIKE: 20.0})
    run(tmp_path / "a", files)
    run(tmp_path / "b", files)
    for name in ("stress_evidence_2026-11-05.csv", "stress_files_2026-11-05.csv", "stress_evidence_2026-11-05.md"):
        assert (tmp_path / "a" / "evidence" / name).read_bytes() == (tmp_path / "b" / "evidence" / name).read_bytes()


def test_the_files_csv_names_every_session_and_its_sha256(tmp_path):
    files = planted(THROUGH)
    run(tmp_path, files)
    lines = (tmp_path / "evidence" / "stress_files_2026-11-05.csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 + len(files) and lines[1] == f"2026-10-01,nsccl.20261001.i1.zip,{manifest(files)[FIRST]}"


def test_no_completed_holding_writes_nothing(tmp_path):
    code, row, sent = run(tmp_path, planted(date(2026, 10, 30)), run_day=date(2026, 10, 31))
    assert code == 1 and row[0] == "2026-10-14" and "no holding completed" in sent[0]


def test_the_seed_s_hand_value_is_not_a_floor(tmp_path):
    """Judge 176: after the seed the run is full; a true maximum of 1.25 is computed 1.3 and held against 1.45."""
    _, row, _ = run(tmp_path, planted(THROUGH, {SPIKE: 8.0}))
    assert row[3] == "1.253012" and row[2] == "1.3"


def test_any_row_without_a_measured_value_forces_a_full_run(tmp_path):
    """Not only the seed: a row with a coverage date but an empty `unrounded` (a hand value) is never a floor."""
    hand = "2026-11-04,1.45,,,applied,owner hand value,2026-11-03,\n"  # after every 2 Nov exit
    _, row, _ = run(tmp_path, planted(THROUGH, {SPIKE: 8.0}), rows=SEED + hand)
    assert row[3] == "1.253012" and row[4] == "held"


def test_an_incremental_run_counts_only_holdings_that_ended_since_the_last(tmp_path):
    files = planted(date(2026, 12, 8))
    run(tmp_path, files, run_day=RUN_DAY)  # full: the 17 holdings entered 1-23 Oct end on 2 Nov
    run(tmp_path, files, run_day=date(2026, 12, 9))  # incremental: the 25 entered 26 Oct-27 Nov end on 7 Dec
    first = (tmp_path / "evidence" / "stress_evidence_2026-11-05.md").read_text(encoding="utf-8")
    second = (tmp_path / "evidence" / "stress_evidence_2026-12-09.md").read_text(encoding="utf-8")
    assert "Holdings completed in this run: 17;" in first and "Holdings completed in this run: 25;" in second


def test_reading_ahead_changes_no_byte_of_the_row_or_the_evidence(tmp_path):
    """The full run's read-ahead (eight Drive downloads at once in config) against one at a time, on files whose
    downloads finish in reverse order: the same factor row and byte-identical evidence."""
    files = planted(date(2026, 12, 8), {SPIKE: 20.0, date(2026, 11, 20): 8.0})
    fed = {"one": [], "ahead": []}

    def mondays_last(day):
        time.sleep(0.05 if day.weekday() == 0 else 0)  # Monday's download finishes after the rest of its week's
        return day_file(files)(day)

    def recording(name):
        def new():
            tracker = sf_tracker()
            feed = tracker.feed
            tracker.feed = lambda day, span, open_new=True: (fed[name].append(day), feed(day, span, open_new))
            return tracker

        return new

    _, one, _ = run(tmp_path / "one", files, run_day=date(2026, 12, 9), tracker=recording("one"))
    _, ahead, _ = run(tmp_path / "ahead", files, run_day=date(2026, 12, 9), workers=8, read=mondays_last,
                      tracker=recording("ahead"))  # fmt: skip
    assert fed["ahead"] == fed["one"] == sorted(files) and ahead == one and one[3] == "1.686747"
    for name in ("stress_evidence_2026-12-09.csv", "stress_files_2026-12-09.csv", "stress_evidence_2026-12-09.md"):
        assert (tmp_path / "ahead" / "evidence" / name).read_bytes() == (
            tmp_path / "one" / "evidence" / name
        ).read_bytes()


def test_a_download_error_writes_nothing_and_says_so(tmp_path):
    files = planted(THROUGH)

    def drive_down(day):
        if day == date(2026, 10, 20):
            raise ConnectionError("Drive answered 503")
        return day_file(files)(day)

    code, row, sent = run(tmp_path, files, workers=4, read=drive_down)
    assert code == 1 and row[0] == "2026-10-14" and not (tmp_path / "evidence").exists()
    assert len(sent) == 1 and "nothing written: the archive could not be read: Drive answered 503" in sent[0]
