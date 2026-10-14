"""Story S2 against story S1: the figures scoreboard B judges with are the protocol's. Each named constant appears in
the protocol item it comes from, so a protocol edit that changes one fails here until the code follows (and the
freeze then hashes both). The board states the protocol version and whether it is frozen."""

from pathlib import Path

from fno.config import ROOT
from fno.evaluation.protocol import PROTOCOL_FILE, parse_protocol
from fno.scoreboard import uncertainty as figures
from fno.scoreboard.protocol_status import protocol_status

TEXT = (ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")


def item(key: str) -> str:
    return parse_protocol(TEXT).items[key].value.replace(",", "")


def test_the_bootstrap_figures_are_the_protocol_s():
    rule = item("uncertainty_criterion")
    assert f"Block length {figures.BLOCK_DAYS} trading days" in rule
    assert f"{figures.RESAMPLES} resamples" in rule and f"seed {figures.SEED}" in rule
    assert f"nearest-rank {figures.LOWER_PERCENTILE}th percentile" in rule
    assert f"at least {figures.MIN_DAYS_SINCE_START} trading days since the common start" in rule


def test_the_sample_figures_are_the_paper_gate_s():
    gate = item("paper_gate")
    assert f"at least {figures.MIN_MONTHS} full calendar months" in gate
    assert f"at least {figures.MIN_POSITIONS} completed positions" in gate


def test_the_board_states_the_protocol_version_and_whether_it_is_frozen(tmp_path: Path):
    (tmp_path / PROTOCOL_FILE).parent.mkdir(parents=True)
    (tmp_path / PROTOCOL_FILE).write_text("Protocol version: 2\n")
    assert protocol_status(tmp_path).label == "protocol v2, not frozen: figures provisional"
    (tmp_path / "research/evaluation/FREEZE_v2.md").write_text("frozen")
    assert protocol_status(tmp_path).label == "protocol v2, frozen"
    assert protocol_status(tmp_path / "none").label == "no evaluation protocol: figures provisional"
