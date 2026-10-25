"""F1 protocol sections 8 and 9: the clustered mean and p, Holm, the random-gate control, the nomination rules and
the held-out seal."""

import subprocess

import pytest
from f1study import seal, stats, summary

from .f1_fakes import EXPIRY


def row(net, expiry="2024-03-07", index="NIFTY", ratio=1.3, status="taken"):
    return {"net": net, "gross": net, "charges": 0.0, "expiry": expiry, "index": index, "ratio": ratio,
            "status": status}  # fmt: skip


def test_trades_of_one_week_are_one_cluster():
    rows = [row(1.0), row(3.0, index="BANKNIFTY"), row(-2.0, expiry="2024-03-14"), row(6.0, expiry="2024-03-14")]
    mean, se, clusters = stats.clustered(rows)
    assert (mean, clusters) == (2.0, 2)
    assert se == pytest.approx(0.0)  # each week's deviations sum to zero


def test_the_clustered_error_by_hand():
    rows = [row(1.0), row(5.0, expiry="2024-03-14"), row(0.0, expiry="2024-03-21")]
    mean, se, g = stats.clustered(rows)
    assert se == pytest.approx(((1 - 2) ** 2 + (5 - 2) ** 2 + (0 - 2) ** 2) ** 0.5 * (3 / 2) ** 0.5 / 3)


def test_p_needs_thirty_clusters_and_is_a_half_at_zero():
    assert stats.one_sided_p(1.0, 1.0, 29) == 1.0
    assert stats.one_sided_p(0.0, 1.0, 30) == pytest.approx(0.5)
    assert stats.one_sided_p(1.645, 1.0, 30) == pytest.approx(0.05, abs=1e-3)
    assert stats.one_sided_p(None, None, 0) == 1.0


def test_holm_steps_down():
    assert stats.holm_family({"a": 0.001, "b": 0.03, "c": 0.04}) == {"a": True, "b": False, "c": False}


def test_the_random_gate_is_seeded_and_bounded():
    rows = [row(float(i), expiry=f"2024-{1 + i // 28:02d}-{1 + i % 28:02d}") for i in range(40)]
    p = stats.random_gate_p(rows, 10, 35.0)
    assert p == stats.random_gate_p(rows, 10, 35.0) and 0.0 <= p < 0.01
    assert stats.random_gate_p(rows, 0, 1.0) is None and stats.random_gate_p(rows, 40, 1.0) is None


def test_the_gate_keeps_its_boundary_and_drops_missing_ratios():
    rows = [row(1.0, ratio=1.2), row(1.0, ratio=1.19), row(1.0, ratio=None)]
    assert len(summary.gated(rows, "G12")) == 1 and len(summary.gated(rows, "G0")) == 3


LOSING_BANKNIFTY = {"NIFTY": {"mean_net": 5.0}, "BANKNIFTY": {"mean_net": -1.0}}


def base(**changes):
    r = {"holm": True, "mean_net_pad2": 10.0, "by_index": {"NIFTY": {"mean_net": 5.0}, "BANKNIFTY": {"mean_net": 1.0}},
         "p_gate": 0.05, "p": 0.001}  # fmt: skip
    return {**r, **changes}


@pytest.mark.parametrize(("name", "changes", "expected"),
                         [("EDGE2-F1-WF-G12", {}, True), ("EDGE2-F1-WF-G12", {"holm": False}, False),
                          ("EDGE2-F1-WF-G12", {"mean_net_pad2": 0.0}, False),
                          ("EDGE2-F1-WF-G12", {"by_index": LOSING_BANKNIFTY}, False),
                          ("EDGE2-F1-WF-G12", {"p_gate": 0.11}, False), ("EDGE2-F1-WF-G0", {"p_gate": None}, True),
                          ("EDGE2-F1-WF-G12", {"by_index": {}}, False)])  # fmt: skip
def test_nomination_needs_all_four_conditions(name, changes, expected):
    assert summary.eligible(name, base(**changes)) is expected


def test_at_most_two_nominees_lowest_p_first():
    rows = {f"EDGE2-F1-WF-G{k}": base(p=p) for k, p in (("0", 0.003), ("12", 0.001), ("15", 0.002))}
    assert summary.nominated(rows) == ["EDGE2-F1-WF-G12", "EDGE2-F1-WF-G15"]


def test_held_out_symbols_are_refused_before_the_seal_opens():
    with pytest.raises(seal.SealBroken):
        seal.allowed(("NIFTY", "FINNIFTY"), held_out_open=False)
    seal.allowed(("NIFTY", "BANKNIFTY"), held_out_open=False)
    seal.allowed(("FINNIFTY", "MIDCPNIFTY"), held_out_open=True)


def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for key, value in (("user.email", "t@example.invalid"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
        subprocess.run(["git", "-C", str(tmp_path), "config", key, value], check=True)
    return tmp_path


def commit(root, path, text):
    path.write_text(text)
    subprocess.run(["git", "-C", str(root), "add", str(path)], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "x"], check=True)


def test_the_seal_needs_a_committed_unchanged_file_with_a_nominee(tmp_path):
    root = repo(tmp_path)
    found = root / "discovery.json"
    with pytest.raises(seal.SealBroken):
        seal.nominated_for_held_out(root, found)
    found.write_text('{"nominated": ["A"]}')
    with pytest.raises(seal.SealBroken):
        seal.nominated_for_held_out(root, found)
    commit(root, found, '{"nominated": ["A"]}')
    assert seal.nominated_for_held_out(root, found) == ["A"]
    found.write_text('{"nominated": ["B"]}')
    with pytest.raises(seal.SealBroken):
        seal.nominated_for_held_out(root, found)
    commit(root, found, '{"nominated": []}')
    with pytest.raises(seal.SealBroken):
        seal.nominated_for_held_out(root, found)


def test_the_fakes_expiry_is_a_weekday():
    assert EXPIRY.weekday() < 5


def test_the_family_has_six_variants_with_holm_and_a_report_line():
    from f1study import report

    weeks = [f"2024-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(60)]
    rows = [row(100.0 + (i % 5), expiry=w, index="NIFTY" if i % 2 else "BANKNIFTY", ratio=1.0 + i / 60)
            for i, w in enumerate(weeks)]  # fmt: skip
    runs = {code: {"pad1": rows, "pad2": rows, "hist": rows} for code in ("WF", "WC")}
    found = summary.family(runs)
    assert len(found) == 6 and all("holm" in r for r in found.values())
    assert found["EDGE2-F1-WF-G0"]["taken"] == 60 and found["EDGE2-F1-WF-G15"]["gated"] == 30
    text = report.tables({"variants": found, "trials": dict.fromkeys(found, 101)})
    assert text.count("\n| EDGE2-F1-") == 6
