"""A22d, criteria D4-D6: the day row's basis columns, the open check against NSE's official open (one tick, write-once
check files, no value in a problem line) and the flat 09:15 label (verified after 5 matched checks)."""

from __future__ import annotations

import csv
import io
from datetime import date

import pytest

from fno.preopen.answers import Reading
from fno.preopen.day_row import columns, day_row
from fno.preopen.parts import Answer
from fno.preopen.run import INCOMPLETE, OK, PartResult

from .desk import Desk, previous_weekday
from .fixtures import DAY, index_close, ist

D21, D20, D19, D16, D15, D14 = (date(2026, 10, d) for d in (21, 20, 19, 16, 15, 14))


def _result(part: str, values: dict, status: str = OK) -> PartResult:
    return PartResult(part, status, 1, Answer(b"raw", Reading(status == OK, None, values), ist(9, 10)), "")


def _row(data: bytes) -> dict:
    return next(csv.DictReader(io.StringIO(data.decode())))


A22_HEADER = ("date", "clock", *(f"{part}_{cell}" for part in ("gift", "fo_list", "nifty", "banknifty")
                                 for cell in ("status", "reads", "seen_at", "source_time", "detail")),
              "gift_level", "gift_contracts", "gift_expiry", "fo_stocks", "fo_with_iep", "nifty_preopen",
              "banknifty_preopen")  # fmt: skip  # the day row's header before A22d (23 Oct's)


def test_d4_the_day_row_gains_one_basis_column_per_index_after_its_value():
    names = columns()
    assert tuple(n for n in names if not n.endswith("_preopen_basis")) == A22_HEADER
    assert names[-4:] == ("nifty_preopen", "nifty_preopen_basis", "banknifty_preopen", "banknifty_preopen_basis")


def test_d4_a_flat_value_carries_its_label_and_a_0909_value_its_basis():
    results = [_result("nifty", {"nifty_preopen": "1.5", "nifty_preopen_basis": "flat_0915"}),
               _result("banknifty", {"banknifty_preopen": "2.5", "banknifty_preopen_basis": "flat_0915"})]  # fmt: skip
    row = _row(day_row(DAY, "ok", results, {"nifty": "verified"}))
    labels = (row["nifty_preopen_basis"], row["banknifty_preopen_basis"])
    assert labels == ("flat_0915_verified", "flat_0915_unverified")
    row = _row(day_row(DAY, "ok", [_result("nifty", {"nifty_preopen": "1.5", "nifty_preopen_basis": "candle_0909"})]))
    assert row["nifty_preopen_basis"] == "candle_0909"


def test_d4_an_index_with_no_value_has_a_blank_basis():
    values = {"nifty_preopen": "1.5", "nifty_preopen_basis": "flat_0915"}
    row = _row(day_row(DAY, "ok", [_result("nifty", values, INCOMPLETE)]))
    assert (row["nifty_preopen"], row["nifty_preopen_basis"]) == ("", "")


@pytest.mark.parametrize(("difference", "result"), [(0.0, "match"), (0.05, "match"), (0.06, "mismatch"),
                                                    (-0.06, "mismatch")])  # fmt: skip
def test_d5_one_tick_is_a_match_more_is_a_mismatch(tmp_path, difference, result):
    desk = Desk(tmp_path, official={D21: index_close(nifty_open=5555.5 - difference, bank_open=6666.5)})
    desk.plant_day_row(D21, nifty="5555.5", banknifty="6666.5")
    summary, problems = desk.open_check().run(DAY)
    rows = {r["index"]: r for r in desk.check_rows(D21)}
    assert summary == "open check: 1 checked, 0 waiting for NSE's file"
    assert (rows["nifty"]["result"], rows["banknifty"]["result"]) == (result, "match")
    assert rows["nifty"]["difference"] == f"{difference:.2f}" and rows["nifty"]["basis"] == "flat_0915_unverified"
    assert (desk.root / "receipts/data/preopen/check/2026/10/2026-10-21.csv.sha256").is_file()
    expected = [] if result == "match" else ["nifty open check mismatch: flat 09:15 candle differs from "
                                             "NSE's official open on 2026-10-21"]  # fmt: skip
    assert [p.line() for p in problems] == expected  # no value and no difference in the line


def test_d5_no_official_file_yet_writes_nothing_and_is_retried_next_morning(tmp_path):
    desk = Desk(tmp_path)
    desk.plant_day_row(D21, nifty="5555.5")
    assert desk.open_check().run(DAY) == ("open check: 0 checked, 1 waiting for NSE's file", [])
    assert desk.check_rows(D21) == []
    desk.official[D21] = index_close()
    assert desk.open_check().run(DAY)[0] == "open check: 1 checked, 0 waiting for NSE's file"
    assert [r["result"] for r in desk.check_rows(D21)] == ["match"]


def test_d5_a_checked_session_is_not_read_again(tmp_path):
    desk = Desk(tmp_path, official={D21: index_close()})
    desk.plant_day_row(D21, nifty="5555.5")
    desk.open_check().run(DAY)
    check = desk.open_check()
    assert check.run(DAY)[0] == "open check: 0 checked, 0 waiting for NSE's file" and desk.files.read_paths == []


def test_d5_no_day_rows_does_nothing(tmp_path):
    desk = Desk(tmp_path, official={D21: index_close()})
    assert desk.open_check().run(DAY) == ("open check: 0 checked, 0 waiting for NSE's file", [])
    assert not (desk.root / "receipts").exists()


def test_d5_a_row_with_no_value_is_skipped_and_an_old_header_row_is_checked_with_a_blank_basis(tmp_path):
    desk = Desk(tmp_path, official={D21: index_close(), D20: index_close()})
    desk.plant_day_row(D21)  # 23 Oct's kind: both incomplete
    desk.plant_day_row(D20, nifty="5555.5", old_header=True)  # written before A22d
    assert desk.open_check().run(DAY)[0] == "open check: 1 checked, 0 waiting for NSE's file"
    assert desk.check_rows(D21) == [] and [(r["basis"], r["result"]) for r in desk.check_rows(D20)] == [("", "match")]


def test_d5_an_unreadable_file_is_one_problem_line_and_the_rest_is_checked(tmp_path):
    def broken(path):
        if "2026-10-21" in path:
            raise RuntimeError("Drive down")

    desk = Desk(tmp_path, official={D21: index_close(), D20: index_close()}, on_read=broken)
    desk.plant_day_row(D21, nifty="5555.5")
    desk.plant_day_row(D20, nifty="5555.5")
    summary, problems = desk.open_check().run(DAY)
    assert [p.line() for p in problems] == ["open check failed: 2026-10-21: RuntimeError"]
    assert summary == "open check: 1 checked, 0 waiting for NSE's file"


def _checked_sessions(desk: Desk, days: list[date], mismatched: tuple[date, ...] = (), basis="flat_0915_unverified"):
    for day in days:
        desk.official[day] = index_close(nifty_open=5555.0 if day in mismatched else 5555.5)
        desk.plant_day_row(day, nifty="5555.5", banknifty="6666.5", basis=basis)
    desk.open_check().run(DAY)


@pytest.mark.parametrize(
    ("days", "mismatched", "label"),
    [([D21, D20, D19, D16], (), "unverified"),  # 4 matches
     ([D21, D20, D19, D16, D15], (), "verified"),  # boundary: 5
     ([D21, D20, D19, D16, D15], (D21,), "unverified"),  # the newest mismatched
     ([D21, D20, D19, D16, D15], (D15,), "unverified"),  # a mismatch among the 5
     ([D21, D20, D19, D16, D15, D14], (D14,), "verified"),  # 5 fresh matches after a mismatch
     ([D21, D20, D19, D16, D15, D14], (D21,), "unverified")],  # a mismatch is never skipped to reach 5 matches
)  # fmt: skip
def test_d6_a_flat_value_is_verified_only_after_5_matched_checks(tmp_path, days, mismatched, label):
    desk = Desk(tmp_path)
    _checked_sessions(desk, days, mismatched)
    assert desk.open_check().labels(DAY) == {"nifty": label, "banknifty": "verified" if len(days) >= 5 else label}


def test_d6_old_header_checks_with_a_blank_basis_never_count(tmp_path):
    desk = Desk(tmp_path)
    for day in (D21, D20, D19, D16, D15):
        desk.official[day] = index_close()
        desk.plant_day_row(day, nifty="5555.5", old_header=True)
    desk.open_check().run(DAY)
    assert desk.open_check().labels(DAY)["nifty"] == "unverified"


def test_d6_no_check_file_and_0909_values_leave_flat_values_unverified(tmp_path):
    desk = Desk(tmp_path)
    assert desk.open_check().labels(DAY) == {"nifty": "unverified", "banknifty": "unverified"}
    _checked_sessions(desk, [D21, D20, D19, D16, D15], basis="candle_0909")
    assert desk.open_check().labels(DAY) == {"nifty": "unverified", "banknifty": "unverified"}


def test_d5_a_banknifty_or_0909_mismatch_names_its_own_index_and_kind(tmp_path):
    desk = Desk(tmp_path, official={D21: index_close(bank_open=6000.0)})
    desk.plant_day_row(D21, nifty="5555.5", banknifty="6666.5", basis="candle_0909")
    assert [p.line() for p in desk.open_check().run(DAY)[1]] == [
        "banknifty open check mismatch: pre-open value differs from NSE's official open on 2026-10-21"
    ]


def test_d5_a_missing_bank_row_is_its_own_problem_and_nifty_is_still_checked(tmp_path):
    no_bank = b"\n".join(line for line in index_close().split(b"\n") if not line.startswith(b"Nifty Bank"))
    desk = Desk(tmp_path, official={D21: no_bank})
    desk.plant_day_row(D21, nifty="5555.5", banknifty="6666.5")
    assert [p.line() for p in desk.open_check().run(DAY)[1]] == [
        "banknifty open check no official value: no readable NIFTY BANK row in NSE's index-close file of 2026-10-21"
    ]
    assert [(r["index"], r["result"]) for r in desk.check_rows(D21)] == [
        ("nifty", "match"),
        ("banknifty", "no official value"),
    ]


def test_d5_a_session_still_waiting_on_its_last_look_back_morning_is_named(tmp_path):
    days, day = [], DAY
    for _ in range(10):
        day = previous_weekday(day)
        days.append(day)
    desk = Desk(tmp_path)
    desk.plant_day_row(days[-1], nifty="5555.5")
    desk.plant_day_row(days[-2], nifty="5555.5")
    summary, problems = desk.open_check().run(DAY)
    assert summary == "open check: 0 checked, 2 waiting for NSE's file"
    assert [p.line() for p in problems] == [f"open check not checked: {days[-1]}: NSE's index-close file still not "
                                            "archived after 10 sessions; it leaves the look-back"]  # fmt: skip


def test_d5_a_receipt_that_cannot_be_read_is_one_failed_line(tmp_path, monkeypatch):
    desk = Desk(tmp_path, official={D21: index_close()})
    desk.plant_day_row(D21, nifty="5555.5")
    check = desk.open_check()

    def broken(path):
        raise ValueError("malformed receipt")

    monkeypatch.setattr(check.files, "has", broken)
    assert check.run(DAY)[1][0].line() == "open check failed: 2026-10-21: ValueError"


def test_d5_a_check_file_written_differently_by_another_run_is_taken(tmp_path):
    desk = Desk(tmp_path, official={D21: index_close()})
    desk.plant_day_row(D21, nifty="5555.5")
    desk.drive.put("data/preopen/check/2026/10/2026-10-21.csv", b"another run's check\n")  # no receipt here
    assert [p.kind for p in desk.open_check().run(DAY)[1]] == ["taken"]


def test_d5_the_look_back_is_10_sessions_the_11th_is_not_checked(tmp_path):
    days, day = [], DAY
    for _ in range(11):
        day = previous_weekday(day)
        days.append(day)
    desk = Desk(tmp_path, official={d: index_close() for d in days})
    for d in days:
        desk.plant_day_row(d, nifty="5555.5")
    assert desk.open_check().run(DAY)[0] == "open check: 10 checked, 0 waiting for NSE's file"
    assert desk.check_rows(days[-1]) == [] and desk.check_rows(days[-2]) != []
