"""Story D4: the trade envelope files, their hash and the `served` entries; and how a verdict resolves (criterion 3)."""

import hashlib

import pytest

from fno.playbook.envelope import ActionStatus, BookTerms, EnvelopeAction, Verdict, resolve
from fno.playbook.envelope_files import EnvelopeError, EnvelopeFiles, component_key, served_envelopes

TEXT = (
    "playbook: sc-a\nversion: 1\nactions:\n  follow_rule: allowed\n  no_trade: allowed\n  choose_width: shadow-only\n"
)


def write(root, name="sc-a-v1.yaml", text=TEXT):
    folder = root / "playbook" / "envelopes"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(text)
    return folder / name


def test_a_file_is_read_with_its_statuses_and_the_hash_of_its_bytes(tmp_path):
    path = write(tmp_path)
    envelope = EnvelopeFiles(tmp_path).all()[("sc-a", 1)]
    assert envelope.status(EnvelopeAction.CHOOSE_WIDTH) == ActionStatus.SHADOW_ONLY
    assert envelope.status(EnvelopeAction.REDUCE_LOTS) == ActionStatus.FORBIDDEN  # not listed
    assert envelope.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert served_envelopes({("sc-a", 1): envelope}, [("sc-a", 1)]) == {"trade_envelope:sc-a-v1": envelope.sha256}
    assert component_key(("sc-a", 1)) == "trade_envelope:sc-a-v1"


@pytest.mark.parametrize("text", [
    TEXT.replace("choose_width", "change_threshold"),  # not an action of the closed list
    TEXT.replace("shadow-only", "maybe"),  # not a status
    "playbook: sc-a\nversion: 1\n",  # no actions
])  # fmt: skip
def test_an_unknown_action_or_status_or_a_missing_section_is_refused(tmp_path, text):
    write(tmp_path, text=text)
    with pytest.raises(EnvelopeError):
        EnvelopeFiles(tmp_path).all()


def test_a_file_whose_name_and_version_disagree_is_refused(tmp_path):
    write(tmp_path, name="sc-a-v2.yaml")
    with pytest.raises(EnvelopeError, match="file name must match"):
        EnvelopeFiles(tmp_path).all()


def test_the_playbook_loader_never_reads_the_envelope_folder(tmp_path):
    """D1's loader parses every *.yaml directly in playbook/ as a strategy; an envelope there would be refused. The
    loader's own pattern on the real folder layout finds no envelope."""
    from fno.playbook.loader import FILE_PATTERN

    write(tmp_path)
    assert list((tmp_path / "playbook").glob(FILE_PATTERN)) == []
    assert len(list((tmp_path / "playbook").rglob(FILE_PATTERN))) == 1  # the envelope exists, one level down


CHOICE, DEFAULT = BookTerms(("sc-a", 1), 200, 1), BookTerms(("sc-a", 1), 300, 1)


@pytest.mark.parametrize(("status", "account", "shadow", "attempted"), [
    (ActionStatus.ALLOWED, CHOICE, None, None),
    (ActionStatus.SHADOW_ONLY, DEFAULT, CHOICE, None),  # the account keeps the rule default; the AI's action is shadow
    (ActionStatus.FORBIDDEN, None, None, CHOICE),  # no trade; the attempt is recorded
])  # fmt: skip
def test_a_verdict_resolves_to_the_account_s_trade_and_what_is_only_recorded(status, account, shadow, attempted):
    resolution = resolve(CHOICE, DEFAULT, Verdict(status, (EnvelopeAction.CHOOSE_WIDTH,), ""))
    assert (resolution.account, resolution.shadow, resolution.attempted) == (account, shadow, attempted)
