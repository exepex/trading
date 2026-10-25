"""Story F5 part 1: Book 2's day sheet, built in the pack step from the pack's own snapshot. It lists every
opportunity with its version's status, the rule default (D2's chosen trades with their terms), the eligible versions
and Book 2's pauses; a paused version is not on it; no rule default when the rules offer none; within the 5 s budget."""

import json
import time

from fno.book2.evaluation import Book2Evaluators
from fno.book2.sheet import SHEET_KIND, Book2Sheet, book2_snapshot
from fno.books.book1 import Book1Day
from fno.constants import BOOK2_HYBRID
from tests.decisions.builders import COMMIT, doc, snapshot
from tests.playbook.evaluation_builders import (
    DAY,
    EXPIRY,
    LIVE_TRUE,
    Counts,
    FixedValues,
    OwnShadowBooks,
    chain_market,
    evaluator,
)  # fmt: skip
from tests.risk.builders import book

R, P = f"sc-research-v1:{EXPIRY.isoformat()}", f"sc-paper-v1:{EXPIRY.isoformat()}"
DOCS = (doc("sc-research", "research", expected="none"), doc("sc-paper"))


def sheet(docs=DOCS, paused=(), values=None):
    rules = evaluator()
    evaluators = Book2Evaluators(rules.finder, rules.builder, rules.allocator, rules.real)
    the_snapshot = snapshot(*docs, registered_research=tuple(d["name"] for d in docs if d["status"] == "research"))
    inputs = lambda day, common: Book1Day(chain_market(), FixedValues(values), book(), Counts(), OwnShadowBooks(), {})  # noqa: E731
    return Book2Sheet(evaluators, lambda: the_snapshot, lambda day: paused, inputs).sheet(BOOK2_HYBRID, DAY, None)


def test_the_sheet_lists_each_opportunity_with_its_status_and_the_rule_default_with_terms():
    body = sheet()
    assert (body["kind"], body["day"], body["playbook_commit"], body["paused"]) == (
        SHEET_KIND,
        "2026-10-13",
        COMMIT,
        [],
    )
    statuses = {o["opportunity_id"]: (o["version"], o["strategy_status"], o["decision"]) for o in body["opportunities"]}
    assert statuses == {R: ("sc-research-v1", "research", "chosen"), P: ("sc-paper-v1", "paper", "chosen")}
    assert {d["opportunity_id"] for d in body["rule_default"]} == {R, P}
    assert all(d["trade"]["structure"] == "SC" and d["trade"]["width"] == 100 for d in body["rule_default"])
    assert {o["widths"] == [300.0, 200.0, 100.0] for o in body["opportunities"]} == {True}
    assert body["eligible"] == ["sc-paper-v1", "sc-research-v1"]
    json.dumps(body)  # it goes into the private pack as JSON


def test_a_paused_research_version_is_not_on_the_sheet():
    body = sheet(paused=("sc-research-v1",))
    assert body["paused"] == ["sc-research-v1"] and [d["opportunity_id"] for d in body["rule_default"]] == [P]
    assert R not in {o["opportunity_id"] for o in body["opportunities"]}


def test_no_rule_default_when_the_rules_offer_none():
    body = sheet(values={**LIVE_TRUE, "F1_live_atm_iv_minus_rv20": -5.0})
    assert body["rule_default"] == [] and body["eligible"] == []


def test_an_empty_playbook_gives_an_empty_sheet():
    body = sheet(docs=())
    assert (body["opportunities"], body["rule_default"], body["eligible"]) == ([], [], [])


def test_book2_s_snapshot_keeps_book1_s_files_and_names_its_pauses_sorted():
    base = snapshot(*DOCS)
    viewed = book2_snapshot(base, ["b-v1", "a-v1"])
    assert (viewed.files, viewed.registry_csv, viewed.commit) == (base.files, base.registry_csv, base.commit)
    assert viewed.paused == ("a-v1", "b-v1")


def test_the_sheet_fits_its_five_second_budget_at_twelve_versions():
    docs = tuple(doc(f"sc-{n:02d}", "research" if n % 2 else "paper", expected="none" if n % 2 else 150.0)
                 for n in range(12))  # fmt: skip
    started = time.perf_counter()
    body = sheet(docs=docs)
    elapsed = time.perf_counter() - started
    print(f"Book 2 sheet at 12 versions: {elapsed:.3f} s")
    assert len(body["opportunities"]) == 12 and elapsed < 5.0
