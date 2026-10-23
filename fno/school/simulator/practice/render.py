"""The practice report as lines (story MS-SIM-d3, criterion 3): every line begins with `practice (simulator)`, so no
line can be cut out and read as a pilot result. The labels the story requires come first: the close slot, the spread's
capture period, the unmeasured size, the margin factor and the clock. Nothing is ranked, licensed or recommended."""

from ..constants import PRACTICE_LABEL, SIZE_GATE_NOT_TESTED_LABEL, SLOT_LABEL, SPREAD_LABEL
from .clock import PRACTICE_CLOCK_LABEL
from .margin import NO_SPAN_LINE
from .report import PracticeReport

NOT_ARCHIVED = "local only, not archived: no practice result may be shown to the owner, reported or used in a decision"
NEVER_TUNES = "practice results are never used to choose, tune or rank a counted driver"
NOT_VALUED = "positions still open at the window's end are not valued"
TOP_BUCKETS = 8
LABELS = (SLOT_LABEL, SPREAD_LABEL, SIZE_GATE_NOT_TESTED_LABEL, PRACTICE_CLOCK_LABEL, NOT_VALUED)


def line(text: str) -> str:
    return f"{PRACTICE_LABEL} | {text}"


def render(report: PracticeReport, status: list[str] | None = None) -> list[str]:
    """`status`: the report's first line(s), already labelled (the archive's); local only, not archived by default."""
    roads = ", ".join(str(road) for road in report.roads)
    lines = [
        *(status or [line(NOT_ARCHIVED)]),
        line(NEVER_TUNES),
        line(f"window {report.first} to {report.last}; roads {roads}"),
    ]
    lines += [line(label) for label in (*LABELS, report.margin_label) if label]
    if report.sessions_without_span:
        lines.append(line(NO_SPAN_LINE.format(count=report.sessions_without_span)))
    for scenario, result in report.scenarios.items():
        failed = f"{result.failed_margin} decisions failed the margin law"
        lines.append(line(f"scenario {scenario}: {result.sessions_run} sessions; {failed}"))
        for driver_id, found in sorted(result.drivers.items()):
            codes = " ".join(f"{code}={n}" for code, n in sorted(found.outcomes.items()))
            lines.append(line(f"{scenario} {driver_id}: scheduled {found.scheduled}, eligible {found.eligible}, "
                              f"fillable {found.fillable}, executed {found.executed}; closed {found.closed_trades}, "
                              f"net Rs {found.net:,.0f}; {codes}"))  # fmt: skip
    lines += _coverage_lines(report)
    return lines


def _coverage_lines(report: PracticeReport) -> list[str]:
    legs = sum(c.legs for c in report.coverage)
    if not legs:
        return [line("coverage: no open road-day")]
    total = lambda name: sum(getattr(c, name) for c in report.coverage)  # noqa: E731
    lines = [line(f"coverage over {len(report.coverage)} road-days, {legs} legs: priced {total('priced')}, "
                  f"untraded {total('untraded')}, impossible {total('impossible')} ({total('impossible') / legs:.0%}), "
                  f"unsellable {total('unsellable')}, insufficient spread data {total('insufficient')}")]  # fmt: skip
    for bucket, count in report.insufficient_buckets.most_common(TOP_BUCKETS):
        lines.append(line(f"insufficient spread data: {bucket}: {count} legs"))
    return lines
