"""Story S1 fixtures: the committed draft protocol, a decided copy of it, and a temporary git repository holding a
protocol, its listed files (the real-money gate of story RM1 among them), a config and the research ledger."""

from __future__ import annotations

import re
from pathlib import Path

from fno.config import ROOT
from fno.evaluation.gate import GATE_FILE
from fno.evaluation.protocol import PROPOSAL, PROTOCOL_FILE
from fno.research_engine.ledger import COLUMNS
from tests.playbook.builders import commit_all, git

DRAFT = (ROOT / PROTOCOL_FILE).read_text(encoding="utf-8")
GATE = (ROOT / GATE_FILE).read_text(encoding="utf-8")  # decided by the owner on 15 Oct 2026
DECIDED_ON = "decided by the owner on 2026-10-20"
CONFIG = """desk:
  timetable:
    pack: "14:58"
    decision_deadline: "15:12"
scorecard_review:
  confidence: 0.95
risk:
  max_loss_per_trade_rs: 10000
charges:
  brokerage_per_order: 20.0
slack:
  channel_id: C0
"""
LEDGER_HEAD = ",".join(COLUMNS) + "\n1,old,an earlier trial,retrospective,no,2026-10-12,,,,\n"


def decided(text: str = DRAFT) -> str:
    return text.replace(f"**Status:** {PROPOSAL}", f"**Status:** {DECIDED_ON}")


def small_frozen_files(text: str) -> str:
    """The protocol listing only files the temporary repository holds."""
    listed = (
        "- **Value:** `research/evaluation/PROTOCOL.md`, `fno/scoring.py`, `config.yaml:desk.timetable`,\n"
        "  `config.yaml:scorecard_review`, `research/evaluation/REAL_MONEY_GATE.md`."
    )
    return re.sub(r"(### `frozen_files` [^\n]*\n)- \*\*Value:\*\*.*?\n(- \*\*Status)", rf"\1{listed}\n\2", text,
                  flags=re.DOTALL)  # fmt: skip


def protocol_repo(root: Path, text: str | None = None, gate: str = GATE) -> str:
    """A repository with a decided protocol (or `text`), its listed files, the gate, config.yaml and the ledger;
    committed."""
    git(root, "init", "-q")
    files = {
        PROTOCOL_FILE: text if text is not None else small_frozen_files(decided()),
        GATE_FILE: gate,
        "fno/scoring.py": "SCORE = 1\n",
        "config.yaml": CONFIG,
        "research/ledger.csv": LEDGER_HEAD,
    }
    for name, body in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(body, encoding="utf-8")
    return commit_all(root, "protocol")
