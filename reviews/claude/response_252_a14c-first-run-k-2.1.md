# Response 252: A14c's first full run applied k = 2.1. What sets it, and whether it is real (for the owner)

Builder session 01Vm1WnH8i9waM8EJG8zwWqg, 16 Oct 2026. Run 38872124236 (workflow_dispatch, full), data commit df9bfaff:
row `2026-10-16, 2.1, computed 2.1, unrounded 2.081729, applied`, peak `PDS 300 entered 2020-04-08 peak 2020-05-04`.
C2 and C4 use it from 17 Oct (the latest row dated strictly before the decision day).

## Run facts (strong evidence: the run's step times and evidence file)

- 1,680 sessions read (2 Jan 2020 to 15 Oct 2026), 58,345 holdings completed, 70 dropped (named in the evidence; 1 Aug
  2025's file has no series for the 25 Sep 2025 expiry).
- The factor step took 1 h 51 m 48 s, which is **3.99 s per file** with 8 downloads ahead. The whole run took 1 h 57 m,
  well inside the 330-minute limit. A weekly incremental run (about 45 files) should take about 3 minutes.

## Why the windows missed it (strong evidence)

My window runs (response 235) used response 77's set: SF, SC and BF at widths 100, 200 and 300. The full run uses every
structure C2 trades: the STR1 one- and two-leg codes LC, LP, CDS, CCS, PDS and PCS, and widths in steps of 50. The top
of the table is STR1 codes in 2020:

| Holding | Needed k |
|---|---|
| PDS 300 entered 8 Apr 2020 | 2.0817 |
| PCS 150 entered 1 Jun 2020 | 1.9308 |
| PDS 200 entered 8 Apr 2020 | 1.8456 |
| PDS 100 entered 7 Apr 2020 | 1.8338 |
| BF 200 entered 8 Apr 2020 | 1.7483 |
| first holding after 2020: PDS 150 entered 9 Mar 2022 | 1.6915 |

## Is 2.08 real? Partly. The cash block was real; most of the rise came from two things that do not apply today

PDS 300 is a put debit spread: bought 8800 PE, sold 8500 PE, the 28 May 2020 expiry. Per lot of 65, from NSE's own files:

| | Scan | NOV | Exposure | What C2 counts |
|---|---|---|---|---|
| Entry, 8 Apr 2020 | 28,860 | 34,424 | 11,430 | 11,430 |
| Peak, 4 May 2020 | 31,980 | 1,758 | 19,227 | 49,449 |

1. **2020's short-option minimum.** In 2020 the scan was NSE's gross minimum: 5% of the index per sold option (444 and
   492 a unit), charged even though the spread can never lose more than 300 a unit. NSE dropped this minimum from
   1 Jun 2020 (0 in every file since). Under today's method the same holding needs **1.68**.
2. **NSE's price for a spread can exceed what the spread can be worth.** The file's prices at entry value the 300-wide
   spread at 529.6 a unit. A put spread can never be worth more than its width (300). NSE uses these prices for NOV,
   and the 14 Oct broker check matched Groww's SPAN after NOV to the rupee. So the 11,430 block at entry was what the
   broker charged. The prices are often inconsistent across strikes, though: 63% of adjacent steps in March 2020, and
   22% even on 14 Oct 2026 (strikes within 10% of the index). Examples on 8 Apr 2020: 8500 CE 826, 8400 CE 1,217,
   8600 CE 1,118. When NOV is held to the spread's width, the need is **1.71** with the 2020 minimum and **1.53**
   without it.
3. **The rest is a real rule effect of today.** Exposure rose from 11,430 to 19,227 (1.68x). The index rose 12%, and
   the sold 8500 PE moved more than 10% out of the money, where NSE charges 3% instead of 2%.

**BF 200 (8 Apr 2020), the earlier 1.75, splits the same way:**

| Basis | Needed k |
|---|---|
| As charged | 1.748 |
| Today's method | 1.402 |
| NOV held to its width (200) | 1.203 |
| Both | 1.039 |

**Reading (each marked):**
- Under the owner's rule (everything since 1 Jan 2020, measured as charged), 2.1 is the correct output of the code
  (strong evidence).
- About 0.4 of it comes from a 2020-only NSE rule that no longer exists (strong evidence: every file since 1 Jun 2020
  has the minimum at 0).
- About 0.15-0.3 more comes from NSE's inconsistent prices at entry. These are real broker blocks, but they turn on
  whichever stale price a strike carried (some evidence).
- Measured under today's method, the factor would probably be about 1.70-1.75. The largest holding after 2020 is
  1.6915 (PDS 150, 9 Mar 2022), and the PCS 150 of 1 Jun 2020 (1.93) also rides on a price inversion: its bought 9450 PE
  is priced above its sold 9600 PE (reasoning: not re-run).

## The owner's choice (any fall is held until the owner approves it with a DESK_DECISIONS row)

1. **Keep 2.1** (the rule as decided: every session since 2020, as charged). Safest; about 45% more margin than 1.45, so
   fewer lots.
2. **Measure 2020's minimum period with today's method** (or start the windows on 1 Jun 2020). The likely result is
   about 1.70-1.75, to be confirmed by one more full run (about 2 h on Actions). This is a lane-1 text and code change.
3. **Also hold each entry's NOV to its structure's no-arbitrage bound** (no more than a vertical spread's width, and so
   on). This lowers it further. Recommendation (reasoning): not alone, because NSE's broker charges use those very
   prices, so a cap would understate a real block.

Builder's recommendation (reasoning, backed by the figures above): **option 2**. The 2020 minimum is an NSE method that
ended on 1 Jun 2020. The owner's own words ("as it was measured", "today's method" in response 77) point to measuring
history under the rules that apply now. Exposure's real 3% step stays in.
