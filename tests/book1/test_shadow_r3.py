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
OTHER_WIDTHS = [50]  # a narrower condor than Book 1's, so the shadow's terms differ


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


def test_s3_book1_actions_are_unchanged_by_a_shadow_on_the_same_day(tmp_path):
    """Criterion 9 for S3 (scoreboard A, `action_of` through `MatchedDays`): the same action rows with and without a
    shadow candidate's record in Book 1's run of the day."""
    from fno.constants import Decision
    from tests.scoreboard.matched_builders import board, record, write_pack
    from tests.scoreboard.test_matched_board import D1, EXIT, QUOTES, runs_for

    def actions(root, with_shadow: bool) -> list[dict]:
        pack = write_pack(root, D1, ("O1", EXIT))
        shadow = [record("S1", Decision.SHADOW_TRADE, "shadow", pack=pack, action="trade")] if with_shadow else []
        runs_for(root, D1, [record("O1", pack=pack), *shadow], [], pack=pack)
        return [r for r in board(root, QUOTES).build(D1)["actions"] if r["book"] == BOOK1_RULES]

    alone, both = actions(tmp_path / "alone", False), actions(tmp_path / "both", True)
    assert alone and alone == both


def _decided_day(root, with_shadow: bool):
    """One session through Book 1's real D2 run: a paper version, and (with the shadow) a registered research version
    with other terms in the same run; Book 1's own chosen trades are then filled as the desk would."""
    from tests.decisions.builders import doc as version

    from .builders import book1_doc

    candidate = version("cand", status="research")
    candidate["structure"]["widths"] = OTHER_WIDTHS
    docs = [book1_doc()] + ([candidate] if with_shadow else [])
    playbook = snapshot(*docs, registered_research=("cand",) if with_shadow else ())
    decider, commits = book1(root, playbook, clock_at(FIFTEEN(DAYS[0])))
    decider.decide(DAYS[0])
    [run] = DecisionStore(root, BOOK1_RULES).runs(DAYS[0])
    records = [json.loads(p.read_text()) for p in sorted(run.glob("*.json")) if p.name != "inputs.json"]
    book_ids = [r["structure"]["trade_id"] for r in records
                if r.get("chosen_action") == "trade" and r.get("structure") and r.get("mode") != "shadow"]  # fmt: skip
    open_trades(root, BOOK1_RULES, DAYS[0], run.name, commits.made[0][0], book_ids)
    shadow_ids = [r["structure"]["trade_id"] for r in records if r.get("mode") == "shadow" and r.get("structure")]
    return decider, records, shadow_ids


def test_book1_s_readers_and_account_are_identical_with_a_real_same_day_shadow(tmp_path):
    """ChatGPT review 129 and criterion 9, on D2's own output: Book 1's opening trades, decided exits, trade counts,
    one-decision finder (which runs, where) and the account files are equal (E6 reads only that account) with the shadow
    present or absent. The run's inputs.json differs by design: D2 records the shadow books for replay."""
    from fno.books.book1_records import decided_exit_days
    from fno.desk.trade_counts import DeskTradeCounts

    from .test_exits import FINDER

    def readers(root, with_shadow):
        decider, records, shadow_ids = _decided_day(root, with_shadow)
        account = PaperAccount(root, BOOK1_RULES)
        trades = opening_trades(root, BOOK1_RULES)
        return (
            {
                "trades": {k: (v.version, v.expiry, v.terms) for k, v in trades.trades.items()},
                "problems": (trades.problems, trades.other_runs),
                "exits": decided_exit_days(root, BOOK1_RULES, FINDER).exits,
                "counts": DeskTradeCounts(DeskRecords(account)).open("sc-a", 1),
                "finder": [(f.run_id, f.place) for f in decider.decided.find(DAYS[0])],
                "account": {p.name: p.read_bytes() for p in sorted(account.folder.glob("*")) if p.is_file()},
            },
            records,
            shadow_ids,
        )

    alone, _, _ = readers(tmp_path / "alone", False)
    both, records, shadow_ids = readers(tmp_path / "both", True)
    assert shadow_ids and alone["trades"] and both == alone  # a real shadow decision was recorded, Book 1 unchanged
    assert {r["mode"] for r in records} == {"book", "shadow"}
    widths = {r["mode"]: r["structure"]["width"] for r in records if r.get("structure")}
    assert widths["shadow"] != widths["book"]  # the same session, different terms


def test_s2_book1_section_is_identical_with_a_shadow_record_in_book1_s_run(tmp_path):
    """Criterion 9 for S2: scoreboard B reads every record of Book 1's runs into D6's segments (entry_decisions.py), so
    a shadow record in the same run must leave Book 1's section unchanged."""
    from fno.constants import BOOK2_HYBRID, BOOK3_AI
    from tests.scoreboard.builders import record, write_run
    from tests.scoreboard.test_whole_system import R2, START, build, history

    def section(root, with_shadow):
        history(root)
        if with_shadow:
            shadow = record(BOOK1_RULES, START, R2, "cand-v1:2026-11-24", max_loss=4000) | {"mode": "shadow"}
            write_run(root, BOOK1_RULES, START, R2, record(BOOK1_RULES, START, R2, "d-h1", max_loss=6000,
                      stress=(12_000, 30_000)), record(BOOK1_RULES, START, R2, "d-o1", max_loss=7000,
                      override="owner"), shadow)  # fmt: skip
        board = build(root)
        return {k: v for k, v in board["books"].items() if k not in (BOOK2_HYBRID, BOOK3_AI)}

    alone, both = section(tmp_path / "alone", False), section(tmp_path / "both", True)
    assert alone and both == alone


def test_book1_as_the_app_builds_it_opens_a_registered_research_version_s_account(tmp_path):
    """Judge 210 finding 1, criterion 1 where it takes effect: `build_book1` wires E6's opener (no Drive here). Only
    the playbook and the run finder are fixtures; the day then stops at the inputs (no packs), after the opening."""
    import pytest

    from fno.books.book1_inputs import InputsRefused
    from fno.books.book1_wiring import build_book1
    from fno.config import load_app_config

    from .builders import Commits, DiskRuns

    decider = build_book1(load_app_config(), tmp_path)
    decider.playbook = lambda: snapshot(doc("sc-a"), doc("cand", status="research"), registered_research=("cand",))
    decider.decided = DiskRuns(tmp_path, Commits(clock_at(FIFTEEN(DAYS[0]))))
    with pytest.raises(InputsRefused):
        decider.decide(DAYS[0])
    assert PaperAccount(tmp_path, SHADOW).folder.is_dir()
