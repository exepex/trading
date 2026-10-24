"""Story G11 criterion C12 (round 2c): the stop rule, the transcript-audit draw and the scoring gate read v4's own runs
(`V4_TERMS`: its fire logs, its transcript audits, its draws), with v2's behaviour unchanged as the default. Good: a
clean audited v4 day scores (`test_v4_collect.py`). Bad: two v4 breaches in 20 v4 sessions stop the book. Boundary:
a breach 21 sessions back no longer counts. Empty: no fired v4 session draws nothing."""

import json
from datetime import date, timedelta

from fno.ai.audit_plan import audits_due, fired_sessions, record_draws
from fno.ai.run_terms import V2_TERMS, V4_TERMS
from fno.ai.stop_rule import stop_reason
from fno.ai.transcript_audit import TranscriptAudits, new_audit
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from tests.ai.test_v4_fire import DAY, at

VERSION = "book3_ai/v2/sha256:" + "0" * 64 + "/isolation:sealed_same_day"
SESSIONS = [DAY - timedelta(days=n) for n in range(1, 31)]  # 30 plain session days before DAY (calendar not needed)


def fire_log(root, day, terms=V4_TERMS, books=(BOOK3_AI,)):
    entries = {b: {"fired": True, "version": VERSION, "session": f"https://example.invalid/{b}"} for b in books}
    log = {"released": True, "books": entries} if terms is V4_TERMS else entries
    path = root / terms.fired_path(day)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log))
    return entries


def breach(root, day, terms=V4_TERMS):
    fired = fire_log(root, day, terms)[BOOK3_AI]
    audit = new_audit(day, BOOK3_AI, fired, ["read_other_records"], "opened research/forecasts/", "judge", at(16, 0))
    TranscriptAudits(root, terms).record(day, audit)


def test_two_v4_breaches_in_twenty_v4_sessions_stop_the_book(tmp_path):
    breach(tmp_path, SESSIONS[0])
    breach(tmp_path, SESSIONS[19])
    assert stop_reason(tmp_path, BOOK3_AI, VERSION, DAY, V4_TERMS, SESSIONS).startswith("stopped: 2 transcript")


def test_a_breach_twenty_one_v4_sessions_back_no_longer_counts(tmp_path):
    breach(tmp_path, SESSIONS[0])
    breach(tmp_path, SESSIONS[20])
    assert stop_reason(tmp_path, BOOK3_AI, VERSION, DAY, V4_TERMS, SESSIONS) == ""


def test_v2_breaches_never_stop_a_v4_book_and_v2_keeps_its_own_count(tmp_path):
    breach(tmp_path, SESSIONS[0], V2_TERMS)
    breach(tmp_path, SESSIONS[1], V2_TERMS)
    assert stop_reason(tmp_path, BOOK3_AI, VERSION, DAY, V4_TERMS, SESSIONS) == ""
    assert stop_reason(tmp_path, BOOK3_AI, VERSION, DAY, V2_TERMS, SESSIONS).startswith("stopped: 2 transcript")


def test_the_v4_draw_reads_only_v4_fire_logs_and_its_first_days_are_all_due(tmp_path):
    fire_log(tmp_path, SESSIONS[0], V2_TERMS, (BOOK2_HYBRID, BOOK3_AI))
    fire_log(tmp_path, SESSIONS[1], V4_TERMS, (BOOK2_HYBRID, BOOK3_AI))
    v4 = [(s.day, s.book) for s in fired_sessions(tmp_path, V4_TERMS)]
    assert v4 == [(SESSIONS[1], BOOK2_HYBRID), (SESSIONS[1], BOOK3_AI)]
    assert [(s.day, s.book) for s in audits_due(tmp_path, {}, V4_TERMS)] == v4


def test_a_v4_log_without_a_released_pack_has_no_fired_session(tmp_path):
    path = tmp_path / V4_TERMS.fired_path(DAY)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"released": False, "reason": "system_late"}))
    assert fired_sessions(tmp_path, V4_TERMS) == []


def test_no_fired_v4_session_draws_nothing(tmp_path):
    assert fired_sessions(tmp_path, V4_TERMS) == [] and audits_due(tmp_path, {}, V4_TERMS) == []
    assert record_draws(tmp_path, {}, V4_TERMS) == [] and not (tmp_path / V4_TERMS.draws_folder).exists()


def test_v4_paths_are_its_own_folder():
    assert V4_TERMS.transcript_audit_path(date(2026, 10, 26), BOOK3_AI).startswith("research/forecasts/ai_v4/2026/")
    assert V4_TERMS.draws_folder == "research/forecasts/ai_v4/draws" and V2_TERMS.draws_folder.endswith("ai_v1/draws")


def test_audit_record_for_a_v4_run_lands_in_the_v4_folder(tmp_path, monkeypatch, capsys):
    from fno import cli
    from fno.models import IST

    monkeypatch.setattr("fno.config.ROOT", tmp_path)
    monkeypatch.setattr("fno.models.now_ist", lambda: at(16, 0).astimezone(IST))
    fire_log(tmp_path, DAY)
    argv = ["ai", "audit-record", "--protocol", "v4", "--day", DAY.isoformat(), "--book", BOOK3_AI,
            "--evidence", "tool calls read", "--auditor", "judge"]  # fmt: skip
    assert cli.main(argv) == 0
    assert TranscriptAudits(tmp_path, V4_TERMS).get(DAY, BOOK3_AI).result == "clean"
    assert TranscriptAudits(tmp_path, V2_TERMS).get(DAY, BOOK3_AI) is None


def test_reveals_ready_for_v4_waits_for_every_fired_books_reveal(tmp_path, monkeypatch):
    from fno import cli

    monkeypatch.setattr("fno.config.ROOT", tmp_path)
    argv = ["ai", "reveals-ready", "--protocol", "v4", "--day", DAY.isoformat()]
    assert cli.main(argv) == 0  # nothing fired: nothing to wait for
    fire_log(tmp_path, DAY)
    assert cli.main(argv) == 1  # Book 3 fired, its reveal not in yet
    reveal = tmp_path / V4_TERMS.reveal_path(DAY, BOOK3_AI)
    reveal.parent.mkdir(parents=True, exist_ok=True)
    reveal.write_text("{}")
    assert cli.main(argv) == 0 and cli.main(["ai", "reveals-ready", "--day", DAY.isoformat()]) == 0
