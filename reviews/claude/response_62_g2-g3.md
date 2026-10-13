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
| 2 | Each baseline reproduces hand-computed values on fixture days | as above | `test_baselines.py`: lognormal Q1 0.4890 and Q2 0.588 written out (spread 0.05539, m -0.000767). Risk-neutral on the G1 fixture day: IV30 14.4937%, tau 28/365, carry ln(22050/22000)/(16/365) = 0.051788, Q1/Q2 from the protocol's formulas. Base rate: on day 40 the 4 most recent known outcomes are no, yes, no, yes = 0.5, and day 20's outcome, known on day 40 itself, is left out. `test_models.py`: OLS y = 1 + 2x with residuals (0.5, -1, 0.5) recovered exactly; residual shares 2/3 and 0 (strict) |
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
