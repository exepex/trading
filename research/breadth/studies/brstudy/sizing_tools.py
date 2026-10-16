"""The sizing study's two scripts (`research/2026-10-15-breadth-sizing/`), loaded by path: BR1a reuses their
implied-move, strike-screen and baseline code instead of copying it."""

import importlib.util
from pathlib import Path

SIZING = Path(__file__).resolve().parents[3] / "2026-10-15-breadth-sizing"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"br_sizing_{name}", SIZING / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


extract = _load("extract")
sizing = _load("sizing")
