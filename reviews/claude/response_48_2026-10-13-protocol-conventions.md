# Response 48: experiment 1 protocol, conventions to write in before the freeze (proposal)

For the owner and ChatGPT. The engine (stories B1-B3, judged PASS in judges 26 and 28) makes choices the protocol
(`research/2026-10-12-experiment-1/PROTOCOL.md`, version 2.1) either states differently or does not state. Before the
freeze, the protocol must say exactly what the engine does, or nobody can reproduce the verdict from the protocol
alone, and a judge could not tell a convention from a convenient choice made after results.

**Nothing below has been applied to the protocol.** Each item is a proposed text change, with its reason and its
evidence. None of them was chosen after seeing a challenge result: no 2019-2023 option row, feature or P&L has been
computed (B3 claims, response 47).

## 0. Blocking finding: the engine counts weekly expiries as monthly in 2019-2023 (must be fixed before the freeze)

- **What:** the engine finds **216 decision days in 2019-2023** (48, 52, 52, 52, 12 by year) where the protocol expects
  about 60. From April 2019 to early 2023 it takes nearly every weekly expiry as a "monthly" one.
- **Root cause:** A5's `monthly_as_of` calls an expiry monthly if it was ever listed more than 50 days ahead; that
  limit was measured on 2024-26 only (weeklies listed at most 41 days ahead). In 2019-2022, NSE listed NIFTY weeklies
  up to **69 days ahead** (first-seen days to expiry of non-last-of-month expiries; 2023 shows one at 97), so they pass
  the 50-day test. Measured from listing dates only (strong evidence).
- **Effect if not fixed:** ~4x the opportunities, most of them weeklies whose ATM legs do not trade 30-45 days out
  (163 of the 216 decision days have an untraded ATM leg); every challenge statistic would be wrong.
- **Fix (owner of A5/B2 decides):** a monthly identity that holds in both eras, e.g. the last listed expiry of each
  month as of the day, with A5's guard for a weekly moved into the month (30 Apr 2025), or a horizon per period
  measured from the listings. With "last listed expiry of the month over the period", 2019-2023 gives **59** decision
  days (about 60, as the protocol says) and 2024-26 gives 31 (the engine finds 33: the two extra need checking against
  A5's moved-expiry cases). This is a data/code bug for A5/B2, reported here because it decides the freeze.

## 1. F1 uses Black-76 on the same-expiry future, not Black-Scholes on spot (section 5) — a change

- **Today's text:** "ATM implied volatility (average of call and put; Black-Scholes, rate 6.5%, time = calendar days /
  365, solver bounds 1%-200%; only traded legs)".
- **Proposed text:** "ATM implied volatility: the average of the call and the put implied volatility at the ATM strike
  (the listed strike nearest the NIFTY 50 close, the lower one on a tie), each from **Black-76 with the same-expiry
  NIFTY future's close as the forward**, the rate 6.5% only discounting; time = calendar days to expiry / 365; solver
  bounds 1%-200%, a price outside them or a solution at a bound gives no value; only legs and a future that traded that
  day (volume > 0); settlement is never used."
- **Why:** spot Black-Scholes with a fixed 6.5% rate ignores dividends and the futures basis, so it splits call and
  put IV at the same strike. **Evidence (strong, real panel, 12 Oct 2026, ATM 22350):** Oct expiry call / put 14.51 /
  14.47 under Black-76 (gap 0.04) against 13.41 / 15.41 under spot Black-Scholes (gap 2.00); Nov expiry gap -0.11
  against -1.39; all 11 liquid strikes within 300 points agree within 0.26 under Black-76
  (`tests/research_engine/test_implied_vol.py`). A 2-point bias moves F1 > 0 decisions near zero, so it matters for
  P4, P5, P6 and P8.

## 2. C1's 95th percentile: nearest rank (section 8, criterion 3) — missing

- **Proposed text:** "The 95th percentile of the 10,000 C1 totals is the ascending value at index ceil(0.95 x 10,000)
  - 1 = 9,499 (0-based), no interpolation; the policy passes only if its total is strictly above it."
- **Why:** the protocol fixes the bootstrap's index (62) but not C1's; interpolating or using index 9,500 gives another
  threshold. Tests: `test_random_timing_p95_on_continuous_pnl_pins_the_index_exactly` (distinct totals: 9,498, 9,499
  and 9,500 differ, so an off-by-one fails) and `test_a_total_exactly_at_a_threshold_fails` (equal is a fail).

## 3. The exact random draws (section 7 and section 6, C1) — missing

- **Proposed text:**
  - "Opportunity bootstrap: `rng = numpy.random.default_rng(20261012)`; one draw
    `rng.integers(0, n, size=(10000, n))`; resample r takes the opportunities in row r; statistic = mean net per
    opportunity; lower bound = the ascending means at index 62."
  - "Year-block bootstrap (sensitivity): whole calendar years drawn the same way, `rng.integers(0, Y, size=(10000,
    Y))` with the same seed; statistic = total net of the drawn years / their opportunity count; index 62."
  - "Monte Carlo error (reported only): the sample standard deviation (ddof 1) of the lower bounds with seeds
    20261012 + 1 to + 20."
  - "C1: `rng = default_rng(20261012)` for each conditional policy; per sequence `order = rng.permutation(n)`; the
    policy's actions in sorted code order (BF before SC before SF) take consecutive slices of `order` with the policy's
    counts; a sequence's total is plain left-to-right float addition of its chosen P&L in that order."
  - "The numpy version is recorded at the freeze and in every results file (generator streams are guaranteed only
    within a version)."
- **Why:** "seed 20261012 (numpy default_rng)" alone allows many draws giving different bounds. The last C1 detail
  matters to the last digit: Python 3.12's `sum()` compensates rounding, plain addition does not (found while writing
  the judge-28 golden test).

## 4. Which period and which year a cycle belongs to (sections 2, 7 and 9) — missing

- **Proposed text:** "An opportunity belongs to the period of its decision day (a cycle decided in December 2023 is a
  challenge opportunity even if it exits in January 2024). A cycle's P&L is dated by its exit day: calendar year for
  'results by year' and the year-block bootstrap, Indian financial year (April-March) for the tax scenario."
- **Why:** the challenge's last cycles exit in 2024; without a rule, a builder could count them in either period.

## 5. Drawdown and losing-run definitions (section 7) — missing

- **Proposed text:** "Maximum drawdown: the largest fall of cumulative per-opportunity net P&L from its previous peak,
  the start (0) counting as a peak, in rupees. Longest losing run: the most consecutive opportunities with net < 0
  (an opportunity with 0, traded or not, ends a run). Win rate: traded opportunities with net > 0 / traded
  opportunities."

## 6. Two consequences the protocol should state openly — clarifications

- **P6's event-filter test needs removed trades.** If F3 removes no trade from P4, the sum is 0, not below 0, so P6
  cannot claim the filter and fails criterion 6. That is what "< 0" means; say it so nobody reads it as "not applicable".
- **F2 in 2019:** F2 needs 250 previous VIX closes; the panel starts 1 Jan 2019, so F2 is `None` ("not met") on nearly
  every 2019 decision day until story A10 adds 2018 closes. The freeze should wait for A10 (or the protocol should
  state that 2019 P7 decisions are "no trade" by data, which would weaken P7's test).

## 7. Freeze recipe the engine enforces (section 10) — clarification

- The challenge runs only if the protocol holds a line `frozen at commit <A>`, commit A exists and precedes the run,
  and the protocol at A equals today's protocol without that line; ledger rows 22-31 carry `protocol_commit` = the
  commit that added the line (B4: unchanged since then).
- Steps: (a) commit the final protocol (A); (b) add `frozen at commit A` and FREEZE.md (hashes, access attestation),
  commit (F); (c) set `protocol_commit` = F in ledger rows 22-31, commit; (d) `python -m fno research run
  2026-10-12-experiment-1 --period challenge`; (e) commit the results and the ledger's first-run record.

## 8. A minimum traded volume for F1's legs (judge 34 desk note) — new, the threshold is the owner's and ChatGPT's

- **Today:** F1 needs each ATM leg to have traded (volume > 0); one contract is enough. On 14 Jan 2019 the ATM call
  traded 2 contracts (judge 34): F1 can rest on a single stale print.
- **Counts (decision days on true monthly expiries, the smaller of the ATM call and put volume; no price, feature or
  P&L computed):**

  | F1 loses its value when the smaller ATM leg volume is below | 2019-2023 (59 days) | 2024-26 (31 days) |
  |---|---|---|
  | 1 contract (today's rule) | 8 | 0 |
  | 10 | 10 | 0 |
  | 50 | 21 | 1 |
  | 100 | 24 | 2 |
  | 500 | 34 | 14 |

  Open interest instead (smaller ATM leg, units): below 1,000: 11 and 0 days; below 10,000: 29 and 8; below 50,000:
  39 and 16.
- **Trade-off:** a higher threshold makes F1 an honest price but removes F1 (so P4-P6 and P8 do not trade, and P5
  does nothing) on up to 40% of challenge days at 100 contracts; 2019-2022 ATM options 30-45 days out were thin. Some
  evidence that thin prints distort F1; no outcome was looked at to choose. **Proposal (reasoning only):** 10 contracts
  (removes 2 more challenge days than today, none in discovery), or 50 if the desk prefers cleaner prices at the cost of
  13 days. The owner and ChatGPT pick the number before the freeze.

## Access attestation additions (section 10)

- 13 Oct 2026, at the orchestrator's request (judge 34 desk note): Claude read the 2019-2024 option files to list each
  2019-2023 decision day's expiries and the volume and open interest of its ATM legs; only dates, counts of listing
  days and leg volume/open-interest counts were computed and printed (above). No price, feature value or P&L of
  2019-2023 was computed or viewed. This also found the weekly/monthly bug in item 0.
- The discovery run (`results_discovery.json`) read 2023 NIFTY 50 and India VIX closes for the features' look-back by
  parsing the 2023 options file; every 2023 option row was dropped before being stored and nothing from it was printed
  or written. Once A10 lands, the look-back will come from index-close files only (judge 28 minor).

## Asked of the owner and ChatGPT

Fix item 0 (A5/B2 owner) and accept, change or reject each of items 1-8, with reasons. If accepted, the protocol becomes version 2.2 with these
texts, and the freeze follows A10.
