# Response 105: story C5, risk buckets and the Rs 20 lakh paper account (claims for the judge)

Builder: Claude, 15 Oct 2026. Branch `story/c5-risk-buckets` (lane 1: money and risk). Story text:
`docs/stories/C-code-roles.md` section C5. Not merged; G6 not used. Owner decisions used: 14 Oct (Rs 20 lakh, Rs 10,000
a trade), 15 Oct (caps and brake; "1 A" and "2 A"), 13 Oct (Manual account), all quoted in the story text.

## Addendum 4: LC and LP mapped by the orchestrator's decision (owner to confirm)

- **The orchestrator's decision**, made while the owner was away on 15 Oct 2026 and logged by the orchestrator:
  - LC (long call) counts in bullish and long volatility;
  - LP (long put) counts in bearish and long volatility;
  - each counts its full maximum loss in both buckets.

  Its reason: a bought option is a directional bet that gains when movement grows, so it follows "1 B". This is the
  same as my recommendation (a) in addendum 3.
- **Marked in two places:** `config.yaml` (comment and both rows) and story criterion 5 say "orchestrator decision,
  owner to confirm".
- **Said plainly:** judge 105 addendum 1 asked to leave LC and LP refused until the owner answers. This decision
  **loosens** that: LC and LP trades now pass the bucket check instead of being refused. The owner should confirm or
  reverse it on return.
- **Tests:**
  - C2: `tests/risk/test_buckets.py::test_a_bought_option_is_its_direction_and_long_volatility`.
  - C4: `tests/checks/test_validity_caps.py::test_c4_puts_each_real_vertical_in_its_two_owner_buckets` now covers LC
    and LP with STR1's real legs.
  - The deliberate break (LC with one side) is caught: 46 of 46.

## Addendum 3: judge 105 addendum 1 (FAIL on 56bc6ed), new should-fixes 5 and 6

| Item | My check | Fix | Test |
|---|---|---|---|
| SF5 merge `main` (STR1 merged) | True: two code conflicts and two STR1 tests on the old signatures | Merged `origin/main` and kept both sides: `fno/risk/margins.py` uses the profile's `MarginAge` and STR1's `terms.bought_only`; `fno/playbook/wiring.py` uses the books profile and `build_tradable_structures()`. STR1's two tests now use the new signatures, unloosened: `tests/checks/test_validity_shapes.py` gets the 7-day Manual margin age as before, plus `max_age_sessions=None`; `tests/risk/test_bought_only.py` uses `DaysOld(7)` | full suite on the merged tree (below) |
| SF6 the verticals' mapping | True: with the real config, PCS was "unmapped" | `config.yaml` books `bucket_sides`: PCS [bullish, short_volatility], CCS [bearish, short_volatility], CDS [bullish, long_volatility], PDS [bearish, long_volatility]. LC and LP stay unmapped and refused (judge's ruling); **question to the owner below** | C2: `tests/risk/test_buckets.py::test_the_repository_maps_str1s_verticals_to_the_owners_two_buckets`, `test_a_bought_option_stays_unmapped_until_the_owner_decides`, `test_a_real_bull_put_spread_counts_with_a_held_fly_and_a_held_call_debit_spread` (wired caps; binds at exactly the larger bucket total, Rs 0.01 less refuses). C4: `tests/checks/test_validity_caps.py::test_c4_puts_each_real_vertical_in_its_two_owner_buckets`, `test_c4_refuses_a_bought_option_until_the_owner_maps_it` |
| Note: an exit that leaves a larger maximum loss is not new risk | Agreed; the bucket and open-risk caps still count it; needs a partial exit | none (information) | — |

Deliberate breaks re-run on the merged tree: **46 of 46 caught**, including 3 for the verticals' mapping.

**Owner question (new):** LC and LP (a bought call or put alone). By the logic of "1 B" a bought option is directional
and long volatility (LC: bullish and long volatility; LP: bearish and long volatility), but the owner's row names only
vertical spreads. Options:
- (a) map them so: two buckets each, the full maximum loss (the premium plus costs) in each;
- (b) direction only.

Superseded by addendum 4 (the orchestrator mapped them as (a); owner to confirm). My view (reasoning
only): (a), because a bought option loses its whole premium both in a fall and in a volatility crush.

## Addendum 2: judge 105 (FAIL on f4f2e35, 4 should-fix, 5 minor), each checked and answered

All accepted after checking each one myself.

| Item | My check | Fix | Test |
|---|---|---|---|
| SF1 margin age on muhurat days | True: on A7's calendar Sun 8 Nov 2026 is muhurat. `previous_session(9 Nov)` = 8 Nov, so Fri 6 Nov's row was refused. A14 writes rows only on `TradingDays` (no row for 8 Nov) | C2 `SessionsOld` steps over `TradingDays` (`fno/risk/margin_age.py`). C4 has its own rule: a trading day is a regular or special session, never muhurat (`MarginSettings.fresh`, `fno/checks/validity_settings.py`, reading `session_kind`) | `tests/risk/test_margin_age.py` and `tests/checks/test_validity_caps.py::test_c4_counts_margin_age_in_a14s_trading_days`. Both cover 6 Nov to 9 Nov (fresh), 5 Nov to 9 Nov (refused), and Fri 30 Jan to Mon 2 Feb (refused: the Sun 1 Feb special session counts) |
| SF2 C4 unsigned restart | True: C4's `restart_days` checked the action and reason only | C4 now requires a non-empty `entered_by` | `test_c4_refuses_an_unsigned_restart_row_on_its_own` |
| SF3 five C4 plants survived (N1, N2, N5, N17, N19) | The judge's evidence (all 5 survived at f4f2e35). I did not re-plant them before writing the tests: reasoning only that they would still have survived on the addendum-1 tree | Tests only; the code was already right | `test_each_c4_cap_passes_at_exactly_its_limit` (N1), `test_c4_does_not_count_a_held_position_of_the_other_side` (N2), `test_c4_counts_a_locked_in_held_position_as_zero_never_negative` (N5), `test_c4_refuses_a_position_on_two_underlyings` (N17), `test_c4_counts_a_two_lot_proposal_at_its_units` (N19). All 5 plants are now caught (table below) |
| SF4 P10 rule text | True | `docs/stories/P-publishing.md` criterion 1: `limit_max` = the books' `open_risk_cap_rs` (Rs 1,50,000, owner "2 A"). Once P10 publishes open trades, `limit_used` = the sum of open maximum losses. The dashboard's contract wording goes to the P1 builder (orchestrator) | doc |
| Minor 1 stray keys under `risk` | True: a leftover flat `max_open_trades` started C2 silently | `risk_settings` refuses any key outside profiles, scenarios, stress_line, margins and stressed_margin | `test_a_stray_key_under_risk_stops_start_up` (3 keys) |
| Minor 2 C4 value types | True | C4 checks its own types: rules a list of names, amounts positive numbers (no bool, no string), `bucket_sides` a non-empty mapping, margin age a positive number | `test_c4_checks_its_own_value_types` (5 cases) |
| Minor 3 "signed" | True: it is a typed name | Stated in story criterion 8: protected by lane 1 only; a CI guard would be a later story. **The owner should know this.** | doc |
| Minor 4 E1-topup | Agreed | Written into C5's Out list as criteria for `e1-topup`: `PaperAccountSize` reads the opening plus top-ups; a top-up never raises the brake's high-water mark | doc (next story) |
| Minor 5 brake per book | Orchestrator's decision (owner away), logged | Story criterion 8: the brake and caps apply per book, each book on its own Rs 20 lakh; the owner confirms on return | doc |

Every deliberate break re-run on this tree with `PYTHONDONTWRITEBYTECODE=1`: **43 of 43 caught**. This includes the
judge's 5 survivors, SF1 for C2 and C4 (muhurat counted), SF2 (C4 unsigned row) and both minors.

## Addendum 1 (owner's answers of 15 Oct 2026, rows on main 665c835)

- **"1 B" two buckets:** `bucket_sides` takes one side or a list. A position counts its full maximum loss in each of
  its buckets; a two-sided proposal must fit every one of its buckets; open risk counts each position once. C2
  (`fno/risk/caps.py`, `buckets.py`) and C4 (`fno/checks/validity_caps.py`). The spread codes themselves come with
  STR1; the tests use placeholder codes.
- **"3 A" same-session round trips count:** new risk is now every trade first filled on the decision day, open or
  already closed, at the largest maximum loss it carried after any fill time that day (C2: `RiskBook.session_trades`
  from the ledger, D2's same-session choices, D3's codec; C4: `AccountFacts.session` from its own ledger read). This
  replaces the earlier "first-fill day of open trades" design (`opened_on` is removed). A trade first filled earlier
  and traded again today is not new risk.
- **"4 A"** stress-line assumptions accepted, information only; **"5 A"** stocks stay refused until A18. No code change.
- **"2 B"** top-up is a separate story (`story/e1-topup`, response 110), not in C5.
- **C4 per-cap failure:** each C4 cap now fails closed on its own inputs, so an unmappable held position fails the
  bucket and open-risk caps in C4 exactly as in C2 (before, C4 also failed new risk).
- Re-run of every deliberate break: 33 of 33 caught (table below); first try missed one (a trade first filled earlier
  counted as new); a test now has such a trade.

## What changed

- **Risk profiles** (`config.yaml` `risk.profiles`): `books` and `manual`. Each lists the rules it runs and holds
  exactly their settings; any problem in any profile stops start-up (`fno/risk/profile_settings.py`).
  - Books: paper account Rs 20,00,000, Rs 10,000 a trade, bucket Rs 30,000, open risk Rs 1,50,000, new risk Rs 50,000 a
    session, brake Rs 1,20,000, margins at most one session old. No flat 3-trade, stress or exposure limit.
  - Manual: its 13 Oct limits unchanged (Rs 5 lakh, Rs 10,000, 3 open, Rs 30,000 brake, C2's stress and exposure, 7-day
    margins).
- **C2:** four new rules behind `RiskRule` (`paper_account`, `bucket_cap`, `open_risk_cap`, `new_risk_per_day`),
  each summing B2 maximum losses and only refusing. The composition root builds a profile's rules from a `RULES` table.
- **C4:** recomputes the same profile's rules with its own arithmetic (`fno/checks/validity_caps.py`); the 3-open,
  stress and exposure checks run for the Manual profile only.
- **E1** opens new accounts with the books' `paper_account_rs` (the Rs 5 lakh constant is gone).
- **Margin age:** a strategy, calendar days (Manual) or NSE sessions (books, design 6.1a), in C2 and C4.
- **The session's trades** (first filled on the decision day, open or closed, with their state after each fill time)
  come from the ledger, D2's same-session entries and D3's codec (addendum 1; this replaced `opened_on`).
- **The daily stress line** is a computed record, not a limit (`build_stress_line`).

## Gap list: design 6.1-6.3 and the C5 paragraph, each mapped

| Requirement (source) | Where | Criterion or reason out |
|---|---|---|
| Paper account Rs 20 lakh (6.1) | `config.yaml:49` books; `fno/risk/caps.py:87`; `fno/composition.py` | 7 |
| Rs 10,000 max loss per trade, charges included (6.1) | C2's `MaxLossPerTrade`, books profile | 10 (unchanged rule, new profile) |
| Worst loss fixed at entry; never unprotected selling (6.1) | `fno/risk/open_risk.py:36` refuses a net short tail | 6 (C4 shape checks already refuse naked shorts) |
| Stressed margin multiplier 1.45, funds at entry (6.1) | C2's `MarginRoom`, unchanged | out: unchanged by C5 |
| Strategy pauses Rs 30,000 cumulative (6.1) | E6 | out: E6's rule, not an account cap |
| Four kinds of loss; caps count kind 1 (6.1a) | `HeldMaxLoss` = B2's terminal loss plus charges | 6; kinds 2-4 out (8.4, E7) |
| Fail closed: margin older than one session (6.1a) | `fno/risk/margin_age.py:38`; `fno/checks/validity_settings.py:35` | 12 |
| Fail closed: unmapped bucket (6.1a) | `fno/risk/buckets.py:45`; `fno/checks/validity_caps.py:45` | 5 |
| Fail closed: missing margin row (6.1a) | C2 `MarginTable`, C4 `stressed_per_lot`, unchanged | existing C2/C4 tests |
| Bucket mapping frozen with C5 (6.1a) | `config.yaml` `risk` is in S1's `frozen_files` settings | reasoning: S1 hashes `config.yaml:risk` |
| Bucket = underlying group and side (6.2) | `fno/risk/buckets.py` | 5; stocks and results week out (A6/A12, A18) |
| Bucket cap Rs 30,000 (6.2) | `fno/risk/caps.py:69` | 1 |
| Account cap Rs 1.5 lakh, a cap on entries, not a stop (6.2) | `fno/risk/caps.py:75` | 2, 4 |
| New risk Rs 50,000 a session (6.2) | `fno/risk/caps.py:81` | 3 |
| Drawdown brake Rs 1.2 lakh, owner restart in writing (6.2) | `config.yaml` books; C2 `drawdown.py`, `overrides.py` | 8 |
| Weather RED: no new trades (6.2) | weather layer | out: M1/T1, not a C5 cap |
| Daily stress line on every card (6.2) | `fno/risk/stress_line.py:51` | 9; showing it on the card is T1 |
| Effective sample: distinct buckets-and-weeks (6.2) | scoreboard | out: S2/S3 reporting; `Bucket` gives them the key |
| Overnight holding allowed; events calendar (6.3) | strategy and E7 rules | out: not account caps |
| Physical settlement of stock options (6.3) | C4 | out: no stock options yet (A18) |
| "Config through fno/config.py" (C5 paragraph) | `risk` is an allowed key; profiles checked at start-up | 10 |
| Books drop 3-open, stress, exposure; Manual unchanged ("1 A", "2 A") | profiles | 10, 11, 13 |
| C4 in step (judge C) | `fno/checks/validity_caps.py`, `validity_limits.py` | 13 |

## Claims (acceptance criteria)

| # | Criterion | Code | Test | Evidence |
|---|---|---|---|---|
| 1 | Bucket cap at Rs 30,000 passes, Rs 0.01 over refused, other buckets not counted; a two-sided position counts its full loss in each bucket, a two-sided proposal must fit every one ("1 B") | `fno/risk/caps.py` (`MaxLossCap.check`, `BucketCap`); `fno/risk/buckets.py` | `tests/risk/test_caps.py` (`test_bucket_cap_at_just_under_and_just_over_rs_30000`, `test_another_bucket_does_not_count_against_this_one`, `test_a_two_bucket_proposal_must_fit_both_buckets_with_its_full_loss`, `test_a_held_two_bucket_position_counts_in_each_of_its_buckets`, `test_the_real_position_risks_count_the_held_trades_of_the_book`) | strong evidence |
| 2 | Open-risk cap at Rs 1,50,000 across buckets | `fno/risk/caps.py:75` | `tests/risk/test_caps.py:60` | strong evidence |
| 3 | New risk per day at Rs 50,000 for every trade first filled this session, open or closed ("3 A"), at its largest maximum loss; same-session choices count; earlier trades traded today do not; unknown session refused | `fno/risk/caps.py` (`NewRiskPerDay`); `fno/risk/open_risk.py` (`of_session`); `fno/risk/book_view.py` (`session_trades`); `fno/playbook/book_effects.py`; `fno/playbook/decision_codec.py` | `tests/risk/test_caps.py` (`test_new_risk_per_day_at_just_under_and_just_over_rs_50000`, `test_a_trade_opened_and_closed_this_session_still_counts`, `test_a_book_whose_session_trades_are_unknown_fails_closed`); `tests/risk/test_c5_account.py` (`test_the_session_trades_are_every_trade_first_filled_today_with_each_state`) | strong evidence |
| 4 | A cap only refuses; same proposal, lots unchanged | `fno/risk/caps.py:35` | `tests/risk/test_caps.py:90` | strong evidence |
| 5 | Buckets as 6.2: one side, or a listed pair for a directional spread ("1 B"); unmapped (incl. stocks, "5 A") refused | `fno/risk/buckets.py`; `fno/risk/profile_settings.py` (`_sides`); `config.yaml` `bucket_sides` | `tests/risk/test_buckets.py` (incl. `test_a_directional_spread_listed_with_two_sides_is_in_both_buckets`); `tests/risk/test_c5_account.py` (`test_a_two_sided_structure_is_read_as_a_list_of_sides`, malformed lists) | strong evidence (code); reasoning only for the SF/SC/BF sides; STR1 adds the spread codes |
| 6 | Held maximum loss = B2's; net short tail refused; locked-in counts 0 | `fno/risk/open_risk.py:36`, `:60` | `tests/risk/test_buckets.py:90`, `:99`, `:106`; reviewer's 3,000 random positions agree exactly | strong evidence |
| 7 | New accounts open with Rs 20 lakh; any other opening refused | `fno/books/account.py`, `fno/composition.py`, `fno/risk/caps.py:87` | `tests/books/test_paper_account.py`; `tests/risk/test_caps.py:82`; `tests/risk/test_c5_account.py:144` | strong evidence |
| 8 | Brake at Rs 1,20,000; only a signed restart row lifts it | `config.yaml` books; C2's `drawdown.py`, `overrides.py` | `tests/risk/test_c5_account.py:156`, `:184` | strong evidence |
| 9 | Daily stress line, five scenarios, below the sum of maximum losses (assumptions accepted, "4 A") | `fno/risk/stress_line.py`; `config.yaml` `stress_line` | `tests/risk/test_c5_account.py` (`test_the_daily_stress_line_reports_every_scenario_below_the_sum_of_maximum_losses`) | some evidence (one structure checked; reasoning beyond) |
| 10 | Books run exactly their rules; any setting problem in any profile stops start-up | `fno/risk/profile_settings.py:60`, `:71`, `:108`; `fno/risk/wiring.py:90` | `tests/risk/test_c5_account.py:44`, `:93`, `:98`, `:118`, `:125`, `:225` | strong evidence |
| 11 | Manual keeps its 13 Oct limits, runs exactly those rules | `config.yaml:64` | `tests/risk/test_c5_account.py:60`; `tests/risk/test_settings.py` | strong evidence |
| 12 | Books' margin older than one trading day refused (A14's `TradingDays`; addendum 2); weekends, holidays and muhurat Sundays never age a row | `fno/risk/margin_age.py:38`; `fno/checks/validity_settings.py:35` | `tests/risk/test_margin_age.py:28`, `:37`; `tests/checks/test_validity_caps.py:107` | strong evidence |
| 13 | C4 in step: own caps, books without old checks, breach C2 allowed refused, 4 open pass books and fail Manual, C4 max loss = C2's, C4 refuses to start on a missing setting | `fno/checks/validity_caps.py`, `validity_limits.py:58`, `validity_settings.py:129` | `tests/checks/test_validity_caps.py:50`, `:57`, `:66`, `:78`, `:85`, `:92`, `:102`, `:117`, `:132`, `:139` | strong evidence |

## Margin freshness: how C5 differs from C4's 7-day lookback (judge C, point a)

- **Books (C5, design 6.1a):** a margin row is usable only if dated on or after the previous NSE session (the day's
  own row or the previous session's), counted on A7's session calendar. A row from two sessions back is refused even
  if it is two calendar days old; Friday's row is fine on Monday; 20 Oct 2026 (holiday) is skipped. A day the calendar
  cannot answer refuses (C2: `CalendarError` is a `ValueError`, refused by the manager; C4: `fresh` returns False).
- **Manual (C2/C4 as before):** at most 7 calendar days.
- **Fit with A14:** A14 writes each session's rows from NSE's first file of the day (before 09:00 IST), so at 15:00 the
  day's own row normally exists. Today `research/data/margins/margins.csv` has no data rows at all, so every trade is
  refused for this reason too until A14 writes rows.

## Self-review by two independent review agents (owner's step 2)

Both read the diff only, verified claims with snippets, made no edits.

| Finding | Verdict | Action |
|---|---|---|
| Held maximum loss C2 vs C4 vs B2 | No bug: 3,000 random 2-4 leg positions, plus unequal units, agree exactly | none |
| Cap boundaries, brake, opened_on paths, margin session counting | No bug found | none |
| C4 crashes (TypeError) instead of refusing when a profile setting is missing | Accepted: verified | fixed: C4 checks its own settings at start-up (`fno/checks/validity_settings.py:129`); test `tests/checks/test_validity_caps.py:132` |
| C4 margin check lets a `CalendarError` through | Accepted (reasoning only, unreachable today) | fixed: `fresh` fails closed; test `:139` |
| Manual profile never read at runtime, so a wrong value passes silently | Accepted: verified | fixed: `all_profiles` checks every profile when any risk manager is built; test `tests/risk/test_c5_account.py:225` |
| Refusal text named `risk.caps.bucket_sides` | Accepted | fixed |
| C4 took the first ledger row as first-fill day, C2 the minimum | Accepted (reasoning only; the ledger is append-only) | fixed then; superseded by addendum 1 (both sort fills by time). Was: C4 takes the minimum too |
| C4 needs a two-sided quote for a held leg's strike; C2 accepts a stale mark | Partly accepted: true; C4's existing `margin_room` already needs the same mid, so C4 already refuses such a book. Kept: C4 is the stricter check and fails closed | known limit 6 |
| Stress line not shown anywhere | True; showing it is T1's scope (6.2 "every card shows") | out of scope, stated |
| Same-session exits make room for more new risk | True, C2 and C4 agree | known limit 3, question 3 |
| All three books refused (opened at Rs 5 lakh) | True, intended | owner "2 B": top-up story |

## Each criterion broken on purpose (owner's step 3)

Each line is one deliberate change, the test run, and its result; every file was restored after its run. Script:
`/tmp/.../scratchpad/mutate.py` (outside the repository), run with `PYTHONDONTWRITEBYTECODE=1`. **Found while doing
this:** without that flag, a mutation restored within the same second, at the same file size, left a stale `.pyc`, so
the restored code ran the mutated bytecode. The first run's results were thrown away and all were re-run with bytecode
writing off. One mutation was missed in the first run (first-fill day max instead of min); the test now has a second,
later fill and catches it.

| Criterion broken | File | Test run | Result |
|---|---|---|---|
| 1 bucket cap boundary | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 2 passed in 0.16s |
| 2 open-risk counts all | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 11 passed in 5.24s |
| 4 cap never resizes (proposal kept) | `fno/risk/manager.py` | `test_caps.py` | caught: 1 failed, 22 passed in 0.28s |
| 5 index groups only | `fno/risk/buckets.py` | `test_buckets.py` | caught: 1 failed, 9 passed in 0.17s |
| 5 unlisted structure refused | `fno/risk/buckets.py` | `test_buckets.py` | caught: 1 failed, 8 passed in 0.22s |
| 6 held max loss exit pads | `fno/risk/open_risk.py` | `test_buckets.py` | caught: 1 failed, 13 passed in 0.29s |
| 6 net short tail refused | `fno/risk/open_risk.py` | `test_buckets.py` | caught: 1 failed, 16 passed in 0.38s |
| 7 paper account exact | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 20 passed in 0.16s |
| 7 E1 opens at books size | `fno/composition.py` | `test_paper_account.py` | caught: 1 failed in 0.41s |
| 8 brake amount | `config.yaml` | `test_c5_account.py` | caught: 1 failed in 0.42s |
| 8 restart needs signature | `fno/risk/overrides.py` | `test_c5_account.py` | caught: 1 failed, 27 passed in 0.63s |
| 9 stress line max-loss sum | `fno/risk/stress_line.py` | `test_c5_account.py` | caught: 1 failed, 28 passed in 0.73s |
| 10 unused setting refused | `fno/risk/profile_settings.py` | `test_c5_account.py` | caught: 1 failed, 17 passed in 0.46s |
| 10 every profile checked | `fno/risk/wiring.py` | `test_c5_account.py` | caught: 1 failed, 33 passed in 0.81s |
| 11 Manual unchanged | `config.yaml` | `test_c5_account.py` | caught: 1 failed, 1 passed in 0.49s |
| 12 margin one session (C2) | `fno/risk/margin_age.py` | `test_margin_age.py` | caught: 1 failed, 2 passed in 0.20s |
| 13 C4 bucket breach | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 2 passed in 0.32s |
| 13 C4 old 3-trade check off for books | `fno/checks/validity_limits.py` | `test_validity_caps.py` | caught: 1 failed in 0.19s |
| 13 C4 paper account | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 10 passed in 0.88s |
| 13 C4 held max loss | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 2 passed in 0.31s |
| 13 C4 margin one session | `fno/checks/validity_settings.py` | `test_validity_caps.py` | caught: 1 failed, 12 passed in 0.89s |
| 13 C4 checks its own settings | `fno/checks/validity_settings.py` | `test_validity_caps.py` | caught: 1 failed, 15 passed in 0.92s |
| 1 bucket selector (per bucket) | `fno/risk/caps.py` | `test_caps.py::test_another_bucket_does_not_count_against_this_one` | caught: 1 failed in 0.14s |
| 1B every proposal bucket checked | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 5 passed in 0.15s |
| 1B list of sides read | `fno/risk/profile_settings.py` | `test_c5_account.py` | caught: 1 failed in 0.46s |
| 1B both buckets mapped | `fno/risk/buckets.py` | `test_buckets.py` | caught: 1 failed, 7 passed in 0.16s |
| 3A closed same-session trade counts (C2) | `fno/risk/open_risk.py` | `test_c5_account.py` | caught: 1 failed, 29 passed in 0.81s |
| 3A session = first filled today | `fno/risk/book_view.py` | `test_c5_account.py` | caught: 1 failed, 29 passed in 0.84s |
| 3A same-session choice counts | `fno/playbook/book_effects.py` | `test_c5_account.py` | caught: 1 failed, 29 passed in 0.81s |
| 3A unknown session refused | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 18 passed in 0.17s |
| 3A C4 closed round trip counts | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 3 passed in 0.40s |
| 1B C4 per-bucket group | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 7 passed in 0.68s |
| 3A C4 session from ledger | `fno/checks/validity_account.py` | `test_validity_inputs.py` | caught: 1 failed, 9 passed in 0.25s |
| J105 N1 C4 cap at its limit | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 25 passed in 1.16s |
| J105 N2 C4 bucket on group only | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 28 passed in 1.16s |
| J105 N5 C4 negative held loss | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 29 passed in 1.22s |
| J105 N17 C4 mixed underlyings | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 30 passed in 1.25s |
| J105 N19 C4 proposal on one lot | `fno/checks/validity_limits.py` | `test_validity_caps.py` | caught: 1 failed, 31 passed in 1.20s |
| SF1 C4 muhurat counted | `fno/checks/validity_settings.py` | `test_validity_caps.py` | caught: 1 failed, 20 passed in 1.02s |
| SF1 C2 muhurat counted | `fno/risk/margin_age.py` | `test_margin_age.py` | caught: 1 failed, 6 passed in 0.20s |
| SF2 C4 unsigned restart | `fno/checks/validity_account.py` | `test_validity_caps.py` | caught: 1 failed, 24 passed in 1.11s |
| minor1 stray risk keys | `fno/risk/settings.py` | `test_c5_account.py` | caught: 1 failed, 30 passed in 0.85s |
| minor2 C4 value types | `fno/checks/validity_settings.py` | `test_validity_caps.py` | caught: 1 failed, 32 passed in 1.37s |
| SF6 PCS mapped to the owner's buckets | `config.yaml` | `test_validity_caps.py` | caught: 1 failed, 18 passed in 0.25s |
| SF6 CDS long volatility | `config.yaml` | `test_buckets.py` | caught: 1 failed, 20 passed in 0.31s |
| LC/LP orchestrator mapping | `config.yaml` | `test_validity_caps.py` | caught: 1 failed, 22 passed in 0.26s |

## Sample of real output (owner's step 4)

The app's wired books risk manager (`build_risk_manager(config.yaml)`) on a temporary account, synthetic prices (not a
live chain), margin rows dated the previous session. Each refusal names its rule; the brake engages after a closed loss
of about Rs 1.24 lakh and lifts after a signed `restart_brake` row.

```text

== empty Rs 20 lakh book, one 1-lot short fly: OPEN
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00
  (this trade's B2 maximum loss: Rs 3,354.54)

== 8 short flies open since an earlier session, one more: REFUSED
  bucket_cap: REFUSED - bucket NIFTY/short_volatility: maximum losses Rs 30,190.88 with this trade's Rs 3,354.54 are above the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 30,190.88 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00
  (a 1-lot long fly: Rs 11,133.40)

== 5 long flies opened THIS session, one more short fly: REFUSED
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 59,021.53 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: REFUSED - trades opened this session: maximum losses Rs 59,021.53 with this trade's Rs 3,354.54 are above the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00

== 5 long flies opened AND CLOSED this session (none open), one more short fly: REFUSED
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: REFUSED - trades opened this session: maximum losses Rs 59,021.53 with this trade's Rs 3,354.54 are above the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00

== 14 long flies open since an earlier session, one more short fly: REFUSED
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: REFUSED - all open positions: maximum losses Rs 159,222.12 with this trade's Rs 3,354.54 are above the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00

== closed loss of about Rs 1.24 lakh on 6 Oct (drawdown brake): REFUSED
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: REFUSED - closed equity Rs 1,876,381.76 is Rs 123,618.24 below its high Rs 2,000,000.00; new trades wait for the owner's restart

== after the owner's written restart row of 7 Oct: OPEN
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00
```

<details><summary>The script that produced it</summary>

```python
"""C5 sample output: the app's wired books manager (config.yaml) on a temporary account, synthetic prices."""
import sys, tempfile
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
sys.path.insert(0, "/home/user/trading")
from fno.accounting.ledgers import Order
from fno.books.fills import Fill
from fno.composition import open_account_writer
from fno.config import load_app_config
from fno.constants import BOOK1_RULES, BOOKS, SIDE_BUY, SIDE_SELL
from fno.models import IST
from fno.risk.book_view import load_risk_book
from fno.risk.inputs import SessionTrade, TradeTerms
from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.overrides import OVERRIDE_COLUMNS, overrides_file
from fno.risk.wiring import build_risk_manager
from tests.risk.builders import CHARGES, FLY, LOT, contract, market, open_trade, proposal, short_fly

DAY = date(2026, 10, 14); EXPIRY = date(2026, 10, 27)
PRICES = {(25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0}
root = Path(tempfile.mkdtemp())
(root / "margins.csv").write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,9000,-10270,65000,sample,2026-10-13\nBF,200,3000,10270,65000,sample,2026-10-13\n")
cfg = load_app_config(overrides={"risk": {"margins": {"file": str(root / "margins.csv")},
                                           "stressed_margin": {"as_of": "2026-10-14"}}})
manager = build_risk_manager(cfg, root)
m = market(25000, PRICES, EXPIRY, day=DAY)
for b in BOOKS:
    with open_account_writer(b, root) as w:
        w.start(date(2026, 9, 1))
book = load_risk_book(root, BOOK1_RULES, m, {})

def show(title, decision):
    print(f"\n== {title}: {'OPEN' if decision.ok else 'REFUSED'}")
    for v in decision.verdicts:
        if not v.ok or v.rule in ("bucket_cap", "open_risk_cap", "new_risk_per_day", "drawdown_brake"):
            print(f"  {v.rule}: {'ok' if v.ok else 'REFUSED'} - {v.reason}")

new = lambda lots=1, tid="new": proposal(tid, FLY, 200, short_fly(25000, 200), EXPIRY, lots=lots)
one = manager.evaluate(new(), book, m)
show("empty Rs 20 lakh book, one 1-lot short fly", one)
loss = next(v for v in one.verdicts if v.rule == "max_loss_per_trade").numbers["max_loss_rs"]
print(f"  (this trade's B2 maximum loss: Rs {loss:,.2f})")
cash = one.entry_cash_rs
from fno.constants import STRUCTURE_LONG_IRON_FLY as LONG
long_fly = [(k, kind, -side) for k, kind, side in short_fly(25000, 200)]
long_cash = manager.costs.entry_cash_flow(proposal("l", LONG, 200, long_fly, EXPIRY), m)
def held(n, structure=FLY):
    legs, flow = (long_fly, long_cash) if structure == LONG else (short_fly(25000, 200), cash)
    return tuple(open_trade(f"{structure}{i}", structure, 200, legs, EXPIRY, flow) for i in range(n))
def today(trades):  # these trades were first filled this session
    return tuple(SessionTrade(t.trade_id, ((dict(t.units), t.cash_flow),)) for t in trades)
n_bucket = int((30000 - loss) // loss) + 1
show(f"{n_bucket} short flies open since an earlier session, one more", manager.evaluate(new(), replace(book, open_trades=held(n_bucket)), m))
long_loss = manager.evaluate(proposal("l", LONG, 200, long_fly, EXPIRY), book, m).verdicts[2].numbers["max_loss_rs"]
print(f"  (a 1-lot long fly: Rs {long_loss:,.2f})")
fresh = held(int((50000 - loss) // long_loss) + 1, LONG)
show(f"{len(fresh)} long flies opened THIS session, one more short fly", manager.evaluate(new(), replace(book, open_trades=fresh, session_trades=today(fresh)), m))
closed = today(held(int((50000 - loss) // long_loss) + 1, LONG))
show(f"{len(closed)} long flies opened AND CLOSED this session (none open), one more short fly", manager.evaluate(new(), replace(book, session_trades=closed), m))
many = held(int((150000 - loss) // long_loss) + 1, LONG)
show(f"{len(many)} long flies open since an earlier session, one more short fly", manager.evaluate(new(), replace(book, open_trades=many), m))

with open_account_writer(BOOK1_RULES, root) as w:
    when = lambda d: datetime(d.year, d.month, d.day, 15, 15, tzinfo=IST)
    c = contract(25000, "CE", EXPIRY)
    w.apply_fill(Fill.priced("f1", "loser", when(date(2026, 10, 5)), c, Order(SIDE_SELL, 100.0, LOT, 0.0), CHARGES))
    w.apply_fill(Fill.priced("f2", "loser", when(date(2026, 10, 6)), c, Order(SIDE_BUY, 2000.0, LOT, 0.0), CHARGES))
braked = load_risk_book(root, BOOK1_RULES, m, {})
show("closed loss of about Rs 1.24 lakh on 6 Oct (drawdown brake)", manager.evaluate(new(), braked, m))
overrides_file(root, BOOK1_RULES).write_text(",".join(OVERRIDE_COLUMNS) + "\n2026-10-07,restart_brake,reviewed the 6 Oct loss,owner\n")
show("after the owner's written restart row of 7 Oct", manager.evaluate(new(), load_risk_book(root, BOOK1_RULES, m, {}), m))
```
</details>

## Tests changed, and why (not weakened)

- C2's old limit tests (`tests/risk/test_settings.py`, `test_manager.py`) now test the Manual profile, which keeps
  them; the books' rule list is asserted exactly.
- C4's existing tests run on the Manual profile (its old checks, Rs 5 lakh fixtures); the books are in the new
  `tests/checks/test_validity_caps.py`.
- `tests/books/test_paper_account.py`: the committed books really were opened at Rs 5 lakh on 13 Oct; the test says so
  and asserts it differs from the books' account.
- `tests/risk/test_books.py`, `tests/checks/test_validity_limits.py`: brake cases at Rs 1,20,000.
- E4, E6, P10 tests: Rs 20 lakh cash; Home's `limit_max` is now the books' open-risk cap (Rs 1,50,000) instead of C2's
  stress limit, which the books no longer have.

## Known limits (said plainly)

1. **Every book trade is refused today**, by design: the books opened at Rs 5 lakh (the "2 B" top-up story fixes it) and the margins file
   has no rows.
2. **Bucket side comes from the recorded structure code**, not from the legs; a wrong code in a decision record would
   put a position in the wrong bucket. C4 shape checks tie the code to the legs at entry.
3. **New risk is rebuilt from the ledger's fill times.** A state after a fill time that is not defined risk (a
   partial fill that left a short leg unprotected) makes the new-risk cap refuse for the rest of that session (fail
   closed). E4 fills protection first and all legs at one snapshot, so this should not happen; reasoning only.
4. **Open trades' maximum loss is recomputed from the ledger** and can rise after a partial exit (hand check: a short
   fly with its short call bought back holds a put spread with Rs 12,350 maximum loss against Rs 2,600 at entry). The
   caps count that real number. It needs a quote for every held contract (C2 accepts a stale mark).
5. **Records written before C5** have no `session_trades` and are refused by the new-risk cap on replay.
6. **C4 needs a two-sided quote** for every held leg (caps and margin room); C2 does not. C4 is the stricter, so a
   thinly quoted wing refuses the whole book's entries that day.
7. **VIX +50% is each leg's implied volatility x 1.5** (no smile change); "+5%" keeps volatility unchanged.
8. **S1's protocol text** (`catastrophic_loss_book`: "Rs 30,000") is not edited, as instructed.

## Owner decisions (all five answered on 15 Oct 2026, rows on main 665c835)

1. Directional spreads: **"1 B"**, both buckets, full maximum loss in each. Built (addendum 1).
2. Books opened at Rs 5 lakh: **"2 B"**, a dated Rs 15 lakh top-up entry; separate story `story/e1-topup`.
3. Same-session round trips: **"3 A"**, they count. Built (addendum 1).
4. Stress-line assumptions: **"4 A"**, accepted, information only.
5. Stocks: **"5 A"**, wait for A18.

## What the judge should test hardest

- Each cap at its number and Rs 0.01 over with real B2 maximum losses, in C2 and in C4.
- A two-sided position against proposals sharing one or both of its buckets; a round trip closed this session.
- `HeldMaxLoss` and C4's `held_max_loss` after partial exits and with unequal units.
- That a broken Manual profile, a missing books setting, or an unused setting stops start-up in both C2 and C4.
- That nothing in `fno/` sizes the books on Rs 5 lakh, and the committed Rs 5 lakh books are refused.
