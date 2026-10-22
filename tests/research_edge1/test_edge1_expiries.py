"""Protocol section 3, revision 6: a monthly contract NSE moved to a new expiry date keeps one date, the one it
really expired on; a weekly of another date is left alone; the relabel never reads past the rows it is given."""

from datetime import date

from edge1study.day_files import DayRows
from edge1study.expiries import final_expiries, relabelled_panel, relabelled_rows

from fno.research_data.panel_reader import FutureQuote, NiftyPanel, OptionQuote, SessionClose

OLD, NEW, WEEKLY = date(2024, 3, 28), date(2024, 3, 27), date(2024, 3, 6)
BEFORE, AFTER = date(2024, 2, 28), date(2024, 3, 4)


def future(expiry):
    return FutureQuote(expiry, 1.0, 1.0, 10, 100)


def option(expiry):
    return OptionQuote(expiry, 100.0, "CE", 1.0, 1.0, 10, 100)


def test_the_last_listed_date_wins():
    assert final_expiries({BEFORE: (future(OLD),), AFTER: (future(NEW),)}) == {OLD: NEW, NEW: NEW}


def test_rows_move_options_futures_and_lots_but_not_a_weekly():
    rows = [DayRows(BEFORE, (option(OLD), option(WEEKLY)), (future(OLD),), {OLD: 15}, "udiff"),
            DayRows(AFTER, (option(NEW),), (future(NEW),), {NEW: 15}, "udiff")]  # fmt: skip
    moved = relabelled_rows(rows)
    assert [q.expiry for q in moved[0].options] == [NEW, WEEKLY] and moved[0].futures[0].expiry == NEW
    assert moved[0].lots == {NEW: 15}
    assert relabelled_rows(rows[:1])[0].futures[0].expiry == OLD  # nothing after the rows given is read


def test_the_panel_moves_the_same_way():
    panel = NiftyPanel((SessionClose(BEFORE, "regular", 1.0, None), SessionClose(AFTER, "regular", 1.0, None)),
                       {BEFORE: (option(OLD),), AFTER: (option(NEW),)},
                       {BEFORE: (future(OLD),), AFTER: (future(NEW),)})  # fmt: skip
    moved = relabelled_panel(panel)
    assert moved.options[BEFORE][0].expiry == NEW and moved.futures[BEFORE][0].expiry == NEW
