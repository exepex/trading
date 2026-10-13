# Response 47: story B3 (policy runner and verdict), builder's claims

Builder session for story B3 (GitHub issue #32). Code commit `79fc685` (merged into `main` as `f0e2101`). Before it,
the two judge-26 minors of story B1 in `aa77615` (harness cutoff never later than the decision-day close, with a planted
F1 leak declaring `known_at` a week later that now fails; a direct test that a non-zero settlement on an untraded leg or
future never gives F1). Checks on the merged head: `python -m pytest -q` 795 passed; `ruff check fno tests tools` clean;
`ruff format` applied; `python tools/check_imports.py` clean (177 files); largest new file 125 lines.

## What was built

| File | What |
|---|---|
| `fno/research_engine/policies.py` | `Policy` interface; `RulePolicy` = ordered (condition, structure) rules; conditions `Positive`, `NotPositive`, `Known`, `IsTrue`, `IsFalse`, `AllOf`, `AnyOf`, `Always` (a `None` input never meets a condition) |
| `fno/research_engine/experiments.py`, `experiment_1.py` | the experiment as data: periods, P1-P8 with their C2 opposites, "compared with" lists, branch tests (P5 BF branch, P6 event filter), ledger trials 22-31, statistics terms |
| `fno/research_engine/opportunities.py` | one opportunity per cycle: features, every structure's B2 result; per-opportunity P&L (net if traded, else 0); `checked_status` (B2's enum exactly, anything else is an error) |
| `fno/research_engine/metrics.py` | totals, means, traded-only stats, win rate, worst, longest losing run, max drawdown, net by year, best-year share, status counts, assumed tax by financial year, no-settlement total, largest modelled max loss |
| `fno/research_engine/statistics.py` | opportunity bootstrap (index 62), year-block bootstrap, Monte Carlo error, nearest-rank percentile |
| `fno/research_engine/controls.py` | C1 random timing (action counts kept, mixed actions included) |
| `fno/research_engine/verdict.py` | protocol section 8 criteria, each with value, rule, threshold, pass; per-policy verdict; criterion 7 voids the run |
| `fno/research_engine/trial_guard.py` | `TrialGuard` interface and `LedgerTrialGuard` (registration for discovery; full B4 check plus the frozen-at-commit line for the challenge) |
| `fno/research_engine/runner.py`, `period_report.py`, `results_file.py`, `research_cli.py` | the run, the results document, `results_<period>.json` / `.md`, the command |
| `fno/research_engine/ledger.py` | `require_committed` split out of `require_registered` (DRY); `Git.commit_exists`; `committed_text` at any commit |
| `fno/composition.py` | `build_experiment_runner`, `load_period_data`, `research_inputs` (SHA-256 of panel manifest, events, calendar, config terms; numpy version) |
| `requirements.txt` | `numpy>=2.0` (the protocol names numpy `default_rng`; it was installed but not declared) |
| `research/2026-10-12-experiment-1/results_discovery.json` / `.md` | the engine's discovery output (already looked-at period, reported only) |

## Criteria

| # | Criterion | Evidence | Status |
|---|---|---|---|
| 1 | Unregistered policy stops with "not registered" (via B4) | `test_trial_guard.py::test_an_unregistered_trial_stops_with_not_registered` (temporary git repo, real `LedgerTrialGuard`); `test_runner.py::test_the_guard_runs_before_any_data_is_read` (the data loader raises if called: the guard comes first). B4's message now reads "trial X is not registered: it is not in research/ledger.csv" | met |
| 2 | Same panel and protocol run twice: byte-identical results files | `test_runner.py::test_two_runs_give_byte_identical_results_files` (JSON and Markdown). Real data: `python -m fno research run 2026-10-12-experiment-1 --period discovery` run three times, before and after merging main: SHA-256 of `results_discovery.json` always `83dd3d6403daf6f8fdd6df9a9f548c0af78422e3d978785170e990cc7371bef1`. The file holds no time, commit or path that changes between runs | met |
| 3 | Golden tests: 60 committed P&L values, bootstrap lower bound vs an independent script to Rs 0.01; C1 95th percentile exactly, binary and mixed | `test_statistics_golden.py`: `tests/fixtures/research_engine/golden_pnl_60.csv`; engine -759.42 = independent plain-Python script = committed value; C1 p95 binary (7 SC of 12) 3,930.00 and mixed (5 SC + 4 BF of 12) 5,000.00, each equal to its independent script and the committed value exactly; a test that sequences keep each action's count | met |
| 4 | A never-trading policy scores 0 per opportunity and fails criterion 1; counts by status in the results | `test_runner.py::test_a_policy_that_never_trades_scores_zero_and_fails_criterion_1` (P7 with F2 never known: total 0, `status_counts` = {no_trade: 60}, criterion 1 value 0, threshold 0, failed) | met |
| 5 | Each criterion shows value, threshold, pass/fail; overall pass only if all pass | `test_every_criterion_shows_value_threshold_and_pass_and_all_must_pass` (P1 passes all three that apply; P4 passes criterion 1 but fails `4_above_P1` and so fails); `test_criterion_7_breach_voids_the_run`; `test_branch_tests_use_the_protocols_opportunities` | met |
| 6 | Challenge runs only with a "frozen at commit" line whose commit exists and precedes the run | `test_trial_guard.py`: no line refused; unknown commit refused; rules changed after the named commit refused; a valid freeze runs. Real repository today: `python -m fno research run 2026-10-12-experiment-1 --period challenge` prints `refused: trial 22 has no frozen protocol commit`, exit 2, before any data is read | met |

Policies and controls are tested against a hand transcription of protocol section 6 on all 24 combinations of F1
(None, -1.5, 0, 2), F2 (None, true, false) and F3 (`test_policies.py`); metrics in `test_metrics.py`.

## Design choices (each is a decision; the protocol must say the same before the freeze)

1. **Protocol text that must change before the freeze** (I did not edit the protocol; the owner and ChatGPT decide):
   - Section 5 still says F1 uses "Black-Scholes, rate 6.5%". The engine uses Black-76 on the same-expiry future (story B1
     note; judge 26 passed). The protocol must say Black-76, or the engine and the protocol disagree at the freeze.
   - Section 8 criterion 3 says "95th percentile" of C1 with no convention. The engine uses nearest rank: the ascending
     value at index ceil(0.95 x 10,000) - 1 = 9,499, no interpolation (the same family as the bootstrap's index 62).
   - Section 7 names numpy `default_rng` but not the draw. The engine draws `rng.integers(0, n, size=(10000, n))` once
     (resample r takes row r); C1 uses `rng.permutation(n)` per sequence with sorted action codes taking consecutive
     slices; the year-block bootstrap draws whole years the same way. Without these lines nobody can reproduce the
     numbers from the protocol alone.
   - A cycle's P&L belongs to its exit day (calendar year and financial year); an opportunity belongs to the period of
     its decision day (a cycle decided in December 2023 is a challenge opportunity even if it exits in 2024).
   - Longest losing run = most consecutive opportunities with net < 0 (a zero ends it); max drawdown = largest fall of
     cumulative per-opportunity P&L from its previous peak, the start counting as a peak of 0.
2. **Discovery needs registration only; the challenge needs the full freeze.** B4's `require_registered` refuses any
   trial without a frozen protocol commit, which would make discovery unrunnable until the freeze (and the judge could
   not re-run it). Discovery is already looked at and never judged, so it needs only a committed registration
   (`require_committed`); the challenge needs B4's full check and the frozen-at-commit line. Reasoning only: say if the
   desk wants discovery frozen too.
3. **The frozen line cannot hide a rule change.** Beyond the story's "commit exists and precedes", the protocol at the
   named commit must equal today's protocol without that line. B4's own check (protocol unchanged since the ledger's
   `protocol_commit`) still applies, so the ledger's `protocol_commit` is the commit that added the line. Freeze recipe:
   (a) commit the final protocol (commit A); (b) add `frozen at commit A` and commit (F); (c) set `protocol_commit` = F
   in ledger rows 22-31 and commit; (d) run the challenge.
4. **The challenge run records the first run** (`mark_run` for trials 22-31) after writing results; commit the ledger
   with the results. Discovery runs never touch the ledger (so two runs stay identical).
5. **P6's event filter with nothing removed fails.** Criterion 6 needs the removed trades' sum < 0; if F3 removes no
   trade the sum is 0, not below 0, so P6 cannot claim the filter (protocol-exact; flagged because it may surprise).
6. **numpy's generator streams are stable within a numpy version**, not promised across versions; the results record
   the numpy version (now 2.5.3) and the freeze should too.

## Data access (for experiment 1's access attestation)

- No 2019-2023 option row, cycle, feature or P&L was computed or viewed. All B3 tests use synthetic opportunities; the
  only real run is discovery.
- **The discovery run reads 2023 index closes (Nifty 50 and India VIX) for the features' look-back** (F1 needs 21
  closes, F2 250 before January 2024). `load_period_data` keeps no option row dated before the period start: the 2023
  options file is parsed (its rows carry the closes) but every 2023 option row is dropped before it is stored, and
  nothing from it is printed or written. Without this, F1 and F2 would be `None` on early 2024 decision days. If the
  desk counts parsing as access, the clean fix is A10's index-close files (closes without option rows).

## Discovery output (2024-01-01 to 2026-10-09, 33 opportunities; in-sample, reported only)

Every structure traded on all 33 cycles (no data statuses); F1, F2 known on all 33; F3 true on 8; one SF cycle
(decided 12 Aug 2024) used a settlement price.

| Policy | Total net (Rs) | Traded | Win rate | Max drawdown |
|---|---|---|---|---|
| P1 SC always | 5,055 | 33 | 73% | 13,634 |
| P2 SF always | -18,286 | 33 | 36% | 18,610 |
| P3 BF always | -34,735 | 33 | 9% | 34,735 |
| P4 SC if F1 > 0 | 21,452 | 27 | 81% | 4,802 |
| P5 SC / BF | 15,194 | 33 | 73% | 8,981 |
| P6 SC if F1 > 0, no event | 8,545 | 19 | 79% | 4,802 |
| P7 SC if F2 | -6,603 | 21 | 67% | 18,296 |
| P8 SF if F1 > 0 | -8,848 | 27 | 37% | 9,171 |

Desk reading (some evidence at most; these are the cycles the policies were chosen on, so they prove nothing):
- Volatility trader: P4's edge over P1 (+16,396) is entirely the 6 cycles with F1 <= 0, which lost 16,396 together
  (P4's opposite). Six cycles carry the whole difference: too few to trust.
- Options strategist: buying the fly (P3) lost on 30 of 33 cycles; P5's BF branch cost 6,258 versus P4. On this
  sample the BF branch subtracts value.
- Risk manager: P4's worst cycle is -4,802 and its drawdown 4,802, inside the Rs 10,000 cap; P1's worst is -6,298.
- Statistician / red team: F2 points the wrong way here (P7 loses, its opposite gains 11,658). Policies were picked
  after meeting 1 on this data; only the challenge decides.

## Not met, limits

- Nothing in the six criteria is unmet. The challenge itself cannot run until the protocol is frozen (by design).
- F2 is `None` for nearly all 2019 decision days until A10 adds 2018 closes (B1 limit 1, confirmed by judge 26).
- Discovery is in-sample and must not be read as evidence (protocol section 2).

## Judge 28 minor 2 (13 Oct 2026, after story A10): look-back from index-close files only

- `load_period_data` now opens only the period's own years' option and future files (plus one year after, for late
  exits); the features' look-back before the period comes from the panel's index-close file
  (`research/data/nifty-panel/warmup_closes.csv`, built by `python -m fno nifty-warmup` from NSE's index-close files
  only), now extended from 2017-18 to every session up to 12 Oct 2026 (2,423 sessions; its 2017-18 rows are
  unchanged). The panel reader puts closes-only sessions before the first session it reads.
- Evidence: `tests/research_engine/test_period_data.py` (no earlier year's option file is opened for either period;
  the file equals the panel's closes on every 2026 session); `tests/research_data/test_panel_reader.py` (earlier closes
  come from the file, earlier option rows are never held). The discovery results are byte-identical before and after
  (SHA-256 `814a79a56db4361d9925364642c791d0b82c6a7cb15f98fd18170cfe3353c98b`): the index-close closes equal those the
  panel held.
- **F2 in 2019:** every 2019 daily session now has a VIX close and at least 250 valid earlier VIX closes
  (`test_every_2019_session_has_250_previous_vix_closes`), so F2 has a value on every 2019 decision day. Checked by
  counts only; no 2019 F2 value was computed before experiment 1's freeze.
- Two A10 tests assumed the file held 2017-18 only; they now check the pre-2019 rows as before and the whole range.
- Found while counting for judge 34 (response 48, item 0, blocking): the engine takes 2019-2023 weekly expiries as
  monthly (A5's 50-day listing rule; weeklies were listed up to 69 days ahead then), giving 216 challenge decision days
  instead of about 59. This is for the A5/B2 owner to fix before the freeze.
