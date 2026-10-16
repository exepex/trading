"""Story E2d criteria 3, 9 and 10: the daily run's `trade_marks` step over every account, each in its locked journal:
one alert per unmarked trade, one account's failure never stops another's, each shadow account is marked in its own
files, and nothing is committed (no public file for a shadow account)."""

from fno.books.account import PaperAccount
from fno.books.paths import account_folder, shadow_account
from fno.books.trade_marks import TRADE_MARKS_FILE, UNMARKED, VALUED
from fno.constants import BOOK1_RULES, BOOK2_HYBRID
from fno.desk.trade_marking import MarkingStep, TradeMarker, marked_accounts
from fno.desk.wiring import open_account_writer, open_desk_journal
from fno.scoreboard.sources import SnapshotMarks
from tests.scorecard.history import SHORT, trade

from .test_trade_marking import D1, D2, quotes, sessions

SHADOW = shadow_account("fly-a-v1")


def step(root, alerts, snaps, ids, books=(BOOK1_RULES, BOOK2_HYBRID), failing=None):
    marker = lambda: TradeMarker(sessions, SnapshotMarks(snaps, ids))  # noqa: E731
    return MarkingStep(Journals(root, failing), marker, lambda: marked_accounts(root, books), alerts)


def test_an_unmarked_trade_sends_exactly_one_alert_naming_book_trade_and_contracts(root, alerts):
    """Criterion 3: nothing is posted while building (the recording fake), and no equity row for that book today."""
    trade(root, BOOK1_RULES, "fly", "t1", D2)
    result = step(root, alerts, *quotes((D2, (15.0, None)))).run(D2).result
    unmarked = [{"trade_id": "t1", "status": UNMARKED}]
    assert result[BOOK1_RULES] == {"marked": True, "equity_row": False, "trades": unmarked}
    assert alerts.sent == [f"F&O paper desk {D2} {BOOK1_RULES}: trade t1 not valued: never validly quoted: "
                           f"{SHORT.contract}; no equity row for the book today"]  # fmt: skip
    assert result[BOOK2_HYBRID] == {"marked": True, "equity_row": True, "trades": []}


class Journals:
    """Each account's locked journal; the `failing` one cannot be opened (Drive down for it, a lock held elsewhere)."""

    def __init__(self, root, failing=None):
        self.root, self.failing = root, failing

    def __call__(self, account):
        if account == self.failing:
            raise RuntimeError("Drive could not be read")
        return open_desk_journal(account, self.root)


def test_one_account_s_failure_is_alerted_and_never_stops_another_s_marking(root, alerts):
    """Criterion 9 (the exits ran before this step, so a marking failure can never stop them)."""
    trade(root, BOOK2_HYBRID, "fly", "b1", D1)
    marking = step(root, alerts, *quotes((D1, (19.0, 69.0))), failing=BOOK1_RULES)
    result = marking.run(D1).result
    assert result[BOOK1_RULES] == {"marked": False, "error": "RuntimeError: Drive could not be read"}
    assert result[BOOK2_HYBRID]["trades"] == [{"trade_id": "b1", "status": VALUED}]
    assert alerts.sent == [f"F&O paper desk {D1} {BOOK1_RULES}: MARKING FAILED: RuntimeError: Drive could not be read "
                           "(the other accounts are marked as usual)"]  # fmt: skip


def test_each_shadow_account_is_marked_in_its_own_files(root, alerts):
    """Criterion 10: R3's shadow account, beside the books, never in a book's folder."""
    with open_account_writer(SHADOW, root) as writer:
        writer.start(D1)
    trade(root, SHADOW, "fly-a", "s1", D1)
    assert SHADOW in marked_accounts(root, (BOOK1_RULES,))
    result = step(root, alerts, *quotes((D1, (19.0, 69.0))), books=(BOOK1_RULES,)).run(D1).result
    assert result[SHADOW]["trades"] == [{"trade_id": "s1", "status": VALUED}]
    assert (account_folder(root, SHADOW) / TRADE_MARKS_FILE).is_file()
    assert not PaperAccount(root, BOOK1_RULES).file(TRADE_MARKS_FILE).exists()
    assert [r["date"] for r in PaperAccount(root, SHADOW).equity_history()][-1] == D1.isoformat()
    assert not (root / "journal" / "shadow" / "fly-a-v1" / "daily_totals.csv").exists()  # nothing public written


def test_an_account_not_started_has_nothing_to_mark(root):
    assert marked_accounts(root, (BOOK1_RULES, shadow_account("never-v1"))) == [BOOK1_RULES]
