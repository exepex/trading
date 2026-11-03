"""Story F7 criteria 1, 2, 4 and 5: one shadow entry per common opportunity (the answer's, or `no_decision` with its
reason); the reader counts only a file committed before the execution snapshot, as written, for the day's own common
pack, and reads takes as D4's `BookTerms` at one lot."""

import os
import subprocess
from datetime import datetime, time

import pytest

from fno.book3.shadow_file import MISSING, UNKNOWN, shadow_body, shadow_path, write_shadow
from fno.book3.shadow_reader import EDITED, NO_FILE, OTHER_PACK, Book3ShadowReader
from fno.models import IST
from fno.playbook.envelope import BookTerms
from fno.playbook.history import PlaybookGit
from fno.scoreboard.matched_actions import NOT_OBSERVED, SKIP, TAKE
from tests.book3.builders import init_repo
from tests.book3.engine_builders import DAY, Pack

A, B = "sc-a-v1:2026-11-27", "sc-b-v1:2026-11-27"
COMMON = [{"opportunity_id": A, "strategy": "sc-a", "version": 1}, {"opportunity_id": B, "strategy": "sc-b",
          "version": 1}, {"opportunity_id": "no_trade"}]  # fmt: skip
PACK = Pack("a" * 64, {"opportunities": COMMON})
SNAPSHOT = datetime.combine(DAY, time(15, 15), IST)


def widths(name, version):
    return {"sc-a": (300.0, 200.0, 100.0), "sc-b": (200.0,)}.get(name)


def take(opportunity, width, reason="cheap"):
    return {"opportunity_id": opportunity, "action": "take", "width": width, "reason": reason}


def skip(opportunity):
    return {"opportunity_id": opportunity, "action": "no_trade", "width": None, "reason": "event week"}


def entries(answered, common=COMMON):
    return {e["opportunity_id"]: e for e in shadow_body(DAY, PACK.sha256, common, answered, widths)["entries"]}


def test_every_common_opportunity_gets_exactly_one_entry_and_no_trade_none():
    found = entries([take(A, 200), skip(B)])
    assert set(found) == {A, B}
    assert (found[A]["action"], found[A]["width"], found[B]["action"]) == ("take", 200.0, "no_trade")


def test_a_missing_entry_or_a_width_outside_the_set_is_no_decision_with_its_reason():
    found = entries([take(A, 250)])
    assert found[A]["action"] == "no_decision" and "not in sc-a-v1's set" in found[A]["reason"]
    assert (found[B]["action"], found[B]["reason"]) == ("no_decision", MISSING)


@pytest.mark.parametrize("width, kept", [(100, True), (300, True), (99.9, False), (300.1, False)])
def test_widths_at_and_just_beyond_the_set(width, kept):
    assert (entries([take(A, width)])[A]["action"] == "take") is kept


def test_an_unknown_id_is_dropped_and_listed_as_refused():
    body = shadow_body(DAY, PACK.sha256, COMMON, [take("sc-z-v1:2026-11-27", 200)], widths)
    assert body["refused"] == [{"opportunity_id": "sc-z-v1:2026-11-27", "why": UNKNOWN}]
    assert "sc-z-v1:2026-11-27" not in {e["opportunity_id"] for e in body["entries"]}


def test_a_day_with_only_no_trade_gives_a_file_without_entries_and_it_is_written_once(tmp_path):
    body = shadow_body(DAY, PACK.sha256, [{"opportunity_id": "no_trade"}], [], widths)
    assert body["entries"] == []
    write_shadow(tmp_path, body)
    with pytest.raises(FileExistsError):
        write_shadow(tmp_path, body)


def committed(root, body, at: datetime):
    root.mkdir(parents=True, exist_ok=True)
    init_repo(root)
    write_shadow(root, body)
    env = {**os.environ, "GIT_COMMITTER_DATE": at.isoformat(), "GIT_AUTHOR_DATE": at.isoformat()}
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "shadow"], cwd=root, check=True, env=env)
    return root


def reader(root, pack=PACK):
    return Book3ShadowReader(root, PlaybookGit(root), lambda day: pack, lambda day: SNAPSHOT)


def test_a_file_committed_before_the_snapshot_reads_as_written(tmp_path):
    body = shadow_body(DAY, PACK.sha256, COMMON, [take(A, 200), skip(B)], widths)
    actions = reader(committed(tmp_path, body, SNAPSHOT.replace(minute=11))).actions(DAY)
    assert (actions[A].kind, actions[A].terms) == (TAKE, BookTerms(("sc-a", 1), 200.0, 1))
    assert actions[B].kind == SKIP and actions[B].terms is None


@pytest.mark.parametrize("second", [0, 1])
def test_a_file_committed_at_or_after_the_snapshot_reads_as_not_observed(tmp_path, second):
    body = shadow_body(DAY, PACK.sha256, COMMON, [take(A, 200)], widths)
    at = SNAPSHOT.replace(second=second)
    actions = reader(committed(tmp_path, body, at)).actions(DAY)
    assert {a.kind for a in actions.values()} == {NOT_OBSERVED} and actions[A].reason.startswith("late")


def test_just_before_the_snapshot_counts(tmp_path):
    body = shadow_body(DAY, PACK.sha256, COMMON, [take(A, 200)], widths)
    actions = reader(committed(tmp_path, body, SNAPSHOT.replace(hour=15, minute=14, second=59))).actions(DAY)
    assert actions[A].kind == TAKE


def test_a_missing_edited_or_other_pack_file_is_not_observed_for_every_opportunity(tmp_path):
    (tmp_path / "none").mkdir()
    init_repo(tmp_path / "none")
    assert {a.reason for a in reader(tmp_path / "none").actions(DAY).values()} == {NO_FILE}
    body = shadow_body(DAY, PACK.sha256, COMMON, [take(A, 200)], widths)
    root = committed(tmp_path / "edited", body, SNAPSHOT.replace(minute=10))
    path = root / shadow_path(DAY)
    path.write_text(path.read_text().replace('"take"', '"no_trade"'))
    assert {a.reason for a in reader(root).actions(DAY).values()} == {EDITED}
    other = committed(tmp_path / "other", body, SNAPSHOT.replace(minute=10))
    assert {a.reason for a in reader(other, Pack("e" * 64, PACK.body)).actions(DAY).values()} == {OTHER_PACK}


def test_no_common_pack_means_no_opportunities_to_read(tmp_path):
    init_repo(tmp_path)
    assert Book3ShadowReader(tmp_path, PlaybookGit(tmp_path), lambda day: None, lambda day: SNAPSHOT).actions(DAY) == {}


def test_an_opportunity_answered_twice_is_no_decision():
    found = entries([take(A, 200), skip(A), skip(B)])
    assert found[A]["action"] == "no_decision" and "twice" in found[A]["reason"] and found[B]["action"] == "no_trade"


def test_the_no_trade_opportunity_is_never_in_the_reader_s_result(tmp_path):
    body = shadow_body(DAY, PACK.sha256, COMMON, [take(A, 200), skip(B)], widths)
    actions = reader(committed(tmp_path, body, SNAPSHOT.replace(minute=11))).actions(DAY)
    assert set(actions) == {A, B} and "no_trade" not in actions
