"""Story R3: a registered research version's shadow account is opened before Book 1's D2 reads it, each shadow is
valued on its own terms, and Book 1's readers never take a shadow's record (criteria 1, 2 and 9)."""

import hashlib
import json

from fno.books.account import PaperAccount
from fno.books.book1_records import opening_trades, recorded_terms
from fno.books.paths import shadow_account
from fno.constants import BOOK1_RULES, FILL_OPEN
from fno.desk.records import FILL_COLUMNS, DeskRecords
from fno.playbook.decision_store import SUMS_FILE, DecisionStore
from fno.risk.inputs import TradeTerms
from tests.decisions.builders import doc, snapshot

from .builders import DAYS, book1, clock_at
from .openings import open_trades
from .test_book1 import FIFTEEN

SHADOW = shadow_account("cand-v1")


def test_shadow_accounts_are_opened_before_d2_reads_its_inputs(tmp_path):
    playbook = snapshot(doc("sc-a"), doc("cand", status="research"), registered_research=("cand",))
    decider, _ = book1(tmp_path, playbook, clock_at(FIFTEEN(DAYS[0])))
    events, read = [], decider.inputs.day
    decider.open_shadows = lambda strategies, day: events.append(("open", [s.name for s in strategies], day)) or []
    decider.inputs.day = lambda day: events.append(("inputs", day)) or read(day)
    decider.decide(DAYS[0])
    assert events[:2] == [("open", ["cand"], DAYS[0]), ("inputs", DAYS[0])]  # opened first, only the research version


def _run(root, records: list[dict]):
    """One committed Book 1 run holding a book record and a shadow record, as D2 writes them (one shared folder)."""
    folder = DecisionStore(root, BOOK1_RULES).day_folder(DAYS[0]) / f"{DAYS[0]}-r1"
    folder.mkdir(parents=True)
    sums = []
    for i, record in enumerate(records):
        body = json.dumps(record).encode()
        (folder / f"{i}.json").write_bytes(body)
        sums.append(f"{hashlib.sha256(body).hexdigest()}  {i}.json")
    (folder / SUMS_FILE).write_text("\n".join(sums) + "\n")
    return folder


def _record(trade_id, mode, lots):
    return {"chosen_action": "trade", "opportunity_id": "x-v1:2026-11-24", "mode": mode, "corrects": None,
            "structure": {"trade_id": trade_id, "structure": "SC", "width": 200, "lots": lots}}  # fmt: skip


def _open_shadow_fill(root, trade_id):
    fills = DeskRecords(PaperAccount(root, SHADOW)).fills
    fills.path.parent.mkdir(parents=True, exist_ok=True)
    opened = {"fill_id": f"{trade_id}-open", "trade_id": trade_id, "action": FILL_OPEN}
    fills.append(dict.fromkeys(FILL_COLUMNS, "") | opened | {"filled_at": f"{DAYS[0]}T15:15:30+05:30"})


def test_each_account_takes_only_its_own_records_and_terms(tmp_path):
    run = _run(tmp_path, [_record("t1", "book", 1), _record("shadow-t2", "shadow", 3)])
    open_trades(tmp_path, BOOK1_RULES, DAYS[0], run.name, "c1", ["t1"])
    _open_shadow_fill(tmp_path, "shadow-t2")
    assert recorded_terms(tmp_path, BOOK1_RULES) == {"t1": TradeTerms("SC", 200, 1)}
    assert recorded_terms(tmp_path, SHADOW, BOOK1_RULES) == {"shadow-t2": TradeTerms("SC", 200, 3)}


def test_book1_s_readers_are_unchanged_by_a_shadow_on_the_same_day(tmp_path):
    """Criterion 9 for E5's readers: the same trades, terms, problems and other runs with and without the shadow."""
    alone, both = tmp_path / "alone", tmp_path / "both"
    for root, records in ((alone, [_record("t1", "book", 1)]),
                          (both, [_record("t1", "book", 1), _record("shadow-t2", "shadow", 3)])):  # fmt: skip
        run = _run(root, records)
        open_trades(root, BOOK1_RULES, DAYS[0], run.name, "c1", ["t1"])
    _open_shadow_fill(both, "shadow-t2")
    without, with_shadow = opening_trades(alone, BOOK1_RULES), opening_trades(both, BOOK1_RULES)
    assert {k: v.terms for k, v in with_shadow.trades.items()} == {k: v.terms for k, v in without.trades.items()}
    assert (with_shadow.problems, with_shadow.other_runs) == (without.problems, without.other_runs)


def test_a_record_of_the_wrong_mode_is_never_taken_even_with_a_matching_id(tmp_path):
    """The isolation does not rest on the `shadow-` prefix (judge 208): a book-mode record named by a shadow fill is
    not the shadow's, and a shadow-mode record named by a Book 1 fill is not Book 1's."""
    run = _run(tmp_path, [_record("same", "shadow", 3), _record("other", "book", 1)])
    open_trades(tmp_path, BOOK1_RULES, DAYS[0], run.name, "c1", ["same"])
    _open_shadow_fill(tmp_path, "other")
    assert recorded_terms(tmp_path, BOOK1_RULES) == {}
    assert recorded_terms(tmp_path, SHADOW, BOOK1_RULES) == {}
