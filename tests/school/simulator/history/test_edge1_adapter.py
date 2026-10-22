"""EDGE1 is read by file path under its own package name and never joins sys.path (judge 500, minor a)."""

import sys

from fno.school.simulator.history import edge1


def test_edge1_is_loaded_under_a_unique_name_and_its_folder_is_not_on_the_path():
    edge1.module("lots")
    assert edge1.PACKAGE in sys.modules
    assert not any(p.rstrip("/").endswith("research/edge1") for p in sys.path)
    assert "edge1study" not in sys.modules or sys.modules["edge1study"] is not sys.modules[edge1.PACKAGE]


def test_the_schedule_is_asked_only_for_the_indices_it_covers():
    from datetime import date

    assert edge1.circular_lot_or_none("FINNIFTY", date(2022, 1, 27)) is None
    assert edge1.circular_lot_or_none("NIFTY", date(2021, 6, 24)) == 75
