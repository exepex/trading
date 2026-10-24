"""Story A4c-2, round 2 (judge 571): the alert points to the sidecars only for indices that were attempted, and each
index's result line and its part of the alert print the same outcome, "canonical none" exactly when its day was closed
none."""

from datetime import datetime

import pytest

from fno.models import IST
from fno.quotes.expiry_listing import ExpiryListUnavailable
from fno.quotes.indices_cli import SIDECAR_POINTER, record_indices
from tests.quotes.index_fakes import SPOTS, Clock, IndexProvider, Listing, recorders
from tests.quotes.test_recorder_calendar import Alerts

TOO_EARLY = "not started: too early (before 14:41); a rerun from 14:41 to 15:13 records it"
AT_1438 = "DRY2's 14:38 replay"
POINTER = "the sidecars in research/data/quotes/groww/ say why"


class NoNseFile(Listing):
    def listed(self, underlying, today):
        raise ExpiryListUnavailable("no NSE F&O file in the 7 days")


def at(hour, minute, second=0):
    return datetime(2026, 10, 13, hour, minute, second, tzinfo=IST)


def _alerted(tmp_path, start, capsys, **kwargs):
    clock, alerts = Clock(start), Alerts()
    code = record_indices(lambda: recorders(tmp_path, clock, **kwargs), alerts, "cal.csv", clock.now, clock.sleep)
    return code, alerts.sent, capsys.readouterr().out.splitlines()


def test_the_too_early_alert_points_to_no_sidecar_word_for_word(tmp_path, capsys):
    """Should-fix 2: at 14:38 nothing is attempted and no file is written, so the alert names no file to read."""
    code, sent, _ = _alerted(tmp_path, at(14, 38), capsys)
    names = "; ".join(f"{name} ({TOO_EARLY})" for name in SPOTS)
    assert code == 1 and sent == [f"3 pm index recorder: not recorded today: {names}. Data only; NIFTY is separate."]
    assert not list(tmp_path.rglob("*"))


def test_an_attempted_index_that_failed_keeps_its_pointer(tmp_path, capsys):
    code, sent, _ = _alerted(tmp_path, at(15, 0, 30), capsys, provider=IndexProvider(refuse={"FINNIFTY"}))
    assert code == 1 and sent[0].endswith(SIDECAR_POINTER.format(names="FINNIFTY") + ".")
    assert list(tmp_path.rglob("finnifty_*.meta.json"))


def test_the_pointer_names_only_the_attempted_indices_beside_ones_never_asked(tmp_path, capsys):
    """Boundary: from 15:12:40 BANKNIFTY gets one attempt; FINNIFTY and MIDCPNIFTY are never asked, have no sidecar,
    and are still closed none."""
    _, sent, _ = _alerted(tmp_path, at(15, 12, 40), capsys)
    assert sent[0].endswith(f"; {POINTER} for BANKNIFTY.")
    assert (
        "FINNIFTY (window closed, canonical none)" in sent[0]
        and "MIDCPNIFTY (window closed, canonical none)" in sent[0]
    )
    assert {p.name.split("_")[0] for p in tmp_path.rglob("*.meta.json")} == {"banknifty"}


def test_a_run_after_the_window_closes_every_index_none_with_no_pointer(tmp_path, capsys):
    _, sent, _ = _alerted(tmp_path, at(15, 13), capsys)
    assert POINTER not in sent[0] and sent[0].count("(window closed, canonical none)") == 3


CASES = {
    AT_1438: (at(14, 38), {}),
    "refused": (at(15, 0, 30), {"provider": IndexProvider(refuse={"FINNIFTY"})}),
    "not listed": (at(15, 0, 30), {"listing": Listing(listed={"BANKNIFTY", "FINNIFTY"})}),
    "no NSE file": (at(15, 0, 30), {"listing": NoNseFile()}),
    "turn after the window": (at(15, 12, 40), {}),
    "after the window": (at(15, 13), {}),
}


@pytest.mark.parametrize("case", CASES)
def test_each_index_line_and_the_alert_print_the_same_outcome(tmp_path, capsys, case):
    """Minor 1: one text for both; every index not recorded is in the alert with exactly its line's outcome."""
    start, kwargs = CASES[case]
    _, sent, lines = _alerted(tmp_path, start, capsys, **kwargs)
    index_lines = {line.split(" ", 1)[0]: line for line in lines if line.startswith(tuple(SPOTS))}
    failed = {name: line.split(") - ", 1)[1] for name, line in index_lines.items() if "complete=False" in line}
    names = "; ".join(f"{name} ({text})" for name, text in failed.items())
    assert failed and len(sent) == 1
    assert sent[0].startswith(f"3 pm index recorder: not recorded today: {names}. Data only; NIFTY is separate")


def test_a_closed_none_line_says_canonical_none_and_a_too_early_line_never(tmp_path, capsys):
    _, _, lines = _alerted(tmp_path, at(15, 0, 30), capsys, provider=IndexProvider(refuse={"FINNIFTY"}))
    (finnifty,) = [line for line in lines if line.startswith("FINNIFTY")]
    assert finnifty.endswith("(0 contracts, complete=False) - incomplete, canonical none")
    _, _, early = _alerted(tmp_path / "early", at(14, 38), capsys)
    assert all(line.endswith(f") - {TOO_EARLY}") for line in early if line.startswith(tuple(SPOTS)))


def test_a_complete_day_has_no_outcome_on_any_line_and_no_alert(tmp_path, capsys):
    """Empty case: nothing to say, so no " - " tail and no alert."""
    code, sent, lines = _alerted(tmp_path, at(15, 0, 30), capsys)
    index_lines = [line for line in lines if line.startswith(tuple(SPOTS))]
    assert code == 0 and sent == [] and len(index_lines) == 3
    assert all(line.endswith("(12 contracts, complete=True)") for line in index_lines)
