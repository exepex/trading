"""Story G6 freeze, criterion 11 (judges 596-597): an import walk from every byte-checked and recorded v4 module; every
`fno` module it reaches is byte-checked, recorded or named as not deciding, with a reason. A new import of an unclassed
module fails here, so a file on a v4 input path is never missed by hand. S1's walk (judge 229), its `imported` reused;
recorded modules are followed too (their imports may decide a value), not-deciding ones are not."""

from pathlib import Path

from fno.forecast_scoring.v4.freeze_check import byte_checked
from fno.forecast_scoring.v4.freeze_classes import NOT_DECIDING, RECORDED
from tests.evaluation.test_scoring_closure import imported

ROOT = Path(__file__).resolve().parents[2]


def walk(followed: set[str], stops: set[str], read=imported) -> tuple[dict[str, set[str]], set[str]]:
    """The reached modules outside every class (each with its importers), and every module reached."""
    todo, seen, missing, reached = sorted(f for f in followed if f.endswith(".py")), set(), {}, set()
    while todo:
        current = todo.pop()
        if current in seen:
            continue
        seen.add(current)
        for target in read(current):
            reached.add(target)
            if target in followed:
                todo.append(target)
            elif target not in stops:
                missing.setdefault(target, set()).add(current)
    return missing, reached


def _classes() -> tuple[set[str], set[str]]:
    return {p for p in byte_checked(ROOT) if p.endswith(".py")} | set(RECORDED), set(NOT_DECIDING)


def test_every_module_v4_reaches_is_in_a_class():
    assert walk(*_classes())[0] == {}


def test_every_recorded_and_not_deciding_entry_is_reached_and_in_one_class_only():
    followed, stops = _classes()
    reached = walk(followed, stops)[1]
    assert (set(RECORDED) | stops) - reached == set()  # a stale entry is removed, never kept
    assert not stops & followed


def test_dropping_a_module_from_the_classes_names_it_and_its_importer():
    followed, stops = _classes()
    missing = walk(followed - {"fno/intraday/candle_rv_table.py"}, stops)[0]
    assert set(missing) == {"fno/intraday/candle_rv_table.py"}


def test_an_import_inside_a_function_counts_and_a_module_without_fno_imports_reaches_nothing(tmp_path):
    graph = {"a.py": {"b.py"}, "b.py": set(), "c.py": {"d.py"}}
    missing, reached = walk({"a.py", "c.py"}, set(), read=lambda m: graph.get(m, set()))
    assert missing == {"b.py": {"a.py"}, "d.py": {"c.py"}} and reached == {"b.py", "d.py"}
    source = tmp_path / "late.py"
    source.write_text("def f():\n    from fno.analytics import norm_cdf\n    return norm_cdf\n", encoding="utf-8")
    from tests.evaluation import test_scoring_closure

    original = test_scoring_closure.ROOT
    test_scoring_closure.ROOT = tmp_path
    try:
        (tmp_path / "fno").mkdir()
        (tmp_path / "fno" / "analytics.py").write_text("", encoding="utf-8")
        assert imported("late.py") == {"fno/analytics.py"}
    finally:
        test_scoring_closure.ROOT = original
