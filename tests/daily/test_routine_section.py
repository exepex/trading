"""Story O1, criterion 8: CLAUDE.md's "Daily desk routine" section is the one place the routine's start is written."""

from fno.config import ROOT

CLAUDE = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
SECTION = CLAUDE.split("\n## Daily desk routine", 1)[1].split("\n## ", 1)[0]
PROMPT = "\"Run the daily desk routine in CLAUDE.md, section 'Daily desk routine'.\""


def test_the_section_names_the_setup_the_command_and_the_stored_prompt():
    assert all(line in SECTION for line in ("sh tools/routine_setup.sh --groww", "python -m fno daily run", PROMPT))


def test_no_second_routine_section_starts_the_quote_recorder():
    assert "## 3 pm quote recorder" not in CLAUDE and CLAUDE.count("python -m fno daily run") == SECTION.count(
        "python -m fno daily run"
    )
