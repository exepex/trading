# Response 122: story A16b, NIFTY 15-minute candle back-fill (build claims)

Branch `story/a16b-candle-backfill`, code at the SHA given in the message to the orchestrator (this file is in it).
The story text passed at 1c9c5c3 (judge 122 addendum 4) and 1109296 (addendum 5). Quality rule 9: no money path, so no
ChatGPT review (stated, not skipped). Evidence labels: **strong** (test or real run), **some** (partial data),
**reasoning** (no data).

Decisions applied:
- **Decision 53:** A16's NSE-open finding. Out of scope here; the step-0 recount stands.
- **Decision 55:** every session with 25 candles is checked against its own 1-minute candles at all 26 marks, within
  0.05.
- **Decision 56:** a back-filled row is never a live forecast input. Each row carries `provenance` (A17's
  `provenance()`, imported); the README says so in bold; using the rows is G6's job.

## What was built

`python -m fno intraday backfill [--from] [--to] [--dry-run FOLDER]` and `python -m fno intraday backfill-verify`.

New modules in `fno/intraday/`:

| Module | Job |
|---|---|
| `candle_levels.py` | the 26 levels (09:15 open + 25 closes) |
| `minute_check.py` | the 1-minute check |
| `nse_range.py` | the NSE range check |
| `nse_days.py` | `NseDays` interface; NSE files via A1's library: absent vs failed |
| `candle_source.py` | `IntradayCandleSource` interface; `GrowwCandleSource` over `ReadOnlyGroww`, paced |
| `candle_archive.py` | raw answers to Drive; per-kind manifests |
| `candle_rv_table.py` | the row table |
| `deferral_log.py` | deferred sessions |
| `session_deriver.py` | one row from its copies, pure |
| `previous_close.py` | one rule for the run and verify |
| `backfill.py` | the run |
| `backfill_verify.py` | `backfill-verify` |
| `backfill_report.py` | the printed report |
| `backfill_cli.py` | the CLI |
| `dry_run.py` | the dry-run folder rule |
| `backfill_wiring.py` | composition root, added to CLAUDE.md |

Tests are in `tests/intraday_backfill/`: 86 tests. The largest file is `backfill.py` at 200 lines.

## A16 files changed: more than the story said (stated plainly)

The story text says the allow-list constant is "the only line of A16's code this story touches". That is not true of the
build. Every other change is a behaviour-neutral refactor so that A16's rules are shared rather than copied (DRY):

| File | Change | Why |
|---|---|---|
| `read_only.py` | `CANDLE_INTERVAL_MIN_15` added to `CONSTANTS`. No call added (the diff is exactly that, reformatted to fit the line) | the 15-minute interval |
| `realised_vol.py` | the arithmetic moved into `session_rv()`, used by `QuoteSnapshotRv15m` and the new `CandleCloseRv15m` | criterion 4: "they share one function" |
| `rv_table.py` | file layout and columns as class attributes; a `row(day)` read | `CandleRvTable` subclasses it and keeps the write-once rule |
| `session_rv.py` | `_figure` renamed `figure`; a local renamed | the deriver formats figures the same way |
| `cli.py` | registers the two commands; `_inside_repository` moved to `dry_run.py` | shared by A16 and A16b |
| `tests/intraday/test_safety.py` | the composition-root check also allows `backfill_wiring.py` | CLAUDE.md lists it |

A16's `wiring.py` and all of `fno/global_cues/` are unchanged (`git diff origin/main...HEAD` shows no change). The full
suite passes, including A16's tests. **Strong.**

## Real run (rule 6): live, read-only dry run, 1 Jan to 31 Mar 2020

Groww and NSE's archive were read live; every file went to a scratchpad folder; nothing was archived to Drive and
nothing was committed. It took 1 min 56 s. Output, verbatim (counts only):

```
window 2020-01-01..2020-03-30: 1571 of 1575 session candles (63 sessions)
window 2020-03-31..2020-03-31: 25 of 25 session candles (1 sessions)
sessions 64: 64 written now, 0 held before, 0 deferred
void 5 of 64 (7.8%) - above 5%: propose a new version (design 5.2); by reason: {'missing_candles': 2, 'no_previous_close': 3, 'outside_nse_range': 2}
provenance: {'backfilled': 64}
pre-open gap above 0.05 on 1 of 62 sessions with a 1-minute answer: 2020-01-20
void missing_candles: 2020-03-13, 2020-03-23
void no_previous_close: 2020-01-01, 2020-03-16, 2020-03-24
void outside_nse_range: 2020-03-13, 2020-03-23
exit 0
```

- **Verify:** the verify logic over the dry folder's own copies said "64 rows; every row equals its copies". **Strong.**
- **Resume:** a rerun of the same range said "63 sessions already derived, not fetched" and "0 written now, 64 held
  before". **Strong.**
- **What the voids are:**
  - 13 and 23 Mar 2020 are the circuit-breaker days. Each has 23 of 25 candles, and a candle low or high is outside
    NSE's official range (the 23 Mar high is 196.30 points above it, as step 0 found).
  - 16 and 24 Mar follow them, so their overnight part cannot start from an untrusted 15:30 level.
  - 1 Jan 2020 is the series start.
- **Void share:** 7.8% for Q1 2020, above the 5% flag. This quarter holds the crash, so it says nothing yet about
  2020-2026 as a whole (**some**); the full run gives the real share.
- **Not yet done:** the full back-fill run (criterion 14). It runs only after the PASS and merge, under owner rule
  "1 B", as the orchestrator set. Its counts will be added here.

## Criteria: claims and evidence

| # | Claim | Evidence |
|---|---|---|
| 1 | Raw first. A failed call or an unreadable answer defers its sessions and archives nothing. The order rule defers a session whose previous session has no row. A rerun fetches only windows with sessions still to write. A failed middle window resumes with no refusal. Each window line shows its candle count against 25 × its sessions | tests in `test_backfill_run.py`; `test_an_unreadable_answer_...`; the real run above. **Strong** |
| 2 | 26 levels exactly. 09:00, 15:30 and later candles are counted, never used as levels. A missing candle is `None`, never filled. A time with an offset is `CandleParse` | `test_levels_and_checks.py`. **Strong** |
| 3 | Calendar: regular and special sessions get rows; muhurat, holiday and weekend get none. All eight rule-5 sessions give their named reasons. 10 Oct 2025 shape: `missing_candles:25`, and the next session has a void overnight part and a computed intraday part. A year outside the calendar stops with A7's message, exit 1 | `test_the_rule_5_sessions_...` (8 cases); `test_a_session_without_candles_...`; `test_a_day_outside_the_calendar_...`. **Strong** |
| 4 | One arithmetic: `CandleCloseRv15m` equals `QuoteSnapshotRv15m` on the same input and a hand computation (2·ln(1.01)², ln(100/99)², vol 1.7292%). A missing level voids only the part that needs it. Rows are written once, and other inputs are refused | `test_rv_and_rows.py`. **Strong** |
| 5 | NSE range at 0.05 / 0.06. The 23 Mar 2020 shape (one high 196.30 above, every close inside) voids. Pre-open gaps are printed. The 1-minute check is made at 0.05 and 0.06; an exact tick in float noise (18000.15 − 18000.10) is not beyond it. Pacing: no two calls less than 0.5 s apart. Three failures in a row stop the run | `test_levels_and_checks.py`; `test_read_only.py`; `test_backfill_run.py`. **Strong** |
| 5 | The four transient/permanent tests: (1) a Groww 1-minute error defers, and the next run writes it; (2) a received answer missing a minute gives `no_1m_check:1`, and the next session's overnight part is void; (3) an NSE read error defers; (4) NSE absent gives `nse_unchecked`, and the next session's overnight part is void | `test_backfill_run.py`. **Strong** |
| 6 | Provenance comes from A17's `provenance()` with `next_open`. Cases: 18:00 the same day is `live`; 09:14:59 the next session is `live`; 09:15:00 is `backfilled`; across a weekend; across the 2 Oct holiday and the weekend; a special Saturday session is the next open. `first_seen_at` is the latest copy's first fetch time | `test_provenance_...` (8 cases). **Strong** |
| 7 | The void share is flagged above 5%; every void session is listed by reason with its date (short and halted sessions are listed, never excluded) | `test_the_report_gives_...`; the real run. **Strong** |
| 8 | Verify names: a planted change to a row; a copy whose SHA-256 differs; a copy missing from Drive; a row whose copy has no manifest row. It is read-only: no Groww, and no NSE file archived | `test_report_and_verify.py`; `test_the_verifier_is_built_without_groww_...`. **Strong** |
| 9 | No price in any repository file. A test scans every written CSV for every candle value and for price-sized numbers. The real run's files hold counts, times, SHA-256 values, RV and gaps | `test_no_repository_file_holds_a_price`. **Strong** |
| 10 | Read-only: a whole back-fill runs through `ReadOnlyGroww` over a fake SDK whose order, position and margin calls fail the test. The allow-list diff is one constant. The import closure of `backfill_wiring.py` (walked through every `from` import) names no trading call. A planted secret appears in no output or file, even when Groww's sign-in fails | `test_read_only.py`. **Strong** |
| 11 | A run writes only `rv-candle/` under the intraday folder; A16's `wiring.py` is unchanged | `test_the_run_writes_only_its_own_folder_...`; diff. **Strong** |
| 12 | Interfaces: `IntradayCandleSource`, `NseDays`, `IntradayRealisedVol`, wired only in `backfill_wiring.py`. **`CandleArchive` has no interface of its own** (see below) | code; `test_safety.py`. **Reasoning** for the archive choice |
| 13 | Exit 0 only when every requested session has a row. A dry-run folder inside the repository is refused. An unexpected error prints its class name only. The default end date is today only from 21:00 IST | `test_cli.py`. **Strong** |
| 15 | Gates: `pytest -q` 4740 passed; `ruff check` and `ruff format --check` clean; `check_imports` clean; code size passes | run on the merged tree before pushing. **Strong** |

**Criterion 12, the archive (open to the judge).** `CandleArchive` is concrete. What it stores into, Drive, is behind
`RawFileStore`, so swapping Drive is one class plus one line in the root. CLAUDE.md says "never add a pattern without a
second use", and the archive has no second implementation; the tests use the real class over a local folder.
`NseDays` did get an interface, because `FakeNse` is a real second implementation. If the judge reads criterion 12
literally, an archive interface is 10 lines.

## Mutation proofs (rule 4)

I planted 54 mutations, one at a time, against `tests/intraday_backfill`:
- **53 caught** (50 in the first rounds, plus 4 for decision 62 below, all caught; 1 of the 50 is the equivalent one).
- **1 equivalent:** reading the previous close from the earliest copy instead of the previous row's copy. Every row is
  derived from the earliest copy covering its day, so the two are always the same copy; verify independently pins the
  row's own copy.

Every criterion has at least one caught mutation:

| Criterion | Mutations planted |
|---|---|
| Levels | open vs close; candle set shifted by one; 24 candles |
| Tolerance | `>=`; 0.06; unrounded |
| Missing minute | not counted |
| NSE range | high and low not checked |
| Transient vs permanent | absence raises; failure writes a void row; 1-minute failure not deferred; a 1-minute call made for an incomplete session |
| Pacing and stop | pacing reversed; stop after 4 |
| Void rule | `no_1m_check` and `nse_unchecked` trusted; always computed; status always ok |
| Previous close | last level from 15:15 |
| Arithmetic | shared arithmetic changed |
| Provenance | earliest fetch; `<=` boundary; next session = same day |
| Order and resume | order rule off; a rerun refetches |
| Unreadable answer | archived |
| Deferrals | count fixed at 1; log not written |
| Calendar | muhurat recorded |
| Report | pre-open count over all rows; void sessions not listed |
| Verify | verify blind; SHA check skipped |
| No prices | a level in the row |
| Read-only and secrets | 15m constant not allowed; error text leaks; constant read outside the `try` |
| Separation from A16 | rows written into A16's `rv/` |
| CLI | exit 0 always; dry run inside the repository allowed; settle at 16:00 |
| Self-review fixes | derive from the fresh copy; changed sessions not named; rerun moves the fetch time; 404 final at once; full session without its check is ok; NSE `KeyError` escapes; verifier archives NSE files; mismatch hidden by a missing minute |

The first pass found four test gaps; tests were added for each and all four are now caught:
- an exact tick in float noise;
- the overnight figure's value;
- untrusted rows must be blank;
- a missing minute together with a mismatch.

## Self-review (rule 3): two independent agents, and what I did with each finding

**Correctness reviewer:**
- **M1, accepted (strong, reproduced).** Rows were derived from the newest copy while the previous close came from the
  earliest copy, and a later answer with other bytes was never named, which broke the story's archive rule. Now:
  - each session is derived from the first copy covering it;
  - a later answer whose candles differ is printed as `CHANGED <session>: ...`;
  - the previous close is read from the previous row's own copy (`previous_close.py`, shared with verify).

  Test: `test_a_later_answer_with_other_candles_...`.
- **M2, accepted (strong).** A rerun with identical bytes stamped the new fetch time, so verify could never reproduce
  `first_seen_at`. `save()` now keeps the manifest's first fetch time. Test: `test_a_rerun_after_a_deferral_...`.
- **M3, accepted (strong reasoning plus the repo's own 21:00 constant).** An evening run between 16:00 and NSE's
  publication would have written a permanent `nse_unchecked` for a file that was only late. Two changes:
  - a 404 now counts as absent only from 21:00 IST on the day after the session; before that the session is deferred
    as "not published yet";
  - the default end date is today only from 21:00.

  Test: `test_nse_s_404_defers_until_the_file_is_final_then_voids`.
- **S1, accepted.** A full session with no 1-minute copy is now void with `no_1m_check:26`, never ok.
- **S2, decided by the orchestrator after this report (decision 62, option b); see the last section.** As first
  reported: A `missing_candles` session (for example 23 of 25 candles)
  has no 1-minute check, by the passed story's rule. Yet its present levels give an overnight figure and its 15:30
  level starts the next overnight return.
  - What already protects it: the NSE range check still applies to those levels (within 0.05 of NSE's range).
  - What it does not catch: a wrong level inside the range.
  - Options:
    - (a) keep as is;
    - (b) also make the 1-minute check for incomplete sessions, at the marks that have levels (one more call each;
      about 20 such sessions in 2020-2026 by step 0's counts);
    - (c) treat `missing_candles` levels as untrusted (more voids).
  - My view is (b), on reasoning only. It changes the passed text, so it is the orchestrator's call.
- **S3, rejected on evidence.** The worry was that "an empty answer could be treated as failed". Groww answers
  `{"candles": []}` on days without candles: probed live today for 10 Oct 2025 and Sunday 11 Oct 2026, shape only. A
  missing list is a malformed answer, so transient is right.
- **Minors.**
  - Accepted:
    - a missing minute and a mismatch are both named now;
    - store failures include `ValueError` and `KeyError`;
    - the answer is serialised inside the `try`.
  - Kept: a `CalendarError` from `next_open` at the end of the calendar stops the run with A7's message (criterion 3's
    stop). The rows written so far stay.

**Safety and design reviewer:**
- **1, accepted:** the same finding as M1.
- **2, accepted:** "every changed session is named" is now implemented.
- **3, accepted (strong, reproduced).** The SDK constant was read outside the `try`; reading it signs in to Groww, and a
  sign-in error could carry a key. It is now inside the `try`. Test: `test_a_sign_in_failure_...`.
- **4, accepted.** An NSE file with a missing column or a short row crashed the run. It is now unreadable, which is
  transient. Two test cases.
- **5, accepted.** Verify used the run's wiring, which builds Groww and archives NSE files into Drive. It now has its own
  read-only wiring.
- **6, not fixed: risk stated for the orchestrator.** A16's live committer adds everything under
  `research/data/intraday`. On the same checkout it could commit `rv-candle/` files without the candle manifests.
  - Changing A16's commit paths is outside this story.
  - The live run is mine, on my own checkout; I commit rows, manifests and the deferral log together right after it.
- **7, partly accepted:** `NseDays` got an interface; for the archive, see criterion 12 above.
- **8, rejected.** The test already asserts that the set of top-level folders written under the intraday folder is
  exactly `{"rv-candle"}`, which rules out `slots/`, the heartbeat and `rv/`.
- **9, accepted:** the code now uses the story's names (`candles`, `minute_candles`, `nifty-15m.csv`). It also adds
  `nifty-1m.csv`, because decision 55's 1-minute copies came after the design text.
- **10, accepted:** the deferral label now reads "(deferred by N run(s), never written)". A run whose range stops
  before the session adds no row, so "in a row" overclaimed.
- **11, skipped:** a copy whose SHA-256 matches its manifest cannot be malformed unless we wrote it malformed.

## Plan after PASS and merge (rule 8; owner rule "1 B")

1. One real `backfill` from 1 Jan 2020 to the latest finished session (about 23 min of Groww, plus about 1,700 1-minute
   checks at no more than 2 calls a second).
2. Then `backfill-verify`.
3. Commit `research/data/intraday/rv-candle/` and `research/data/manifests/groww-candles/` together.
4. Add here, as counts: windows and calls; sessions, ok, void by reason, void share; backfilled and live counts;
   pre-open gaps above 0.05; the verify result. Never a level.

## After the first report: decision 62 and Groww's 1-minute history

**Decision 62 (orchestrator, option b), built.** A session with some but not all of its 25 candles now gets the
1-minute call too. Each present level is checked at its mark; an absent level needs no minute. Any failed present mark
makes the session's levels untrusted: no figure, and the next overnight part is void. A session with no candle makes
no call. The story has one added line with the tests (`docs/stories/A16b-candle-backfill.md`, "Incomplete sessions
too"), plus the matching `nse_open_gap` sentence.

New tests:
- `test_a_missing_middle_candle_keeps_the_checked_15_30_level_...`: the call is made, the absent mark's minute is not
  needed, and the next session is ok;
- `test_an_incomplete_session_whose_present_level_fails_its_check_is_untrusted`;
- `test_an_incomplete_session_whose_1_minute_call_fails_is_deferred`;
- `test_an_incomplete_session_without_its_1_minute_copy_is_never_trusted`.

Mutations, all 4 caught:
- the absent level still needs its minute;
- the incomplete session is not checked;
- the incomplete session is trusted without its copy;
- the empty session is called.

**Where Groww's 1-minute history begins (judge D's question): measured, strong.** I ran a read-only binary search over
NSE's regular sessions from 1 Jan 2019 to 31 Mar 2020 (10 calls, counts only):
- The last session without 1-minute candles is **31 Dec 2019**; the first with them is **1 Jan 2020** (377 candles).
  This matches the 15-minute history's start.
- Every session from 11 to 31 Dec 2019 has 0; every session from 1 to 22 Jan 2020 has 377-379.
- A sample of every 15th session after it found 5 of 5 with candles.
- Judge D's 12 Mar 2019 finding fits this: that is before the start.

**2020 sessions that lack it: measured, strong.** A live read-only dry run of all of 2020 on this code took 7 min
40 s, exit 0:

```
window 2020-01-01..2020-03-30: 1571 of 1575 session candles (63 sessions)
window 2020-03-31..2020-06-28: 1450 of 1450 session candles (58 sessions)
window 2020-06-29..2020-09-26: 1625 of 1625 session candles (65 sessions)
window 2020-09-28..2020-12-26: 1525 of 1525 session candles (61 sessions)
window 2020-12-28..2020-12-31: 100 of 100 session candles (4 sessions)
sessions 251: 251 written now, 0 held before, 0 deferred
void 5 of 251 (2.0%); by reason: {'missing_candles': 2, 'no_1m_check': 2, 'no_previous_close': 3, 'outside_nse_range': 2}
provenance: {'backfilled': 251}
pre-open gap above 0.05 on 2 of 251 sessions with a 1-minute answer: 2020-01-20, 2020-09-18
void missing_candles: 2020-03-13, 2020-03-23
void no_1m_check: 2020-03-13, 2020-03-23
void no_previous_close: 2020-01-01, 2020-03-16, 2020-03-24
void outside_nse_range: 2020-03-13, 2020-03-23
```

- **Every 2020 session had a 1-minute answer: 251 of 251.**
- `no_1m_check` hit only the two circuit-breaker days, and only under decision 62 (13 Mar lacks 2 needed minutes, 23
  Mar lacks 1). Both were already void for `outside_nse_range`, so **no 2020 session is voided by missing 1-minute
  history**.
- The 2020 void share is 2.0%, under the 5% flag; Q1 alone was 7.8%.
- Verify over the dry folder: "251 rows; every row equals its copies".


## Criterion 14: the full range as a dry run (judge 122 addendum 6)

This was a live, read-only dry run from 1 Jan 2020 to 14 Oct 2026, the latest finished session (run at about 14:15 IST
on 15 Oct). Files went to scratch only: nothing to Drive, nothing into the repository. It resumed from the 2020 dry
folder, so 2020's 251 rows were held and 2021-2026 was fetched fresh, taking 45 min 16 s. Exit 0. **Strong** for
everything in this section.

- **Calls:** 29 fifteen-minute windows (2020's 5 from the earlier dry run, plus 24 now) and 1,679 one-minute calls.
  That is one per session with any candle; 10 Oct 2025 had none. No Groww failure, no stop.
- **Sessions:** 1,680: 1,661 ok and 19 void (1.1%, under the 5% flag). **0 deferred. 0 CHANGED.**
- **Void by year:** 2020 5, 2021 2, 2022 2, 2023 0, 2024 4, 2025 4, 2026 2. Of the void sessions, 10 are
  `no_previous_close` follow-ons: the session after each void day, plus 1 Jan 2020.
- **Void reasons, counting each reason once per session:** `missing_candles` 8, `no_1m_check` 8, `no_previous_close`
  10, `outside_nse_range` 5.
- **Provenance:** 1,680 backfilled, 0 live.
- **Pre-open gap above 0.05:** 4 of 1,678 sessions with a pre-open check (20 Jan 2020, 18 Sep 2020, 5 and 6 Sep 2023).
- **Verify** over the dry folder's own copies: "1680 rows; every row equals its copies", exit 0. It took about 30 min,
  mostly reading NSE's 1,680 files from Drive.

The 19 void sessions. Gaps are NSE minus Groww; negative means Groww is outside NSE's range.

| Session | Reasons | Levels | Out-of-session candles | Note |
|---|---|---|---|---|
| 2020-01-01 | no_previous_close | 26 | 09:00, 15:30 | series start |
| 2020-03-13 | missing_candles:2; no_1m_check:2; outside_nse_range | 24 | 09:00, 15:30 | circuit-breaker halt; low 79.00 below NSE's |
| 2020-03-16 | no_previous_close | 26 | | after 13 Mar |
| 2020-03-23 | missing_candles:2; no_1m_check:1; outside_nse_range | 24 | | circuit breaker; high 196.30 above NSE's |
| 2020-03-24 | no_previous_close | 26 | | after 23 Mar |
| **2021-02-24** | missing_candles:20; no_1m_check:2 | 6 | **8: 09:00, 15:30, 15:45, 16:00, 16:15, 16:30, 16:45, 17:00** | NSE's halt, trading extended to 17:00: the after-hours candles are counted, never levels |
| 2021-02-25 | no_previous_close | 26 | | after 24 Feb |
| **2022-03-07** | no_1m_check:2; outside_nse_range | **26 (all 25 candles)** | | **new defect found by the full run: a full session whose high is 251.60 above NSE's high, and 2 needed minutes missing. Caught and void** |
| 2022-03-08 | no_previous_close | 26 | | after 7 Mar |
| **2024-03-02** | missing_candles:15; no_1m_check:3; outside_nse_range | 11 | 09:00 only | **special session (DR drill), 10 of 25 candles**; high 0.70 and low 0.10 beyond NSE's |
| 2024-03-04 | no_previous_close | 26 | | after 2 Mar |
| **2024-05-18** | missing_candles:15; no_1m_check:3; outside_nse_range | 11 | 09:00 only | **special session (DR drill), 10 of 25**; low 127.30 below NSE's |
| 2024-05-21 | no_previous_close | 26 | | after 18 May (20 May was a holiday) |
| **2025-09-26** | missing_candles:3; no_1m_check:1 | 23 | 09:00 only | **Groww's hole** (22 of 25, as step 0) |
| 2025-09-29 | no_previous_close | 26 | | after 26 Sep |
| **2025-10-10** | missing_candles:25 | 0 | none | **Groww's hole: no candle at all**; no 1-minute call, blank gaps |
| 2025-10-13 | no_previous_close | 26 | | after 10 Oct |
| **2026-09-29** | missing_candles:5; no_1m_check:1 | 21 | 09:00 only | **Groww's hole** (20 of 25, as step 0) |
| 2026-09-30 | no_previous_close | 26 | | after 29 Sep |

**The other special sessions are ok.** 20 Jan 2024 (Saturday, full session), 1 Feb 2025 and 1 Feb 2026 (budget
Saturdays) each have all 26 levels, every check passed.

**The 15:45 candles from 2025.** Groww gives a 15:45 candle on every session from **6 May 2025** on. 5 May 2025 is the
last session with only 09:00 and 15:30 outside the session; from 6 May every session has 09:00, 15:30 and 15:45, which
is 193 sessions in 2026 and 163 in 2025. Earlier, out-of-session candles past 15:30 appear only on:
- 24 Feb 2021 (to 17:00);
- 28 Jun 2021 (15:45, 16:00);
- 1 Dec 2023 (16:00).

None of them is a level; all are counted in `outside_candles`. The 25-candle set (09:15 to 15:15 starts) is unaffected.
This is the case criterion 2 tests.

**Observation, not a void (some evidence; reasoning on the cause).** On 106 ok sessions, NSE's high or low lies more
than 5 points beyond every Groww candle on the inside side: Groww's candles never reached NSE's extreme. The maximum is
91.95 points.

| Year | Sessions |
|---|---|
| 2020 | 21 |
| 2021 | 1 |
| 2022 | 3 |
| 2023 | 6 |
| 2024 | 5 |
| 2025 | 40 |
| 2026 | 30 |

Only levels outside NSE's range void a session, by the story's rule, so these stay ok. Their levels are closes inside
NSE's range, and the 1-minute check passed. A likely cause, unverified, is NSE's high or low being set by a tick that
Groww's candles do not carry, for example around the open. It does not touch the realised variance, which uses closes
only, but the `nse_high_gap` and `nse_low_gap` columns record it per session for anyone using highs or lows.

**What this means for the live run (rule 8):** the same run against Drive will write 1,680 rows with these counts,
unless Groww's answers differ from today's, which the output would show as CHANGED lines. `backfill-verify` on it will
take about 30 min.
