"""Story D3b criterion 5 (and judge 125 minors 3-4): a trade's terms and time exit come only from the run that opened
it (the entry day's run log), only for trades opened by fills. A record in another run naming the trade, a correction
included, never changes it and is alerted; a missing or mismatched run log gives no terms and no exit, with the
reason, and never falls back to another run."""

import hashlib
import json
from datetime import date

from fno.books import book1_exits
from fno.books.account import PaperAccount
from fno.books.book1_exits import PlaybookExitRules
from fno.books.book1_records import DecidedExits, book_trades, recorded_terms
from fno.books.opening_runs import CHANGED, GONE, NO_LOG
from fno.constants import BOOK1_RULES, FILL_OPEN
from fno.desk.records import FILL_COLUMNS, DeskRecords
from fno.playbook.decision_store import SUMS_FILE, DecisionStore
from fno.risk.inputs import TradeTerms

from .openings import open_trades

DAY, LATER = date(2026, 10, 13), date(2026, 10, 14)
OPPORTUNITY = "sc-a-v1:2026-11-24"


def run(root, day, n, trades: dict[str, int], corrects=None):
    """A committed run choosing each trade with `lots`, with its records.sha256."""
    folder = DecisionStore(root, BOOK1_RULES).day_folder(day) / f"{day}-r{n}"
    folder.mkdir(parents=True)
    sums = []
    for i, (trade_id, lots) in enumerate(trades.items()):
        record = {"chosen_action": "trade", "opportunity_id": OPPORTUNITY, "corrects": corrects,
                  "structure": {"trade_id": trade_id, "structure": "SC", "width": 200, "lots": lots}}  # fmt: skip
        body = json.dumps(record).encode()
        (folder / f"{i}.json").write_bytes(body)
        sums.append(f"{hashlib.sha256(body).hexdigest()}  {i}.json")
    (folder / SUMS_FILE).write_text("\n".join(sums) + "\n")
    return folder


def as_committed(root):
    """The sums files as the commit the run log names holds them: the bytes on disk when this test committed them."""
    held = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob(SUMS_FILE)}
    return lambda path, commit: held.get(path) if commit == "c1" else None


def test_only_filled_trades_count_each_from_its_opening_run(tmp_path):
    opening = run(tmp_path, DAY, 1, {"t1": 1, "t3": 1})  # t3 chosen, never filled
    run(tmp_path, DAY, 2, {"t2": 1})  # a run E3 never collected
    open_trades(tmp_path, BOOK1_RULES, DAY, opening.name, "c1", ["t1"])
    assert recorded_terms(tmp_path, BOOK1_RULES, as_committed(tmp_path)) == {"t1": TradeTerms("SC", 200, 1)}


def test_a_later_record_or_correction_naming_the_trade_never_changes_it_and_is_alerted(tmp_path):
    opening = run(tmp_path, DAY, 1, {"t1": 1})
    open_trades(tmp_path, BOOK1_RULES, DAY, opening.name, "c1", ["t1"])
    fixed = {"run_id": opening.name, "opportunity_id": OPPORTUNITY}
    run(tmp_path, DAY, 2, {"t1": 4}, corrects=fixed)  # same day, after: the latest record by any order
    run(tmp_path, LATER, 1, {"t1": 9})  # another day's run naming the same trade ID
    found = book_trades(tmp_path, BOOK1_RULES, as_committed(tmp_path))
    assert found.trades["t1"].terms == TradeTerms("SC", 200, 1) and found.trades["t1"].run == opening
    assert found.other_runs == {"t1": (f"{DAY}-r2", f"{LATER}-r1")}


def no_opening(tmp_path, change):
    opening = run(tmp_path, DAY, 1, {"t1": 1})
    open_trades(tmp_path, BOOK1_RULES, DAY, opening.name, "c1", ["t1"])
    sums_at = as_committed(tmp_path)
    run(tmp_path, DAY, 2, {"t1": 1})  # a later run that could be fallen back to: it never is
    change(tmp_path, opening)
    return book_trades(tmp_path, BOOK1_RULES, sums_at)


def test_a_missing_run_log_gives_no_trade_and_never_falls_back(tmp_path):
    found = no_opening(tmp_path, lambda root, run: (root / "journal" / "runs" / f"{DAY}.json").unlink())
    assert found.trades == {} and found.problems == {"t1": NO_LOG.format(day=DAY, book=BOOK1_RULES)}


def test_a_run_log_naming_a_gone_or_changed_run_gives_no_trade(tmp_path):
    def gone(root, folder):
        folder.rename(folder.with_name(".gone"))

    def resummed(root, folder):  # a record edited and its sums file rewritten to match: not the committed sums
        record = folder / "0.json"
        record.write_bytes(record.read_bytes().replace(b'"lots": 1', b'"lots": 3'))
        (folder / SUMS_FILE).write_text(f"{hashlib.sha256(record.read_bytes()).hexdigest()}  0.json\n")

    def edited(root, folder):
        (folder / "0.json").write_text("{}")

    assert no_opening(tmp_path / "a", gone).problems == {"t1": GONE.format(run=f"{DAY}-r1", day=DAY)}
    for name, change in (("b", resummed), ("c", edited)):
        found = no_opening(tmp_path / name, change)
        assert found.trades == {} and found.problems == {"t1": CHANGED.format(run=f"{DAY}-r1", commit="c1")}


def test_the_exit_rules_name_why_and_alert_the_other_runs(monkeypatch):
    """No exit is set for a trade without an opening run (E4 holds it; its own risk exits still run, see
    tests/desk/test_exits.py), and every review alerts the other runs naming a trade."""
    alerts = []
    monkeypatch.setattr(book1_exits, "open_positions", lambda records: [type("P", (), {"trade_id": "t1"})])
    decided = DecidedExits({}, {"t1": NO_LOG.format(day=DAY, book=BOOK1_RULES)}, {"t1": (f"{DAY}-r2",)})
    exits = PlaybookExitRules(
        lambda book: decided, lambda v: None, lambda b: None, type("A", (), {"send": alerts.append})()
    )
    assert exits.rules(BOOK1_RULES) == {}
    assert "other runs name it" in alerts[0] and f"{DAY}-r2" in alerts[0]
    assert "names no decision" in alerts[1] and "E4 holds it" in alerts[1]


def test_other_runs_are_listed_by_day_and_counter_never_by_name(tmp_path):
    opening = run(tmp_path, DAY, 1, {"t1": 1})
    open_trades(tmp_path, BOOK1_RULES, DAY, opening.name, "c1", ["t1"])
    for n in (2, 10):
        run(tmp_path, DAY, n, {"t1": 1})
    found = book_trades(tmp_path, BOOK1_RULES, as_committed(tmp_path))
    assert found.other_runs == {"t1": (f"{DAY}-r2", f"{DAY}-r10")}


def test_the_opening_run_is_the_first_open_fill_s_day(tmp_path):
    """E4 opens every leg at one snapshot; should a trade's open fills ever span days, the first day's run opened it."""
    opening = run(tmp_path, DAY, 1, {"t1": 1})
    open_trades(tmp_path, BOOK1_RULES, DAY, opening.name, "c1", ["t1"])
    later = run(tmp_path, LATER, 1, {"t1": 5})
    fills = DeskRecords(PaperAccount(tmp_path, BOOK1_RULES)).fills
    fills.append(dict.fromkeys(FILL_COLUMNS, "") | {"fill_id": "t1-leg2", "trade_id": "t1", "action": FILL_OPEN,
                                                     "filled_at": f"{LATER}T15:15:30+05:30"})  # fmt: skip
    open_trades(tmp_path, BOOK1_RULES, LATER, later.name, "c1", [])  # LATER's log names its own run
    assert book_trades(tmp_path, BOOK1_RULES, as_committed(tmp_path)).trades["t1"].run == opening
