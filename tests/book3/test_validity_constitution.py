"""Story D5 criteria 1-4 and 7 at C4, on the app's checker and composition root over a temporary repository: the
constitution file, its D6 component, a strategy registered on 13 Oct 2026 and committed. C4's fixture trade is an SF
of width 200, one lot, on 14 Oct 2026 with the 27 Oct expiry, so a spec exiting 3 days before expiry is held 10 days."""

from dataclasses import replace
from datetime import date

import pytest

from fno.book3.constitution import COMPONENT
from fno.books.version_registry import VersionRegistry, VersionRow
from fno.books.versions import VERSIONS_FILE
from fno.checks.wiring import validity_modes
from fno.constants import BOOK3_AI
from fno.playbook.documents import strategy_from_text
from tests.book3.builders import PROVENANCE, commit, constitution, constitution_bytes, init_repo, registry, spec_text
from tests.checks.validity_builders import check, committed_store, failed, proposal

SPEC = spec_text(name="b3-sf", code="SF", min_days=10, max_days=24, exit_days=3)


def repo_with(tmp_path, holding=21, registered_sha=None, on=date(2026, 10, 13), spec=SPEC):
    tmp_path.mkdir(parents=True, exist_ok=True)
    init_repo(tmp_path)
    raw = constitution_bytes(max_holding_days=holding)
    (tmp_path / "book3").mkdir()
    (tmp_path / "book3" / "constitution-v1.yaml").write_bytes(raw)
    sha = registered_sha or constitution(max_holding_days=holding).sha256
    VersionRegistry(tmp_path / VERSIONS_FILE).append(
        VersionRow(BOOK3_AI, "b3-v1", date(2026, 10, 1), "c" * 40, {COMPONENT: sha}, "test"))  # fmt: skip
    registry(tmp_path, today=on).register(spec, PROVENANCE, constitution(max_holding_days=holding))
    commit(tmp_path, "constitution and strategy")
    return tmp_path


def book3(**changes):
    spec = strategy_from_text(SPEC, "spec")
    trade = replace(proposal("SF"), book=BOOK3_AI, strategy=None, approved=frozenset(), strategy_id="b3-sf-v1",
                    rule_sha256=spec.parameters_sha256)  # fmt: skip
    return replace(trade, **changes)


def run(root, the_proposal):
    return check(the_proposal, store=committed_store(), modes=validity_modes(root))


def test_a_registered_strategy_within_the_constitution_passes(tmp_path):
    report = run(repo_with(tmp_path), book3())
    assert report.ok and report.mode == "constitution"


def test_an_unregistered_or_same_day_strategy_is_refused(tmp_path):
    """Criterion 1."""
    assert "not registered" in run(repo_with(tmp_path / "a"), book3(strategy_id="b3-other-v1")).failures[0].reason
    same_day = repo_with(tmp_path / "b", on=date(2026, 10, 14))
    assert "not before" in run(same_day, book3()).failures[0].reason


def test_a_constitution_not_matching_its_d6_component_is_refused(tmp_path):
    """Criterion 4: an edited constitution no longer matches the registered hash."""
    report = run(repo_with(tmp_path, registered_sha="the-old-constitution"), book3())
    assert failed(report) == {"constitution"} and "no constitution file" in report.failures[0].reason


def test_a_trade_held_past_the_constitution_s_limit_is_refused(tmp_path):
    """Criterion 3 at C4: held 10 days against a constitution of 9 (registration checks the spec's own window)."""
    with pytest.raises(Exception, match="over the constitution"):
        repo_with(tmp_path / "a", holding=9)
    root = repo_with(tmp_path / "b", holding=21)
    (root / "book3" / "constitution-v1.yaml").write_bytes(constitution_bytes(max_holding_days=9))
    edited = run(root, book3())
    assert "constitution" in failed(edited)  # the edited file no longer matches D6: refused before anything else


def test_the_trade_must_be_the_registered_spec_s_own_terms(tmp_path):
    """The playbook mode's checks against the spec: another width or more lots is refused."""
    root = repo_with(tmp_path)
    assert "lots" in failed(run(root, book3(lots=2)))
    assert "version" in failed(run(root, book3(rule_sha256="another-rule")))


def test_objections_are_no_input_so_they_can_never_block_criterion_7(tmp_path):
    """C4's Book 3 check takes the proposal and the evidence only: a red-team or judge objection has no way in."""
    import inspect

    mode = validity_modes(tmp_path)[BOOK3_AI]
    assert list(inspect.signature(mode.checks).parameters) == ["proposal", "evidence"]


def test_c4_measures_the_trade_s_own_holding_not_only_the_spec_s_window(tmp_path):
    """The spec plans at most 12 - 3 = 9 days, within a 9-day constitution; this trade's expiry is 13 days away, so its
    exit falls 10 days after entry. Registration passes and C4 refuses the trade itself."""
    short = spec_text(name="b3-sf", code="SF", min_days=5, max_days=12, exit_days=3)
    root = repo_with(tmp_path, holding=9, spec=short)
    rule = strategy_from_text(short, "spec").parameters_sha256
    report = run(root, book3(rule_sha256=rule))
    assert "planned exit 2026-10-24 is 10 days after entry" in report.failures[0].reason


def test_a_damaged_constitution_file_fails_the_named_constitution_check(tmp_path):
    root = repo_with(tmp_path)
    (root / "book3" / "constitution-v1.yaml").write_bytes(constitution_bytes(underlying="BANKNIFTY"))
    report = run(root, book3())
    assert failed(report) == {"constitution"} and "damaged constitution file" in report.failures[0].reason
