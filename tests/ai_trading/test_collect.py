"""Story F1t criteria 5-7 and 9: the collector judges each book from its sealed submission and the two readings, hands
an accepted answer to its decider with exactly what was fired, and writes one outcome record per book."""

from fno.ai_trading.outcome import PROMOTED, REFUSED
from fno.ai_trading.paths import outcome_path

from .builders import DAY, FakeDecider, draft
from .day import BOOKS, DEADLINES, Day, SameCards


def full_day(tmp_path, **kwargs):
    day = Day(tmp_path, **kwargs)
    day.fire()
    for book in BOOKS:
        day.seal(book, draft())
    day.observe(DEADLINES.receipt)
    for book in BOOKS:
        day.reveal(book)
    day.observe(DEADLINES.reveal)
    return day


def test_two_on_time_books_are_promoted_with_one_record_each(tmp_path):
    day = full_day(tmp_path)
    collected = day.collect()
    assert {b: r["status"] for b, r in collected.outcomes.items()} == dict.fromkeys(BOOKS, PROMOTED)
    assert sorted(p.name for p in collected.paths if p.suffix == ".json") == sorted(
        outcome_path(DAY, b).split("/")[-1] for b in BOOKS
    )
    record = collected.outcomes["book2_hybrid"]
    assert record["received"] == {"commitment": DEADLINES.receipt.isoformat(), "reveal": DEADLINES.reveal.isoformat()}
    assert record["consulted_units"] == ["analyst_volatility"] and record["run_id"] == f"{DAY}-r1"


def test_the_decider_gets_exactly_what_was_fired_and_only_its_own_book(tmp_path):
    day = full_day(tmp_path)
    day.collect()
    for book in BOOKS:
        (accepted,) = day.deciders[book].calls
        assert accepted.book == book and accepted.private_pack.book == book
        assert accepted.session == f"https://example.invalid/{book}" and accepted.model_reported == "claude-opus-5-5"
        assert accepted.consulted_units == ("analyst_volatility",)


def test_a_rerun_judges_nothing_again(tmp_path):
    day = full_day(tmp_path)
    first = day.collect()
    again = day.collect()
    assert again.outcomes == first.outcomes and again.paths == ()
    assert [len(d.calls) for d in day.deciders.values()] == [1, 1]


def test_a_late_book_and_an_on_time_book_on_the_same_day(tmp_path):
    day = Day(tmp_path)
    day.fire()
    day.seal("book2_hybrid", draft())
    day.observe(DEADLINES.receipt)
    day.seal("book3_ai", draft(), when=(15, 10, 5))
    for book in BOOKS:
        day.reveal(book)
    day.observe(DEADLINES.reveal)
    outcomes = day.collect().outcomes
    assert outcomes["book2_hybrid"]["status"] == PROMOTED and outcomes["book3_ai"]["status"] == "late"
    assert day.deciders["book3_ai"].calls == []


def test_no_reading_at_all_makes_every_fired_book_late(tmp_path):
    day = Day(tmp_path)
    day.fire()
    day.seal("book2_hybrid", draft())
    assert day.collect(("book2_hybrid",)).outcomes["book2_hybrid"]["status"] == "late"


def test_a_missing_submission_is_no_submission(tmp_path):
    day = Day(tmp_path)
    day.fire()
    day.observe(DEADLINES.receipt)
    day.observe(DEADLINES.reveal)
    outcome = day.collect(("book2_hybrid",)).outcomes["book2_hybrid"]
    assert (outcome["status"], outcome["run_id"]) == ("no_submission", "")


def test_a_book_never_fired_is_not_fired(tmp_path):
    day = Day(tmp_path)
    day.fire(("book2_hybrid",))
    outcome = day.collect(("book3_ai",)).outcomes["book3_ai"]
    assert (outcome["status"], outcome["reason"]) == ("not_fired", "no fire log entry for the day")


def test_cards_that_changed_since_the_fire_refuse_the_book(tmp_path):
    day = full_day(tmp_path)
    day.cards = SameCards({"input_sha256": "d" * 64, "role_set_version": "roles-v1", "roles": []})
    outcome = day.collect(("book2_hybrid",)).outcomes["book2_hybrid"]
    assert outcome["status"] == REFUSED and "not the ones fired" in outcome["reason"]


def test_a_decider_refusal_is_refused_and_the_other_book_is_untouched(tmp_path):
    day = full_day(tmp_path, deciders=None)
    day.deciders["book2_hybrid"] = FakeDecider(day.root, refuse="envelope sheet missing")
    outcomes = day.collect().outcomes
    assert (
        outcomes["book2_hybrid"]["status"] == REFUSED and "envelope sheet missing" in outcomes["book2_hybrid"]["reason"]
    )
    assert outcomes["book3_ai"]["status"] == PROMOTED


def test_consulted_units_are_the_roles_whose_card_was_given():
    from fno.ai_trading.ports import consulted_units

    item = {"roles": [{"unit_id": "analyst_volatility", "status": "valid"},
                      {"unit_id": "analyst_macro", "status": "not_applicable"},
                      {"unit_id": "analyst_positioning", "status": "late"},
                      {"unit_id": "analyst_equity", "status": "no_submission"}]}  # fmt: skip
    assert consulted_units(item) == ("analyst_macro", "analyst_volatility")
    assert consulted_units({}) == () and consulted_units({"roles": []}) == ()
