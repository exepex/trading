"""Scope 5 (owner, 21 Oct 2026): NSDL's back-filled values are private. Only the flow-history package names their
table or raw folder, so no screen, card, report or Slack line can read them without a change a judge would see."""

from __future__ import annotations

from pathlib import Path

FNO = Path(__file__).resolve().parents[2] / "fno"
PRIVATE_NAMES = ("nsdl-fpi", "flows/nsdl/raw")


def test_only_the_flow_history_package_names_the_private_nsdl_data():
    naming = sorted(
        path.relative_to(FNO).as_posix()
        for path in FNO.rglob("*.py")
        if any(name in path.read_text(encoding="utf-8") for name in PRIVATE_NAMES)
    )
    assert naming == ["flow_history/nsdl_backfill.py", "flow_history/wiring.py"]
