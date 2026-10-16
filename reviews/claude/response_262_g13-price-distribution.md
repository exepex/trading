# Response 262: story G13, the daily valuation record and NIFTY price-distribution forecasts (builder's claims)

Builder: session_01UkTaDeTRF9ksDgQB9cTU5C · Story: `docs/stories/G13-price-distribution.md` (text PASS, judge 304
addendum 1, at 85eba3a8) · Branch: `story/g13-price-distribution` · Judge: E · Lane 1.

## Verdict first

Everything in the story is built and tested:
- **Valuation record:** parity forward, ATM IV, delta surface, skew, term structure, the Breeden-Litzenberger
  distribution with anchored lognormal tails, and smile values.
- **Forecasts:** three NIFTY quantile forecasters at four horizons, plus two AI slots.
- **Scoring:** quantile scores, calibration and the bootstrap comparison.
- **Back-fill** from the 3 pm chains and from the end-of-day panel, and **O1's `price_distribution` step**, not live
  (`daily.live_from.price_distribution: null`).

Evidence:
- **Tests:** 106 G13 tests. The full suite passes on the pushed tree: 7,841 passed.
- **Mutations:** all 38 planted mutations are caught (table below).
- **Real chain:** the real 16 Oct NSE chain reproduces the text's probe exactly.
- **History:** the exploratory end-of-day back-fill over 1,918 sessions (2019 to Oct 2026) gives the desk its first
  price-range evidence (section "What the data says").

## Criteria: code, test, broken-code proof

"Mutation" is the code change planted by `scratchpad/mutate.py` (session scratchpad, not committed); every one made
its test file fail, and the file was restored.

| # | Criterion | Code | Tests | Mutation caught |
|---|---|---|---|---|
| 1 | Forward and filter | `forward.py:12`, `chain.py:61`, `valuation.py` `value_expiry` | `test_chain_forward.py` (7, incl. at/just over 10% and Rs 0.50, invalid, one-sided, expiry on the day, empty, no pair) | forward without `e^{rT}`; `>` to `>=` at the spread limit |
| 2 | ATM IV and surface | `surface.py:48`, `:58` | `test_surface.py` (hand ATM, tie to the lower strike, delta interpolation, outside range missing, RR/fly, flat no skew) | tie to the higher strike; extrapolating a delta point |
| 3 | Term structure | `valuation.py:84` (frozen `interpolate_30d`, imported) | `test_surface.py::test_the_30_day_iv_...` (bracketed and flagged) | ATM points x101 |
| 4 | Distribution | `density.py:56, 71, 115, 123, 135` | `test_density.py` (13) and `test_real_chain.py` (fixture) | gap rule off; gap-weighted pooling; log-strike interpolation; tail without its anchor; mean limit x10; 7 points allowed; forward from 5 strikes (fixture) |
| 5 | Smile value | `smile.py:55, 66` | `test_smile.py` (flat = mid within Rs 0.01, one planted contract alone outside, 5/4/0 points, note) | 4 points allowed; inside-spread always true |
| 6 | Forecasters | `forecasters.py:80, 115, 129`, `horizons.py:55`, `records.py:77` | `test_forecasters.py` (12), `test_build_records.py` | no median centring; 20 closes allowed; 499 returns allowed; weekday count ignoring the holiday; a tied quantile accepted; not_started for a rule forecaster |
| 7 | Point in time | `build.py:52`, `build.py:87` | `test_build_records.py::test_no_close_on_or_after_the_day_is_read` and the stale-closes tests; `test_recorder.py` (only the day's chain asked) | `<` to `<=` on closes; stale check off |
| 8 | Labels and regeneration | `backfill.py:30`, `folders.py`, `recorder.py:53` | `test_backfill.py` (6), `test_recorder.py` | no stop before live; gzip with a time stamp; path without the content digest; hand run allowed live |
| 9 | Daily step | `fno/daily/wiring.py:22, 61, 90`, `constants_operations.py:55`, `config.yaml:206` | `test_daily_step.py` (5) and O1's own tests (3 extended, nothing loosened) | pathspecs widened to `receipts/` |
| 10 | Storage | `store.py`, `recorder.py` (already recorded) | `test_recorder.py` (never rebuilt, lost receipt restored, Drive failure leaves no receipt) | the already-recorded branch off |
| 11 | Scoring | `scoring.py:10`, `score_report.py:41, 75, 96` | `test_scoring.py` (11) | pinball as absolute error; scoring non-ok rows; pooling labels |
| 12 | Failures | `recorder.py`, `sources.py:36` | `test_recorder.py` (14), `test_sources.py` (2) | partial exit 0; missing record not written; not-live check; build failure not contained; unreadable written as missing; no source fallback |
| 13 | Indices | `build.py:55` | `test_build_records.py::test_an_index_gets_a_valuation_and_no_forecasts` | forecasts for every underlying |
| 14 | No frozen file changes | none edited; nothing added to `fno/forecast/` | the existing freeze tests, unedited, in the full suite | n/a |
| 15 | Real output | below | `test_real_chain.py` | n/a |

Positive, negative, boundary and empty cases: each test file's docstring names its cases; the boundary cases are the
spread limit (at, just over), Rs 0.50, 8 vs 7 CDF points (9 vs 8 strikes), 5 vs 4 smile points, 21 vs 20 closes, 505
vs 504 closes (500 returns), a mean 0.42% vs 0.55% off, the live date itself, and the 40-day bootstrap minimum.

## Builder self-review (quality rule 3)

One independent correctness and silent-failure agent read the whole diff. It found no math error and no look-ahead
(it re-ran the tails' inverse, the exact mean and the flat-chain round trip itself). Its findings and what I did:

1. **Stale closes never reported** (should-fix). **Accepted:** story section 7 lists "the closes file missing a session
   needed". Now, when the last close is not the previous regular session, `rv20` and `hist750` are `missing` ("closes
   stale: ...") and the step fails with one alert (`build.py:87`).
   - Its add-on, also alerting a horizon past the calendar's end: **rejected**. The judged text makes that
     `not_eligible` (never guessed), and O8b already alerts once when the calendar nears its end.
2. **A passing Drive failure became a permanent `missing` day; NSE never tried** (should-fix). **Accepted, both
   parts:**
   - A source that cannot be read is passed over and named (`source_note`), so NSE's chain is used.
   - An unreadable chain writes no file and exits 1, so a rerun records it. Only a chain never captured gets a
     `missing` record.
3. **One build exception lost every underlying's file** (should-fix). **Accepted:** each record is written as soon as
   it is built, and a `ValueError` or `ArithmeticError` (a refused row, a NaN) is contained to its underlying, with no
   file, so it can be retried.
4. **A back-fill rerun with a changed calendar conflicted** (should-fix). **Accepted:** the file name now carries the
   payload's SHA-256, so new inputs go to a new path.
   - Its minor note on zlib builds: **noted, not changed.** A different zlib could compress the same content to other
     bytes. That gives a loud `RawFileConflict`, never a silent change.
5. **`not_started` refused** (should-fix, criterion 6's text). **Accepted:** `not_started` is a status for the AI slots
   only (`records.py:77`), tested both ways.
6. **Back-fill printed no counts for written problem days** (minor). **Accepted:** it prints counts per kind.
7. **Bootstrap seed depended on group order** (minor). **Accepted:** the comparison number is derived from (label,
   method, horizon, baseline) (`score_report.py:96`), tested.
8. **Spec and code differences** (minor):
   - (a) One line per problem: **accepted**, each problem is printed.
   - (b) A hand run on the live day wrote `live`: **accepted**. `record` writes live rows only with `--live`, which
     only O1's step passes.
   - (c) The back-fill file name is `<underlying>_<first>_<last>_<digest>.json.gz`, not the text's
     `<underlying>_<YYYY>.json.gz`: **kept, and said here.** A yearly file would grow as days arrive, and Drive is
     write-once, so the run's range plus its content hash is the write-once form.
   - (d) The panel keeps an expiry on the day itself: **kept**, as A4 does (`fno/quotes/recorder.py:65`, `e >= today`);
     the record makes it `not_eligible`.
9. **Thin index chains may fail the step daily** (note). **Agreed, untested:** A4c's first data is 19 Oct. I will
   read the first A4c days before anyone sets `live_from`, and report it (below, open points).

## Real output sample (quality rule 6)

Made by the committed code: `python -m fno pricedist value --day 2026-10-16 --source nse --dry-run`. It writes
nothing. It uses NSE's public chain, committed in the repository: index levels only, no strategy and no Groww value.

| 16 Oct 2026, 14:54 NSE chain | 27 Oct (11 days) | 23 Nov (38 days) |
|---|---|---|
| Parity forward / future last | 23,121.96 / 23,122.0 | 23,225.22 / 23,225.0 |
| Quotes used / dropped | 94 / none | 93 / 1 invalid |
| ATM IV | 11.85 | 12.73 |
| IV 10P / 25P / 25C / 10C | 14.64 / 12.81 / 11.37 / 11.62 | none / 14.46 / 11.91 / none (outside the quoted deltas) |
| 25-delta risk reversal / butterfly (points) | -1.44 / +0.24 | -2.55 / +0.45 |
| Implied 5% / 50% / 95% | 22,263 / 23,147 / 23,822 (all body) | 21,500 (tail) / 23,330 / 24,691 (tail) |
| Raw CDF decreases fixed | 3 | 10 |
| Mean minus forward | +0.013% | +0.103% |
| Smile fit RMSE (IV points) | 0.20 | 0.06 |

The 30-day ATM IV is 12.64 (not flagged). `rv20` is 15.54, so near ATM IV minus `rv20` = **-3.69 points**: options are
priced below the last 20 days' realised movement.

NIFTY's 5% to 95% ranges for the near expiry (27 Oct):
- `implied`: 22,263 to 23,822.
- `rv20`: 22,210 to 24,033.
- `hist750`: 22,391 to 23,850.

**One weakness to state plainly.** The quadratic smile misses the quotes by about 0.2 IV points on average (RMSE).
That is wider than NSE's 5-20 paisa spreads, so 75 of 94 near-month contracts show `smile_value_inside_spread:
false`. That flag carries little information on NSE's tight books. `smile_gap_iv_points` is the useful number, and
the record says it is no trade signal. A tighter curve (SVI or a spline) would be a new method version, for the
owner to ask for, not built here (reasoning only).

## What the data says (desk view; exploratory, `backfill_eod`, never pooled with live)

The end-of-day panel 2 Jan 2019 to 15 Oct 2026 was built in memory with the committed method (scratch script). It
covers 1,918 sessions built and 22,242 resolved rows; nothing was written to Drive. The real back-fill runs into Drive
after the merge (judge rule 8). Units: QS (quantile score), lower is better, in log return.

| Horizon | `implied` QS | `rv20` QS | `hist750` QS | `implied` 90% band holds the close | `implied` minus `rv20` (p) | minus `hist750` (p) |
|---|---|---|---|---|---|---|
| h1 | 0.00421 | 0.00439 | 0.00456 | 91% | -0.00010 (0.025) | -0.00021 (0.045) |
| h5 | 0.00971 | 0.01026 | 0.01035 | 89% | -0.00032 (0.011) | -0.00031 (0.044) |
| e1 | 0.01420 | 0.01477 | 0.01569 | 88% | -0.00037 (0.051) | -0.00107 (0.009) |
| e2 | 0.02601 | 0.02727 | 0.02822 | 88% | -0.00016 (0.701) | -0.00099 (0.141) |

(These numbers are from method hash `514e3e0e`, before the review fixes. The fixes change no value on complete
end-of-day data: there were no stale closes and every chain was readable. The method hash changed.)

By role:
- **Statistician (some evidence):** `implied` has the lowest quantile score at all four horizons. This is overlapping,
  end-of-day, exploratory data with a block-20 bootstrap and 8 comparisons with no multiplicity control, so it is a
  lead, not a claim. The e2 differences are not distinguishable from zero.
- **Volatility trader (some evidence, against my own prior in the story text):** the text expected implied quantiles
  to be "too wide on average". On these data they are not: the 90% band held the close 88-91% of the time, about right
  or slightly narrow. The volatility risk premium shows up in IV-versus-RV levels, not in a too-wide price range. On
  16 Oct itself, implied was 3.7 points below `rv20`.
- **Risk manager (reasoning only):** 88% coverage at e1/e2 means NIFTY ended outside the implied 90% band about 12% of
  the time. A short strangle sold at those strikes would be breached more often than "10%" suggests. Any option-selling
  idea must size for that, not for the nominal level.
- **Red team:** 2020's crash months lose many distributions ("no implied volatility at the lower edge", missing
  distributions for the Mar-Jun 2020 expiries), so the hardest days are under-scored. A score without the crash is
  flattering. Live 3 pm data will tell more than end-of-day closes.

## Deviations from the text, said plainly

- The back-fill file name (finding 8c) and the `--live` flag (8b), as above.
- The record adds `source_note` (finding 2). The story's row columns are all present.
- **A chain that was recorded but cannot be read (Drive down), or a build that fails, writes no file for that
  underlying** (findings 2 and 3; judge 310 minor 3). The text says every failure writes a `missing` record. A
  write-once file for a failure that may pass would turn a one-minute Drive outage into a lost day. So only a chain
  never captured gets a `missing` record. The other two fail the step (exit 1, one alert) with the reason, and a
  rerun records the day.
- O1's own tests were extended for the new step, nothing loosened:
  - `tests/daily/test_day_run.py`: the fake steps, the call lists and a rerun's calls;
  - `tests/daily/test_steps.py`: the live dates;
  - `tests/health/test_desk_and_data_checks.py`: the steps not run.
- **O1's owner reviews the `fno/daily/`, `constants_operations.py` and `config.yaml` diff (agreed, 16 Oct).**
- CLAUDE.md's composition-root list adds `fno/price_distribution/wiring.py` (the story said so).

## Judge 310 (FAIL at 794877c2, 1 should-fix, 3 minor): answers

Each was checked against the code before it was fixed; all four are correct.
1. **Should-fix: a rerun turned a problem day into `ok`. Accepted.** The judge is right. `record()` saw any existing
   live file as "already recorded" with no problem, so O1's rerun of a failed step exited 0 and O8 saw a good day.
   - Now a stored record's `problems` (a stored `missing` record included) count again: `<underlying>: already
     recorded with N problems`, and the last line `written with problems: ...`, exit 1.
   - Test: `test_recorder.py::test_a_rerun_of_a_problem_day_still_fails_with_the_stored_problems`.
   - Mutation (stored problems dropped): caught.
2. **Minor 1: the 200-point boundary and the [0, 1] clip were untested. Accepted.**
   - `test_density.py::test_a_pair_exactly_200_points_apart_still_forms_a_midpoint` (200 kept, 250 dropped).
   - `::test_pooled_values_are_clipped_to_zero_and_one`: raw CDF -0.58 and 1.58; the stored points start at 0.0 and
     end at 1.0.
   - Both mutations (`<=` to `<`, the clip removed) are caught.
3. **Minor 2: a refused row stopped a whole back-fill range. Accepted.** A `ValueError` or `ArithmeticError` skips
   that day only, counted as `build failed (...)`.
   - Test: `test_backfill.py::test_a_day_whose_build_fails_is_skipped_and_counted_the_rest_are_written`.
   - Mutation: caught.
4. **Minor 3: the deviation is now listed** under "Deviations".

Mutations now: 42 planted, 42 caught. G13 tests: 111.

## Gates (on the pushed tree)

`ruff check fno tests tools` clean; `ruff format --check` clean; `tools/check_imports.py` clean;
`tools/check_records.py` clean; full suite `python -m pytest -q -p no:cacheprovider -n auto`: **7,841 passed**, 2
warnings, 0 failed (code at fb0efca5; this file is the only change after it).

## Open points

1. After the merge, as the merger (orchestrator's instruction, 16 Oct):
   - run the real back-fills into Drive (`pricedist backfill --source eod` 2019 to 2026, and `--source 3pm` 14-16
     Oct), commit their receipts, and score them once (rule 8);
   - record the command and result in the conversation log.
2. Before the owner sets `daily.live_from.price_distribution`, read A4c's first index chains (19 Oct on) for thin-chain
   failures (finding 9) and report.
3. The rate stays config's 6.5% until A21 lands (orchestrator, 16 Oct), then a new `method_version`.
