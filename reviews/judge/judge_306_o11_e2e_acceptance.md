# Judge 306: the O11 end-to-end acceptance harness (story/o11-e2e-acceptance at 5fc86cce)

**Verdict: FAIL, 1 blocking finding (the suite is stale on today's `main`) and 2 minor. Lane 1.** The design is
sound and honest. The fix is the builder's own criterion 4: replace the strict xfails that have turned real with real
checks.

## Run myself
- **At 5fc86cce, alone:** `pytest tests/e2e_acceptance -rxX` gives 10 passed and 16 xfailed (strict), in 6.3 s.
- **At 5fc86cce merged with `origin/main`** (c03d353b, after O1, D3, D4 and D5 merged):
  - **collection error**: `test_expected_missing.py:11` imports `WaitsFor` from `fno.checks.validity_modes`, and that
    class no longer exists (D4 and D5 replaced it with `EnvelopeMode` and `ConstitutionMode`, `fno/checks/wiring.py:84-92`);
  - with that import stubbed, **5 strict xfails now pass**, so the suite fails as designed:
    - O1, twice: the routine steps, and the refused-step alert;
    - D4: Book 2's C4 mode;
    - D5: Book 3's C4 mode;
    - D3c: the override refusal.
  - The replay and failure modules pass on the merged tree: 10 passed.
- `ruff check` and `ruff format --check` on `tests/e2e_acceptance`: clean. Largest file 213 lines;
  `tests/test_code_size.py` passes. No skips.

## My break of a stage (quality rule 4)
I made C4 skip the listing check (`fno/checks/validity.py`: removed `self._listing(proposal)` from the results). Two
tests failed:
- `test_book1_chooses_a_trade_on_the_pack_that_passes_risk_and_every_c4_check`;
- `test_no_nse_file_blocks_the_trade_in_c4_with_its_failure_row_and_c3_alerts`.
Restored; `git status` clean.

## Inputs table against the files (strong evidence)
- **The 3 pm chain is real:** `real_day.py` reads `nifty_20261016_145500.csv`. Contract IDs are restated, with
  prices, sizes and times unchanged (`restated`).
- **Margins and stress factor are real:** the folder `research/data/margins` (`margins.csv`, `stress_factor.csv`,
  `stress/`) is copied.
- **Session calendar is real:** `build_session_calendar()` (`tests/checks/builders.py:16-19`).
- **Charges are real:** `config.yaml`'s (`tests/desk/builders.py:28`).
- **Synthetic or test only, and labelled so:** NSE's F&O file (`nse_file(...)`), the approved strategy
  (`book1_doc()`), and the live features.
- Nothing is called real that is not.

## Findings
**Blocking 1. The suite is stale on today's `main`.** Strong evidence (above). Before the merge, the builder must, on
the branch with `main` merged in:
1. Drop the `WaitsFor` import.
2. Turn the five passing xfails into real checks on the recorded day:
   - O1: run the day's steps through the merged daily run, and show a refused step alerted while the run goes on;
   - D4 and D5: Book 2's and Book 3's C4 modes refuse a trade outside the envelope or constitution;
   - D3: a record with `owner_override` is refused.
3. Show `pytest tests/e2e_acceptance` passing with 0 XPASS.

**Minor.**
1. The F8c xfail names a story under judge B's review. Keep it, but mark the owner in the reason so the next update
   goes to the right builder.
2. Plan finding 2 (NSE contract IDs parse as `OPTIDXNIFTY` in C5's bucket map): I did not reproduce it (reasoning only
   for me). Whoever builds the NSE fallback must re-check it.
