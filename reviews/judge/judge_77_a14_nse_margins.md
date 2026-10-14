# Judge 77: story A14, margins from NSE automatically (branch, before merge)

Date: 14 Oct 2026 (UTC). Branch `story/A14-nse-margins` at f13f225 (code tip e2e4de9; draft PR #90). Claims:
`reviews/claude/response_77_a14-nse-margins.md`. Story: `docs/stories/A-data-foundation.md` A14. Builds on judge 75.

## Verdict: FAIL, two small must-fixes

The calculator is right: my own parser of NSE's real file gives the same rows. The C2 change is only stricter. But:
- one "never looser than the broker" case is untested, and dropping it loosens C2;
- nothing in code stops a manual run from feeding C2 an exposure that a real broker shows 5.6% higher.

## Gates (my runs, `python -B`, caches cleared)

- Full suite: 2,336 passed.
- `ruff check`: clean. `ruff format --check`: 503 files already formatted. Imports: clean.
- `git merge-tree` with current `main`: clean.

## The story's own check: two rows recomputed by hand from the real file

- I downloaded `nsccl.20261014.i1.zip` from NSE myself. Its SHA-256 `d85b883a…0e8b5b` equals the manifest row
  (criterion 6).
- I parsed it with my own script, not the builder's code. For each structure I took the NIFTY 23 Nov 2026 series, the
  legs' risk arrays summed with sides (long +1, short −1), the largest of the 16 scenarios floored at 0, times 65. NOV
  is the signed prices times 65.

| Row | My scan | My NOV | Builder's scan | Builder's NOV |
|---|---|---|---|---|
| SF 100 (sell 22,700 CE and PE, buy 22,800 CE and 22,600 PE) | 822.25 | −6,071.00 | 822.25 | −6,071.00 |
| SC 100 (sell 23,200 CE and 22,250 PE, buy 23,300 CE and 22,150 PE) | 2,650.70 | −3,786.25 | 2,650.70 | −3,786.25 |
| BF 100 (the SF legs reversed) | 831.35 | +6,071.00 | 831.35 | +6,071.00 |

Exposure: 2 short legs × 2% × 22,721.95 × 65 = 59,077.07, equal.

## Per criterion

| # | Criterion | Check | Result |
|---|---|---|---|
| 1 | Computed figures equal an independent figure within a stated tolerance; until then manual only | SPAN and NOV equal Zerodha's (the builder's evidence) and my recomputation. **Exposure is 5.6% below Zerodha's** (Rs 3,316 a lot; Zerodha's base is 23,997.35, unexplained). The job is `workflow_dispatch` only, as the criterion requires | **NOT MET** (stated by the builder) |
| 2 | Hand computation on a planted file | Tests pass. My plants on the formula: scan only (6 failed), the stress scaling the netted figure (1), the stress also scaling exposure (1) | MET |
| 3 | Point in time | My plant switching off the 09:00 `<created>` check is caught (3 failed) | MET |
| 4 | Fail closed | Tests per cause (read); not planted one by one | MET (read) |
| 5 | Append-only | My plant switching off the conflict check is caught (1 failed) | MET |
| 6 | Provenance | SHA-256 equals the manifest (above) | MET |
| 7 | Stressed-margin proposal, C2 config unchanged | The 1.45 proposal is written; config is unchanged. It is still the owner's decision | MET |
| 8 | Size, lint, imports, suite; nothing in forecast or AI | Pass; the diff touches neither | MET |

## The C2 change (the orchestrator's question): only stricter, MET, with one gap in its tests

`MarginRoom` now takes `min(cash + cf, marked equity + cf + marked, cash + cf + liabilities)`, where liabilities are
the negative values of every open trade and of the proposal.
- A minimum with one more term can only be lower, so the change is stricter or equal, never looser.
- My plant dropping the new term is caught (4 failed).
- My check of the case that showed the bug (an open credit trade, then a new debit trade) by algebra: broker free =
  cash − (credit's netted SPAN) − …, and the new term gives the same.
- E4's changed fixtures are equivalent. Old `40000` total becomes scan 40,000, NOV 0, exposure 0. C2 counts 40,000
  and the stressed figure is 1.5 × 40,000 = 60,000, as before.

**Must-fix 1 (test only):** my plant that drops the **proposal's own** liability from that term
(`+ min(0.0, marked)`) passes all 211 risk, margin and desk tests. That is the mirror case: an open **debit** trade
(value +D), then a new **credit** trade (premium P).
- With the proposal's liability, C2 leaves `cash − D`, the broker figure.
- Without it, C2 leaves `cash − D + P`: looser by the whole premium.
- The code is right today; one test with that book makes the property hold for both orders.

## The exposure gap: ruling

**Must-fix 2:** the job is manual, but a manual run commits rows to `research/data/margins/margins.csv`, and C2 then
trusts them. While a real broker charges 5.6% more exposure for the same basket, a row at NSE's base makes C2 looser
than that broker by about Rs 3,316 a lot. Being too loose is the dangerous direction, and the gap is not explained.

Code must stop that until the owner's Groww check answers. Pick one, and say which:
- **(a) Hold the rows.** The job computes and prints but writes no row to `margins.csv` until a config switch,
  with source and date, records that criterion 1 passed. Then it can be scheduled.
- **(b) A broker floor.** Store a broker-observed exposure per lot with its source and time. C2 counts the higher of
  NSE's rule and that figure. A missing or stale observation fails closed.

My recommendation (risk manager, reasoning only): (a) now, because it is simplest and C2 already refuses trades
without rows. Then (b) only if Groww's check shows a higher base too. A "stated haircut" in text alone is not enough:
nothing would enforce it.

## Claims vs reality

| Claim | Reality |
|---|---|
| "SPAN and NOV match Zerodha" | Consistent with my own recomputation of the same file |
| "Equals the broker to the paisa in 8 cases" | Not re-run; the mirror case is untested (must-fix 1) |
| "Only ever stricter" | True by construction (a minimum with one more term) |
| Exposure 5.6% below Zerodha, job manual | True; the manual job still writes rows C2 uses (must-fix 2) |

## Project rules

- New package `fno/nse_margins/` with its own wiring.
- Constants in `fno/constants.py`. Raw data through the A9 librarian with manifest rows.
- Alerts to #fno-desk. No orders, no broker login, no secrets in files.

## Addendum 1 (round 2, branch 2c3865e; fixes in 9f8b815): PASS, to merge with the `constants.py` conflict resolved as both sides

**Must-fix 1 met.** The mirror never-looser tests cover an open debit or credit followed by a new credit or debit, 14
cases. My plant that drops the new trade's own liability (`+ min(0.0, marked)` in `fno/risk/rules.py`): **3 failed**.

**Must-fix 2 met, option (a).**
- `IndependentCheck` reads `config.yaml` `risk.margins.nse_span_check` (source and `passed_on`; both null today).
- Until it holds a passed check dated on or before the day, the job prints the computed rows, writes **none**, and
  fails by name ("N rows computed, none written: no independent broker check has passed").

**My plants (4; `tests/nse_margins`, `risk`, `desk`; Slack token unset): all caught.**

| Plant | Result |
|---|---|
| Own liability dropped | 3 failed |
| The check switched off in the job | 4 failed |
| The check ignores its date | 5 failed |
| The check needs no source | 1 failed |

**Gates.**
- The branch predates today's merges and conflicts with `main` (as of 10:50 UTC) in `fno/constants.py`
  and `reviews/claude/README.md`. Both sides only add lines.
- I merged `main` into a scratch copy (never pushed) and kept both sides. On that merged tree: **full suite 3,092
  passed** (token unset), ruff clean, imports clean (701).

**Still open (owner, not code):** criterion 1's evidence, the owner's Groww check of the exposure figure. Until then
`margins.csv` gets no NSE row, and C2 and C4 keep refusing every trade for want of margin rows (the accepted limit
from judge 83). That is the intended safe state.

**Verdict: PASS** for 2c3865e. The merge must resolve `fno/constants.py` by keeping both sides and run the full suite
on the merged tree. Then I check `main` and CI.
