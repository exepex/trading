"""REC1d's words guard (item 7; criterion f and judge 664.1's note): every line either section makes is one of the
allowed templates with each field of its own kind (dates, versions, paths, counts, rupees, codes); a check's problem
is shown only as one of REC1c's problem templates, any other text withheld. A line carrying anything more fails."""

import re
from dataclasses import replace
from datetime import timedelta
from string import Formatter

import pytest

from fno.recommend import check_text as c
from fno.recommend import post as p
from fno.recommend import report_words as w
from fno.recommend.constants import REASON_TEXT, NoTradeReason
from fno.recommend.report_section import EveningSection, MorningSection
from fno.recommend.shelf import check_path
from fno.recommend.store import record_path
from tests.recommend.builders import DAY, established_day, paper_trade
from tests.recommend.report_fakes import TUESDAY, WEDNESDAY, Store, quiet, traded

TOKEN = r"[\w./#@:-]+"
DATE = r"\d\d [A-Z][a-z]{2} \d{4}"
RUPEES = r"-?[\d,]+\.\d\d"


def either(*patterns: str) -> str:
    return "(?:" + "|".join(patterns) + ")"


def pattern(template: str) -> str:
    return "".join(re.escape(text) + (f"(?:{FIELDS[name]})" if name is not None else "")
                   for text, name, _, _ in Formatter().parse(template))  # fmt: skip


FIELDS = {
    "day": DATE, "on": DATE, "days": f"{DATE}(?:, {DATE})*", "version": TOKEN, "path": TOKEN,
    "versions": f"{TOKEN}(?:, {TOKEN})*", "kind": r"[A-Z]\w*", "rung": r"\d", "name": r"[a-z]+",
    "status": TOKEN, "reason": TOKEN, "count": r"\d+", "open": r"\d+", "closed": r"\d+", "quiet": r"\d+",
    "tickets": r"\d+", "net": RUPEES, "total": RUPEES, "amount": RUPEES, "sources": f"{TOKEN}(?:, {TOKEN})*",
    "code": either(*(re.escape(r.value) for r in NoTradeReason)),
    "verdict": either("not known yet", "complete", "incomplete", "data check failed"),
    "text": either(*(re.escape(t) for t in REASON_TEXT.values())),
}  # fmt: skip
FIELDS["rungs"] = f"{pattern(w.RUNG)}(?:; {pattern(w.RUNG)})*"
FIELDS["why"] = either(re.escape(p.NO_PROVEN), re.escape(p.NOT_ELIGIBLE), pattern(p.BRAKED), FIELDS["text"])
FIELDS["problem"] = either(*(r.pattern for r in w.ALLOWED_PROBLEMS), pattern(w.WITHHELD))
FIELDS["answer"] = either(*(pattern(t) for t in (c.FAILED, c.INCOMPLETE, c.TRADED, c.NOTHING_TRADED, c.SAVED,
                                                  c.COST, w.NOT_KNOWN)))  # fmt: skip
FIELDS["trades"] = pattern(c.COUNTS)
LINES = (w.STANDING, w.RUNGS, w.NO_VERSIONS, w.NOTHING_YET, w.NOT_READ, w.CHECK, w.CHECK_NOT_READ, w.NOT_DATED,
         w.NO_CHECKS, w.TONIGHT, w.NO_RECORD, w.NO_RECORD_STEP, p.DO_NOT, p.ELIGIBLE, p.NO_TRADE, p.TRADE)  # fmt: skip
ALLOWED = [re.compile(pattern(t)) for t in LINES]


def allowed(line: str) -> bool:
    return any(a.fullmatch(line) for a in ALLOWED)


def scenarios(tmp_path):
    """Every kind of day the sections show: answers of each kind, each check verdict, unread and missing files."""
    store = Store(tmp_path)
    yield store, DAY
    monday = store.record(traded(DAY))
    store.check(monday, DAY)
    yield store, TUESDAY
    store.check(monday, TUESDAY, net=250.0)
    store.record(replace(paper_trade(), session=TUESDAY))
    yield store, WEDNESDAY
    store.record(established_day(session=WEDNESDAY), WEDNESDAY)
    store.failed_check(DAY, WEDNESDAY, "school/dashcam/s.json#nifty_monthly: 2 live outcomes for one candidate")
    yield store, WEDNESDAY + timedelta(days=1)
    store.failed_check(DAY, WEDNESDAY, "the 51200 put lost Rs 300")
    store.record(quiet(TUESDAY + timedelta(days=7)))
    store.steps[WEDNESDAY + timedelta(days=1)] = ("failed", "recommend:NOT_POSTED")
    yield store, WEDNESDAY + timedelta(days=1)
    store.files[record_path(WEDNESDAY)] = b"{damaged"
    del store.files[check_path(DAY, WEDNESDAY)]
    yield store, WEDNESDAY + timedelta(days=1)


def lines_of(tmp_path) -> list[str]:
    out = []
    for store, day in scenarios(tmp_path):
        evenings = [*store.ports().shelf.recorded_days(day), day]  # each recorded day's evening, and today's
        out += [
            *MorningSection(store.ports()).render(day),
            *(l for d in evenings for l in EveningSection(store.ports()).render(d)),
        ]
    return out


def test_every_line_the_sections_make_is_an_allowed_template(tmp_path):
    lines = lines_of(tmp_path)
    assert len(lines) > 15 and [line for line in lines if not allowed(line)] == []


@pytest.mark.parametrize("line", [
    "Real money: DO NOT TRADE (no version has passed). school/dashcam/CS1/2026-11-02.json",  # a decision path added
    "Check of 02 Nov 2026 on 03 Nov 2026: data check failed. The check failed: the 51200 put lost Rs 300; no total "
    "is given. (0 closed, 0 open, 0 no trade, 0 ticket(s)).",  # a free-text problem
])  # fmt: skip
def test_a_line_carrying_anything_more_is_refused(line):
    assert not allowed(line)


def test_a_free_text_problem_is_withheld_and_its_check_file_named(tmp_path):
    lines = lines_of(tmp_path)
    assert not any("51200" in line for line in lines)
    assert any("a problem whose text is not shown here; see recommend/" in line for line in lines)
