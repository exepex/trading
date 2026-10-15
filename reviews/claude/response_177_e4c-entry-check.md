# Response 177: story E4c code, every leg checked before any fill (claims for the judge)

Builder: Claude (E2c/E5b builder; E4c moved to this session on 15 Oct, register row updated). Branch
`story/e4c-protective-leg-refusal`, rebased on `main` after E2c merged. Story text: "E4c" in
`docs/stories/E-paper-desk.md` (text PASS judge 120 addendum 1; ChatGPT review 104 accepted it, response 131). Quality
rule 9: ChatGPT reviews the code after the judge's PASS.

## What changed

- `fno/desk/entry_check.py` (new): `entry_problems(snapshot, legs, units)`. It goes through the legs in E4's order
  (protection first). For each leg it checks the opening side, then, for a protective leg, the closing side, with E4's
  `price_leg`, so there is no second pricing rule. It returns `"<code> (<contract>, <units> units)"` for every failure,
  and never a quote figure.
- `fno/desk/entries.py`: `EntryDesk.enter` calls it after C3's checks and E4's `refusal`, and before the entry limit.
  A problem records `not_opened` with the first one, and nothing fills. The leg loop's unwind is unchanged and is now a
  guard: it runs only if a fill fails after the check passed.
- `fno/constants.py`: `PROTECTION_NOT_BUYABLE`, `PROTECTION_NOT_SELLABLE`, `SHORT_LEG_NOT_SELLABLE`.
- `fno/desk/daily_steps.py`: when a fill result's reason starts with one of the three codes, `_fill_one` sends one
  alert, "F&O paper desk <day> <book>: trade <id> not opened: <code> (<contract>, <units> units): information, no
  action". When the sender's outcome is not "sent" (no token), it prints that outcome ("alert NOT sent: ..."), and the
  run goes on.
- Story texts: E2b now lists two exceptions, exception 1 only through the guard, and the third removed; Status lines
  for E2c (done) and E4c are updated.

## Claims per criterion

| # | Claim | Evidence |
|---|---|---|
| 1 | Any failing check makes the entry `not_opened` with one of the three codes. No fill row, no E1 ledger row (only the opening), the account unchanged | `tests/desk/test_entry_check.py`: `nothing_written` in every refusal test |
| 2 | Boundaries 64 / 65 / 66 units on a protective bid, a protective ask and a short bid: 64 refused with the side's code, 65 and 66 open. STR1's LC, LP and the credit verticals (CCS, PCS): one leg short on its checked side refuses the whole structure; with sizes covering, it opens | `test_a_size_equal_to_the_units_passes_one_less_is_refused_before_any_fill` (9 cases), `test_str1_structures_one_leg_or_vertical_are_checked_the_same` (4) |
| 3 | A protective leg that A4 makes unusable (no quote, no bid, bid 0, no bid size, crossed, no trade today) or whose ask size is short gives `protection_not_buyable`, the second wing included; a short leg gives `short_leg_not_sellable`. No unwind, no legging cost | `test_a_protective_leg_a4_cannot_use_is_not_buyable_and_nothing_is_bought` (6); `test_entries.py`: `test_a_second_protective_leg_failing_buys_nothing`, `test_a_short_leg_that_cannot_be_sold_buys_no_protection` |
| 4 | Order: C3, then E4's refusals, then the check (legs in order, opening then closing), then the entry limit, then fills. Two failures record the first. A rerun returns the recorded outcome | `test_a_case_failing_two_checks_records_the_first_in_the_fixed_order`, `test_the_refusals_before_the_entry_check_come_first_and_a_rerun_returns_the_record` |
| 5 | The event row holds no quote figure | `test_the_event_row_holds_no_quote_figure` (every bid and ask of the snapshot, the planted size 64 and the default size 1000) |
| 6 | Exception 3 is gone: E2b's scenario (a wing's bid size 1) is `not_opened`, and no row reveals both sides | `test_public_fills.py::test_unverified_protection_at_the_opening_snapshot_is_never_bought_the_third_exception_is_gone`; E2b's text edited |
| 7 | One alert per refused entry, ending "information, no action", holding no quote figure. Without the token, "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set" is printed and the run reaches its exits | `tests/timetable/test_entry_check_alert.py` (fake sender; `NoAlertSender`) |
| 8 | Guard: with a check double that passes, E4's unwind runs as built (short legs bought back first, protection sold last, legging cost; an unwind leg it cannot trade back stays an exit order). The moved assertions are unchanged | `test_entries.py`: `test_the_guard_unwinds_...` (two), `test_an_unwind_leg_without_bid_size_stays_as_an_exit_order`; fixture `check_passed` |
| 9 | Later snapshots: `protection_unverified` is unchanged | `test_exits.py` stays green; one line changed (below) |
| 10 | C5 is merged: a refused entry leaves `RiskBook.session_trades` empty for the day | `test_a_refused_entry_is_not_new_risk_of_the_session` |
| 11 | The check depends only on the snapshot it is given (the E8 hook) | `test_the_check_depends_only_on_the_snapshot_it_is_given` |
| 12 | Never an order call | `tests/desk/test_safety.py` scans every `fno/desk/*.py`, `entry_check.py` included |
| 13 | Engineering | constants in `fno/constants.py`; `entry_check.py` is 32 lines; interfaces unchanged; ruff, import check and the full suite pass |

## Tests changed on purpose (no assertion dropped)

The five tests the story names:
- the size boundary;
- the second protective leg (split into a refusal test and a guard test that keeps every old assertion);
- the short leg (likewise);
- the unwind leg without bid size (through the guard, assertions unchanged);
- E2b's third-exception test (now: never bought).

Beyond the story's list, stated here:
- `test_entries.py::test_a_protective_leg_without_a_valid_quote_opens_nothing` (the "No bid" row of the story's
  table): its reason now leads with `protection_not_buyable`.
- `test_exits.py`, one line in the later-snapshot test: another book's refused entry is still `not_opened`, and its
  reason still names the bad wing. Only the reason's start changed. The `protection_unverified` assertions are
  untouched.
- `test_public_fills.py::test_only_an_unwind_reveals_both_sides_within_one_account` (exception 1) and
  `test_shadow_books.py::test_trade_counts_come_from_the_shadow_accounts_own_records` (an unwound entry as a fixture)
  now reach the unwind through the guard double, with their assertions unchanged.

## Plants (all caught; desk and alert tests)

| Plant | Tests failing |
|---|---|
| the check call removed from `enter` | 23 |
| a protective leg's closing side not checked | 10 |
| a protective leg's opening side not checked | 13 |
| legs checked in reverse order | 1 |
| a size figure in the reason | 22 |
| the guard's unwind removed | 5 |
| no alert | 2 |
| "alert NOT sent" not printed | 1 |

## Said plainly

- **Strong evidence (code: `.gitignore`, E2c): the privacy half of E4c is now moot.** Since E2c merged, `desk_fills.csv` and
  `desk_events.csv` live in Drive, not in the public repository. E4c's value is the money half: no spread paid twice
  for a trade the book cannot hold, and no new-risk budget used by a trade that never stays open.
- **E6's legging-cost figure** now stays at zero unless the guard fires. That is a known effect of decision 43, not a
  change to E6.
- **The alert fires again on a rerun** of a fills step that did not complete. That is rare, and only the step's own
  rerun, never a new trade.
- **Open questions 1 and 2** (a maximum spread; a short leg's buy-back depth) stay with the owner, unchanged.
- **A sample refusal**, from the fixture day in `test_entry_check_alert.py`:
  "F&O paper desk 2026-10-14 book1_rules: trade t1 not opened: protection_not_sellable (NIFTY26102725200CE, 65 units):
  information, no action".
