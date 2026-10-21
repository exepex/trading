# Response 295: FL1-1, judge 422 answered (story/fl1-forecast-lab)

Builder: session_01FWkBH4zNAEFSEpjUzVEgnd. Judge 422 judged ad13de4e. My later heads 7e04ed77 and 2392def1 already
matched the previous session (the owner's decision: "15:45, match lags 1 day"), but they fixed only part of
should-fix 1. I checked every finding against the code and with my own probes and mutations.

**Verdict on the review:** all 4 should-fix findings and minors 1, 3 and 4 accepted; minor 2 partly. The reasons
follow.

## Should-fix 1: accepted, and the fix goes past my previous-session change

The judge is right on both counts, and 7e04ed77 left two holes:
- The seal check still ran only inside the match, behind the close.
- A day was matched only by the very next report. A missed report day, or a close archived after the next report's
  15:45, was skipped silently.

The fix is a change of design:
- **The seal check runs separately** (`MatchSection.seal_lines`). It runs on the target's own day, whatever the
  close's state: every seal deadline for that target has passed by 15:45.
- **Each written report records what it covered** (`WrittenReport.checked` and `.matched`, per underlying and target
  day, kept in its Drive record).
- **Each report takes up every target day of the last 5 regular sessions** (`LOOKBACK_SESSIONS`) that no earlier
  report has checked or matched yet:
  - a day missed by the routine is checked and matched by the next report;
  - a close archived late is matched by a later report;
  - nothing is alerted twice;
  - a day older than the window is left to the scoreboard;
  - days before the lab's first live day (`daily.live_from.lab_close`) are never taken up, so go-live raises no false
    "missing" alerts.
- **The match header states the lag**, per the owner.

Tests (`tests/forecast_lab/test_report.py`):
- `test_a_late_seal_is_alerted_on_its_day_before_the_close_exists_and_matched_once_in_the_next_report`: the judge's
  two-day probe, plus a third day that must not match the same day again;
- `test_a_missed_report_day_is_checked_and_matched_by_the_next_report`;
- `test_a_close_archived_late_is_matched_by_a_later_report`.

Evidence: strong (tests and mutations, below).

**A second bug, found while fixing this one: FL1 stepped over every session, G13b over regular sessions only.** Both
the issue-day lookup and the report day used `previous_session`, which counts special and muhurat sessions. G13b
counts horizons with `nth_regular_session` and issues on regular sessions only. NSE's calendar has a muhurat session
on Sunday 8 Nov 2026. So the 9 Nov report would have looked for forecasts targeting 8 Nov, and an N1 issued on 6 Nov
would never have been found. `fno/forecast_lab/sessions.py` (`RegularSessions`) now steps over regular sessions only,
and `lab close` runs only on a regular session. Test: `test_fl1_steps_over_regular_sessions_only_as_g13b_does`, on
the real calendar. Evidence: strong.

**The daily score step:** the orchestrator approved G13b's `pricerange score` step (DESK_DECISIONS, 21 Oct). The owner
is the G13b builder (session_01UkTaDe), and the step goes right after `price_ranges`, before `lab_close`. Until it is
live, a matched day shows "no scored row yet", truthfully.

## Should-fix 2: accepted

- **Alerts are sent once.** The alerts have their own write-once marker (`.alerted.json`, with the outcomes).
  - A rerun after a refused post retries only the post.
  - A rerun after a crash between the post and the alerts sends only the alerts.
  - The marker is written after the sends: a crash in between sends them again rather than losing them. I chose a
    possible duplicate over a possible loss, and I say so.
- **Every outcome is printed:**
  - `lab close <day>: <n> of <m> alert(s) sent to #fno-desk`, counting only alerts actually sent;
  - then one line per unsent alert, `alert NOT sent: <reason>: <the alert's text>`, so the routine's step 3 posts it
    by hand.

Tests: `test_an_alert_not_sent_is_printed_with_its_text_and_counted_as_not_sent` (with `NoAlertSender`),
`test_a_refused_post_fails_the_step_without_its_own_alert_and_the_rerun_retries_only_the_post`,
`test_a_rerun_after_a_crash_between_the_post_and_the_alerts_sends_only_the_alerts`. Evidence: strong.

## Should-fix 3: accepted, built

`python -m fno lab channels` (`fno/forecast_lab/membership.py`) checks both channels:
- it calls Slack's `conversations.info` once per channel (a GET; the test's fake session fails on any post) and reads
  `channel.is_member`;
- it exits 1 unless the bot is a member of both; an unknown answer never passes;
- without a token it checks nothing and exits 1;
- the token is never in a line.

It is a named go-live check before `daily.live_from.lab_close` is set (story criterion 7). I did not add it to
`tools/routine_setup.sh`: that is O7's file, and a daily Slack call is not needed once membership is proved. The
orchestrator can decide otherwise. Evidence that `is_member` comes back for a bot token with `channels:read`: some
evidence (Slack's documented response); the first real run will confirm it.

## Should-fix 4: accepted, both parts

- **FL1's own rule is now the story's rule, the same as G13b's deadline:** a forecast counts only if it was sealed
  before 09:15 of the next regular session after its issue day.
  - `test_the_seal_deadline_is_the_next_regular_session_s_open_after_the_issue_day_not_the_target_s`: an N3 issued
    19 Oct and pushed 21 Oct 09:16 is late, though before its target's open. A push on the 20 Oct holiday is in time.
- **G13b's own verdict through the adapter:** `test_g13b_s_own_late_verdict_reaches_fl1_through_the_adapter` uses
  G13b's real `SealCheck` and `Seals` on a record pushed 19 Oct 09:16. It asserts `late is True` from the adapter
  (this kills M16) and the alert.

## Minors

1. **M3, M5, M13 and M17, accepted.** Each now has an assertion:
   - `test_today_s_issue_is_shown_only_once_pushed_by_the_report_s_time`;
   - `test_the_trust_line_counts_a_day_scored_for_either_underlying` (BANKNIFTY only);
   - `test_only_an_ok_row_of_the_same_issue_day_is_matched` (two cases).
2. **Wording, partly done.**
   - The report line now reads `report to #fno-forecast: posted`, not T1's "alert sent".
   - A "may have posted" failure now ends "check #fno-forecast before any repost".
   - T1's own `UNKNOWN` text still says "(check #fno-desk)". That is T1's constant in `fno/cards/posting.py`, so under
     the one-builder rule I have not changed it; I raised it with the orchestrator. The proposal is to pass the
     channel name in, or say "check the channel".
3. **Accepted.** The story now says the channel constants are in `fno/constants_channels.py`.
4. **Accepted.** Criterion 8 now says the replay needs G13b's issue plus `lab close` before `live_from` is set. The
   orchestrator has asked for it as its own change after the PASS. The strict xfail stays until then.

## My own mutation run (15 planted, each restored; `tests/forecast_lab`)

All 15 are caught: M3, M5, M13, M16, M17, and ten new ones:
- the deadline at the target's open;
- the seal check behind the close;
- earlier reports' `checked` ignored;
- earlier reports' `matched` ignored (it survived my first run; the two-day test now has a third day);
- only the previous session matched;
- alerts resent on a rerun;
- an unsent alert counted as sent;
- every session kind counted as regular;
- an unknown membership passing (it survived first; now asserted);
- the first live day ignored.

## Gates

On the head sent to the judge: listed in the message with its SHA.
