"""`--archive` for one practice run (story MS-SIM-e2): names the run, archives its files and the report text, and gives
back what the report's first line says. The default run never comes here, so it writes nothing outside its home."""

from collections.abc import Callable
from pathlib import Path

from ..practice.render import render
from ..practice.report import PracticeReport
from ..practice.runner import PracticeRunner
from ..practice.window import RunWindow
from .archive import PracticeArchive
from .files import run_files
from .inputs import inputs_digest
from .names import run_id
from .outcome import ArchiveOutcome, report_head
from .run import archive_run


def archive_practice(report: PracticeReport, window: RunWindow, runner: PracticeRunner, commit: str,
                     build_archive: Callable[[str], PracticeArchive]) -> ArchiveOutcome:  # fmt: skip
    """`commit`: the checked-in code commit (`inputs.code_commit`); `build_archive`: the run's archive by its id."""
    scenarios = tuple(scenario.value for scenario in runner.scenarios)
    roads = [str(code) for code in window.roads]
    digest = inputs_digest(runner.parts.spreads, report.margin_label)
    run = run_id(window.first, window.last, roads, scenarios, commit, digest)
    text = "\n".join(render(report, [report_head(run)])) + "\n"
    files = run_files(run, Path(runner.home), scenarios)
    return archive_run(build_archive(run), run, files, text)
