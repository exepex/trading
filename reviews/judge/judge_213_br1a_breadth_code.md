# Judge 213: BR1a code round: studies, breadth protocol and freezer (judge A)

**Checked:** `story/br1a-protocol` at `a2e4adf9ee3da5834739940adca0202ba751678e` (main merged in), against the passed
text (judge 186 addendum 1) and the builder's claims (response 201). The builder sent it to me directly, and I told
the orchestrator.

**Verdict: FAIL, 1 should-fix (one word in `PROTOCOL.md`), no blocking.** The studies reproduce exactly from the
Drive archive, and the freezer leaves S1 unchanged. The outcome, claims postponed, is the pre-registered rule
working as written.

## My independent re-run of the studies (the "judge verifies" list)

- **Data:** I copied 1,366 legacy and 693 UDiFF bhavcopies from the Drive raw archive (read only), with
  `research/2026-10-15-breadth-sizing/fetch.py`. `run.py panel` checked every SHA-256 against the manifests. The
  UDiFF manifest has one more day than the builder's run (16 Oct), outside the 2024-25 window.
- **`run.py panel` then `run.py studies`:** `study1.json`, `study2.json` and `study3.json` are **identical** to the
  committed files (sorted-key JSON diff: no line differs). That covers:
  - study 1: agreement 96.0%, 22,364 of 23,296 pairs equal;
  - the fallback window 2024-25;
  - primary `trail60`, mean Brier 0.19241, against `cal60` 0.19307 and `market` 0.19409;
  - δ = 0.0038482;
  - the excluded counts;
  - the study 2 table;
  - the whole study 3 loop.
- **One year's SD, lag-1 and look counts, by hand:** 2024's `market`/`trail60` pair has SD 0.0199109 and lag-1
  0.253757, so the inflated variance is 0.000666064, the same as `study2.json`. With z = Φ⁻¹(1 − rate/3) + Φ⁻¹(0.8)
  and look 2 = ⌈z² × v / δ²⌉, I get 248/495, 263/526, 285/569 and 321/642 at 0.02, 0.015, 0.01 and 0.005. These are
  exactly the committed looks.
- **Study 3 at another seed (777 instead of 20261016):**
  - The decision is the same: no rate passes, so claims are postponed.
  - The −d failures repeat at every rate. At 0.02, whole window, −d: 0.0915 against 0.0835 at look 1, 0.082 against
    0.079 at look 2, and 0.1355 against 0.130 at either.
  - Every cell agrees within 2 SE except one, at about 2.0 SE (0.005, whole, −d, either: 0.0705 against 0.088),
    which changes no decision.
- **The outcome screen sees only t+1:** `daily.outcomes` excludes a (u, t) when `sizing.adjusted(a, b)` is true for
  t+1's row. The flag never enters the forecasts (`sizing.forecasts(series)` takes the outcomes only), and it applies
  to every baseline alike.

## The deviations in response 201 (asked to accept or reject)

1. **Item key `target`, not `target_t1`: accepted.** S1's parser takes `[a-z_]+` only. Widening it would edit
   `protocol.py`, which S1's `frozen_files` lists. The title still says "T1 target".
2. **v4's sign of d: accepted.** `batch_means_p` is one-sided for P(T ≤ t), so a negative mean favours the second
   series. `study2.differences` is second minus first, and the claim's meaning is unchanged.
3. **The fallback cuts the inputs too: accepted.** The story's "use 2024-2025 alone" after the proxy failed its gate
   is best read as no old-format row anywhere, so 2024's first 60 sessions are history only (189 + 248 = 437 scored
   sessions). The other reading would feed the failed proxy into `trail60` and `cal60`. The choice was written in
   `primary_baseline_rule` and runner.py's order before the run, and the run reproduces.
4. **The window (437) is shorter than look 2 (495-642): accepted as disclosed.** The circular bootstrap wraps. The
   300-day diagnostic, outside the frozen procedure, shows the failure is not that artefact.
5. **No rolling real windows: accepted.** It follows from 4 (`windows: 0`).

## Freezer (scope 3): S1 unchanged

- **No S1 test was edited.** The only test changes are two new files.
- `EVALUATION` carries the exact S1 strings, so the record and the ledger are byte-identical: "Evaluation protocol
  freeze record", "story S1, criterion 3", "Evaluation protocol v{n}: the three books' comparison rules (story S1)",
  "evaluation-protocol-v{n}", and `requires_gate=True`.
- `protocol.py`, `completeness.py`, `gate.py` and `review_dates.py` are untouched, and `parse_protocol` and
  `PROTOCOL_FILE` keep their names (the F9 agreement).
- Only `wiring.py` maps the names to definitions.
- `python -m fno evaluation check` prints S1 and the gate as before, and `--protocol breadth` prints "complete".
- **RM1's gate is kept:** plant P1 (S1's definition with `requires_gate=False`) fails 3 tests. BR1 has
  `requires_gate=False`, and plant P2 (forcing it True) fails 3 tests.

**My plants** (`tests/evaluation` and the study tests; 81 pass unplanted):

| Plant | Result |
|---|---|
| P1 S1 drops the gate | 3 fail |
| P2 breadth requires the gate | 3 fail |
| P3 the freeze checks S1's items for any protocol | 3 fail |
| P5 Holm without the division by K | 2 fail |
| P6 no centring of the null | 2 fail |
| P4 the CLI's `verify` ignores `--protocol` | 0 fail (note) |
| P7 every bootstrap path starts at 0 | 0 fail (note) |

The study code's other check is my byte-identical re-run.

## Should-fix

**SF1. `PROTOCOL.md` `looks` states the opposite of the result.**
- **Evidence:** it reads "at every rate the sign-flipped null (-d) on the whole window **passed** the limits of 0.025
  per look and 0.045 at either (at 0.02: 0.092, 0.082, 0.136 …)". The numbers are above the limits: −d **failed**.
  `null_size_check`, `DIAGNOSTICS.md` and the README all say "no rate passes".
- **Path:** the owner decides `PROTOCOL.md` item by item, and this item tells them the opposite of what happened, in
  the one item that explains why claims are postponed.
- **Fix:** "passed" becomes "exceeded" (or "failed").

## Notes (one line each, no fix asked)

- **P4:** the CLI's `verify --protocol breadth` is untested. CI uses the `verify(root, definition)` function, through
  `test_the_suite_fails_when_a_frozen_breadth_target_changes`. A one-line CLI test would close it.
- **P7:** no test catches study 3's block starts collapsing. The study was run once and committed, and my re-run is
  the check. A test that path starts vary would guard a rerun.
- **For S1's text owner (the builder's own note, agreed):** S1's `frozen_files` lists `protocol.py` and
  `completeness.py` but not `freeze.py` or `definition.py`, where `requires_gate=True` now lives. This is no weaker
  than before (the gate call was in the unfrozen `freeze.py`), but both belong on the list before S1's freeze.
- **Merge:** the branch conflicts with main in `reviews/claude/README.md`, rows only. Unresolved conflict markers
  fail 4 tests, so keep both sides.
- **What the result means, for the desk (some evidence):** on 2024-25 the daily cross-sectional Brier differences are
  so crash-skewed that `confirmatory_test` over-rejects under −d (0.064-0.088 per `market` member against 0.0067).
  A breadth claim is therefore not available under v1. A new version (a crash-day gate, a rank test, or a calibrated
  threshold) is the owner's decision.

## Gates

- On the trial merge with origin/main f10735e7 (tree 7b958d0, README rows resolved by keeping both sides), `-n auto`:
  pytest 6852 passed; `ruff check` clean; `ruff format --check` 1214 files formatted; `check_imports` clean.
- On the branch itself: 81 of 81 evaluation and study tests pass.

**A re-check needs only the one word in `looks`.**
