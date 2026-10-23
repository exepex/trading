"""Part e's review and comparison (story MS-INS, criteria 5-6 and 8): every denominator with its refusals, account
rupees without tickets, a planted cause in the counts, the paired rows from counted decisions with RC1 against N0 as
the live null, orphan corrections and unreadable files in words; the plain P2 line first."""

from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

from fno.school.constants import SLOT_1500, Outcome, RecordKind
from fno.school.drivers.cards import CARDS_FOLDER, load_cards
from fno.school.instructor.causes.classify import Classifier
from fno.school.instructor.contracts import ClosedRead, Measure
from fno.school.instructor.fakes import FakeInstructorStore
from fno.school.instructor.outputs.comparison import CountedComparison, SealedDecisions, sealed_decisions
from fno.school.instructor.outputs.review import build_review, driver_summary
from fno.school.instructor.outputs.review_text import P2_LINE, review_lines
from fno.school.instructor.outputs.run import InstructorRun
from tests.school.instructor.builders import DRIVER, OTHER, RULES, SESSIONS, decision_record, held_trade
from tests.school.instructor.causes.test_evidence import builder
from tests.school.instructor.reading import WriteRefusingDashcam, reader

CARDS = load_cards(Path(__file__).resolve().parents[4] / CARDS_FOLDER)


@dataclass
class CountEverything:
    def verdict(self, candidate):
        return type("Verdict", (), {"counted": True})()


def scenario():
    dashcam = WriteRefusingDashcam()
    record = held_trade(dashcam)
    read = reader(dashcam)
    run = InstructorRun(read, Classifier(builder(), RULES), FakeInstructorStore(), 0.0, RULES)
    run.for_session(SESSIONS[2], write=True)
    return dashcam, read, run, record


def test_the_review_shows_every_denominator_refusals_included_and_the_planted_cause():
    dashcam, read, run, record = scenario()
    sessions = read.sessions(SESSIONS[0], SESSIONS[2])
    decisions = sealed_decisions(dashcam, sessions)
    base = decision_record(SESSIONS[0], OTHER)
    refused = replace(base, decision=replace(base.decision, outcome=Outcome.REFUSED, reason="max_loss"))
    decisions = SealedDecisions(decisions.records + ((refused, "c"),), decisions.unsealed)
    review = build_review(SESSIONS[0], SESSIONS[2], sessions, read.closed_between(SESSIONS[0], SESSIONS[2]),
                          decisions, run.store, (), 1)  # fmt: skip
    mine = next(d for d in review.drivers if d.driver_id == DRIVER)
    assert mine.outcomes == {"trade": 1} and mine.trades == 1 and mine.net_rs == round(record.net, 2)
    assert sum(mine.primary.values()) + mine.unclassified == 1
    other = next(d for d in review.drivers if d.driver_id == OTHER)
    assert other.outcomes == {"refused": 1, "trade": 3}  # every scheduled decision, the refusal kept
    lines = review_lines(review)
    assert lines[1] == P2_LINE and any("refused 1" in line for line in lines)
    assert lines[-1].endswith("corrections naming no outcome: 1")


def test_tickets_are_never_summed_into_rupees():
    _, read, _, record = scenario()
    closed = read.closed_on(SESSIONS[2])
    ticket = ClosedRead(tuple(replace(p, outcome=replace(p.outcome, is_ticket=True)) for p in closed.paths), ())
    summary = driver_summary(DRIVER, ticket, Counter(), [], [])
    assert (summary.trades, summary.tickets, summary.net_rs, summary.worst_trade_rs) == (0, 1, 0, None)


def test_the_comparison_pairs_counted_decisions_and_adds_rc1_against_n0():
    dashcam, read, _, _ = scenario()
    decisions = sealed_decisions(dashcam, read.sessions(SESSIONS[0], SESSIONS[2]))
    cards = {code: CARDS[code] for code in ("CS1", "REF", "RC1", "N0")}
    rows = CountedComparison(CountEverything(), cards, RULES).rows(
        decisions, read.closed_between(SESSIONS[0], SESSIONS[2]).paths
    )
    assert {(r.driver_id, r.control_id) for r in rows} == {("CS1@1", "REF@1")}  # only CS1 and REF decided together
    assert all(r.note.startswith("descriptive, not a test") for r in rows) and {r.measure for r in rows} == set(Measure)


def test_a_session_without_a_readable_decisions_file_is_listed():
    dashcam, read, _, _ = scenario()
    del dashcam.files[(SESSIONS[1], SLOT_1500, RecordKind.DECISIONS)]
    assert sealed_decisions(dashcam, read.sessions(SESSIONS[0], SESSIONS[2])).unsealed == (SESSIONS[1],)


def test_rc1_is_compared_with_n0_only_as_the_live_null():
    records = tuple((decision_record(day, driver, outcome=Outcome.NO_TRADE), "c")
                    for day in SESSIONS for driver in ("RC1@1", "N0@1", "REF@1"))  # fmt: skip
    cards = {code: CARDS[code] for code in ("REF", "RC1", "N0")}
    rows = CountedComparison(CountEverything(), cards, RULES).rows(SealedDecisions(records, ()), ())
    assert {(r.driver_id, r.control_id) for r in rows} == {("RC1@1", "N0@1")}
    assert all(r.road_slots == 3 and r.driver_abstentions == 3 for r in rows)


def test_the_review_command_prints_the_review_and_writes_the_paired_file_only_with_write():
    from fno.school.instructor.outputs.command import run as command
    from fno.school.instructor.ports import InstructorKind
    from tests.school.instructor.outputs.test_counts_and_command import school

    _, read, instructor, _ = scenario()
    cards = {code: CARDS[code] for code in ("CS1", "REF", "N0", "RC1")}
    parts = {"build_path_reader": lambda: read, "build_instructor_store": lambda: instructor.store,
             "build_comparison": lambda: CountedComparison(CountEverything(), cards, RULES)}  # fmt: skip
    wiring = type("Wiring", (), parts)
    argv = ["--review", str(SESSIONS[0]), str(SESSIONS[2])]
    lines = command(argv, school(True), wiring)
    assert lines[1] == P2_LINE and lines[-1] == "(dry run: nothing written)"
    assert instructor.store.read(SESSIONS[2], InstructorKind.PAIRED) is None
    command(argv + ["--write"], school(True), wiring)
    assert instructor.store.read(SESSIONS[2], InstructorKind.PAIRED)


def test_the_review_prints_fs_three_counts_when_supplied_and_says_so_when_not():
    from fno.school.contracts.tickets import OpportunityCounts
    from fno.school.instructor.outputs.review_text import review_lines as text

    _, read, instructor, _ = scenario()
    sessions = read.sessions(SESSIONS[0], SESSIONS[2])
    decisions = sealed_decisions(read.dashcam, sessions)
    closed = read.closed_between(SESSIONS[0], SESSIONS[2])

    class Counts:
        def counts(self, session):
            return (OpportunityCounts(session, closed.paths[0].outcome.road, DRIVER, 2, 1, 1),)

    plain = build_review(SESSIONS[0], SESSIONS[2], sessions, closed, decisions, instructor.store, (), 0)
    supplied = build_review(SESSIONS[0], SESSIONS[2], sessions, closed, decisions, instructor.store, (), 0, Counts())
    assert any("three counts not supplied" in line for line in text(plain))
    mine = next(d for d in supplied.drivers if d.driver_id == DRIVER)
    assert mine.three_counts == (6, 3, 3) and any(
        "eligible 6, fillable 3, executed 3" in line for line in text(supplied)
    )
