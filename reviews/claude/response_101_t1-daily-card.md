# Response 101: story T1, the daily trade card v1 (builder's claims for the judge)

Branch `story/t1-daily-card` (from `origin/main` 96ee83f). Story text: `docs/stories/T-cards.md` section T1. Lane 1
(new story; touches Slack, Drive and an outside clock).

**Verdict in one line:** the card is built, tested and prints correctly from the real repository; it has never been
posted for real (no live Slack or Drive call was made during building), and three of its inputs are honest
placeholders (weather, house-forecast rule, owner availability), each named on the card.

## What the card says today (dry run on the repository, `python -m fno card daily --on 2026-10-15`)

- `PAPER ONLY. ... Information, no action.` / `Status: NO TRADE (no_approved_strategy)` / `Paper trades so far: 0`.
- `Weather: not yet scored (M1 pending)`.
- The 14 Oct live capture (the latest committed; today's capture has not run yet), with: **"Generated 19:27 IST, after
  the 15:15 deadline: these records are not scored (protocol v2 section 5)"**. That is a real finding, not a card
  detail: the 14 Oct live capture missed G1's deadline, so none of its 20 forecasts will ever count (G4's report
  already shows `late_live_records: 20`). If the capture keeps running in the evening, the live forecast record stays
  empty forever. Owner and orchestrator: the capture must run before 15:15 IST to produce any scored live forecast.
- Each forecaster's back-fill record in today's calibration bin, e.g. `book1_rules 0.40` on q3 "said 0.4-0.5 on 159
  days, happened on 25%" (back-fill, not live). Statistician's reading: on question 3, Book 1's back-fill was badly
  over-confident that realised volatility would rise (25% observed in a 40-50% bin; some evidence: one bin, 159
  overlapping 20-day windows, so far fewer independent outcomes).

## Acceptance criteria: claim, code, test, evidence

| # | Criterion | Code | Test | Evidence |
|---|---|---|---|---|
| 1 | PAPER ONLY on the first line; no order instruction | `fno/cards/render.py:11`, `:33` | `tests/cards/test_card.py::test_a_full_card_says_paper_only_no_trade_with_its_reason_and_the_owner_line` (asserts "order" never appears) | strong evidence (test + real dry run) |
| 2 | NO TRADE with reason codes; a `paper` version still NO TRADE; unreadable registry = `data_check_failed`; never a trade | `fno/cards/status.py:46-58`, `:60`; v1 forces NO TRADE whatever a source says: `fno/cards/card.py:78` | `test_a_version_at_paper_still_gives_no_trade_and_never_a_trade`, `test_an_unreadable_registry_or_account_is_a_failed_data_check_named_on_the_card`, `test_open_and_closed_trades_are_counted` | strong evidence |
| 3 | Weather "not yet scored (M1 pending)", no colour word | `fno/cards/weather.py:10` | `test_weather_is_never_a_colour_on_a_v1_card` (regex GREEN/AMBER/RED on the whole card) | strong evidence |
| 4 | Every forecaster of the latest committed capture, back-fill record labelled "not live", live "not enough data yet"; none on record; older capture labelled | `fno/cards/forecasts.py:43-80`, `fno/cards/track_record.py:25-56` | `test_every_forecaster_is_shown_with_its_back_fill_record_and_no_live_record_yet`, `test_no_forecasts_and_no_score_report_still_give_a_card_that_names_them`, `test_a_capture_after_the_day_is_never_used` | strong evidence for the reading; the bin figures are G4's, not recomputed (the card only picks the bin) |
| 5 | Committed records only; footer path + SHA-256 equal to committed bytes | `fno/cards/committed.py:21-39` (`git show HEAD:<path>`), footer `fno/cards/render.py` | `tests/cards/test_records_and_witness.py::test_an_edited_or_untracked_working_tree_file_is_never_read` (real temp git repo), `test_the_footer_lists_every_record_used_with_the_hash_of_its_committed_bytes` | strong evidence |
| 6 | Issuance = Slack server `ts`, stored; `card witness` prints it beside GitHub's push receipt; committer time never read | `fno/cards/posting.py` (`PostReceipt.ts`, `server_time`), `fno/cards/issue.py:43-56`, `fno/cards/witness.py:28-41` (reuses `fno/ai/receipts.py` `PushReceipts`) | `tests/cards/test_issue.py::test_a_posted_card_stores_slacks_ts_as_issuance_time_and_its_full_record_in_drive_only`, `test_the_witness_prints_slacks_time_beside_githubs_push_receipt` | some evidence: fakes only. Slack's real `chat.postMessage` answer carries `ts` (Slack API docs; reasoning from the docs, not tested live). The witness needs `GITHUB_TOKEN`; without it, it prints "unknown (HTTP 401 ...)" |
| 7 | UTC with offset stored, IST shown; host clock vs Slack and GitHub; skew > 5 s WARNING printed and stored | `fno/cards/clock.py:37-91`, `fno/constants.py` `CLOCK_SKEW_WARNING_SECONDS` | `test_a_server_clock_off_by_more_than_five_seconds_is_a_warning_printed_and_stored`, `test_slack_ts_far_from_the_host_clock_is_a_warning` | some evidence (fakes; GitHub's `Date` header has 1 s resolution, allowed for) |
| 8 | Owner-unavailable line, E8 absence stated | `fno/cards/card.py:16` | `test_a_full_card_says_paper_only...` | strong evidence |
| 9 | Card records to Drive only; repository metadata holds no card text | `fno/cards/record_store.py:24-37`, `fno/cards/issue.py:49-51` | `test_the_repository_metadata_holds_no_card_text_and_no_secret` | strong evidence for the code; the Drive write itself is `GoogleDriveUploadStore` (story A9), not re-tested live |
| 10 | The card always arrives; missing inputs named | `fno/cards/card.py:56-86` (`_guarded`, `_status`) | `test_a_source_that_raises_never_loses_the_card`, the empty cases above | strong evidence |
| 11 | Slack down: one retry, "alert NOT sent", Drive + metadata still written, next card names it; Drive down: still posted, "card record NOT saved to Drive", next card names it | `fno/cards/posting.py:17`, `:44-57`, `fno/cards/deliveries.py:66-80` | `test_slack_down_is_retried_once_printed_stored_and_still_saved_to_drive`, `test_a_network_error_then_success_posts_once_more`, `test_drive_down_does_not_stop_the_post_and_is_named_by_error_type_only`, `test_the_next_card_names_the_previous_sessions_misses`, `test_no_token_and_no_drive_print_what_was_not_done_and_never_a_secret` | strong evidence |
| 12 | Dry run by default, no network | `fno/cards/cli.py:36-38` | `tests/cards/test_cli.py::test_the_dry_run_prints_the_real_repositorys_card_and_issues_nothing` (network blocked, issuer must not be built) | strong evidence |
| 13 | Secrets never in files or logs | token only in `SlackCardPoster`'s header; Drive and sign-in failures named by error type only (`record_store.py`, `wiring.py:57-63`) | `test_drive_down_...` (a "secret" in the error never reaches output), `test_the_composition_root_...` (a refused sign-in's message never reaches output) | strong evidence |
| 14 | Non-session day: "not a trading day"; unknown calendar still gets a card naming it | `fno/cards/session.py:27-51`, `fno/cards/cli.py` | `test_a_day_that_is_not_a_session_gets_no_card`, `test_a_day_the_calendar_cannot_answer_still_gets_a_card_naming_the_gap`, `test_a_holiday_prints_not_a_trading_day` | strong evidence |
| 15 | Interfaces, one composition root, sizes, constants | `fno/cards/wiring.py` (listed in `CLAUDE.md`); interfaces `CommittedRecords`, `StatusSource`, `WeatherSource`, `ForecastSource`, `CardRenderer`, `CardPoster`, `CardRecordStore`, `DeliveryLog`, `ServerClock`; constants in `fno/constants.py` (card block at the end) | `tests/test_code_size.py`, `tests/test_import_graph.py` | strong evidence (largest new file under 100 lines) |
| 16 | Live delivery to #fno-desk verified once (orchestrator addendum) | `fno/cards/issue.py` (`TEST_BANNER`, `issue(..., test=True)`), `fno/cards/cli.py` (`--test` needs `--post`), `fno/cards/deliveries.py` (`misses` skips test attempts) | `tests/cards/test_issue.py::test_a_test_post_is_marked_on_its_first_line_and_records_and_never_counts_as_the_card`, `tests/cards/test_cli.py::test_test_marks_one_live_post_and_needs_post` | **NOT MET yet**: the flag is built and tested with fakes; no live post until the owner's yes is relayed. Then: `python -m fno card daily --post --test`, commit and push the delivery file, `python -m fno card witness --on <day>`, and the output goes here |

DRY change outside `fno/cards/`: the Slack HTTP post moved into one function `slack_post` (`fno/alerts/sender.py:23`)
used by both `SlackChannelAlerts` and `SlackCardPoster`; the existing alert tests still pass unchanged.

## Gates (this commit)

`git config core.hooksPath .githooks`; not shallow; `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`; `ruff check fno
tests tools`; `ruff format` (no changes); `python tools/check_imports.py` (clean). Counts in the orchestrator message.
Note: `pip install -r requirements-groww.txt` fails in this container (two old dependencies of `growwapi` do not build);
no T1 code needs it.

## Design choices the owner may want to decide

1. **All forecasters are shown, not one "house forecast".** Design 07 section 7.4's house rule is not frozen and its
   primary baselines are declared for protocol v4's questions (V1-V7), not G1's q1-q5. Choosing one now would be an
   unfrozen choice. Cost: the forecast section is about 25 lines on a phone. (Reasoning only.)
2. **Weather shows nothing.** Response 94's v0 rule exists only as a research script; wiring a research script into a
   daily card would bypass M1's design. And response 94 found the RED filter helped none of the five structures.
3. **A day the calendar cannot answer still gets a card** (a card on a holiday costs nothing; a missing card on a
   session breaks the contract). The A4 recorder makes the opposite choice (stops). Owner may prefer consistency.
4. **The CLI does not commit or push.** The delivery metadata file is written; the scheduled session must commit and
   push it (the push is the second witness). Scheduling is out of scope by instruction.
5. **Exit code 1** when the card was not sent or its record not saved, so a scheduled run can see it.

## Known limits (said plainly)

- **One unintended live Slack post during building.** My first commit attempt held a fake test token shaped like a
  Slack bot token (`xoxb-...`). The record scan (story O5) correctly refused the commit, and its hook posted its own
  standard alert to #fno-desk, because `FNO_SLACK_BOT_TOKEN` is set in this container. That alert names only the file,
  line and kind of value, never the value, and the value was fake. The fake token is now `test-token-not-real`, the
  same style the existing alert tests use. The card code itself made no live call.
- Never run live: no real Slack post of a card, Drive write, GitHub `Date` read or activity-log read was made. First live run
  should be one `--post` by the owner or orchestrator with the real token, then `card witness`.
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
