"""Story F5 criterion 14 (judge 632 B2) and judge 632.1's minor: Book 2's own stop on a research version (one loss at
the version's catastrophic cap, or a realised net at 3 times it, on Book 2's own closed trades), one row and one alert,
the row append-only and never back-dated."""

from datetime import date, timedelta

import pytest

from fno.accounting.ledgers import TradeLine
from fno.book2.pauses import PAUSES_FILE, Book2ResearchPauses, PauseTrigger, PausesRefused, ResearchPauses
from fno.scorecard.strategy_record import ClosedTrade, StrategyRecord
from tests.playbook.evaluation_builders import DAY, playbook, strategy

RESEARCH = strategy("sc-research", "research")  # catastrophic_loss_rs 10,000
CAP = 10_000.0


def closed(*nets, account="book2_hybrid", strategy_tag="sc-research-v1"):
    trades = tuple(ClosedTrade(f"t{n}", DAY, TradeLine(f"t{n}", DAY, net, 0.0), True) for n, net in enumerate(nets))
    return StrategyRecord(account, strategy_tag, trades, (), (), ())


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "sent"


def review(tmp_path, records, committed=None):
    pauses = ResearchPauses(tmp_path, lambda: committed)
    alerts = Alerts()
    step = Book2ResearchPauses(lambda: records, lambda: playbook(RESEARCH, registered=[RESEARCH.key]), pauses, alerts)
    return step.review(DAY, {}), pauses, alerts


@pytest.mark.parametrize(("nets", "paused"), [
    ((-CAP,), True),  # one loss exactly at the cap
    ((-CAP + 1,), False),  # Rs 1 less
    ((-9_999.0, -9_999.0, -10_002.0), True),  # one at the cap (also below 3 x cap)
    ((-9_000.0, -9_000.0, -9_000.0, -3_000.0), True),  # net -30,000 = 3 x cap: cumulative
    ((-9_000.0, -9_000.0, -9_000.0, -2_999.0), False),  # net -29,999
])  # fmt: skip
def test_the_caps_and_their_boundaries(tmp_path, nets, paused):
    result, pauses, alerts = review(tmp_path, [closed(*nets)])
    assert (pauses.paused_on(DAY) == ("sc-research-v1",)) is paused and len(alerts.sent) == int(paused)


def test_a_second_run_adds_nothing_and_only_book2_s_own_trades_count(tmp_path):
    review(tmp_path, [closed(-CAP)])
    again, pauses, alerts = review(tmp_path, [closed(-CAP)])
    assert alerts.sent == [] and len(pauses.rows()) == 1
    shadow = closed(-CAP * 5, account="shadow:sc-research-v1")
    book1 = closed(-CAP * 5, account="book1_rules")
    _, other, other_alerts = review(tmp_path / "b", [shadow, book1])
    assert other.paused_on(DAY) == () and other_alerts.sent == []


def test_a_pause_takes_effect_from_its_day(tmp_path):
    _, pauses, _ = review(tmp_path, [closed(-CAP)])
    assert pauses.paused_on(DAY - timedelta(days=1)) == () and pauses.paused_on(DAY) == ("sc-research-v1",)


def test_an_edited_or_removed_row_is_refused(tmp_path):
    _, pauses, _ = review(tmp_path, [closed(-CAP)])
    committed = (tmp_path / PAUSES_FILE).read_text()
    (tmp_path / PAUSES_FILE).write_text(committed.replace("catastrophic", "mild"))
    with pytest.raises(PausesRefused, match="never edited or removed"):
        ResearchPauses(tmp_path, lambda: committed).paused_on(DAY)
    (tmp_path / PAUSES_FILE).write_text("version,day,reason\n")
    with pytest.raises(PausesRefused):
        ResearchPauses(tmp_path, lambda: committed).paused_on(DAY)


def test_a_back_dated_row_is_refused_on_write_and_on_read(tmp_path):
    pauses = ResearchPauses(tmp_path, lambda: None)
    pauses.append(PauseTrigger("a-v1", "r"), DAY)
    with pytest.raises(PausesRefused, match="back-dated"):
        pauses.append(PauseTrigger("b-v1", "r"), DAY - timedelta(days=1))
    with (tmp_path / PAUSES_FILE).open("a") as file:
        file.write(f"c-v1,{(DAY - timedelta(days=3)).isoformat()},r\n")
    with pytest.raises(PausesRefused, match="back-dated"):
        pauses.rows()


def test_no_file_means_no_pause(tmp_path):
    assert ResearchPauses(tmp_path, lambda: None).paused_on(date(2026, 10, 26)) == ()
