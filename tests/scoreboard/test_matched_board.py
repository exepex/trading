"""Story S3 criteria 1-4, 7 and 9 on a whole board built from fixture records: the known-answer example, the shared
pack and snapshot, not-observed days and opportunities, Book 3 before F7, the miss cap, determinism and the schema."""

from datetime import date

from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, Decision
from fno.scoreboard.matched_board import CLAIM, NO_CLAIM, UNDECIDED_F7, UNDECIDED_OPERATIONS, _verdict
from fno.scoreboard.matched_days import F7_NOT_BUILT, NO_RECORD, NO_SNAPSHOT, OTHER_PACK
from fno.scoreboard.whole_system import canonical
from tests.scoreboard.builders import write_log
from tests.scoreboard.matched_builders import LOT, board, quote, record, write_day, write_pack, write_run

D1, D2, EXIT, ON = date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 4), date(2026, 11, 5)
QUOTES = {D1: [quote(25000, "CE", 99, 100)], D2: [quote(25000, "CE", 99, 100, size=LOT - 1)],
          EXIT: [quote(25000, "CE", 130, 131)], ON: []}  # fmt: skip


def runs_for(root, day, book1=(), book2=(), pack="", book1_on_time=True):
    ids = {book: write_run(root, book, day, *records, pack=pack)
           for book, records in ((BOOK1_RULES, book1), (BOOK2_HYBRID, book2), (BOOK3_AI, ()))}  # fmt: skip
    if not book1_on_time:
        ids[BOOK1_RULES] = None
    write_day(root, day, ids)


def known_answer(root):
    """Day 1: Book 1 takes O1 (closes on its exit day), Book 2 skips it. Day 2: Book 1 takes O2, whose leg has too
    little size at the touch (not filled), Book 2 skips. Days 3-4: nothing to decide. Book 3: before F7."""
    pack = write_pack(root, D1, ("O1", EXIT))
    runs_for(root, D1, [record("O1", pack=pack)], [record("O1", Decision.NO_TRADE, "rule did not fire", pack=pack)],
             pack=pack)  # fmt: skip
    pack = write_pack(root, D2, ("O2", EXIT))
    runs_for(root, D2, [record("O2", pack=pack)], [record("O2", Decision.NO_TRADE, "no", pack=pack)], pack=pack)
    for day in (EXIT, ON):
        runs_for(root, day, pack=write_pack(root, day))
    return board(root, QUOTES).build(ON)


def test_the_known_answer_example_reproduces_book_1s_ratio_and_the_pair_differences(tmp_path):
    result = known_answer(tmp_path)
    head = result["books"][BOOK1_RULES]["head_to_head"]
    # O1: paid 7,520, received 9,730: net 2,210; B2 maximum loss 7,615. O2 not filled: 0, out of the maximum-loss sum.
    assert head["takes"] == {"closed": 1, "open": 0, "not filled": 1, "maximum loss unknown": 0}
    assert (head["judged"]["net_rs"], head["judged"]["risk_rs"], head["judged"]["days"]) == (2210.0, 7615.0, 4)
    assert head["judged"]["ratio"] == round(2210 / 7615, 6)
    pair = result["pairs"][f"{BOOK1_RULES} - {BOOK2_HYBRID}"]["judged"]
    assert (pair["days"], pair["net_rs"], pair["ratio"]) == (4, 2210.0, 552.5)  # differences 2,210, 0, 0, 0
    assert result["pairs"][f"{BOOK1_RULES} - {BOOK3_AI}"]["judged"] == {"days": 0, "reason": "no common day"}


def test_book_3_before_f7_is_counted_apart_and_undecided(tmp_path):
    entry = known_answer(tmp_path)["books"][BOOK3_AI]
    assert entry["verdict"] == UNDECIDED_F7 and entry["misses"] == 0
    assert entry["head_to_head"]["not_observed"] == {F7_NOT_BUILT: 4}


def test_a_record_naming_another_pack_and_a_missing_record_are_not_observed(tmp_path):
    pack = write_pack(tmp_path, D1, ("O1", EXIT), ("O3", EXIT))
    runs_for(tmp_path, D1, [record("O1", pack="another")], [record("O1", pack=pack), record("O3", pack=pack)],
             pack=pack)  # fmt: skip
    rows = {(r["book"], r["opportunity_id"]): r for r in board(tmp_path, QUOTES).build(D1)["actions"]}
    assert rows[(BOOK1_RULES, "O1")]["reason"] == OTHER_PACK and rows[(BOOK1_RULES, "O3")]["reason"] == NO_RECORD
    assert rows[(BOOK2_HYBRID, "O1")]["action"] == "take"


def test_a_day_without_a_valid_snapshot_scores_no_book_and_is_outside_the_miss_cap(tmp_path):
    pack = write_pack(tmp_path, D1, ("O1", EXIT))
    for book in (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI):
        write_run(tmp_path, book, D1, record("O1", pack=pack), pack=pack)
    write_day(tmp_path, D1, {b: f"{D1.isoformat()}-{b}" for b in (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI)}, False)
    entry = board(tmp_path, QUOTES).build(D1)["books"][BOOK1_RULES]
    assert entry["head_to_head"]["not_observed"] == {NO_SNAPSHOT: 1}
    assert (entry["eligible_days"], entry["misses"]) == (0, 0)


def test_a_late_run_is_a_miss(tmp_path):
    pack = write_pack(tmp_path, D1, ("O1", EXIT))
    runs_for(tmp_path, D1, [record("O1", pack=pack)], [record("O1", pack=pack)], pack=pack, book1_on_time=False)
    entry = board(tmp_path, QUOTES).build(D1)["books"][BOOK1_RULES]
    assert (entry["misses"], entry["eligible_days"], entry["miss_share"]) == (1, 1, 1.0)
    assert entry["verdict"] == UNDECIDED_OPERATIONS


def verdict(share, claim=True, holm=True):
    head = {"judged": {"claim_allowed": claim, "holm_pass": holm}}
    return _verdict({"f7_not_built": False, "miss_share": share, "head_to_head": head})


def test_the_miss_cap_is_over_10_percent_not_at_it():
    assert verdict(0.10) == CLAIM and verdict(0.1001) == UNDECIDED_OPERATIONS
    assert verdict(0.0, holm=False) == NO_CLAIM and verdict(None, claim=False) == NO_CLAIM


def test_a_rebuild_from_the_same_records_is_byte_identical(tmp_path):
    assert canonical(known_answer(tmp_path)) == canonical(board(tmp_path, QUOTES).build(ON))


def test_no_field_of_scoreboard_a_holds_a_scoreboard_b_figure(tmp_path):
    text = canonical(known_answer(tmp_path))
    for field in ("raw_account_net_rs", "net_per_unit_of_risk", "scoreboard_b", "reconciliation"):
        assert field not in text


def test_two_books_taking_the_same_opportunity_get_the_same_one_lot_result(tmp_path):
    pack = write_pack(tmp_path, D1, ("O1", EXIT))
    runs_for(tmp_path, D1, [record("O1", pack=pack)], [record("O1", pack=pack)], pack=pack)
    for day in (EXIT, ON):
        runs_for(tmp_path, day, pack=write_pack(tmp_path, day))
    rows = [r for r in board(tmp_path, QUOTES).build(ON)["actions"] if r["opportunity_id"] == "O1"]
    assert [(r["net_rs"], r["max_loss_rs"]) for r in rows] == [(2210.0, 7615.0)] * 2  # one shared snapshot


def test_a_run_committed_after_the_snapshot_started_is_late_and_a_miss(tmp_path):
    pack = write_pack(tmp_path, D1, ("O1", EXIT))
    ids = {book: write_run(tmp_path, book, D1, record("O1", pack=pack), pack=pack)
           for book in (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI)}  # fmt: skip
    write_log(tmp_path, D1, ids, committed="15:16:00")  # the snapshot started at 15:15
    entry = board(tmp_path, QUOTES).build(D1)["books"][BOOK1_RULES]
    assert (entry["misses"], entry["eligible_days"]) == (1, 1)
