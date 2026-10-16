# Response 235: A14c, which quantity sets the stress factor k (a question for the owner, with numbers)

Builder session 01Vm1WnH8i9waM8EJG8zwWqg, 16 Oct 2026. Research only; nothing here changes code or config. The
orchestrator puts the choice to the owner. A14c's head (249eaf8c, `story/a14c-stress-recompute`) waits for the answer.

## Why the question

The owner's rule (15 Oct): "WHOLE MARGIN. k multiplies the whole margin (scan plus exposure), as it was measured."
A14c, as built, measures the rise of C2's counted margin, `initial() = max(0, scan - NOV) + min(0, NOV) + exposure`.
On the archive, that gives **k = 3.55** in Jan-Apr 2020 (BF 200 entered 8 Apr 2020: 23,669 -> 83,970).

The cause (strong evidence, the files' figures): for a debit structure (BF), the bought legs' value (NOV 56,911) nearly
equals the scan (57,720) at entry, so `initial()` is about the exposure alone (22,860 + 809). The ratio's denominator
is small, and the rise is the position losing value, not NSE raising rates. C2c's formula never multiplies NOV.

## The three measures

- **A14c as built:** `initial()` on the peak day / `initial()` at entry.
- **Response 77's:** (scan + exposure) on the peak day / at entry. It ignores NOV. Response 77's anchors reproduce with
  this measure (1.4073 and 1.1272, read to the window's end).
- **Proposed:** the smallest k with `max(0, k*scan_e - NOV_e) + min(0, NOV_e) + k*exp_e >= initial()` on every later
  day. That is, the k that C2c's own formula needed at entry to cover what was later blocked.

Every structure (SF, SC, BF) and width (100, 200, 300), every session as an entry, held to the 21-day exit, A14c's own
code. 26,676+ holdings completed, 0 dropped. Exposure under the coded rule (2%, 3% beyond 10% out of the money), and
under a flat 2% and a flat 3% (the doubt about what NSE charged from Jun 2020 to 2023).


### A14c as built: initial() ratio

| Window | coded 2/3% | flat 2% | flat 3% | holding that sets it (coded) |
|---|---|---|---|---|
| Jan-Apr 2020 | 3.5477 | 3.2769 | 2.5750 | BF 200 entered 2020-04-08 (debit) |
| Jun 2020-2023 | 1.4770 | 1.4770 | 1.3258 | SC 200 entered 2021-05-31 (credit) |
| May-Jun 2024 | 1.3872 | 1.1547 | 1.1098 | BF 100 entered 2024-06-05 (debit) |
| Sep-Oct 2026 | 1.0589 | 1.0589 | 1.0393 | SC 300 entered 2026-09-09 (credit) |

### Response 77: gross (scan+exposure) ratio

| Window | coded 2/3% | flat 2% | flat 3% | holding that sets it (coded) |
|---|---|---|---|---|
| Jan-Apr 2020 | 1.3032 | 1.2162 | 1.2166 | SF 100 entered 2020-04-07 (credit) |
| Jun 2020-2023 | 1.6815 | 1.6815 | 1.4892 | SC 100 entered 2020-11-04 (credit) |
| May-Jun 2024 | 1.4291 | 1.2197 | 1.1528 | BF 300 entered 2024-06-05 (debit) |
| Sep-Oct 2026 | 1.1252 | 1.1252 | 1.0761 | BF 100 entered 2026-09-02 (debit) |

### Proposed: smallest k C2c's formula needs

| Window | coded 2/3% | flat 2% | flat 3% | holding that sets it (coded) |
|---|---|---|---|---|
| Jan-Apr 2020 | 1.7483 | 1.6688 | 1.6008 | BF 200 entered 2020-04-08 (debit) |
| Jun 2020-2023 | 1.4770 | 1.4770 | 1.3258 | SC 200 entered 2021-05-31 (credit) |
| May-Jun 2024 | 1.3872 | 1.1547 | 1.1098 | BF 100 entered 2024-06-05 (debit) |
| Sep-Oct 2026 | 1.0589 | 1.0589 | 1.0393 | SC 300 entered 2026-09-09 (credit) |

**Rounded up to the next 0.05**, the maximum over these windows (coded rule): as built **3.55**, response 77's **1.70**,
proposed **1.75**. Flat 3%: 2.60, 1.50, 1.65. Flat 2%: 3.30, 1.70, 1.70.

## What each would have reserved for BF 200 (8 Apr 2020)

Entry parts per lot: scan 57,720, NOV 56,911, exposure 22,860. The real block at its peak (4 May 2020) was **83,970**.
Reserve = `max(0, k*57,720 - 56,911) + k*22,860`:

| k | Reserved | Against 83,970 |
|---|---|---|
| 1.45 (the owner's seed, in force today) | 59,930 | short 24,040 |
| 1.70 (response 77's measure) | 80,075 | short 3,895 |
| 1.75 (proposed) | 84,104 | covered (+134) |
| 3.55 (as built) | 229,148 | 2.7x the real need |

## Reading of the table (each marked)

- Proposed and as built agree everywhere except Jan-Apr 2020 (strong evidence: the table). For credit structures
  (SF, SC), NOV is negative, so both are the same ratio. They differ only where a debit's NOV offsets the scan.
- Response 77's gross ratio is larger than the proposed one in Jun 2020-2023 (1.68 vs 1.48, SC 100 entered
  4 Nov 2020). There it counts scan that the bought legs' value offsets, so it over-reserves credits. In 2020 it
  under-reserves the debit BF 200 by 3,895 (strong evidence: the figures above).
- Response 77's 1.265 for 2020 was read only to the end of April; held to the exit, the same measure gives 1.303.
  Verified later on 16 Oct (strong evidence): gross read to 30 Apr 2020 gives 1.2650 for every structure (SF/SC
  entered 7 Apr), so all three of response 77's anchors reproduce to 0.001.
- The exposure doubt matters: at a flat 3%, every measure falls, and the proposed one falls from 1.75 to 1.65
  (strong evidence: the table). The coded rule is the safer choice until NSE's 2020-2023 rate is known.
- **Not covered:** Jan 2024-Aug 2026, apart from May-Jun 2024. The real full run reads every session since 2020, so
  its maximum may be higher than any number here (strong evidence that the windows are a subset; no evidence either way
  on the size).

## Recommendation (reasoning, backed by the table)

The proposed measure. It is the only one of the three that measures what the applied formula needs: it covers the one
case where a debit's real block rose (BF 200, 2020), and it does not inflate the factor through a small denominator.
It keeps the owner's intent ("k multiplies scan plus exposure"); only the measuring changes. The cost: k about 1.75
instead of 1.45, so every stressed margin rises about 20%. This is a lane-1 change to the A14c story text and code
(about 20 lines: the rise becomes the needed k), plus the judge. It fits before 7 Nov if the owner answers by about
22 Oct.

Owner's choice: (a) proposed, smallest k needed (about 1.75); (b) response 77's gross ratio (about 1.70); (c) as built
(3.55, would block nearly every trade); or another rule.
