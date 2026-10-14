"""Story D6 criterion 4 and the registry's checks: rows are only ever appended (the repository's own git history is
checked), and a bad row is refused with its place."""

from datetime import date

import pytest

from fno.books.version_registry import VersionError, VersionRegistry, VersionRow, parse_versions, render
from fno.config import ROOT
from fno.playbook.history import PlaybookGit
from fno.playbook.registry import rewritten_history
from tests.playbook.builders import commit_all, git

COMMIT = "a" * 40


def row(version_id="v1", starts_on=date(2026, 10, 20), book="book2_hybrid", commit=COMMIT, components=None):
    return VersionRow(book, version_id, starts_on, commit, components or {"model": "m"}, "first version")


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([row(book="book9")], "unknown book"),
        ([row(commit="abc")], "full git commit"),
        ([row(components={"model": 3})], "components"),
        ([row(), row()], "registered twice"),
        ([row(), row("v2", starts_on=date(2026, 10, 20))], "not after v1"),
    ],
)
def test_bad_rows_are_refused(rows, message):
    with pytest.raises(VersionError, match=message):
        parse_versions(render(rows))


def test_append_keeps_the_old_bytes_and_refuses_a_bad_row(tmp_path):
    registry = VersionRegistry(tmp_path / "journal" / "versions.csv")
    registry.append(row())
    before = registry.path.read_text()
    registry.append(row("v2", starts_on=date(2026, 10, 25)))
    assert registry.path.read_text().startswith(before) and len(registry.rows()) == 2
    with pytest.raises(VersionError):
        registry.append(row("v3", starts_on=date(2026, 10, 1)))
    assert len(registry.rows()) == 2


def test_an_edited_past_row_shows_in_git_history(tmp_path):
    git(tmp_path, "init", "-q")
    registry = VersionRegistry(tmp_path / "journal" / "versions.csv")
    registry.append(row())
    commit_all(tmp_path)
    registry.path.write_text(registry.path.read_text().replace("first version", "renamed"))
    commit_all(tmp_path)
    assert rewritten_history(PlaybookGit(tmp_path).file_versions("journal/versions.csv"))


def test_the_repository_registry_was_only_ever_appended_to():
    versions = PlaybookGit(ROOT).file_versions("journal/versions.csv")
    current = (ROOT / "journal" / "versions.csv").read_text()
    assert rewritten_history([*versions, current]) == []
    parse_versions(current)
