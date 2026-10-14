"""Judge 84 (stories D1 and E5): a version may hold `paper` only if code can enforce every exit it states. Today that
is the time exit; a text exit other than "none" (a stop at 2x credit, say) refuses the version, so no trade is ever
opened under a stop nobody applies. The loader and the status change run the same checks (wiring)."""

from fno.playbook.exit_terms import unenforceable_exits
from fno.playbook.schema import parse_strategy

from .builders import document, loader
from .test_loader import approved_repository, refused

STOP = {"time": "21 days to expiry", "profit": "none", "loss": "stop at 2x credit", "event": "none"}


def test_a_paper_version_with_an_exit_code_cannot_enforce_is_refused(tmp_path):
    approved_repository(tmp_path, exits=STOP)
    refusal = refused(tmp_path)
    assert refusal.field == "sc-test-v1.yaml: exits" and "loss: stop at 2x credit" in str(refusal)


def test_a_paper_version_whose_other_exits_say_none_loads(tmp_path):
    approved_repository(tmp_path)
    assert [s.name for s in loader(tmp_path).load().approved()] == ["sc-test"]


def test_only_the_text_exits_that_say_none_are_enforceable():
    assert unenforceable_exits(parse_strategy(document())) == []
    texts = {**STOP, "profit": "take 50%", "event": "exit before the RBI policy"}
    assert unenforceable_exits(parse_strategy(document(exits=texts))) == [
        "profit: take 50%", "loss: stop at 2x credit", "event: exit before the RBI policy"]  # fmt: skip
