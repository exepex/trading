"""Story STR1b criterion 5: while an activation gate is open, a version whose structure is an STR1 code cannot be
registered as a research shadow or approved to paper (the status changer refuses and writes nothing; the loader refuses
a registry that says otherwise, and D2 takes shadows and approved versions only from the loaded playbook). An
unregistered research file is never refused, and SF, SC and BF are unaffected."""

from datetime import date

import pytest

from fno.constants import STR1_ACTIVATION_PENDING
from fno.playbook import activation
from fno.playbook.fields import PlaybookError

from .builders import changer, commit_all, document, filled_evidence, loader, repository, write

DAY = date(2026, 10, 21)


def candidate(tmp_path, code: str, widths=(200, 100)):
    doc = document(evidence=filled_evidence(repository(tmp_path)))
    doc["structure"] = dict(doc["structure"], code=code, widths=list(widths))
    path = write(tmp_path / "playbook", doc)
    commit_all(tmp_path, "candidate")
    return path


def written(tmp_path, path) -> tuple[str, str]:
    registry = tmp_path / "playbook" / "registry.csv"
    return (registry.read_text() if registry.exists() else ""), path.read_text()


def test_the_gates_as_shipped_block_shadows_until_str1b_2_and_paper_until_e8():
    assert STR1_ACTIVATION_PENDING == {"STR1b-2": ("shadow", "paper"), "E8": ("paper",)}


def test_an_unregistered_str1_research_file_still_loads(tmp_path):
    candidate(tmp_path, "PCS")
    assert loader(tmp_path).load().get("sc-test", 1).structure.code == "PCS"


@pytest.mark.parametrize(("status", "gates"), [("research", "STR1b-2"), ("paper", "STR1b-2, E8")])
def test_an_str1_version_is_refused_for_shadow_and_paper_and_nothing_is_written(tmp_path, status, gates):
    path = candidate(tmp_path, "PCS")
    before = written(tmp_path, path)
    with pytest.raises(
        PlaybookError, match=f"PCS cannot be used for .* while these activation gates are open: {gates}"
    ):
        changer(tmp_path).change("sc-test", 1, status, "owner", DAY)
    assert written(tmp_path, path) == before


@pytest.mark.parametrize("code", ["SF", "SC", "BF"])
def test_four_leg_versions_are_unaffected(tmp_path, code):
    candidate(tmp_path, code, widths=(300, 200, 100))
    changer(tmp_path).change("sc-test", 1, "research", "desk", DAY)
    assert loader(tmp_path).load().shadow_on(date(2026, 10, 22))[0].structure.code == code


def test_after_str1b_2_a_shadow_is_allowed_and_paper_still_waits_for_e8(tmp_path, monkeypatch):
    monkeypatch.setattr(activation, "STR1_ACTIVATION_PENDING", {"E8": ("paper",)})
    candidate(tmp_path, "CDS")
    changer(tmp_path).change("sc-test", 1, "research", "desk", DAY)
    assert loader(tmp_path).load().shadow_on(date(2026, 10, 22))[0].structure.code == "CDS"
    with pytest.raises(PlaybookError, match="CDS cannot be used for paper while these activation gates are open: E8"):
        changer(tmp_path).change("sc-test", 1, "paper", "owner", DAY)
