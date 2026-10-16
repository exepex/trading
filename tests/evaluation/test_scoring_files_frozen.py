"""S1 item 15: the freeze hashes only the paths `frozen_files` lists, so the scoring code of S2, S3 and S6 is listed
module by module. A new scoring module left out of the list, or a listed path that is not a file, fails here before it
can reach a freeze."""

from pathlib import Path

from fno.config import ROOT
from fno.evaluation.freeze import CONFIG_PREFIX, frozen_targets
from fno.evaluation.protocol import PROTOCOL_FILE

SCOREBOARD = ROOT / "fno" / "scoreboard"
NOT_SCORING = {"__init__.py", "cli.py"}  # the package marker and the command line decide no figure


def targets() -> list[str]:
    return frozen_targets((ROOT / PROTOCOL_FILE).read_text(encoding="utf-8"))


def test_every_scoreboard_scoring_module_is_hashed_by_the_freeze():
    modules = {f"fno/scoreboard/{p.name}" for p in SCOREBOARD.glob("*.py") if p.name not in NOT_SCORING}
    assert modules and modules - set(targets()) == set()


def test_every_listed_file_target_is_a_file_in_the_repository():
    files = [t for t in targets() if not t.startswith(CONFIG_PREFIX)]
    assert [t for t in files if not (ROOT / t).is_file()] == []


def test_a_scoring_module_missing_from_the_list_is_caught(tmp_path):
    text = (ROOT / PROTOCOL_FILE).read_text(encoding="utf-8").replace("`fno/scoreboard/t_check.py`,", "", 1)
    assert "fno/scoreboard/t_check.py" not in frozen_targets(text)
    assert Path(SCOREBOARD / "t_check.py").is_file()  # the module exists, so the first test would fail on this text
