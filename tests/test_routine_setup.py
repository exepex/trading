"""Story O7: every routine sets up through tools/routine_setup.sh, which installs with the interpreter it checks."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETUP = ROOT / "tools" / "routine_setup.sh"
ROUTINE_DOCS = ("CLAUDE.md", "AGENTS.md", "README.md")
BARE_PIP = re.compile(r"(?<!-m )\bpip3? install\b")


def _code_lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")]


def test_setup_installs_only_through_the_interpreter_it_checks():
    lines = _code_lines(SETUP)
    assert not [line for line in lines if BARE_PIP.search(line)]
    assert any('"$py" -m pip install' in line and "--use-pep517" in line for line in lines)
    assert any('"$name" -c "import $modules"' in line for line in lines)


def test_setup_covers_both_names_and_turns_hooks_on():
    text = SETUP.read_text(encoding="utf-8")
    assert text.count("for name in python3 python") == 2
    assert "git config core.hooksPath .githooks" in text
    assert "set -eu" in text


def test_routine_docs_never_name_a_bare_pip_install():
    offenders = [
        f"{name}:{number}"
        for name in ROUTINE_DOCS
        for number, line in enumerate((ROOT / name).read_text(encoding="utf-8").splitlines(), 1)
        if BARE_PIP.search(line)
    ]
    assert offenders == []


def test_the_3pm_routine_and_readme_name_the_script():
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    recorder = claude.split("## Daily desk routine", 1)[1].split("\n## ", 1)[0]
    assert "sh tools/routine_setup.sh --groww" in recorder
    assert "sh tools/routine_setup.sh --groww" in (ROOT / "README.md").read_text(encoding="utf-8")
