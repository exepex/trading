"""Story T1e: any failed or refused desk step turns the card's headline into a warning (criteria 1-9, 11): placement
(a), the headline before T1's first line and the step list on line 2; `step_problems` below T2's two codes; a bare
"no breach" qualified; nothing on a clean day; the delivery metadata keeps the code and no warning text."""

import json

from fno.cards import ruled_status, status
from fno.cards.card import CardBuilder
from fno.cards.daily import DailyCard
from fno.cards.deliveries import RepoDeliveryFiles
from fno.cards.forecasts import LiveCaptureForecasts
from fno.cards.issue import CardIssuer
from fno.cards.posting import SlackCardPoster
from fno.cards.problem_steps import DETAIL, FAILED_HEADLINE, GLYPH, UNREADABLE, ProblemSteps
from fno.cards.record_store import DriveCardRecords
from fno.cards.render import SlackTextRenderer, opening
from fno.cards.rule_checks import DecisionOutcome, ExecutionOutcome, RunLogReader, failures_path, run_log_path
from fno.cards.ruled_status import NO_BREACH, NO_BREACH_WARNED, NOT_COMPLETE, REFUSED, RuleChecks, RuledStatus
from fno.cards.sections import CardWarning, StatusSource
from fno.cards.session import SessionCheck
from fno.cards.status import RegistryStatus
from fno.constants import (
    CARD_DATA_CHECK_FAILED,
    CARD_HARD_RULE_BREACH,
    CARD_NO_APPROVED_STRATEGY,
    CARD_STEP_PROBLEMS,
    FNO_DESK_CHANNEL_ID,
    STEP_FAILED,
    STEP_NOT_LIVE,
    STEP_OK,
)
from fno.desk import run_log

from .fakes import NO_CLOCKS, TOKEN, FakeDrive, FakeRecords, FakeSlack, Ticking, planted, slack_ok, weather_of
from .test_problem_steps import C4_TODAY, FAILED_SNAPSHOT, REFUSED_FILLS, _written_by_run_log
from .test_rule_checks import BEFORE, DAY, ON_TIME, TODAY_TIMES, Base, _log

FIRST = "PAPER ONLY. Omenix F&O daily card, Thu 15 Oct 2026 (NSE regular session). Information, no action."
EXITS_FAILED = {"status": STEP_FAILED, "reason": "raised:KeyError"}
VALID = {"valid": True}
CLEAN = {"weather": {"status": STEP_OK}, "forecasts_v4": {"status": STEP_NOT_LIVE}, "decisions": ON_TIME,
         "snapshot": VALID, "fills": {}}  # fmt: skip


def daily(records: FakeRecords, root) -> DailyCard:
    runs = RunLogReader(records)
    rules = (DecisionOutcome(records, runs, TODAY_TIMES, ("book1_rules", "book2_hybrid")),
             ExecutionOutcome(runs, TODAY_TIMES, lambda d: BEFORE))  # fmt: skip
    problems = ProblemSteps(runs)
    status = RuledStatus(RegistryStatus(records, records), RuleChecks(rules), problems)
    builder = CardBuilder(status, weather_of(records), LiveCaptureForecasts(records), problems)
    return DailyCard(SessionCheck(records), builder, SlackTextRenderer(), RepoDeliveryFiles(root, records))


def card_of(tmp_path, log: bytes | None, extra: dict | None = None):
    files = planted() | ({run_log_path(DAY): log} if log is not None else {}) | (extra or {})
    card, text = daily(FakeRecords(files), tmp_path).prepare(DAY)
    return card, text.splitlines()


def steps_warning(steps: str) -> list[str]:
    return [f"{FAILED_HEADLINE} {FIRST}", DETAIL.format(steps=steps)]


def _fresh(tmp_path, name):
    folder = tmp_path / name
    folder.mkdir()
    return folder


def test_only_exits_failed_gives_the_warning_headline_step_problems_and_a_qualified_no_breach(tmp_path):
    card, lines = card_of(tmp_path, _log(**CLEAN, exits=EXITS_FAILED))
    assert lines[:2] == steps_warning("exits (failed)")
    assert lines[0] == "⚠️ WARNING: part of today's desk run did not work. " + FIRST  # the exact wording
    assert lines[1] == "Steps with problems today: exits (failed). Their alerts in #fno-desk give the reasons."
    assert lines[2] == f"Status: NO TRADE ({CARD_STEP_PROBLEMS})" and card.reason_code == CARD_STEP_PROBLEMS
    assert NO_BREACH_WARNED in lines and NO_BREACH not in lines


def test_a_failed_snapshot_and_refused_fills_keep_data_check_failed_with_both_named_in_run_order(tmp_path):
    card, lines = card_of(tmp_path, _log(decisions=ON_TIME, snapshot=FAILED_SNAPSHOT, fills=REFUSED_FILLS))
    assert lines[:2] == steps_warning("snapshot (failed), fills (refused)")
    assert card.reason_code == CARD_DATA_CHECK_FAILED and REFUSED in lines


def test_a_failed_decisions_step_warns_and_stays_data_check_failed(tmp_path):
    card, lines = card_of(tmp_path, _log(decisions=FAILED_SNAPSHOT, snapshot=VALID))
    assert lines[:2] == steps_warning("decisions (failed)") and card.reason_code == CARD_DATA_CHECK_FAILED


def test_a_c4_refusal_today_beats_step_problems_and_the_warning_still_shows(tmp_path):
    extra = {failures_path("book1_rules"): C4_TODAY.encode()}
    card, lines = card_of(tmp_path, _log(**CLEAN, exits=EXITS_FAILED), extra)
    assert lines[:2] == steps_warning("exits (failed)") and card.reason_code == CARD_HARD_RULE_BREACH


def test_boundaries_one_step_a_retry_pending_a_retried_step_and_an_unfinished_day(tmp_path):
    waiting = {"status": STEP_FAILED, "reason": "OSError: disk", run_log.RETRY: True}
    pending = _written_by_run_log(
        _fresh(tmp_path, "pending"), ("decisions", ON_TIME), ("snapshot", VALID), ("fills", waiting)
    )
    card, lines = card_of(tmp_path, pending)
    assert lines[:2] == steps_warning("fills (failed)") and card.reason_code == CARD_STEP_PROBLEMS
    retried = _written_by_run_log(_fresh(tmp_path, "retried"), ("decisions", ON_TIME), ("snapshot", VALID),
                                  ("fills", waiting), ("fills", {}))  # fmt: skip
    card, lines = card_of(tmp_path, retried)
    assert lines[0] == FIRST and card.reason_code == CARD_NO_APPROVED_STRATEGY
    card, lines = card_of(tmp_path, _log(pack={"status": STEP_FAILED, "reason": "raised:OSError"}))
    assert lines[:2] == steps_warning("pack (failed)") and NOT_COMPLETE in lines
    assert card.reason_code == CARD_STEP_PROBLEMS


def test_an_unreadable_run_log_puts_the_doubt_in_the_headline(tmp_path):
    malformed = json.dumps({"day": DAY.isoformat(), "kind": "daily_run", "steps": []}).encode()
    for log in (b"{not json", malformed):
        card, lines = card_of(tmp_path, log)
        assert lines[:2] == [f"{UNREADABLE.headline} {FIRST}", UNREADABLE.detail]
        assert lines[0] == "⚠️ WARNING: today's run log could not be read. " + FIRST
        assert lines[1] == "This card cannot say which desk steps worked. See #fno-desk."
        assert card.reason_code == CARD_DATA_CHECK_FAILED and REFUSED in lines


def test_a_clean_an_empty_or_a_missing_run_log_gives_no_warning_and_t2_s_card(tmp_path):
    for log, summary in ((_log(**CLEAN, exits={}), NO_BREACH), (_log(), NOT_COMPLETE), (None, NOT_COMPLETE)):
        card, lines = card_of(tmp_path, log)
        assert lines[0] == FIRST and lines[1] == f"Status: NO TRADE ({CARD_NO_APPROVED_STRATEGY})", log
        assert summary in lines and card.reason_code == CARD_NO_APPROVED_STRATEGY and card.warning is None
        assert GLYPH not in "\n".join(lines) and not any("Steps with problems" in line for line in lines)


def test_the_warning_has_glyph_and_word_on_line_one_shows_the_list_once_and_never_a_reason_code(tmp_path):
    _, lines = card_of(tmp_path, _log(decisions=ON_TIME, snapshot=FAILED_SNAPSHOT, fills=REFUSED_FILLS))
    assert lines[0].startswith("⚠️ WARNING:") and "PAPER ONLY." in lines[0]
    assert sum("Steps with problems today:" in line for line in lines) == 1
    codes = ("raised:", "needs snapshot", "caps", *ruled_status.SEVERITY, *status.REASONS)
    assert not any(code in line for line in lines[:2] for code in codes)


def test_placement_is_one_function_a_puts_the_headline_before_t1_s_first_line():
    """Criterion 11: the owner's choice of (a) or (b) changes `opening` only; today it is (a)."""
    warning = CardWarning("H.", "D.")
    assert opening("FIRST", None) == ["FIRST"] and opening("FIRST", warning) == ["H. FIRST", "D."]


def issued(tmp_path, log: bytes, test=False):
    records = FakeRecords(planted() | {run_log_path(DAY): log})
    card, text = daily(records, tmp_path).prepare(DAY)
    slack = FakeSlack(slack_ok())
    issuer = CardIssuer(SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, slack), DriveCardRecords(FakeDrive()),
                        RepoDeliveryFiles(tmp_path, records), NO_CLOCKS, Ticking(), "c" * 40)  # fmt: skip
    issuer.issue(card, text, test=test)
    return text, slack.calls[0]["json"]["text"]


def test_the_delivery_metadata_keeps_step_problems_and_no_warning_text(tmp_path):
    text, _ = issued(tmp_path, _log(**CLEAN, exits=EXITS_FAILED))
    path = tmp_path / "research" / "cards" / "deliveries" / "2026" / "2026-10-15-a1.json"
    stored = path.read_text()
    assert json.loads(stored)["reason_code"] == CARD_STEP_PROBLEMS
    assert "⚠" not in stored and "WARNING" not in stored and "Steps with problems" not in stored
    assert not [line for line in text.splitlines()[:2] if line in stored]


def test_a_test_post_keeps_its_banner_first_and_the_warning_follows(tmp_path):
    text, posted = issued(tmp_path, _log(**CLEAN, exits=EXITS_FAILED), test=True)
    banner, card_first, *_ = posted.splitlines()
    assert banner.startswith("TEST — PAPER ONLY:") and card_first == text.splitlines()[0]
    assert card_first.startswith("⚠️ WARNING:")


class Raising(StatusSource):
    def status(self, day):
        raise TypeError("a book entry that is not a mapping")


def test_a_failing_status_source_never_hides_the_warning(tmp_path):
    """Self-review (silent failures): the warning is asked on its own, so T1's STATUS_FAILED keeps it."""
    records = FakeRecords(planted() | {run_log_path(DAY): _log(**CLEAN, exits=EXITS_FAILED)})
    builder = CardBuilder(Raising(), weather_of(records), LiveCaptureForecasts(records),
                          ProblemSteps(RunLogReader(records)))  # fmt: skip
    card, text = DailyCard(SessionCheck(records), builder, SlackTextRenderer(), RepoDeliveryFiles(tmp_path, records)
                           ).prepare(DAY)  # fmt: skip
    lines = text.splitlines()
    assert lines[:3] == [*steps_warning("exits (failed)"), f"Status: NO TRADE ({CARD_DATA_CHECK_FAILED})"]
    assert "status source failed (TypeError)" in card.missing


def test_a_failing_warning_source_is_named_missing_never_a_lost_card(tmp_path):
    class Broken(ProblemSteps):
        def warning(self, day):
            raise OSError("git")

    records = FakeRecords(planted())
    builder = CardBuilder(RegistryStatus(records, records), weather_of(records), LiveCaptureForecasts(records),
                          Broken(RunLogReader(records)))  # fmt: skip
    card, text = DailyCard(SessionCheck(records), builder, SlackTextRenderer(), RepoDeliveryFiles(tmp_path, records)
                           ).prepare(DAY)  # fmt: skip
    assert text.splitlines()[0] == FIRST and "warning source failed (OSError)" in card.missing


def test_an_unreadable_log_is_data_check_failed_even_without_a_rule_reading_it():
    """Self-review (correctness): the unreadable warning adds `data_check_failed`, never `step_problems`."""
    records = FakeRecords({run_log_path(DAY): b"{bad"})
    reading = RuledStatus(Base(), RuleChecks(()), ProblemSteps(RunLogReader(records))).status(DAY)
    assert reading.reason_code == CARD_DATA_CHECK_FAILED


def test_the_drive_record_keeps_the_warning_as_data(tmp_path):
    """Self-review (silent failures): T1d's list was in the record's sections; T1e keeps it as the `warning` field."""
    records = FakeRecords(planted() | {run_log_path(DAY): _log(**CLEAN, exits=EXITS_FAILED)})
    card, text = daily(records, tmp_path).prepare(DAY)
    drive = FakeDrive()
    CardIssuer(SlackCardPoster(TOKEN, FNO_DESK_CHANNEL_ID, FakeSlack(slack_ok())), DriveCardRecords(drive),
               RepoDeliveryFiles(tmp_path, records), NO_CLOCKS, Ticking(), "c" * 40).issue(card, text)  # fmt: skip
    ((_, data),) = drive.files.items()
    assert json.loads(data)["warning"] == {"headline": FAILED_HEADLINE, "detail": DETAIL.format(steps="exits (failed)")}
    clean = daily(FakeRecords(planted() | {run_log_path(DAY): _log(**CLEAN, exits={})}), tmp_path).prepare(DAY)[0]
    assert clean.warning is None
