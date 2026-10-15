# Response 101: story T1, the daily trade card v1 (builder's claims for the judge)

Branch `story/t1-daily-card` (from `origin/main` 96ee83f). Story text: `docs/stories/T-cards.md` section T1. Lane 1
(new story; touches Slack, Drive and an outside clock).

**Verdict in one line:** the card is built, self-reviewed by two independent agents (their 20 findings checked: 18
fixed, 2 kept with reasons), 58 of 58 planted breaks are caught (judge 101's included), and it prints correctly from the real repository.
One live TEST post went to #fno-desk (made by the orchestrator after the owner's yes; this session's permission system
blocked my own attempt) and was read back from the channel, and three
inputs are honest placeholders (weather, house-forecast rule, owner availability), each named on the card.

## Judge 101 (FAIL on 3e705bf): answer item by item

All eight are accepted; each was checked against the code first. Every fix has a test and a planted break that turns
it red. The judge's own planted breaks are in the table below: T12 (read the index), B1 (limit raised to 9.9 s) and B2
(resolution ignored on the early side).

| Item | Check | Fix | Test (and the break it catches) |
|---|---|---|---|
| SF1: GitHub clock trusts any `Date` | Correct: 9f540e9 still read a 403 carrying a `Date` as GitHub's time | `fno/cards/clock.py`: only a 2xx or 3xx answer's `Date` is GitHub's time. Otherwise: "HTTP 403 from GitHub, a Date header: an error answer's time is not trusted" / "HTTP 400 from GitHub, no Date header ..." / "HTTP 200 from GitHub with no Date header" | `test_an_error_answer_carrying_a_date_is_never_trusted_as_githubs_time` (403, 400, 500 with `Date`; 301 accepted), `test_githubs_date_header_is_read_as_utc_and_a_missing_one_is_unknown` (400 and 200 without `Date`). Break "error answer's Date trusted": caught |
| SF2: 5 s boundary untested | Correct: B1 and B2 survived | none needed in code (the rule was right) | `test_the_five_second_boundary_on_both_sides`: 8 cases, early and late, at 5.0 s (no WARNING) and 5.1 s (WARNING), with resolution 0 and 1 s. B1, B2 and `>` to `>=`: all caught |
| SF3: staged edit not pinned | Correct: T12 survived | none needed in code (`git show HEAD:<path>`) | `test_an_edited_or_untracked_working_tree_file_is_never_read` now stages a new file and a staged edit; both are not read. T12: caught |
| SF4: unchecked GitHub clock silent | Partly done in 9f540e9 | `misses()` names every unchecked server on a sent card; stored `checked: false` with the line | `test_the_next_card_names_an_unchecked_github_clock_even_without_any_warning` (no WARNING anywhere, only "not checked"). Removing that line: caught |
| SF4 known limit | Partly agree. True as judged on 3e705bf: the root path gives 400 with no `Date`. **Pushback with evidence on "never available from this host":** 9f540e9 found a route. From this builder container, a HEAD to `https://api.github.com/repos/exepex/trading` passes the proxy with GitHub's `Date`; live, read-only: "clock: host vs GitHub within 0.0 s". | Written in known limits below: the route works from this container but not yet from a scheduled post; if the routine's network refuses it, every card says "clock NOT CHECKED" and the next card names it | judge to re-run the live read-only check |
| Minor 1: `--post` with another `--on` | Correct | `fno/cards/cli.py`: refused unless today (IST); a dry run of any day stays allowed | `test_post_refuses_any_day_but_today`. Break: caught |
| Minor 2: source message in the public file | Correct | `fno/cards/card.py`: a failed source is named by error type only | `test_a_source_that_raises_never_loses_the_card` asserts no message text. Break: caught |
| Minor 3: ConnectionError double post | Correct: a plain `ConnectionError` includes a connection dropped after sending | No idempotency check: that would need `conversations.history`, a new Slack scope, so it is not cheap. Instead a plain `ConnectionError` is now "may have posted": not retried, with "check #fno-desk". Only `ConnectTimeout` (never connected), `ratelimited` and `service_unavailable` are retried | `test_a_failure_that_may_have_posted_or_is_a_refusal_is_never_retried`, `test_a_connect_timeout_then_success_posts_once_more`. My first break for this was equivalent (not caught, because the may-have-posted check runs first); the replacement break then exposed that the case was missing from the test. Added: caught |
| Minor 4: test post's old clock entries | Agree | left as is (append-only) | none |
| Minor (judge A, after 101): weather must say it blocks new trades (owner "4 A") | Correct | `fno/cards/weather.py`: "No new trades while the weather reading is missing (owner rule)." right under the weather line; criterion 3 updated | `test_missing_weather_says_it_blocks_new_trades_owner_rule`. Removing the line: caught (checked in a throwaway worktree) |
| Judge A addendum minors (after 101) | Correct: the WARNING line in `misses()` and "ConnectionError is never retried" had no test that a mutation could not survive | none needed in code; the muhurat note now says "the one-hour Diwali session" (21 Oct 2025 ran 13:45-14:45), not "evening" | `test_the_next_card_names_a_clock_warning`; `test_a_connection_error_is_never_retried_even_when_a_retry_would_succeed` (a success is queued behind the error, so a retry would post). Both mutations (WARNING line removed; ConnectionError moved to the retried set): caught |
| Design note: muhurat | Agree (owner "3 A") | `docs/stories/T-cards.md`: "a card every session with a 15:00 market" in the description and a design note | `test_a_muhurat_session_gets_no_card_and_is_skipped_as_the_previous_session` |

**`fno/ai/receipts.py` (changed in 9f540e9) is in no frozen list.** It is not in G1 v1-v3 (`research/forecasts/FREEZE*.md`),
not in `fno/freeze_sections.py`, and not in S1's `frozen_files` (`research/evaluation/PROTOCOL.md`, which is not frozen
yet). **The G5 collector's results cannot change** (reasoning plus a test): only how page 2 onward is asked changed,
from GitHub's numeric-ID `next` URL to the same endpoint by owner/name with that link's own cursor. GitHub serves the
same page either way, so the pushes read and the receipt chosen are the same. Where the old path worked (GitHub
Actions, no proxy), nothing differs; where it failed (this proxy), it failed closed, and now it reads. A 401 or 403 is
`ReceiptAccessDenied`, a subclass of `ReceiptUnknown`, so the collector's `except ReceiptUnknown` (fail closed) is
unchanged. `tests/ai` passes.

## What the card says today: the real dry-run text

`env -u FNO_SLACK_BOT_TOKEN python -m fno card daily --on 2026-10-15` on this branch, unedited. Each footer hash was
checked against `git show HEAD:<path> | sha256sum`; for example, `research/forecasts/scores/2026-10-13.json` is
740121ba... in both.

```text
PAPER ONLY. Omenix F&O daily card, Thu 15 Oct 2026 (NSE regular session). Information, no action.
Status: NO TRADE (no_approved_strategy)
Reason: no strategy has passed: no playbook version is approved to paper
Paper trades so far: 0 (book1_rules 0, book2_hybrid 0, book3_ai 0)
If you cannot act by 15:25 IST, the paper record assumes: no action (nothing is opened or closed). Owner availability calendar (E8) not built yet.
Previous card: no card on record for 2026-10-14

Weather: not yet scored (M1 pending)
No new trades while the weather reading is missing (owner rule).
No weather model is built yet; the card shows no colour until M1 scores one.

Forecasts on record: live capture of 2026-10-14 (not today's: the latest committed capture); track records from the score report of 2026-10-13
This capture was generated at 19:27 IST, after its 15:15 deadline: its records are not scored
House forecast (baseline_b_base_rate): no primary named in G1; past average shown (orchestrator's fallback rule).
3 other forecasters recorded; none has passed its test yet. None of this is advice.
q1_nifty_up_20d (NIFTY higher in 20 sessions): past average 0.59 | back-fill, not live: said 0.5-0.6 on 175 days, happened on 57%, mean Brier 0.245 over 669; live: not enough data yet (0 scored)
q2_nifty_move_3pct_20d (NIFTY moves 3% or more in 20 sessions): past average 0.35 | back-fill, not live: said 0.3-0.4 on 258 days, happened on 34%, mean Brier 0.237 over 669; live: not enough data yet (0 scored)
q3_rv20_above_trailing (20-day realised volatility rises above the last 20 days'): past average 0.49 | back-fill, not live: said 0.4-0.5 on 261 days, happened on 56%, mean Brier 0.252 over 669; live: not enough data yet (0 scored)
q4_vix_up_10d (India VIX higher in 10 sessions): past average 0.47 | back-fill, not live: said 0.4-0.5 on 679 days, happened on 45%, mean Brier 0.250 over 679; live: not enough data yet (0 scored)
q5_rv20_below_atm_iv30 (20-day realised volatility below today's 30-day implied volatility): past average 0.69 | back-fill, not live: said 0.6-0.7 on 118 days, happened on 84%, mean Brier 0.217 over 630; live: not enough data yet (0 scored)

Missing: weather model (story M1) not built; scored live forecasts for 2026-10-14 (the capture was late)
Valid until 15:25 IST.
Issuance time: this message's Slack server timestamp; GitHub's push receipt of its delivery record is the second witness. Committer time is never used.
Records used (SHA-256 of the committed bytes):
  research/data/calendar/nse_sessions.csv e34fbad752bb244e6116c1e474902208a72a03f5af6037c6d75bf9baa6756b4d
  playbook/registry.csv ae81127a1c191d7bcef1e48feac46e57c75ec51f66cf2db195da11974534da09
  journal/book1_rules/account/positions.json fbae2864b585ba99675babeac21d007c5aaf1a9397008023e8db6e5b67a2e069
  journal/book2_hybrid/account/positions.json e2a1498bc4f8cfd239b7f0d6452609299837fdbeb008236e89147781f9e64ef2
  journal/book3_ai/account/positions.json 1b52d7c00d1791c46e8bb76ff7cd398a95cce24a317c6a19b9fcf3df6a030f6c
  research/forecasts/live_v2/2026/2026-10-14_forecasts.csv 3f1303e8628a6269e74dfc73533efc481a8fa3aefd51ef3135d331bb9d38a21f
  research/forecasts/scores/2026-10-13.json 740121ba9e9b0e0d23f23a0b3cdf3e0d03e963374fe1e45e8e64c9d63b0a588e
dry run: nothing posted, saved or written (add --post to send it to #fno-desk)
```

Readings:
- **The late capture is a real finding, not a card detail.** The 14 Oct live capture was generated at 19:27 IST, after
  G1's 15:15 lock, so none of its 20 forecasts count (G4's report already shows `late_live_records: 20`). The card
  states it for that day only.
- **Point in time.** The card uses the 13 Oct score report, not the 15 Oct one: a report dated the card's own day can
  hold that day's later data (fixed after the review, below).
- **Statistician (some evidence).** In the full list, now on the dashboard side, Book 1's back-fill was over-confident
  on q3: it said 0.4-0.5 on 159 days and the event happened on 25%. One bin of overlapping 20-day windows, so there are
  far fewer independent outcomes.

## The one live test post (criterion 16)

**Made once, by the orchestrator session, after the owner's yes ("test post yes").** I tried it from this builder session
first, and this session's permission system ("External System Writes") refused the command before it ran. The
orchestrator then ran `python -m fno card daily --post --test` from e5dcf69 and pushed the delivery file in cc44109.

- **Slack:** sent to #fno-desk by the bot. ts `1792025414.919329`, which is 2026-10-15 06:20:14 IST (00:50:14 UTC).
  Permalink: https://exepex.slack.com/archives/C0C89E8QCCD/p1792025414919329
- **Checked independently:** I read the channel (read-only Slack connector). The message's ts equals the stored ts. Its
  first line is "TEST — PAPER ONLY: a one-off check of live delivery, not the day's card.". The body is the e5dcf69
  dry-run card.
- **Drive:** "card record saved to Drive: 2026/10/2026-10-15_1792025414919329_test.json".
- **Clock:** host vs Slack skew 0.006 s (no warning).
- **Witness on the branch:** `python -m fno card witness --on 2026-10-15` printed
  `research/cards/deliveries/2026/2026-10-15-a1.json: Slack 2026-10-15 06:20:14 IST (ts 1792025414.919329); GitHub push
  receipt unknown (HTTP 403 from GitHub's activity log)`. The receipt is read from pushes to `main` only, so it is
  checked after the merge, as criterion 16 says. The 403 is this container's token.

Three things the test post showed, each traced to its root cause and fixed with a test and a planted break:
1. **"clock: host vs GitHub not checked (KeyError)", stored as a bare null.** Root cause, reproduced live (read-only):
   the check sent a HEAD to `https://api.github.com`. This cloud container's GitHub proxy answers that root path
   itself, with HTTP 400 and no headers at all, so there is no `Date` (a GET to `/zen` gives 403 "sessions are bound to
   their configured repositories"). A repository path (`/repos/exepex/trading`) passes through and carries GitHub's
   `Date`. Live after the fix: "clock: host vs GitHub within 0.0 s"; the old URL still gives "clock NOT CHECKED: host
   vs GitHub (no Date header in GitHub's answer (HTTP 400))".
   Fixes:
   - `wiring.py` asks the repository path (from `GITHUB_REPOSITORY`, default `exepex/trading`, so it also works on
     GitHub Actions).
   - `clock.py` names the failure in plain words instead of an exception type.
   - Each stored check carries `checked: false` and its line.
   - The next card names an unchecked clock on a sent card ("the <day> card's clock NOT CHECKED: ...").
2. **`card witness` gave "unknown (HTTP 403 ...)" with this session's token.** Root cause, reproduced live: page 1 of
   the activity log returns 200. GitHub's `next` link for page 2 names the repository by numeric ID
   (`/repositories/1414773933/activity`), which the proxy refuses ("Numeric-ID repository paths ... are not supported
   through this proxy"). Fixes:
   - `fno/ai/receipts.py` asks every page by owner/name with GitHub's cursor. This is story F1's reader, not frozen,
     and the AI books' collector benefits too.
   - A 401 or 403 now raises `ReceiptAccessDenied`, a subclass of `ReceiptUnknown`, so the collector still fails
     closed.
   - The witness prints three distinct states: a time, "none yet (...)", or "NOT READABLE: access refused ... (an
     access problem, not a missing receipt)". Live after the fix: "GitHub push receipt none yet (no push of
     cc441095a4 in GitHub's activity log of main)", which is correct, since that commit is on the story branch, not
     `main`.
   - The existing paging test was changed from a placeholder `next` URL to GitHub's real numeric-ID shape and now
     asserts the cursor is carried. It is stricter, not loosened.
3. **That card used the same-day score report (2026-10-15).** It was built from e5dcf69, before the point-in-time fix.
   Cards from this branch now use the latest report dated before the card's day.

## Gap list: every requirement of design 04 (layer 6, section 4.4), design 6.5 and the T1 paragraph

| Requirement (source) | Where in T1 | Status |
|---|---|---|
| A card exists every trading day (4.1) | criteria 10, 14 | in (scheduling is out, by instruction) |
| Status `TRADE` / `NO TRADE` / `WATCH` (4.1, REPLAN) | criterion 2 | v1: `NO TRADE` only; `TRADE` and `WATCH` are slice B (no strategy has passed) |
| `NO TRADE` reason codes (4.1) | criterion 2 | in: no approved strategy, data check failed. Out with reason: weather RED (M1 not built), risk bucket full (no positions; C5), budget stop (BG1), cost wall (R1), devil's advocate (T2) |
| Label PAPER ONLY (4.1, review 97) | criterion 1 | in |
| What, entry range, size, maximum loss, worst case, exit plan, costs and tax, evidence rung, proves-it-wrong (4.1 table) | none | out: slice B trade fields; no trade exists to show |
| Forecast with its forecaster's record "said a-b on n days, happened on x%" (4.1, 7.4) | criterion 4 | in: past average per question, labelled as the fallback (orchestrator, option 1) |
| Weather (4.1) | criterion 3 | in as "not yet scored (M1 pending)"; never a colour |
| Devil's advocate objections and verdict (4.1) | none | out: T2, T3 |
| The card never computes its own numbers (4.1) | criteria 4, 5 | in: reads G4's figures and G4's bin rule |
| Scoring the card (4.1) | none | out: LR1 and the scoreboards (no TRADE card to score) |
| Delivery to #fno-desk with `FNO_SLACK_BOT_TOKEN` only, plain text (4.1, 6.5) | criteria 11, 13; `wiring.py` | in |
| A failed post is retried and logged "alert NOT sent"; the next card says so (4.1) | criterion 11 | in; a retry happens only when the post surely did not land |
| Timing contract: 15:00 cutoff, 15:06 decision, 15:08 sent (4.1) | none | out: the scheduling and S1 timetable item; the card states valid-until 15:25 |
| Card records in Drive only; repo holds hashes and scores only (4.1, owner 15 Oct) | criterion 9 | in |
| Interfaces `TradeCard`, `CardBuilder`, `CardRenderer`, `AlertSender`, wiring `fno/cards/wiring.py` (4.1) | criterion 15 | in. `CardPoster` is new because `AlertSender.send` returns only a line, not Slack's `ts`; the HTTP post is shared (`slack_post`). `DevilsAdvocate` is out (T3) |
| Evaluation metric: delivery time, calibration, share of `NO TRADE` days (4.1) | none | partly: the delivery metadata stores the host and Slack times; computing the metrics is out (LR1) |
| Failure modes: numbers differ from records; stale card; Slack outage; too many messages (4.1) | criteria 5, 11; valid-until line | in, except the message rate, which is one card a day by the schedule (out) |
| Issuance time independent of git: SHA-256 of every forecast, weather record and objection in the footer; Slack ts plus GitHub push receipt (4.4) | criteria 5, 6, 16 | in; no weather record or objection exists yet to hash |
| A record with neither witness before its deadline is unscored (4.4) | none | out: the scorers' rule (G4, v4) |
| Data rights, retention, security (4.4) | criteria 9, 13 | in for cards; no quotes are stored |
| Clock contract: UTC with offset stored, IST shown, host vs Slack and GitHub, skew > 5 s WARNING, calendar decides sessions (4.4) | criteria 7, 14 | in. A source's own time stays in its own record (the card copies none) |
| Owner unavailable: "if you cannot act by HH:MM, the paper record assumes ..." (4.4) | criterion 8 | in; E8 is not built and the line says so |
| DANGER alerts while the owner is away; summary on return (4.4) | none | out: LM1 |
| Alert class CARD, first line says what to do or "information, no action" (6.5) | criterion 1 | in; "by 15:08" is the scheduling (out) |
| Built only from committed records with hashes in the footer (REPLAN T1) | criterion 5 | in |
| Depends D3, E2, G3, M1 (REPLAN T1) | story "Depends" | D3: no decision records exist yet, so status reads the registry and accounts. A TRADE card will read D3 (slice B). E2: no pack field is shown in v1. G3 and G4: read. M1: pending |

## Independent self-review (two review agents, separate contexts, read-only)

Two agents reviewed `96ee83f..HEAD`: one for correctness, one for silent failures and secrets. I checked every
finding against the code. Each fix below has a test and a planted break (next section).

| # | Finding (reviewer) | My check | Outcome |
|---|---|---|---|
| 1 | A corrupt earlier delivery record (bad JSON, missing key, a list) stops the card (both) | reproduced: `prepare()` raised | fixed: `daily.py` names it as a previous miss; `attempts()` skips an unread file |
| 2 | A failed `DeliveryLog.write` loses the post's lines (silent) | correct | fixed: "delivery metadata NOT written (OSError)", the metadata printed for a hand commit, exit 1 |
| 3 | A non-dict Slack answer raises in `slack_post` (both) | correct; also hit the alert sender | fixed in `sender.py` |
| 4 | Drive "saved" when identical bytes already exist (silent) | pushed back: identical bytes at that path mean the record is in Drive, which is what "saved" claims; names carry the `ts` or microseconds | no change |
| 5 | A failed previous-session lookup is silent (silent) | correct | fixed: the card names it |
| 6 | A missing house-forecast row vanishes; the late capture is not under Missing (both) | correct | fixed: a line per question and a missing item; the late capture is listed |
| 7 | A malformed score report, an empty calibration, or a `None` read wipes the forecast section (silent; correctness 8) | correct | fixed: the report is guarded on its own; G4's `calibration_bin`; no bin means a plain line |
| 8 | A naive `Date` header (`-0000`) raises `TypeError`; a non-numeric `ts` raises (silent) | correct | fixed: `-0000` is read as UTC; a `ts` must parse or the post says "no readable ts" |
| 9 | The retry can post the card twice (both) | correct: `chat.postMessage` is not idempotent | fixed: retry only when it surely did not land (connection error, `ratelimited`, `service_unavailable`). A read timeout or unreadable answer says "Slack may still have posted it", is not retried; an accepted post is never retried |
| 10 | Witness crashes on a record without Slack facts (silent) | correct | fixed |
| 11 | Missing git raises; `code_commit` empty (silent) | correct | fixed: reads as "not committed" (named missing); commit "unknown" |
| 12 | Same-day score report may hold later data (silent) | correct: a point-in-time rule | fixed: the report used is the latest dated before the card's day |
| 13 | A muhurat-only day gets a card and counts as the previous session (correctness) | reproduced for 2026-11-08 | fixed as A4 does (no card; skipped as previous). Owner may decide otherwise |
| 14 | An unreadable account does not give `data_check_failed`, unlike the story scope (correctness) | correct | fixed in code (criterion 2 now says registry or account) |
| 15 | Attempt numbers ignore committed attempts from another checkout (correctness) | correct | fixed: the maximum of committed and working-tree numbers |
| 16 | An empty capture loses its date label (correctness) | correct | fixed: the date comes from the file name |
| 17 | `ls-tree` without `-z` quotes non-ASCII names (correctness) | correct | fixed |
| 18 | Criterion 4 wording "live record" vs the code's "live" (correctness) | correct | story text fixed |
| 19 | Missing items and previous misses are copied into the public metadata; the criterion 9 test compares whole lines (both) | correct, but harmless: these strings come from repository paths and error types, never secrets or strikes | kept; stated here so the judge can weigh it |
| 20 | `TOKEN not in stored` never exercises a leaking path (silent) | partly agree: no code path passes the token to a record | kept; the Drive-error and sign-in tests do exercise text that holds a planted "secret" |

Both reviewers found the secret handling clean.

## Planted breaks: one per criterion, each must turn a test red

Script: each break goes into a throwaway git worktree, `tests/cards` and `tests/ai/test_receipts_and_coverage.py` run,
and the file is restored. The main tree is never touched.
- The first run caught 26 of 27 breaks. It missed "UTC stored", because the tests' host clock was already UTC; a test
  with an IST host clock was added.
- After the review, test-post and judge-101 fixes, breaks were added for each fix, including the judge's T12, B1 and
  B2.
- **Result now: 58 of 58 caught.**

| Criterion | Break planted | Test that failed |
|---|---|---|
| 1 | PAPER ONLY first line | `test_a_full_card_says_paper_only_no_trade_with_its_reason_and_the_owner_line` |
| 2 | v1 forces NO TRADE | `test_a_full_card_says_paper_only_no_trade_with_its_reason_and_the_owner_line` |
| 2 | paper version reason | `test_a_version_at_paper_still_gives_no_trade_and_never_a_trade` |
| 2 | unreadable registry | `test_an_unreadable_registry_or_account_is_a_failed_data_check_named_on_the_card` |
| 2 | unreadable account | `test_an_unreadable_account_is_a_failed_data_check` |
| 3 | no colour | `test_weather_is_never_a_colour_on_a_v1_card` |
| 4 | house forecast only | `test_each_question_shows_only_the_past_average_with_its_records_and_the_others_are_counted` |
| 4 | capture on or before day | `test_a_capture_after_the_day_is_never_used` |
| 4 | report dated before the day | `test_a_same_day_score_report_is_never_used_and_a_bad_report_is_named` |
| 4 | G4's bin rule | `test_each_question_shows_only_the_past_average_with_its_records_and_the_others_are_counted` |
| 4 | missing house row named | `test_a_late_capture_and_a_missing_past_average_row_are_named_missing` |
| 4 | late capture named missing | `test_a_late_capture_and_a_missing_past_average_row_are_named_missing` |
| 4 | capture date from its file | `test_an_empty_capture_keeps_its_own_date` |
| 4 | back-fill vs live kept apart | `test_each_question_shows_only_the_past_average_with_its_records_and_the_others_are_counted` |
| 5 | committed bytes only | `test_an_edited_or_untracked_working_tree_file_is_never_read` |
| 5 | footer hash | `test_the_footer_lists_every_record_used_with_the_hash_of_its_committed_bytes` |
| 6 | Slack ts stored | `test_a_posted_card_stores_slacks_ts_as_issuance_time_and_its_full_record_in_drive_only` |
| 6 | witness reads push receipt | `test_the_witness_prints_slacks_time_beside_githubs_push_receipt` |
| 7 | skew limit | `test_a_server_clock_off_by_more_than_five_seconds_is_a_warning_printed_and_stored` |
| 7 | naive Date is UTC | `test_githubs_date_header_is_read_as_utc_and_a_missing_one_is_unknown` |
| 7 | GitHub clock on the repository path | `test_githubs_clock_is_asked_on_the_repository_path` |
| 7 | missing Date header named | `test_githubs_date_header_is_read_as_utc_and_a_missing_one_is_unknown` |
| 7 | unchecked clock stored as such | `test_a_server_clock_off_by_more_than_five_seconds_is_a_warning_printed_and_stored` |
| 7 | next card names an unchecked clock | `test_a_server_clock_off_by_more_than_five_seconds_is_a_warning_printed_and_stored` |
| 6 | receipt pages asked by owner/name | `test_the_activity_log_is_read_across_pages` |
| 6 | access refused named apart | `test_an_unreadable_log_or_an_unknown_commit_fails_closed` |
| 6 | witness names an access problem | `test_the_witness_prints_slacks_time_beside_githubs_push_receipt` |
| 7 | SF1 error answer's Date trusted | `test_githubs_date_header_is_read_as_utc_and_a_missing_one_is_unknown` |
| 7 | SF2 boundary > becomes >= | `test_the_five_second_boundary_on_both_sides[-5.0-0.0-False]` |
| 7 | SF2 limit raised to 9.9 s (judge B1) | `test_the_five_second_boundary_on_both_sides[-5.1-0.0-True]` |
| 7 | SF2 resolution ignored early (judge B2) | `test_the_five_second_boundary_on_both_sides[-6.0-1.0-False]` |
| 5 | SF3 reads the index (judge T12) | `test_an_edited_or_untracked_working_tree_file_is_never_read` |
| 11 | minor 3 ConnectionError treated as may-have-posted | `test_a_failure_that_may_have_posted_or_is_a_refusal_is_never_retried` |
| 13 | minor 2 source message off the record | `test_a_source_that_raises_never_loses_the_card` |
| 12 | minor 1 --post today only | `test_post_refuses_any_day_but_today` |
| 7 | UTC stored | `test_times_are_stored_in_utc_even_when_the_host_clock_is_in_ist` |
| 8 | owner-unavailable line | `test_a_full_card_says_paper_only_no_trade_with_its_reason_and_the_owner_line` |
| 9 | no card text in repo | `test_the_repository_metadata_holds_no_card_text_and_no_secret` |
| 10 | card always arrives | `test_a_source_that_raises_never_loses_the_card` |
| 11 | one retry | `test_slack_down_is_retried_once_printed_stored_and_still_saved_to_drive` |
| 11 | never retry a maybe-posted | `test_a_failure_that_may_have_posted_or_is_a_refusal_is_never_retried` |
| 11 | never retry a refusal | `test_a_failure_that_may_have_posted_or_is_a_refusal_is_never_retried` |
| 11 | accepted never re-posted | `test_an_accepted_post_without_a_readable_ts_is_said_and_not_posted_again` |
| 11 | non-dict answer | `test_a_non_dict_slack_answer_never_raises` |
| 11 | failed metadata write kept | `test_a_failed_metadata_write_keeps_every_line_and_prints_the_metadata` |
| 11 | attempts count committed | `test_attempt_numbers_count_committed_attempts_from_another_checkout` |
| 11 | next card names miss | `test_the_next_card_names_the_previous_sessions_misses` |
| 11 | Drive failure reported | `test_drive_down_does_not_stop_the_post_and_is_named_by_error_type_only` |
| 12 | dry run by default | `test_the_dry_run_prints_the_real_repositorys_card_and_issues_nothing` |
| 13 | errors by type only | `test_drive_down_does_not_stop_the_post_and_is_named_by_error_type_only` |
| 14 | non-session gets no card | `test_a_day_that_is_not_a_session_gets_no_card` |
| 14 | muhurat gets no card | `test_a_muhurat_session_gets_no_card_and_is_skipped_as_the_previous_session` |
| 14 | previous skips muhurat | `test_a_muhurat_session_gets_no_card_and_is_skipped_as_the_previous_session` |
| 14 | corrupt earlier record named | `test_a_corrupt_earlier_delivery_record_is_named_and_never_stops_the_card` |
| 14 | unknown calendar still a card | `test_a_day_the_calendar_cannot_answer_still_gets_a_card_naming_the_gap` |
| 16 | TEST marked | `test_a_test_post_is_marked_on_its_first_line_and_records_and_never_counts_as_the_card` |
| 16 | test never counts as card | `test_a_test_post_is_marked_on_its_first_line_and_records_and_never_counts_as_the_card` |
| 16 | --test needs --post | `test_test_marks_one_live_post_and_needs_post` |

Criterion 15 (structure) has no planted break; `tests/test_code_size.py` and `tests/test_import_graph.py` cover it.

## Acceptance criteria: claim, code, test, evidence

| # | Criterion | Code | Test | Evidence |
|---|---|---|---|---|
| 1 | PAPER ONLY on the first line; no order instruction | `fno/cards/render.py:11`, `:33` | `tests/cards/test_card.py::test_a_full_card_says_paper_only_no_trade_with_its_reason_and_the_owner_line` (asserts "order" never appears) | strong evidence (test + real dry run) |
| 2 | NO TRADE with reason codes; a `paper` version still NO TRADE; unreadable registry = `data_check_failed`; never a trade | `fno/cards/status.py:46-58`, `:60`; v1 forces NO TRADE whatever a source says: `fno/cards/card.py:78` | `test_a_version_at_paper_still_gives_no_trade_and_never_a_trade`, `test_an_unreadable_registry_or_account_is_a_failed_data_check_named_on_the_card`, `test_open_and_closed_trades_are_counted` | strong evidence |
| 3 | Weather "not yet scored (M1 pending)", no colour word | `fno/cards/weather.py:10` | `test_weather_is_never_a_colour_on_a_v1_card` (regex GREEN/AMBER/RED on the whole card) | strong evidence |
| 4 | The house forecast (past average, labelled as the fallback) per question of the latest committed capture, plus the count of other forecasters, back-fill record labelled "not live", live "not enough data yet"; none on record; older capture labelled | `fno/cards/forecasts.py:51-122`, `fno/cards/track_record.py:27-62` | `test_every_forecaster_is_shown_with_its_back_fill_record_and_no_live_record_yet`, `test_no_forecasts_and_no_score_report_still_give_a_card_that_names_them`, `test_a_capture_after_the_day_is_never_used` | strong evidence for the reading; the bin figures are G4's, not recomputed (the card only picks the bin) |
| 5 | Committed records only; footer path + SHA-256 equal to committed bytes | `fno/cards/committed.py:21-43` (`git show HEAD:<path>`), footer `fno/cards/render.py` | `tests/cards/test_records_and_witness.py::test_an_edited_or_untracked_working_tree_file_is_never_read` (real temp git repo), `test_the_footer_lists_every_record_used_with_the_hash_of_its_committed_bytes` | strong evidence |
| 6 | Issuance = Slack server `ts`, stored; `card witness` prints it beside GitHub's push receipt; committer time never read | `fno/cards/posting.py` (`PostReceipt.ts`, `server_time`), `fno/cards/issue.py:45-68`, `fno/cards/witness.py:28-48` (reuses `fno/ai/receipts.py` `PushReceipts`) | `tests/cards/test_issue.py::test_a_posted_card_stores_slacks_ts_as_issuance_time_and_its_full_record_in_drive_only`, `test_the_witness_prints_slacks_time_beside_githubs_push_receipt` | some evidence: fakes only. Slack's real `chat.postMessage` answer carries `ts` (Slack API docs; reasoning from the docs, not tested live). The witness needs `GITHUB_TOKEN`; without it, it prints "unknown (HTTP 401 ...)" |
| 7 | UTC with offset stored, IST shown; host clock vs Slack and GitHub; skew > 5 s WARNING printed and stored | `fno/cards/clock.py:37-92`, `fno/constants.py` `CLOCK_SKEW_WARNING_SECONDS` | `test_a_server_clock_off_by_more_than_five_seconds_is_a_warning_printed_and_stored`, `test_slack_ts_far_from_the_host_clock_is_a_warning` | some evidence (fakes; GitHub's `Date` header has 1 s resolution, allowed for) |
| 8 | Owner-unavailable line, E8 absence stated | `fno/cards/card.py:16` | `test_a_full_card_says_paper_only...` | strong evidence |
| 9 | Card records to Drive only; repository metadata holds no card text | `fno/cards/record_store.py:24-42`, `fno/cards/issue.py:55-60` | `test_the_repository_metadata_holds_no_card_text_and_no_secret` | strong evidence for the code; the Drive write itself is `GoogleDriveUploadStore` (story A9), not re-tested live |
| 10 | The card always arrives; missing inputs named | `fno/cards/card.py:56-86` (`_guarded`, `_status`) | `test_a_source_that_raises_never_loses_the_card`, the empty cases above | strong evidence |
| 11 | Slack down: one retry only when the post surely did not land, never a double post, "alert NOT sent", Drive + metadata still written, next card names it; Drive down: still posted, "card record NOT saved to Drive", next card names it | `fno/cards/posting.py:17-30` (which failures are retried), `:52-93`, `fno/cards/deliveries.py:70-84`, `fno/cards/daily.py:30-36` | `test_slack_down_is_retried_once_printed_stored_and_still_saved_to_drive`, `test_a_network_error_then_success_posts_once_more`, `test_drive_down_does_not_stop_the_post_and_is_named_by_error_type_only`, `test_the_next_card_names_the_previous_sessions_misses`, `test_no_token_and_no_drive_print_what_was_not_done_and_never_a_secret`, `test_a_failure_that_may_have_posted_or_is_a_refusal_is_never_retried`, `test_an_accepted_post_without_a_readable_ts_is_said_and_not_posted_again`, `test_a_non_dict_slack_answer_never_raises`, `test_a_failed_metadata_write_keeps_every_line_and_prints_the_metadata`, `test_a_corrupt_earlier_delivery_record_is_named_and_never_stops_the_card` | strong evidence |
| 12 | Dry run by default, no network | `fno/cards/cli.py:27-46` | `tests/cards/test_cli.py::test_the_dry_run_prints_the_real_repositorys_card_and_issues_nothing` (network blocked, issuer must not be built) | strong evidence |
| 13 | Secrets never in files or logs | token only in `SlackCardPoster`'s header; Drive and sign-in failures named by error type only (`record_store.py`, `wiring.py:57-63`) | `test_drive_down_...` (a "secret" in the error never reaches output), `test_the_composition_root_...` (a refused sign-in's message never reaches output) | strong evidence |
| 14 | Non-session day: "not a trading day"; unknown calendar still gets a card naming it | `fno/cards/session.py:30-62`, `fno/cards/cli.py` | `test_a_day_that_is_not_a_session_gets_no_card`, `test_a_day_the_calendar_cannot_answer_still_gets_a_card_naming_the_gap`, `test_a_holiday_prints_not_a_trading_day` | strong evidence |
| 15 | Interfaces, one composition root, sizes, constants | `fno/cards/wiring.py` (listed in `CLAUDE.md`); interfaces `CommittedRecords`, `StatusSource`, `WeatherSource`, `ForecastSource`, `CardRenderer`, `CardPoster`, `CardRecordStore`, `DeliveryLog`, `ServerClock`; constants in `fno/constants.py` (card block at the end) | `tests/test_code_size.py`, `tests/test_import_graph.py` | strong evidence (largest new file under 100 lines) |
| 16 | Live delivery to #fno-desk verified once (orchestrator addendum) | `fno/cards/issue.py` (`TEST_BANNER`, `issue(..., test=True)`), `fno/cards/cli.py` (`--test` needs `--post`), `fno/cards/deliveries.py` (`misses` skips test attempts) | `tests/cards/test_issue.py::test_a_test_post_is_marked_on_its_first_line_and_records_and_never_counts_as_the_card`, `tests/cards/test_cli.py::test_test_marks_one_live_post_and_needs_post` | Branch half (a) MET: one live post, ts 1792025414.919329, permalink above, read back from the channel. The GitHub receipt half (b) is checked at the merge. Strong evidence for (a) |

DRY change outside `fno/cards/`: the Slack HTTP post moved into one function `slack_post` (`fno/alerts/sender.py:23`)
used by both `SlackChannelAlerts` and `SlackCardPoster`; the existing alert tests still pass unchanged.

## Gates (this commit)

`git config core.hooksPath .githooks`; not shallow; `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`; `ruff check fno
tests tools`; `ruff format` (no changes); `python tools/check_imports.py` (clean). Full suite on the final commit (main merged in): 3541 passed; `tests/cards`: 63.
Note: `pip install -r requirements-groww.txt` fails in this container (two old dependencies of `growwapi` do not build);
no T1 code needs it.

## Design choices the owner may want to decide

1. **House forecast = past average, decided by the orchestrator (option 1, 15 Oct 2026).** I first showed every
   forecaster (about 25 lines). The orchestrator asked for the protocol's primary yardstick per question; I checked
   G1 v1-v3 and none names one (section 4 defines three baselines; section 6's secondary list gives each question two
   baselines of equal standing; design 05 section 5.3's primaries are for v4's V questions). The card now shows the past average (`baseline_b_base_rate`) on all five questions, labelled as the fallback (orchestrator, 15 Oct 2026): G1 v1-v3 name no primary yardstick for any question; the base rate is the only baseline defined on all five and uses no model or market input; it matches REPLAN's "baselines until something passes" and the owner's signed-off Forecast lab mockup (37), whose main yardstick is "Past average". It was never chosen by its scores. It is a display choice only and changes no scoring. When protocol v4 merges, its own primary baselines (design 05 section 5.3) replace this for the V questions. Never chosen by scores: the back-fill
   Brier scores point both ways (q5: base rate 0.218 vs Book 1 0.248; q3: base rate 0.252 vs Book 1 0.219).
2. **Weather shows nothing.** Response 94's v0 rule exists only as a research script; wiring a research script into a
   daily card would bypass M1's design. And response 94 found the RED filter helped none of the five structures.
3. **A day the calendar cannot answer still gets a card** (a card on a holiday costs nothing; a missing card on a
   session breaks the contract). The A4 recorder makes the opposite choice (stops). Owner may prefer consistency.
4. **The CLI does not commit or push.** The delivery metadata file is written; the scheduled session must commit and
   push it (the push is the second witness). Scheduling is out of scope by instruction.
5. **Exit code 1** when the card was not sent or its record not saved, so a scheduled run can see it.

## Known limits (said plainly)

- **GitHub's clock from the routine (judge 101 SF4).** Through this cloud container's GitHub proxy, the API root
  (HEAD `https://api.github.com`) gives HTTP 400 and `/zen` gives 403, both with no `Date`. That was the live test
  post's "not checked (KeyError)". The card now asks `https://api.github.com/repos/exepex/trading`, which passes with
  GitHub's `Date`: "within 0.0 s" live from this builder container (some evidence: one read-only check, not yet a
  scheduled post). If a scheduled routine's network refuses that path too, its cards will store "clock NOT CHECKED:
  host vs GitHub (HTTP ..., ...)", `checked: false`, and the next card names it. The check is then missing, never
  read as "within skew". GitHub's push receipt, the second issuance witness, is unaffected: it is read later, from the
  activity log.
- **One unintended live Slack post during building.** My first commit attempt held a fake test token shaped like a
  Slack bot token (`xoxb-...`). The record scan (story O5) correctly refused the commit, and its hook posted its own
  standard alert to #fno-desk, because `FNO_SLACK_BOT_TOKEN` is set in this container. That alert names only the file,
  line and kind of value, never the value, and the value was fake. The fake token is now `test-token-not-real`, the
  same style the existing alert tests use. The card code itself made no live call.
- One live TEST post only (above). No scheduled card has run yet, and the GitHub clock check succeeded live only in a direct read-only check after its fix (not yet in a post).
- A retry after a lost Slack answer can post the card twice (Slack accepted the first but the answer was lost). The
  delivery metadata then shows one `ts`; the duplicate is harmless but visible.
- The paper trade count reads each book's `positions.json` view, not the ledger it is rebuilt from.
- The card reads `HEAD`: a run before `git pull` shows yesterday's records. The scheduled session must pull first.
- "Previous card: no card on record for <day>" appears until cards run daily; on the first card it is true but noisy.
- The weather line is listed under "Missing" every day until M1.

## What the judge should test hardest

1. Edit `research/forecasts/live_v2/2026/2026-10-14_forecasts.csv` in the working tree and re-run the dry run: the card
   and its hashes must not change (`git show HEAD:<path> | sha256sum` equals the footer).
2. Plant a `paper` row in `playbook/registry.csv` (committed on a scratch branch): still `NO TRADE`, code
   `trade_fields_not_built`.
3. `--post` with no token and no Drive settings: printed failures, exit 1, a delivery file with no card text and no
   secret, then the next session's dry run names the miss (after committing that file).
4. Grep every new file for a token, and the delivery file for any line of the card body.
5. Whether the back-fill track record is labelled clearly enough as "not live" for an owner reading it on a phone.
