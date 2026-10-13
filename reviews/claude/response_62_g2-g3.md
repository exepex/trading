# Response 62: G2 frozen baselines and G3 Book 1 forecast capture, builder's claims (and a proposal for ChatGPT)

Stories: `docs/stories/G-forecasts.md` G2 and G3. Protocol: `research/forecasts/PROTOCOL.md` version 1, frozen
(`cf489e4`, record `fd95a42`).

**Verdict first:**
- **G2 is built in full on history.** The three baselines exactly as the frozen protocol writes them, a history
  back-fill for all 1,921 panel days, hand-checked fixture values, the look-ahead harness, and the refit test.
- **G3 is built, but cannot forecast live yet, and that is not a builder choice.** It has Book 1's frozen method (hash
  in every record), the daily GitHub Actions capture, the record files, the deadline and the Slack line. The frozen
  protocol says (section 1): "Inputs, live: only the common market pack (story E2) ... Until E2 exists there are no live
  forecasts." E2 is not built. So the daily job records an honest "no forecast" with the reason, every trading day,
  until a protocol version names a live input pack. I propose one below for ChatGPT. **The orchestrator's instruction
  to read the A4 snapshot conflicts with the frozen protocol; I did not override the protocol.**
- **Book 1's history** (2019 to 12 Oct 2026) is fully computed in the back-fill, close proxy.

Evidence: strong for the code (hand values, determinism, look-ahead harness on real days); reasoning only for the
proposal.

## How to check

```
python -m pytest -q tests/forecast                 # the G1-G3 forecast tests (the back-fill recompute takes ~30 s)
python -m fno forecast backfill --check            # recompute the back-fill and compare bytes
python -m fno forecast capture --day 2026-10-13    # writes research/forecasts/live/2026/2026-10-13_book1_rules.csv
```

## G2: frozen baselines

| # | Criterion | Code | Evidence |
|---|---|---|---|
| 1 | A look-ahead test (B1 harness) proves no baseline uses data after its cutoff | `fno/forecast/history.py` (an outcome is used only if the day it became known is before `d`), `baselines.py`, `models.py` | `tests/forecast/test_baselines_lookahead.py::test_no_baseline_or_book1_value_moves_when_later_data_changes`: B1's `assert_no_lookahead` on 2 random days (Sep 2025 to Sep 2026) of real 2023-2026 data. Every panel value after the day's close is changed or removed; all 15 baseline and Book 1 values stay equal (at least 14 are real values) |
| 2 | Each baseline reproduces hand-computed values on fixture days | as above | `test_baselines.py`: lognormal Q1 0.4890 and Q2 0.588 written out (spread 0.05539, m -0.001534; corrected after judge 54 minor 1, the asserts were already right). Risk-neutral on the G1 fixture day: IV30 14.4937%, tau 28/365, carry ln(22050/22000)/(16/365) = 0.051788, Q1/Q2 from the protocol's formulas. Base rate: on day 40 the 4 most recent known outcomes are no, yes, no, yes = 0.5, and day 20's outcome, known on day 40 itself, is left out. `test_models.py`: OLS y = 1 + 2x with residuals (0.5, -1, 0.5) recovered exactly; residual shares 2/3 and 0 (strict) |
| 3 | The refit schedule of (c) is fixed; a refit uses only earlier data | `ModelBaseline.refit_day` (first trading day of the month), `_fit_on` (rows known before the refit day) | `test_models.py` (refit day; one fit serves the whole month). `test_baselines_lookahead.py::test_a_refit_uses_only_data_known_before_its_refit_day`: every panel value after the refit day's close is changed, and the coefficients and residuals serving 25 Mar 2026 are equal |
| 4 | Every baseline value is labelled with its method name and version | `backfill.py` | `test_backfill.py`: every record's `method_or_version` is `<baseline>/v1/close-proxy/iv30:<state>` (Book 1: `book1/v1/sha256:<method hash>/close-proxy/iv30:<state>`); the risk-neutral label text is in `baselines.py` |

**What "baselines" means here (frozen protocol section 4):**
- **(a) Risk-neutral:** the lognormal with IV30 and the near future's carry, questions 1-2 only. A flagged IV30 is
  used, and the flag is carried in every record.
- **(b) Base rate:** 750 known outcomes, at least 500 needed.
- **(c) Statistical models:** a HAR-type regression on RV5, RV20 and RV60 (questions 3 and 5) and VIX mean reversion
  (question 4). Ordinary least squares on 750 rows, at least 500, refitted on each month's first trading day, with
  probabilities from the empirical residual distribution.
- **Not used:** Breeden-Litzenberger (an option in the G2 story text). The frozen protocol chose the lognormal.

**History back-fill (for evaluation):**
- **File:** `research/forecasts/backfill/backfill_v1.csv.gz` (309 KB, deterministic gzip). It holds 38,420 records:
  1,921 days x 5 questions x (3 baselines + Book 1).
- **Pack:** `pack_sha256` is the panel manifest's hash.
- **Close proxy:** the cutoff is 15:30 on each day, labelled close proxy.
- **Coverage:** values exist where inputs allow; the rest are recorded "no forecast", never imputed.

| Forecaster | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| (a) risk-neutral | 1,920 | 1,920 | - | - | - |
| (b) base rate | 1,893 | 1,893 | 1,873 | 1,903 | 1,217 |
| (c) model | - | - | 1,818 | 1,654 | 1,817 |
| Book 1 | 1,921 | 1,921 | 1,873 | 1,903 | 1,817 |

- **Q5 base rate:** it starts late (1,217 days) because it needs 500 known outcomes on interpolated IV30 days, and
  2019-2020 are often flagged.
- **What the back-fill computed:** it computed past outcomes, because a base rate is a share of them. No score, Brier
  or comparison was computed.

## G3: Book 1's forecast capture

| # | Criterion | Code | Evidence |
|---|---|---|---|
| 1 | Five probabilities in [0, 1] per session day, or a recorded "no forecast" (never imputed) | `capture.py`, `record_files.py`, the frozen `schema.py` | `test_book1_and_capture.py`: a trading day gets 5 records with empty probabilities; a closed day records nothing; a record is written once (the same bytes again is a no-op, different bytes are refused). History: the back-fill, above |
| 2 | Book 1's method is identical on every day of a version (method file hash in each record) | `book1_method.py` (`book1/v1`, `method_sha256`) | `test_book1_and_capture.py`: the mean rule by hand, and the label carries the file's SHA-256. `test_backfill.py`: on every one of 9,605 back-fill days and questions, Book 1 equals the mean of the question's two baselines |
| 3 | Forecasts committed after the deadline are ignored | `capture.on_time`, `capture.first_commit_time` | Deadline 15:30 IST on the forecast day (the close; after it the day's close is known). A temporary git repository: committed at 15:12 counts, one second after 15:30 does not, and a UTC time is compared in IST |

**The daily job** (`.github/workflows/forecast-capture.yml`):
- **Schedule:** it starts at 14:00 IST, because GitHub can start late, and waits until 15:10 IST, after the 3 pm
  snapshots.
- **Capture:** it runs `python -m fno forecast capture --run-id ...` and commits `research/forecasts/live/` by the
  deadline.
- **Slack:** it posts one line to #fno-desk (`FNO_SLACK_BOT_TOKEN`) and alerts there if the job fails.
- **Run records:** it reuses O6's `RunSummary`/`RunSummaryStore`, saving each run under Drive's pipeline area at
  `runs/forecast-capture/...`. The routine is "none (deterministic, no AI)".
- **Not run here:** the workflow has not run yet. The first scheduled run is the next trading day.

**Records today:**
- **Probabilities:** five "no forecast" records a day, each labelled `book1/v1/sha256:<hash>/no-live-inputs`.
- **Pack hash:** the SHA-256 of an empty pack (`e3b0...b855`), because no input was read. The frozen schema requires
  a pack hash.
- **Slack line:** "no forecast recorded (protocol v1 section 1: no live forecasts until the E2 common market pack
  exists)".

**Snapshot:** the A4 snapshot is not read, by the protocol, as above. Neither the Groww routine nor the NSE Actions
recorder has committed a snapshot to `research/data/quotes/` on `main` yet.

## Two gaps that block live forecasts (please decide)

1. **The protocol's live input rule (section 1).** Live forecasts need E2, which depends on D1 and E1, so it is far
   off. I propose that ChatGPT review a protocol version 2 that adds only this rule:
   - **Forecast input pack** (until E2 exists):
     - the canonical A4 snapshot of `d`, used only if its capture finished by 15:00, as B7's live features do;
     - the NIFTY 50 and India VIX closes through `d-1`;
     - the session calendar.
   - **Hashing:** the pack is hashed and committed with the record.
   - **`d`'s close:** where a definition needs it (trailing RV(d), the models' regressors, base-rate eligibility), the
     15:00 snapshot spot and VIX stand in for it. That is B7's live-F1 rule: the previous 20 closes, then the 15:00
     spot.
   - **Baseline (a):** uses the snapshot's mids for IV30 (B1's ATM rule on mids, never last prices) and the snapshot's
     futures for the carry.
   - **Golden contract:** the history golden values are unchanged, so G1's numbers do not move.
2. **No daily closes after 12 Oct 2026 in the repository.** The panel and the warm-up closes are built by hand. Live
   base rates and models need closes through `d-1`. A daily GitHub Actions download of NSE's index-close file (one of
   the downloads the owner moved to Actions) would close this gap. Without it, even an approved v2 would forecast from
   closes that are days stale.

## Choices to check (reasoning only)

- **The IV30 flag travels in `method_or_version`.** The frozen schema has no column for it: `iv30:interpolated`,
  `iv30:flagged` or `iv30:none`. G4 can also join the golden file by date.
- **The deadline is 15:30 IST.** The protocol leaves it to G3. A later deadline would let a forecast see `d`'s close,
  which question 1 compares against.
- **Commit time is the committer time of the commit that added the file.** A committer can set it, but here the
  committer is the Actions job. GitHub's push time would be stronger evidence; there is no API for it in tests.
- **The freeze stays intact.** `fno/forecast/wiring.py` is one of G1's frozen files, so G2/G3's wiring is a new
  composition root, `fno/forecast/baseline_wiring.py`, added to CLAUDE.md. No frozen file changed:
  `tests/forecast/test_freeze.py` passes, and so does `test_golden.py`.

## Files

- **New:** `fno/forecast/history.py`, `baselines.py`, `models.py`, `book1_method.py`, `backfill.py`,
  `record_files.py`, `capture.py`, `cli.py` (registered in `fno/cli.py`) and `baseline_wiring.py`.
- **Workflow:** `.github/workflows/forecast-capture.yml`.
- **Data:** `research/forecasts/backfill/backfill_v1.csv.gz`.
- **Tests:** `tests/forecast/forecast_fixtures.py`, `test_baselines.py`, `test_models.py`,
  `test_baselines_lookahead.py`, `test_book1_and_capture.py` and `test_backfill.py`.
- **Size:** every file is under 160 lines.

## Addendum: the freeze check in the daily capture (orchestrator note on `fetch-depth: 0`)

- **The freeze check runs before every capture.** `python -m fno forecast capture` now runs G1's
  `require_frozen_before` on HEAD before it writes anything. Records count only under the frozen protocol. If the
  check fails, nothing is recorded, the command exits 1 and the job alerts #fno-desk with the reason.
- **No shallow clones.** A shallow clone cannot see the protocol commit, so it also refuses; the check is never
  skipped. `.github/workflows/forecast-capture.yml` checks out with `fetch-depth: 0`.
- **Test:** `test_the_capture_command_refuses_when_the_protocol_freeze_does_not_hold`.
- **Fixed in the same push:**
  - On a closed day, `git add research/forecasts/live` would have failed, because the folder does not exist before the
    first record. The job now adds `research/forecasts`.
  - The failure alert now carries the command's own line, for example the freeze refusal.

## Addendum: protocol version 2, the interim live input pack (ChatGPT review 29, response 63)

**Status: version 2 written, built and tested; NOT frozen.** It waits for the judge's check and the orchestrator's
confirmation. Until `research/forecasts/FREEZE_v2.md` exists, the daily job prints "nothing recorded" and exits 0.
Version 1 is untouched: no frozen file changed, and the v1 freeze and golden tests pass.

Files:
- protocol: `research/forecasts/PROTOCOL_v2.md`;
- code: `fno/forecast/{live_pack, live_history, closes_source, schema_v2, freeze_v2, capture}.py`;
- golden: `tools/forecast_live_golden.py` and `research/forecasts/v2/golden/`;
- tests: `tests/forecast/test_live_pack.py` and `test_live_capture.py` (16 tests).

Checks run: full suite 1,519 passed, ruff clean, imports clean.

### Each change, with its evidence

| # | Change | Where | Evidence |
|---|---|---|---|
| 1 | Per-field cutoff at 15:00:00 IST | `LivePackBuilder.build` | case B: a put received at 15:00:01 is left out (IV30 falls back to 27 Oct alone, flagged); a row received after the cutoff changes no value (`test_a_row_received_after_the_cutoff_changes_the_hash_but_no_value`) |
| 2 | VIX from A4's NSE-timestamped record, otherwise no forecast | `_vix` | case B (stamp 15:00:30): no VIX; an empty stamp: no VIX (`test_vix_without_an_nse_timestamp_is_missing`) |
| 3 | Live-mid IV30, same expiry, interpolation and flag rules | `_iv30` uses B7's `atm_implied_vol_points` and G1's `interpolate_30d` unchanged | case A: 14.815074 against a hand value of 14.8151 (shown in the test); case B: 14.0 flagged |
| 4 | Closes through d-1 as a hard gate (`history_stale`) | `stale_history` | a one-day gap, or a missing d-1, gives `history_stale`; base rate and model then give "no forecast" for every question, while risk-neutral (pack only) still forecasts |
| 5 | Field-level provenance hash | `LivePack.canonical` | the hash changes with the closes' coverage day, the calendar hash and the raw file bytes; every field carries a source |
| 6 | `live_1500_proxy` as its own mode | `LIVE_MODE`; pack and records | asserted in the pack and record tests |
| 7 | `iv30_status` in a v2 schema | `schema_v2.py`: v1 columns plus `input_mode`, `iv30_status`, `generated_at` | round trip; invalid modes and statuses refused; the method label carries no IV30 state |
| 8 | Generated by 15:15 IST, receipt-locked by the Actions run | `ForecastRecordV2.on_time`; receipt line in the log, the step summary and the O6 run summary; write-once `CaptureRefused` | 15:15:00 counts and 15:15:01 does not; a second run reports "already recorded"; a different pack is refused |

### Gate on O6, not a copy of it (strong evidence)

- O6's `index-closes.yml` (277b31b) appends NSE's closes to `research/data/nifty-panel/warmup_closes.csv` at 21:11 IST.
  The 13 Oct row is already in (e38eabd).
- `CommittedClosesFile` only reads that file. Nothing here downloads closes.
- That file covers 2017 to 13 Oct 2026 with no gap, so the gate holds today.

### Doubts and gaps (please read)

1. **No A4 snapshot has ever been committed.** `research/data/quotes/` does not exist on `main`, so today the live
   capture would find no snapshot and record "no canonical A4 snapshot". (Strong evidence: `snapshot-ready` exits 1
   for 12 and 13 Oct.) The 3 pm recorder is a scheduled Claude session, not an Actions job, so its commit time is not
   guaranteed. The workflow pulls until 15:13 IST. A later commit means that day has no forecast.
2. **A stale history makes Book 1 risk-neutral only, for Q1 and Q2.** This follows the frozen v1 rule ("one baseline
   available: that one"). It is correct, but on stale days Book 1 is not the two-baseline mean. The reports should
   count such days apart. This is my proposal, not one of the 8 changes (reasoning only).
3. **Question 5's base rate needs the panel rebuilt at least every 21 trading days.** The panel's options reach
   12 Oct. Without a rebuild, Q5's base rate turns `iv30_history_stale` after about 10 Nov 2026 (reasoning from the
   offset rule).
4. **A4 captures only two monthly expiries.** When 30 days falls past the second expiry, live IV30 flags where
   history would interpolate. (Some evidence: it can only flag more, never less.)
5. **The golden cases pin a calendar label ("golden-fixture"), not the calendar's bytes.** The calendar grows each
   year, so its bytes are not pinned. The real hash is in every live pack.
6. **One history change.** `history.py` now takes its range to the panel's last day even when that day's close is
   missing, so a live day's spot stands in for it. Re-running `python -m fno forecast backfill --check` shows the
   back-fill unchanged.

## Addendum: judge 54 minor 1 fixed

Judge 54 is right. m = -σ²τ/2 = -0.04 × (28/365) / 2 = -0.001534, not -0.000767. Recomputed:
- spread 0.055394 (the judge wrote 0.055386, a rounding difference);
- Q1 = N(-0.0277) = 0.48895;
- Q2 = 1 - N(0.5613) + N(-0.5222) = 0.58807.

The test docstring and the table row above now carry these values. The asserts did not change.

## Addendum: protocol version 2 frozen; the first live run (Wed 14 Oct 2026)

**Frozen.** This follows judge 47 addendum 3 (PASS at 1b57cb3) and the orchestrator's confirmation, using the same
recipe as v1:
- **Protocol commit `ab2e811`.** Final status text, the run-time golden check in section 8, and ledger trials 37-41
  (`forecasts-v2`) registered.
- **Freeze commit `0fc5723`.** `research/forecasts/FREEZE_v2.md` and the trials' `protocol_commit` set.

**The freeze checks the v2 code, not only the text** (the judge's point on experiment 1). 34 files are checked byte for
byte:
- the protocol;
- every `fno/forecast/*.py`: the pack, history and gates, closes source, v2 schema, capture, freeze check, command
  line, and the v1 code they use;
- `tools/forecast_live_golden.py`;
- every v2 golden input and output.

Shared libraries are recorded, not byte-checked: B7's live ATM rule, B1's Black-76, and the panel and quote readers.
The daily job recomputes both golden cases before it captures, so a behaviour change in any of them fails the run
before a forecast is made.

Tests in `tests/forecast/test_freeze_v2.py`:
- the real repository's freeze holds, and covers every v2 code file and golden file;
- a planted cutoff edit (15:00:01) is refused;
- no record means "not yet frozen";
- ledger trials 37-41 carry `ab2e811`.

**What the first live run needs** (`forecast-capture.yml`, starts 14:00 IST):
1. **The freeze in history.** Done; the job checks out with `fetch-depth: 0`.
2. **Both golden cases reproduce.** True today.
3. **Official closes through Tue 13 Oct** in `warmup_closes.csv`. True: O6 added 13 Oct (e38eabd), and the file
   covers 2017 to 13 Oct with no gap.
4. **Panel IV30 for Q5's base rate**, up to 21 trading days before the forecast day. True until 12 Nov 2026 (first stale day 13 Nov, by the calendar; corrected in response 65),
   because the panel ends 12 Oct.
5. **A canonical A4 snapshot for 14 Oct, committed by 15:13 IST.** It can come from the Groww routine
   (`research/data/quotes/groww/...`), used first, or the NSE Actions recorder (`research/data/quotes/nse/...`). Inside
   the snapshot:
   - quotes received by 15:00:00;
   - the futures and VIX read before the first quote request, at or before 15:00:00;
   - NSE's VIX stamp at or before 15:00:00.

   This is the one input not yet proven. No snapshot has ever been committed on `main`.

**If an input is missing** (shown by a dry run of 14 Oct on today's repository, with no snapshot, into a scratch
folder):
- **No snapshot by 15:13:** spot, VIX, futures and IV30 are all missing.
  - The pack lists four problems; `iv30_status` is `none`.
  - Risk-neutral and the model record "no forecast".
  - The base rate still forecasts all five questions. It needs only past outcomes, so this is correct under the
    protocol. Book 1 is then the base rate alone: 10 of 20 probabilities.
  - Q5 on that day is void at scoring anyway, because IV30 is missing.
  - The pack, the records and the receipt are still written once, so the day stays an honest record of what was
    known at 15:00.
- **Snapshot present but a field late (after 15:00:00):** only that field is missing.
  - Late VIX: no VIX input.
  - Late futures (the first request after 15:00): no futures and no IV30.
  - A late ATM leg: that expiry has no IV, so IV30 falls back to a single expiry and is flagged, or is `none`.
- **Closes for d-1 missing (O6 failed the evening before):** `history_stale`. Base rate and model record "no
  forecast" for every question. Book 1 is risk-neutral alone for Q1-Q2; Q3-Q5 have no Book 1 forecast.
- **Golden difference or a changed frozen file:** the run fails before any forecast, with a #fno-desk alert. Nothing
  is recorded, and a new version is needed.
- **The run starts after 15:15** (GitHub's schedule is late): records are written with their `generated_at`.
  `on_time` is false, so scoring ignores them.

**Risks for Wednesday** (reasoning only, except where marked):
- **The 3 pm snapshot's timing.** The recorder captures from 14:55. If the first attempt is incomplete, its retries
  run after 15:00, and their quotes are excluded under the per-field cutoff. A bad 14:55 attempt therefore means a
  partial or empty pack, not wrong numbers. This is the judge's "watch the first live day".
- **The NSE fallback.** Using NSE's snapshot when Groww's is missing is in the frozen text (section 1). The orchestrator
  said the NSE recorder "runs side by side" and that nothing switches until the owner has seen `quotes compare` for 3
  sessions. If the owner wants NSE snapshots excluded from forecasts until then, that needs a version 3. Please
  decide.
