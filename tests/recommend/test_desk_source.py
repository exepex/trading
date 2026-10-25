"""REC1b section 5 for `desk:book1`: complete only with the day's decision run named in the run log and every file
matching records.sha256 (judge 641 SF1); anything else unavailable with its status, a changed file an input failure."""

import hashlib
import json
from datetime import datetime

import pytest

from fno.desk.run_log import RunLog
from fno.recommend.constants import SourceState
from fno.recommend.desk_source import DeskSource
from fno.recommend.ports import InputFailed
from tests.recommend.builders import DAY

RUN = f"{DAY}-r1"


def write_run(root, decisions: dict[str, dict], tamper: str = "", unlisted: str = ""):
    folder = root / "journal" / "book1_rules" / "decisions" / DAY.isoformat() / RUN
    folder.mkdir(parents=True)
    lines = []
    for name, record in {"inputs.json": {}, **decisions}.items():
        data = json.dumps(record).encode()
        (folder / name).write_bytes(data)
        if name != unlisted:
            lines.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
    (folder / "records.sha256").write_text("\n".join(lines) + "\n")
    if tamper:
        (folder / tamper).write_bytes(b'{"tampered": true}')
    return folder


def log_step(root, result: dict | None):
    log = RunLog.open(root, DAY)
    if result is not None:
        now = datetime.now().astimezone()
        log.record("decisions", now, now, {}, result)


def record(action: str, version=None, mode: str = "book") -> dict:
    outcome = "chosen" if action == "trade" else "no trade"  # D2's Decision values
    return {"book": "book1_rules", "version_id": version, "mode": mode,
            "decision": {"action": action, "outcome": outcome}}  # fmt: skip


def source(root) -> DeskSource:
    return DeskSource(root, root / "journal")


def test_a_named_run_whose_files_match_is_complete(tmp_path):
    write_run(tmp_path, {"no_trade.json": record("no trade"), "opp1.json": record("trade", "b0-monthly-sc@1")})
    log_step(tmp_path, {"book1_rules": {"run_id": RUN, "commit": "a" * 40}})
    reading = source(tmp_path).read(DAY)
    assert reading.source.state is SourceState.COMPLETE
    assert [(d.version, d.traded) for d in reading.decisions] == [("book1_rules", False), ("b0-monthly-sc@1", True)]
    assert reading.used[0].path.endswith("records.sha256")


@pytest.mark.parametrize(("result", "status"), [
    (None, "missing, the decisions step is not in the run log"),
    ({"status": "failed", "reason": "command:exit_1"}, "failed, command:exit_1"),
    ({"status": "refused", "reason": "desk:TOO_LATE"}, "refused, desk:TOO_LATE"),
    ({"status": "not_live", "reason": "o1:NOT_LIVE"}, "not_live, o1:NOT_LIVE"),
    ({"book2_hybrid": {"run_id": "x"}}, "ok, no Book 1 decision run"),
])  # fmt: skip
def test_no_decision_run_is_unavailable_with_its_status(tmp_path, result, status):
    write_run(tmp_path, {"no_trade.json": record("no trade")})
    log_step(tmp_path, result)
    reading = source(tmp_path).read(DAY)
    assert (reading.source.state, reading.source.step_status, reading.decisions) == (
        SourceState.UNAVAILABLE,
        status,
        (),
    )


def test_a_changed_file_is_an_input_failure(tmp_path):
    write_run(tmp_path, {"no_trade.json": record("no trade")}, tamper="no_trade.json")
    log_step(tmp_path, {"book1_rules": {"run_id": RUN}})
    with pytest.raises(InputFailed, match="not the one in records.sha256"):
        source(tmp_path).read(DAY)


def test_a_file_missing_from_the_manifest_is_an_input_failure(tmp_path):
    write_run(tmp_path, {"no_trade.json": record("no trade"), "late.json": record("trade")}, unlisted="late.json")
    log_step(tmp_path, {"book1_rules": {"run_id": RUN}})
    with pytest.raises(InputFailed, match="not in records.sha256"):
        source(tmp_path).read(DAY)


def test_a_named_run_without_its_folder_is_an_input_failure(tmp_path):
    log_step(tmp_path, {"book1_rules": {"run_id": RUN}})
    with pytest.raises(InputFailed, match="records.sha256"):
        source(tmp_path).read(DAY)


def test_a_file_listed_but_missing_is_an_input_failure(tmp_path):
    """The review's case: a listed decision file gone must never leave a complete source with fewer decisions."""
    folder = write_run(tmp_path, {"no_trade.json": record("no trade"), "opp1.json": record("trade", "b0@1")})
    (folder / "opp1.json").unlink()
    log_step(tmp_path, {"book1_rules": {"run_id": RUN}})
    with pytest.raises(InputFailed, match="listed in records.sha256 but missing"):
        source(tmp_path).read(DAY)


def test_a_shadow_s_trade_is_never_a_traded_candidate(tmp_path):
    shadow = {
        **record("trade", "b0@1", mode="shadow"),
        "decision": {"action": "trade", "outcome": "shadow: would trade"},
    }
    write_run(tmp_path, {"opp1.json": shadow})
    log_step(tmp_path, {"book1_rules": {"run_id": RUN}})
    assert [d.traded for d in source(tmp_path).read(DAY).decisions] == [False]


def test_a_decision_file_that_does_not_read_is_an_input_failure(tmp_path):
    write_run(tmp_path, {"opp1.json": {"book": "book1_rules"}})
    log_step(tmp_path, {"book1_rules": {"run_id": RUN}})
    with pytest.raises(InputFailed, match="not a readable decision record"):
        source(tmp_path).read(DAY)


def test_a_run_log_that_does_not_read_is_an_input_failure(tmp_path):
    log = tmp_path / "journal" / "runs" / f"{DAY}.json"
    log.parent.mkdir(parents=True)
    log.write_text("{not json")
    with pytest.raises(InputFailed, match="does not read"):
        source(tmp_path).read(DAY)


def test_a_book_entry_without_a_run_is_unavailable(tmp_path):
    """Judge 653 m2: a failed book's entry names no run; it is never complete and never a crash."""
    write_run(tmp_path, {"no_trade.json": record("no trade")})
    log_step(tmp_path, {"book1_rules": {"status": "failed", "reason": "book1:STOPPED"}})
    reading = source(tmp_path).read(DAY)
    assert (reading.source.state, reading.decisions) == (SourceState.UNAVAILABLE, ())
