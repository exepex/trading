"""Story D4 criteria 2, 4, 5 and 9: C4's Book 2 mode on the app's checker, independent of any decider. The fixture is
C4's correct SF trade (width 200, one lot) on a version that allows up to 2 lots, made a Book 2 trade with a rule
default; the D6 registry is a temporary file."""

from dataclasses import replace
from datetime import date

from fno.books.registered_components import RegisteredComponents
from fno.books.version_registry import VersionRegistry, VersionRow
from fno.checks.validity_envelope import EnvelopeMode
from fno.checks.wiring import validity_modes, validity_shapes
from fno.constants import BOOK2_HYBRID
from fno.playbook.envelope import BookTerms
from fno.playbook.envelope_files import component_key
from tests.checks.validity_builders import DAY, check, committed_store, failed, proposal
from tests.envelope.builders import FORBIDDEN, SHADOW, envelope, version

VERSION = version("c4-sf", lots=2, widths=(300, 200, 100), code="SF")
KEY = VERSION.key
RULE_DEFAULT = BookTerms(KEY, 200.0, 2)  # the version's own width at the rule's width, its 2 lots


def book2(width=200.0, lots=1, rule_default=RULE_DEFAULT, approved=frozenset({KEY})):
    base = proposal("SF")
    return replace(base, book=BOOK2_HYBRID, strategy=VERSION, rule_sha256=VERSION.parameters_sha256, width=width,
                   lots=lots, rule_default=rule_default, approved=approved)  # fmt: skip


def report(tmp_path, the_proposal, statuses=None, registered_sha=None):
    the_envelope = envelope(KEY, **(statuses or {}))
    registry = VersionRegistry(tmp_path / "versions.csv")
    sha = the_envelope.sha256 if registered_sha is None else registered_sha
    registry.append(VersionRow(BOOK2_HYBRID, "b2-v1", date(2026, 10, 1), "c" * 40, {component_key(KEY): sha}, "test"))
    mode = EnvelopeMode(validity_shapes(), lambda: {KEY: the_envelope}, RegisteredComponents(registry))
    modes = {**validity_modes(tmp_path), BOOK2_HYBRID: mode}
    return check(the_proposal, store=committed_store(), modes=modes)


def test_a_reduced_lot_on_the_rule_s_own_width_passes(tmp_path):
    result = report(tmp_path, book2())
    assert result.ok and result.mode == "envelope"


def test_a_forbidden_width_choice_is_blocked_by_c4_without_any_decider(tmp_path):
    """Criterion 5: C4 alone blocks it; nothing upstream checked the envelope."""
    result = report(tmp_path, book2(rule_default=BookTerms(KEY, 300.0, 2)), {"choose_width": FORBIDDEN})
    assert failed(result) == {"envelope"} and "choose_width forbidden" in result.failures[0].reason


def test_a_lot_increase_another_structure_and_a_changed_threshold_are_refused(tmp_path):
    """Criterion 2, at C4: more lots than the version's; another structure; a rule fingerprint that is not the
    version's (a changed threshold is a different rule); a width outside the set."""
    assert {"lots", "envelope"} <= failed(report(tmp_path / "a", book2(lots=3)))
    assert "structure" in failed(report(tmp_path / "b", replace(book2(), structure="SC")))
    assert "version" in failed(report(tmp_path / "c", replace(book2(), rule_sha256="another-rule")))
    assert {"width", "envelope"} <= failed(report(tmp_path / "d", book2(width=250.0)))


def test_an_envelope_edited_after_registration_is_refused(tmp_path):
    """Criterion 4: the file's hash differs from the registered D6 component, so C4 fails closed."""
    assert "envelope_registered" in failed(report(tmp_path, book2(), registered_sha="the-old-hash"))


def test_a_shadow_only_action_is_never_the_account_s_trade(tmp_path):
    result = report(tmp_path, book2(rule_default=BookTerms(KEY, 300.0, 2)), {"choose_width": SHADOW})
    assert failed(result) == {"envelope"} and "shadow-only" in result.failures[0].reason


def test_an_ineligible_version_is_refused_even_with_its_envelope_allowing_it(tmp_path):
    """Criterion 9: not in the day's approved set."""
    assert {"permitted", "envelope"} <= failed(report(tmp_path, book2(approved=frozenset())))


def test_no_rule_default_means_no_trade_to_take(tmp_path):
    assert "envelope" in failed(report(tmp_path, book2(rule_default=None)))


def test_book_1_still_needs_exactly_the_version_s_lots():
    assert "lots" in failed(check(proposal("SF", lots=2)))
    assert DAY  # the C4 fixture's day, shared by both books
