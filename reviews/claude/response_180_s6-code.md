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
