"""Story D4 criteria 2, 4, 5 and 9: C4's Book 2 mode on the app's checker, independent of any decider. The fixture is
C4's correct SF trade (width 200, one lot) on a version that allows up to 2 lots, made a Book 2 trade with a rule
default on a version D2 found eligible; the D6 registry is a temporary file."""

from dataclasses import replace
from datetime import date

from fno.books.registered_components import RegisteredComponents
from fno.books.version_registry import VersionRegistry, VersionRow
from fno.checks.validity_envelope import EnvelopeMode
from fno.checks.wiring import validity_modes, validity_shapes
from fno.constants import BOOK2_HYBRID
from fno.playbook.envelope import BookTerms
from fno.playbook.envelope_files import EnvelopeError, component_key
from tests.checks.validity_builders import DAY, check, committed_store, failed, proposal
from tests.envelope.builders import FORBIDDEN, SHADOW, envelope, version

VERSION = version("c4-sf", lots=2, widths=(300, 200, 100), code="SF")
KEY = VERSION.key
RULE_DEFAULT = BookTerms(KEY, 200.0, 2)  # the version's own width at the rule's width, its 2 lots


def book2(width=200.0, lots=1, rule_default=RULE_DEFAULT, approved=frozenset({KEY}), eligible=frozenset({KEY}),
          the_version=VERSION):  # fmt: skip
    base = proposal("SF")
    return replace(base, book=BOOK2_HYBRID, strategy=the_version, rule_sha256=the_version.parameters_sha256,
                   width=width, lots=lots, rule_default=rule_default, approved=approved, eligible=eligible)  # fmt: skip


def mode_with(tmp_path, envelopes, registered_sha=None):
    registry = VersionRegistry(tmp_path / "versions.csv")
    shas = {component_key(k): e.sha256 if registered_sha is None else registered_sha for k, e in envelopes.items()}
    registry.append(VersionRow(BOOK2_HYBRID, "b2-v1", date(2026, 10, 1), "c" * 40, shas, "test"))
    return EnvelopeMode(validity_shapes(), lambda: envelopes, RegisteredComponents(registry))


def report(tmp_path, the_proposal, statuses=None, registered_sha=None, mode=None):
    mode = mode or mode_with(tmp_path, {KEY: envelope(KEY, **(statuses or {}))}, registered_sha)
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
    """Criterion 9: not in the day's approved set, so D2 never evaluated it and it is not eligible either."""
    unapproved = book2(approved=frozenset(), eligible=frozenset())
    assert {"permitted", "envelope"} <= failed(report(tmp_path, unapproved))


def test_an_approved_version_whose_rule_did_not_fire_is_refused_judge_260(tmp_path):
    """Criterion 9 (judge 260): A and B are both approved and B's envelope allows choose_strategy, but only A fired
    with a valid candidate; choosing B at a B width would trade B against its own unmet thresholds."""
    other = version("c4-sf-b", lots=2, widths=(300, 200, 100), code="SF")
    mode = mode_with(tmp_path, {KEY: envelope(KEY), other.key: envelope(other.key)})
    approved = frozenset({KEY, other.key})
    choose_b = book2(approved=approved, eligible=frozenset({KEY}), the_version=other)
    result = report(tmp_path, choose_b, mode=mode)
    assert failed(result) == {"envelope"} and "not eligible" in result.failures[0].reason
    assert report(tmp_path, replace(choose_b, eligible=approved), mode=mode).ok  # had B fired, the same choice passes
    assert "envelope" in failed(report(tmp_path, replace(choose_b, eligible=frozenset()), mode=mode))  # C4's default


def test_a_damaged_envelope_file_fails_the_named_envelope_check(tmp_path):
    def damaged():
        raise EnvelopeError("playbook/envelopes/c4-sf-v1.yaml: needs exactly playbook, version and actions")

    mode = EnvelopeMode(validity_shapes(), damaged, lambda book, day: {})
    result = report(tmp_path, book2(), mode=mode)
    assert failed(result) == {"envelope"} and "damaged trade envelope" in result.failures[0].reason


def test_no_rule_default_means_no_trade_to_take(tmp_path):
    assert "envelope" in failed(report(tmp_path, book2(rule_default=None)))


def test_book_1_still_needs_exactly_the_version_s_lots():
    assert "lots" in failed(check(proposal("SF", lots=2)))
    assert DAY  # the C4 fixture's day, shared by both books
