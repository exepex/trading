# Response 180: story S6 code, scorecard measures (claims for the judge)

Branch `story/s6-scorecard-measures`, built on S3 (`story/s3-scoreboard-a`, judge 191 addendum 1 PASS) and main. The text
passed in judge 158 addendum 1. Builder: session 0185gR5DmoDh2zBAvgRU4CEB, 15 Oct 2026. Lane 1. The S6 commits are those
after the S3 merge (`git log origin/story/s3-scoreboard-a..HEAD`).

## What was built, by story section

| Section | Code | Tests |
|---|---|---|
| 1. S1 items | `research/evaluation/PROTOCOL.md`: `do_nothing_benchmark`, `scorecard_measures`, `t_check`, `missed_runs` and `random_control`, decided 15 Oct with their numbers as proposals. `fno/evaluation/protocol.py` `REQUIRED_ITEMS`. Open question 2 is closed. S3's series and Holm wording is added. `frozen_files`' scoring-code sentence now names S6. | `tests/evaluation/test_completeness.py` (each item required; S1's decided list updated) |
| 2. Trade measures | `fno/scoreboard/trade_measures.py`, in every S2 section as `measures` | `test_scorecard_measures.py` (criteria 2-3) |
| 3. t-check | `fno/scoreboard/t_check.py`, in `uncertainty.t_check`; a disagreement is appended to the reason; `claim_allowed` never changes | same (criterion 4, uneven block risk, 39/40/45 sessions) |
| 4. Do-nothing | `fno/scoreboard/do_nothing.py`: views (a) and (b), F&O tax per financial year, the fund taxed once with its exemption, cash at slab; `ArchivedIndexLevels` (NSE's index-close files in Drive's raw area via `read_index_figures`); the capital path from held trades; `strategies` per book and version | `test_do_nothing.py` (criteria 5, 6, 8; real NSE files 7-13 Oct 2026, literal hand figures); `test_whole_system_measures.py` (criteria 7, 11, 12) |
| 5. Missed runs | `CommittedRuns.missed_runs`; per book and at the board's top level | `test_missed_runs.py` (criterion 9; a real NSE holiday, 2 Oct) |
| 6. Random control | `fno/scoreboard/random_control.py`, on judged sections and segments | `test_random_control.py` (criterion 10; an exact two-twin percentile from the seeded stream) |
| S3 criterion 5 | `fno/scoreboard/matched_measures.py`: measures and view (a) on scoreboard A, with one-lot capital = the record's capital ÷ its lots | `test_matched_board.py` |

## Decisions made in code (judge, please check)

1. **Cash rate:** a proposal of 5.5% in `Terms.cash_rate`, labelled on the board. I do not know the RBI repo rate of
   October 2026. The protocol now says the freeze-day rate is written there and in the protocol, and it is hashed
   with the scoring code.
2. **AI cost:**
   - A part of a book (segment, unscored, overridden, strategy version) has no share of the book-level AI cost. Its
     do-nothing verdict therefore stands only when the book's AI cost is zero (Book 1), and is null otherwise. This is
     never counted twice.
   - Scoreboard A carries no operating or AI cost: it is one lot with no account, so its verdict stands for every book.
     This is stated in `matched_measures.py`.
3. **The random control's own risk** is B2's model on the real legs at the entry snapshot's touch, the same basis as
   its twins. The record's figure is priced at the pack's mids and would never tie the trade's own twin.
4. **Missed runs:**
   - The report day before its run is not listed.
   - An exits step whose result for the book is `error` or `waiting` is a missed exit review. This is the daily run's
     own rule (daily_run.py:98-117).
5. **Drive unreachable:** the index source names that cause instead of "index day missing".

## Gates

- **pytest:** see the message to the judge (run on the final tree).
- **ruff check and format:** clean. **check_imports:** clean.
- **File size:** every file is under 350 lines. The largest new one is `do_nothing.py` at about 160 lines.
- **S2's tests:** unedited.
- **Broken-code proof:** 28 mutations, all caught, across the measures, the t-check, tax, the exemption, the
  financial-year split, missing index days, zero capital-days, the AI verdict, idle credit, missed exits, the report
  day, strategy reconciliation (an unwound entry), ties, the bucket, the window, the 10% missing boundary, the
  one-lot capital, the own-risk basis, the segment AI rule and the brake share.
  - Two survived at first and were fixed: the t-check data happened to give equal spreads with and without the
    linearisation, and the fixture had no unwound entry.

## Self-review

One independent agent found 1 must-fix and 8 should-fix points:
- **Fixed:** items 1-6 and 8. Its view (a) figures (1,376 / 462.86 / 62.20) match the literal test values.
- **Partly fixed, item 7:** the cash rate's place at the freeze is now stated. The `frozen_files` explicit list is
  completed at the freeze (option A); the freeze reads explicit paths, not globs.
- **Stated, item 9:** twins exit at the real exit day's snapshot, so a real trade settled at expiry or exited by E4's
  retry has its twin valued at that day's quotes. This is a known limit.

The catch-up exit "dated that day" is E3 and E4's behaviour, already tested in `tests/desk/test_exits.py`. S6 only
lists the miss.

## Known limits

- Do-nothing is a point comparison. The trailing-yield total return is approximate (some evidence). The tax figures
  are the owner's scenario.
- View (a)'s capital at entry is not re-margined (it leans for the book); view (b) does not have this bias.
- The random control replays the per-trade and bucket caps only. It holds the real dates (selection luck only), and
  its twins exit at the real exit day's quotes.
- No real paper decision exists yet, so every real board today is empty ("not started").

## Revision 1: judge 196 (FAIL at a9f745bf), both should-fixes and both notes

All four points were checked against the code first, and all were found correct. Each fix is verified by a mutation
that now fails a test.

1. **The cash rate can no longer be frozen silently.**
   - `PROTOCOL.md` now states "cash rate = 5.5% a year (set at the freeze)".
   - `undecided_items` (fno/evaluation/completeness.py) treats any item whose value carries the "(set at the freeze)"
     marker as not decided. Because of that, `evaluation check --decided` and the freezer both refuse it, and both
     name `do_nothing_benchmark`.
   - A test keeps `Terms.cash_rate` equal to the protocol's number: `test_the_cash_rate_in_the_code_is_the_protocol_s_number`.
   - Refusal tests: `test_a_decided_item_whose_value_waits_for_the_freeze_day_is_not_decided` and
     `test_a_decided_protocol_with_a_number_still_marked_for_the_freeze_day_is_never_frozen`.
   - Mutation check: dropping the marker check fails 4 tests.
   - The marker is generic, so any later freeze-day number uses the same guard.
2. **The three test gaps are closed. The judge's three surviving mutations now each fail:**
   - **t-check:** 7 big losing sessions are placed before the 6 known blocks, and the bound equals the 6-block answer
     with `left_out == 7`. Keeping the oldest sessions instead fails.
   - **Bucket redraw, end to end:** a one-strike snapshot makes every unflipped twin tie the book. A bucket too small
     for a long put must redraw every flip, so the percentile is 0.5. With room in the bucket it rises above 0.5.
     Removing `_bucket_room` from `_twin` fails.
   - **Window boundary:** with the money at 25,000 and 50-point steps, 24,500 and 25,500 are in the window, while
     24,450 and 25,550 are out unless 25,550 is the real trade's strike. Changing `<=` to `<` fails.
3. **Note 1 (view (a) on scoreboard A):** the output now carries `capital_cut`, which counts the takes whose exit falls
   after the series' last day and says view (a) flatters the book for them. It is empty when nothing is cut. Tested
   both ways. I labelled it rather than extending the capital path: extending it would need index days beyond the
   series and a second timeline, and view (a) on A is descriptive (RM1 reads scoreboard B).
4. **Note 3 (fixtures):** the 12 and 13 Oct fixtures are now the archived bytes, taken from Drive's raw area. Their
   SHA-256 values are fc847998… and a402bb45…, equal to `research/data/manifests/index-close.csv`. A new test pins all
   five fixtures to the manifest. Their "Nifty 50" rows are unchanged, so every figure stands.

The branch also merges main (433845b8 and later). Gates on the merged tree:
- `pytest -q -n auto`: 6,641 passed, 0 failed, 0 skipped;
- ruff check and format are clean;
- the import check is clean.

## Revision 2: ChatGPT review 120 (PARTIAL), as accepted in response 200, for S3 and S6

Review 120 is not committed on any branch, so the source is response 200. I checked each point against the code before
changing anything, and every point holds:
- **Fix 1:** `_apply_holm` built its family from eligible claims only, so its size moved with eligibility.
- **Fix 2:** `_misses` put every D6-unscored day outside the miss cap. D6 "unscored" is one book's own AI-model
  fallback (docs/stories D6, rules 2-3).
- **Fix 3:** `_reviewed` treated `{"reviewed": false}` without an error, or a book missing from the exits result, as
  reviewed. E3 writes `reviewed: True` or `False` on every outcome (`fno/desk/daily_steps.py:199-212`).
- **Disclosure 4:** "inputs" fails only with "is already open in" today (`fno/risk/manager.py:58`, its only failing
  verdict).

**Fixes:**
1. **Fixed Holm family** (`matched_board._apply_holm`): it holds each book's head-to-head claim and every directional
   pair; with three books that is 9. A member that cannot be tested (sample not met, no p-value, or incomplete) enters
   with p = 1, and `holm_family` is written on the board. Test: book x at p = 0.006 fails 0.05 / 9 whether pair y - z is
   testable or not; a family of eligible claims only (8) would pass it.
2. **Book-specific unscored days are misses** (`_misses`): an unscored day counts as a miss when another book was
   scored on the same common pack. A day unscored for every book stays apart. Test: Book 1 unscored while Book 2
   submits gives 2 eligible days and 1 miss; the existing test keeps the all-unscored case apart.
3. **`_reviewed` requires `reviewed is True`.** Test: `reviewed: false` with no error, and a book missing from the
   exits step, are both missed exit reviews. The existing tests now use E3's real outcome shapes.

**Disclosures:**
4. **Refusal reasons and the board label.** A take refused only by account limits lists each original refusal, for
   example "account limit only (bucket_cap: over by 2,000; margin_room: short)". "inputs" counts as an account limit
   only with its "already open" reason; any other "inputs" failure is a skip (new fixture). The board carries
   `"label": "hypothetical one-lot idea quality"`.
5. **Staggered exits and no-fill share.** `StandardResult.staggered` is set when legs exit on different sessions. Each
   section reports `staggered_exits` (count and holding days) and `no_fill_share`.
6. **After the cut.** Each section has `after_cut`, labelled "not a claim":
   - later closed takes and their provisional net;
   - unresolved takes and their age in calendar days;
   - `incomplete` when a take is open past its expiry without a settlement price
     (`StandardResult.past_expiry`). An incomplete section gets `claim_allowed` False, an "incomplete" reason, and
     p = 1 in Holm.
7. **Ratios beside the rupee result.** Each pair carries `net_per_risk` for both books on its shared days, with a label
   saying the rupee result is never a risk-adjusted verdict.
8. **View (a) withheld when capital is cut.** When `capital_cut` is nonzero, scoreboard A's view (a) keeps its
   figures, but `beats_*` are null and the reason reads "not comparable: …; RM1 reads scoreboard B's full capital
   path".
9. **Random control.** It shows `flipped_share` (the share of accepted twins in the mirrored direction) and
   `rejected_draws` by reason: not quotable, over the per-trade cap, maximum loss unknown, bucket full. Both appear
   also when the control is not computable. Its label is "feasible-random selection on the same dates …".

**Owner decisions applied:**
- The cash-rate text in `PROTOCOL.md`, `do_nothing.py` and the story is now the owner's 16 Oct rule: the latest 91-day
  T-bill yield on the S1 freeze date, from RBI's auction result, with its date and source written in. The
  "(set at the freeze)" guard stays.
- Tax is labelled "the owner's tax scenario, not a tax determination; checked before RM1".
- `PROTOCOL.md` (`scoreboard_a_standardisation` and `missed_runs`) and the S3 story text state the fixed family and the
  unscored-miss rule. `missed_runs` keeps its 15 Oct owner status: the change refines which unscored days are the
  book's own fault, and the orchestrator is asked to confirm that with the owner.

**Mutations:** each change was broken on purpose, one at a time, and all 16 breaks fail a test: 2 for Holm, 2 for the
miss rule, 1 for `_reviewed`, 2 for the refusal reasons, 2 for staggered exits and no-fill share, 3 for the cut, and 1
each for the pair ratio, "not comparable", the flip share and the bucket reason.
