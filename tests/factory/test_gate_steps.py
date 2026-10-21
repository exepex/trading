"""G1-G3 end to end in a temporary repository (story R1b): register, screen, spend, plan; each gate once, in order,
on committed inputs; a measurement is never screened."""

from datetime import date

import pytest

from fno.factory.constants import DATA_SPEND_FILE
from fno.factory.gate_log import figures
from fno.factory.gate_order import GateStepError
from fno.factory.wiring import build_gate_log, build_gate_steps, build_registration, read_idea

from .helpers import BLOCK, INPUTS, REGISTER, commit, git, init_repo, write_card

DAY = date(2026, 10, 17)


@pytest.fixture
def repo(tmp_path):
    init_repo(tmp_path)
    (tmp_path / DATA_SPEND_FILE).write_text(REGISTER)
    write_card(tmp_path, BLOCK + INPUTS)
    build_registration(tmp_path).register(read_idea("X1", tmp_path), DAY)
    commit(tmp_path, "register X1")
    return tmp_path


def run(root, gate):
    return getattr(build_gate_steps(root), gate)(read_idea("X1", root), DAY)


def test_screen_spend_and_plan_log_one_row_each_in_order(repo):
    screened = run(repo, "screen")
    assert screened.figures["net"] == pytest.approx(1200 - 300 - 450)
    run(repo, "spend")
    plan = run(repo, "plan")
    rows = build_gate_log(repo).rows()
    assert [(r.gate, r.outcome) for r in rows] == [("G0", "idea"), ("G1", "passed"), ("G2", "fresh"), ("G3", "planned")]
    assert figures(rows[1]) == {"bound": "1200.0", "expected": "1200.0", "cost": "300.0", "tail": "450.0",
                                "net": "450.0", "ratio": "4.00", "thin_margin": "no"}  # fmt: skip
    assert plan.n == 241 and figures(rows[3])["n"] == "241"  # (2.3263 x 3000 / 450)^2 = 240.5
    assert all(row.commit == git(repo, "rev-parse", "HEAD") for row in rows[1:])


def test_a_gate_runs_once_and_only_after_the_one_before(repo):
    with pytest.raises(GateStepError, match="its last gate is G0 idea; this gate runs after G1 passed"):
        run(repo, "spend")
    run(repo, "screen")
    with pytest.raises(GateStepError, match="its last gate is G1 passed; this gate runs after G0 idea"):
        run(repo, "screen")


def test_a_screened_out_idea_stops(repo):
    card = repo / "research/ideas/X1.md"
    card.write_text(card.read_text().replace("least_favourable: 1200", "least_favourable: 500"))
    commit(repo, "inputs")
    assert run(repo, "screen").outcome == "screened_out"
    with pytest.raises(GateStepError, match="this gate runs after G1 passed"):
        run(repo, "spend")


def test_uncommitted_inputs_and_other_staged_files_are_refused(repo):
    card = repo / "research/ideas/X1.md"
    card.write_text(card.read_text().replace("loss: 9000", "loss: 1"))
    with pytest.raises(GateStepError, match="uncommitted changes: commit its inputs"):
        run(repo, "screen")
    commit(repo, "inputs")
    (repo / "notes.md").write_text("x\n")
    git(repo, "add", "notes.md")
    with pytest.raises(GateStepError, match=r"other files are staged \(notes.md\)"):
        run(repo, "screen")
    assert len(build_gate_log(repo).rows()) == 1


def test_a_measurement_is_never_screened(tmp_path):
    init_repo(tmp_path)
    write_card(tmp_path, BLOCK.replace("measurement: no", "measurement: yes") + INPUTS)
    build_registration(tmp_path).register(read_idea("X1", tmp_path), DAY)
    commit(tmp_path, "register X1")
    with pytest.raises(GateStepError, match="a measurement is never screened"):
        run(tmp_path, "screen")
