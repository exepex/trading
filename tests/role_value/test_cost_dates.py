"""Judge 194 addendum 3: each scored opportunity is charged its own date's cost. One unit, macro, consulted alone on
three days of November 2026. Plan Rs 600 over 60 minutes, so Rs 10 a minute:
- 2 Nov, 20 minutes, Rs 200: shadow unavailable (not scored), placed first;
- 3 Nov, 30 minutes, Rs 300: scored, the call bought at Rs 100 and sold at Rs 120 on 4 Nov, net Rs 1,460;
- 5 Nov, 10 minutes, Rs 100: scored, the same trade on 5 and 6 Nov, net Rs 1,460.
Net values: 1,460 - 300 = 1,160 and 1,460 - 100 = 1,360, mean 1,260. Cost on the scored dates (300 + 100) / 2 = 200;
operating cost (200 + 300 + 100) / 3 = 200. Charging the first consulted date's 200 to both gives 1,260 twice; so
does charging the scored dates' mean. Only the exact series tells them apart."""

from datetime import date, timedelta

from fno.budget.allocation import allocate
from fno.constants import Decision
from fno.role_value import score as score_module
from fno.role_value.report import Period
from fno.role_value.score import Opportunity, score_unit
from fno.role_value.verdict import EARNS, verdicts
from fno.role_value.wiring import role_value_report_from
from fno.scoreboard.ports import ProtocolStatus
from tests.role_value.builders import BOOK, row, usage, write_rows, write_shadow
from tests.role_value.unit_fixture import LOTS
from tests.scoreboard.matched_builders import (
    Calendar,
    Settlements,
    Snapshots,
    quote,
    record,
    write_day,
    write_pack,
    write_run,
)

D2, D3, D4, D5, D6 = (date(2026, 11, d) for d in (2, 3, 4, 5, 6))
QUOTES = {D3: [quote(25000, "CE", 98, 100)], D4: [quote(25000, "CE", 120, 122)],
          D5: [quote(25000, "CE", 98, 100)], D6: [quote(25000, "CE", 120, 122)]}  # fmt: skip
USAGE = [usage(D2, "20.00"), usage(D3, "30.00"), usage(D5, "10.00")]
ONLY = ("macro",)


def journal(root, usage_rows=USAGE):
    for day, exit_day in ((D3, D4), (D5, D6)):
        pack = write_pack(root, day, ("o1", exit_day))
        write_run(root, BOOK, day, record("o1", pack=pack), pack=pack)
        write_shadow(root, day, record("o1", Decision.NO_TRADE, "no trade", legs=(), pack=pack))
    for day in (D2, D3, D4, D5, D6):
        write_day(root, day, {BOOK: f"{day.isoformat()}-{BOOK}"} if day in (D3, D5) else {})
    units = root / "agents" / "role_units.yaml"
    units.parent.mkdir(parents=True, exist_ok=True)
    units.write_text(f"{BOOK}:\n  '1':\n    macro: [macro_economist]\n")
    write_rows(root, [row(D2, "macro", status="shadow_unavailable", consulted=ONLY), row(D3, "macro", consulted=ONLY),
                      row(D5, "macro", consulted=ONLY)])  # fmt: skip
    built = role_value_report_from(root, LOTS, Calendar().sessions, Snapshots(QUOTES), Settlements(),
                                   ProtocolStatus(None, False), lambda month: allocate(month, 600.0, usage_rows),
                                   lambda month: usage_rows)  # fmt: skip
    return built.build(Period(BOOK, date(2026, 11, 1), date(2026, 11, 30), D2))


def test_each_scored_opportunity_is_charged_its_own_date_s_cost_and_the_series_shows_it(tmp_path, monkeypatch):
    fed = []
    real = score_module.resampled_ratios
    monkeypatch.setattr(score_module, "resampled_ratios", lambda series: fed.append(series.net) or real(series))
    macro = journal(tmp_path).scores[0]
    assert fed == [(1160.0, 1360.0)]  # the exact series given to S3's resampler, in date order
    assert (macro.applicable, macro.mean_difference, macro.mean_net_value) == (2, 1460.0, 1260.0)
    assert (macro.cost, macro.operating_cost) == (200.0, 200.0)


def test_an_unknown_day_that_was_not_scored_leaves_the_cost_known(tmp_path):
    macro = journal(tmp_path, [usage(D3, "30.00"), usage(D5, "10.00")]).scores[0]  # no usage on 2 Nov
    assert macro.operating_cost is None
    assert (macro.cost, macro.mean_net_value) == (300.0, 1160.0)  # Rs 600 over 40 minutes: 450 and 150


def test_an_unknown_unscored_day_leaves_the_verdict_possible():
    days = [date(2026, 11, 2) + timedelta(i) for i in range(30)]
    opportunities = [Opportunity(d, 500.0 if i % 3 else -100.0, True, 0.0, 10.0) for i, d in enumerate(days)]
    scored = score_unit("macro", opportunities, operating_cost=None)
    assert scored.cost == 10.0 and scored.operating_cost is None
    assert verdicts([scored], True, date(2027, 6, 29), [date(2027, 6, 29)]) == {"macro": EARNS}
