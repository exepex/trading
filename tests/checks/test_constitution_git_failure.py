"""C4's Book 3 mode fails closed by name when git fails (the D4/D5 builder's request, 22 Oct 2026; judges 260/263): a
failed git read inside the registry check gives a failed "constitution" check, never an exception out of C4."""

from datetime import date
from types import SimpleNamespace

from fno.book3.constitution import COMPONENT
from fno.checks.validity_constitution import ConstitutionMode
from fno.research_engine.ledger import GitFailed

SHA = "c" * 64


class FailingRegistry:
    def require_registered(self, strategy_id, day, head):
        raise GitFailed("git log failed (exit 128): fatal: unable to read tree (simulated)")


def test_a_git_failure_in_the_registry_check_is_a_named_failed_check():
    mode = ConstitutionMode({}, lambda: {SHA: object()}, lambda book, day: {COMPONENT: SHA}, FailingRegistry(),
                            lambda: "a" * 40)  # fmt: skip
    proposal = SimpleNamespace(book="book3_ai", day=date(2026, 10, 26), strategy_id="s1")
    [result] = mode.checks(proposal, None)
    assert (result.name, result.ok) == ("constitution", False)
    assert result.reason.startswith("git failed: git log failed (exit 128)")
