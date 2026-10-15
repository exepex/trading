"""Story A16 criteria 10, 11 and 12: no order, position, margin or funds call anywhere in the package; the repository
files hold no price; the concrete classes are wired only in the composition root."""

import ast
import csv
import io
import re
from datetime import date, time
from pathlib import Path

from fno.intraday import wiring
from fno.intraday.slots import marks
from tests.intraday.fakes import FakeClock, build, ist, level_at
from tests.intraday.groww_fakes import FORBIDDEN

PACKAGE = Path(wiring.__file__).parent
CONCRETE = ("GrowwIntradaySource", "FirstVersionStore", "HttpDateClock", "QuoteSnapshotRv15m", "GitManifestRecorder",
            "SlackChannelAlerts", "GrowwProvider")  # fmt: skip


def _names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} | {
        n.id for n in ast.walk(tree) if isinstance(n, ast.Name)
    }


def test_no_file_of_the_package_names_an_order_position_margin_or_funds_call():
    found = {p.name: sorted(_names(p) & set(FORBIDDEN)) for p in PACKAGE.glob("*.py")}
    assert not {name: calls for name, calls in found.items() if calls}
    assert not [p.name for p in PACKAGE.glob("*.py") if re.search(r"order|margin|position", p.read_text(), re.I)
                and re.search(r"\.(place|modify|cancel)_", p.read_text())]  # fmt: skip


def test_concrete_classes_are_built_only_in_the_composition_root():
    for path in PACKAGE.glob("*.py"):
        if path.name == "wiring.py":
            continue
        calls = {n.func.id for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)}  # fmt: skip
        assert not calls & set(CONCRETE) - {"RatePacer"}, path.name


def test_the_repository_files_hold_no_price(tmp_path):
    clock = FakeClock(ist(date(2026, 10, 14), 9, 10))
    recorder, *_ = build(tmp_path, clock)
    recorder.run(time(15, 35))
    levels = {f"{level_at(m):g}" for m in marks(date(2026, 10, 14))}
    repository_files = [p for p in tmp_path.rglob("*") if p.is_file() and "drive" not in p.parts]
    assert {p.suffix for p in repository_files} == {".csv", ".json"}
    for path in repository_files:
        text = path.read_text(encoding="utf-8")
        assert not any(level in text for level in levels), path.name
        if path.suffix == ".csv":
            header = next(csv.reader(io.StringIO(text)))
            assert not {"bid", "ask", "last", "level", "spot", "price", "index_level"} & set(header), path.name
