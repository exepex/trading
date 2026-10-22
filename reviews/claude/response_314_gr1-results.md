# Response 314: GR1 sharper ranges, results of both runs (for judge B)

**From:** G13/G13b builder, session_01UkTaDeTRF9ksDgQB9cTU5C · **Branch:** `story/gr1-sharper-ranges` · **Protocol:**
`research/gr1/PROTOCOL.md` (deviations 1-4), code frozen at 08731ac6 (judge 442.1 PASS) · **Run 1:** 476aa240,
`selection.json` sha256 `083756a0...de65c`, reproduced byte for byte by judge B (442.2) · **Run 2:** 56fe1c8f, run
once, `final.json` sha256 `55f636f3...4f62` · **Records:** back-fill sha256 `6f39e4de...2c27` in both runs.

## The answer

**No conditioned scaling makes G13b's implied range sharper. Implied stays as it is; nothing goes live, so there is
no sealed-shadow proposal (owner rule f2293cea applies only to a passing winner)** [strong evidence for these
candidates on 2025-26; exploratory, because the data was spent before the study].

| Cell | 2024 winner | 2025 - 20 Oct 2026: paired mean QS, winner minus implied | Two-sided p (bootstrap) | Holm | Verdict |
|---|---|---|---|---|---|
| NIFTY N1 | C8 (intraday RV vs implied) | +1.84e-5 (+0.47%, worse), 95% CI [-0.13e-5, +3.40e-5], 437 days | 0.048 | no | not sharper |
| NIFTY N3 | C9 (weekday) | +1.16e-5 (+0.17%, worse), CI [-0.93e-5, +3.68e-5], 440 days | 0.319 | no | not sharper |
| BANKNIFTY N3 | C10 (VIX tercile) | +1.26e-5 (+0.17%, worse), CI [-1.04e-5, +4.22e-5], 424 days | 0.335 | no | not sharper |
| BANKNIFTY N1 | none (every candidate and implied outside the 50% band on 2024) | not tested | - | - | not shown at this sample size |

Each 2024 winner turned the wrong way on new data. That is the classic sign of selection on noise: the 2024 gains were
0.2-0.8% of QS, the same size as the year-to-year wobble. NIFTY N1's C8 came close to being significantly *worse*
(p 0.048 before Holm, not after; its percentile interval just includes 0, so the two bootstrap
summaries sit on either side of the 5% line).

## What the numbers do say (descriptive, never decided on)

- **Implied's own calibration on 2025-26 is good.** 90% coverage 0.919 / 0.909 / 0.927 / 0.915 (NIFTY N1, NIFTY
  N3, BANKNIFTY N1, BANKNIFTY N3), and 50% coverage 0.47-0.54. On N1 it runs slightly wide (0.92-0.93 against 0.90).
- **Every constant shrink (C1, C2) scores a little better on the N1 cells** (-0.13% to -0.20% QS, coverage
  0.91), because implied runs slightly wide. That is a 3-8% narrower 90% range: NIFTY 590 against 611 points,
  BANKNIFTY 1,490 against 1,611. It was not the 2024 winner in any cell, so it is **not tested and not a finding**
  [reasoning only]. A shrink like this is what the variance risk premium would predict; it is worth a fresh,
  prospective trial only on data not yet seen (from 21 Oct 2026), if the owner wants one.
- **BANKNIFTY N1's best on 2025-26 was C9 / C11(C4+C9)** (-0.5% QS). These are post-hoc, so they are not evidence.
- **C9's split at the expiry breaks** (reported, never decided on): NIFTY N1 -3.2e-5 before 1 Sep 2025 and +0.8e-5
  after. The weekday effect changes sign with the expiry day, which is consistent with an expiry artefact rather than
  a stable weekday rule.

## N0: how much a 09:15 range narrows (measurement, NIFTY)

| | days | 90% inside | 50% inside | median 90% width | width / N1's |
|---|---|---|---|---|---|
| N1 (15:45 the day before) | 442 | 0.919 | 0.529 | 611 points | 1 |
| N0-A (implied moved to 09:15, share 0.607) | 442 | **0.900** | **0.507** | 475 points | **0.779** |
| N0-B (+ one fitted scale) | 442 | 0.889 | 0.484 | 458 | 0.751 |
| N0-C (+ gap and S&P overnight) | 442 | 0.869 | 0.471 | 448 | 0.730 (CI 0.726-0.737) |

N0-A was carried from 2024 as the rule says and is the honest one: same coverage as N1, 22% narrower, no fitted
parameter. N0-B and N0-C are narrower only by giving up coverage. N0-C's 0.869 is below the 0.87 band, as it was on
2024 (0.861). This supports phase 2's 09:15 issue (A22) using N0-A's rule [some evidence: one index, 442 days, a
measurement, not a contest].

## Checks and notes

1. **NIFTY's Tuesday break, confirmed from the files.** The first F&O file whose nearest NIFTY expiry is a Tuesday is
   29 Aug 2025 (expiry 2 Sep 2025); before it the nearest is a Thursday. The pinned break (1 Sep 2025) is right for
   target days. The 29 Aug row falls in the old piece; it is one day and only matters for C9's descriptive split. One
   gap: `splits.py`'s docstring says run 2 "reports the first Tuesday expiry it reads", but `final.json` does not
   carry it. I read it from run 2's own expiry cache (`work/gr1/expiries.json`, from the same files) for this note.
   The code is frozen, so I have not changed it; the docstring promised more than the code does.
2. **Late-Dec 2024 rows (judge note 1).** The seal works by issue day, so select-period rows issued in the last
   sessions of 2024 have target closes in early Jan 2025, inside the final period: N3 rows of 27, 30 and 31 Dec, and
   the N1 row of 31 Dec (target 1 Jan 2025). Run 1 read those outcomes. That is at most three rows per cell, it touched
   only the selection, and it does not weaken the final verdict, which went against every winner anyway.
3. **Dropped days in run 2.** VIX-based candidates lost 10-12 days (2.3-2.7%) for "India VIX of d", and C8 lost 6
   for intraday RV or implied's N1 variance. All are under the 5% gap rule.
4. **Ledger.** Rows 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 68, 69 and 70 have their first run recorded (22 Oct
   2026, commit 08731ac6, the frozen code). Row 67 (FII/DII, not tested) has no run. `LEDGER.md` carries the
   result; `DATA_SPEND.md` marks the global cues `exposed`.

## What I propose

- Close GR1 as "no sharper candidate". Merge the branch (research files, tests, results) to `main` after your PASS.
- No live change. G13b's implied stays the range of record.
- Owner question (Q-GR1): a prospective trial of one constant N1 shrink (about 5%) on data from 21 Oct 2026 on,
  registered before any of it is read. It is cheap; it has a reason (implied runs slightly wide on N1) but no
  evidence yet.
