"""Story A16c: every documented command that installs `requirements-groww.txt` carries `--use-pep517`. Without it pip
builds the Groww SDK's two old source dependencies (`clint`, `args`) with a container's Debian-patched setuptools, which
fails; pip refuses the flag inside a requirements file, so the commands must carry it."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTED = ("CLAUDE.md", "README.md", "AGENTS.md", "docs", ".github", ".claude")
INSTALL = re.compile(r"pip install[^`\n]*-r requirements-groww\.txt")


def install_commands() -> list[tuple[str, str]]:
    found = []
    for entry in DOCUMENTED:
        path = ROOT / entry
        files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()] if path.is_dir() else []
        for file in files:
            text = file.read_text(encoding="utf-8", errors="ignore")
            found += [(file.relative_to(ROOT).as_posix(), m.group(0)) for m in INSTALL.finditer(text)]
    return found


def test_every_documented_groww_install_carries_use_pep517():
    commands = install_commands()
    # CLAUDE.md and README.md now name tools/routine_setup.sh (story O7); tests/test_routine_setup.py checks its flag.
    assert {name for name, _ in commands} >= {"docs/stories/A16-intraday-quote-recorder.md"}
    assert [(name, command) for name, command in commands if "--use-pep517" not in command] == []


def test_the_requirements_file_says_how_to_install_it():
    text = (ROOT / "requirements-groww.txt").read_text(encoding="utf-8")
    assert "sh tools/routine_setup.sh --groww" in text
    assert "--use-pep517" in text
