# Response 93: weekly NIFTY options and a market-weather signal (desk study, 14 Oct 2026)

Owner: YES to the combined study. The goal is evidence, not luck: defined-risk trades held for days, and a signal that
says when to stay out.

The study is in `research/2026-10-14-weekly-weather/`:
- `PROTOCOL.md`, `study.py` and `report.py` were frozen at commit `650dd8f` (SHA-256 hashes in `FREEZE.md`), before any
  P&L or signal outcome was computed.
- Ledger trials 43-52 were registered at `ea52245`, also before the run.
- It ran once; a second run was byte-identical (`results.json` SHA-256 `8f7b5af2...`).
- Results are in `results.md`, `results.json` and `trades.json` (every trade).

## Verdict

**No edge, and the filter does not help.**
- None of the 5 weekly defined-risk structures made money over 378-394 weekly trades (2019-2026). All fail the frozen
  test.
- The RED "unstable market" signal did not separate bad weeks from good for any structure. For two of them, RED weeks
  were the better ones.
- Strong evidence for "no edge shown". It is not proof that none exists: the predictors were exposed, and fills use
  close prices, not quotes.

## Part 1: weekly options

**Data (answer to "do we have, or can we legally get, weekly prices?").**
- We have them: the NIFTY panel (story A3) holds every NIFTY expiry from 1 Jan 2019, weeklies included, built from
  NSE's public daily bhavcopy files. Weekly NIFTY options began in February 2019, so the first trade is 1 Feb 2019.
- Our A4 15:00 snapshots record monthly expiries only. Groww's read-only API could add live weekly quotes going
  forward, but gives no history.
- Gaps: no bid-ask history, so fills are close prices plus the Rs 1 pad. There are no opening prices either.

**What was used and what was fresh.**
- Monthly 2019-23 options were used up by experiment 1.
- Weekly option prices had never been used in a trial: this study used them once.
- NIFTY and VIX history was already seen (experiment 1 features; desk meeting 2), so the weather thresholds, while set
  by reasoning, were set by someone who had seen that history.

**Results** (1 lot of 65, held to expiry and settled on the index close, C1 charges; net Rs per trade, pre-tax):

| Id | Structure | Trades | Per year | Mean net | SD | t | 2019-23 mean | 2024-26 mean | Mean gross | Mean costs | Worst | Pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W1 | Bought call (1% out) | 378 | 48.6 | -489 | 7,307 | -1.30 | +67 | -1,491 | -452 | 37 | -8,861 | no |
| W2 | Bought put (1% out) | 380 | 48.8 | -665 | 8,915 | -1.46 | -901 | -242 | -631 | 35 | -9,856 | no |
| W3 | Bull call spread (ATM/+100) | 394 | 50.6 | -3 | 3,067 | -0.02 | +277 | -505 | +96 | 99 | -4,363 | no |
| W4 | Bear put spread (ATM/-100) | 394 | 50.6 | -321 | 2,962 | -2.15 | -573 | +132 | -232 | 89 | -3,694 | no |
| W5 | Short iron condor (1.5% out, 100 wings) | 393 | 50.5 | -224 | 2,604 | -1.71 | -223 | -226 | -100 | 124 | -6,348 | no |

What each role reads:
- **Mathematician (strong evidence).** Weekly options were priced close to fair. The mean gross per trade before costs
  is between -631 and +96, so there is no premium to harvest in either direction.
  - Holding to expiry makes costs small (Rs 35-124 a trade, with no exit pads), which is much better than the monthly
    four-leg Rs 810-940. Costs are not the problem here; the absence of a gross edge is.
- **Volatility trader.** Selling protected weekly premium (W5) lost in both periods (-223, -226). Buying it lost more
  (W1, W2).
  - The variance premium that shows in monthly options (response 92) does not show as profit in weekly protected
    condors at 1.5% out.
- **Statistician.**
  - All five t-statistics are between -2.15 and -0.02; the pass needed t >= 2.33.
  - No structure was positive in both periods.
  - Weekly trading gives about 50 independent trades a year, 4 times the monthly rate. But an edge of, say, Rs 100 a
    trade with an SD of Rs 2,600-3,000 would still need about 2,700-3,600 trades at 2 SE, which is 54-72 years.
  - A weekly forward test proves a small edge no faster in practice. Only a large edge (about Rs 500+ a trade on a
    spread) could show within 2-3 years, and nothing here is near that.
- **F&O trader.** Bought weekly options lost their maximum loss (at least 90% of what was paid) in 71% (W1) and 80% (W2)
  of trades. That is the lottery-ticket pattern; the rare big wins (+76,453 on a put in March 2020) do not pay for
  the rest.
- **Risk manager.** Every structure kept its loss within its cap: the worst W5 week was -6,348 on a cap of about 6,500.
  Defined risk works as designed. It just does not make money.

## Part 2: the market-weather signal (GREEN / AMBER / RED)

**The rule was fixed before testing** (PROTOCOL section 5). RED if any of:
- VIX at least 1.30 times its 250-session median;
- VIX up at least 20% in 5 sessions;
- a daily NIFTY move of at least 2% in the last 5 sessions;
- 10-day realised volatility at least 25%.

AMBER uses lower thresholds (1.10x, +10%, 1.25%, 18%) or a scheduled event (budget, RBI policy, election result) in
the holding window. Over 396 weeks the colours were GREEN 157, AMBER 137 and RED 102. RED is 26% of weeks, which is a
lot to sit out.

| Id | GREEN n / mean | AMBER n / mean | RED n / mean | Max-loss hit rate, RED vs rest | RED worse? (Welch t, needs >= 1.645) | Cost of staying out on RED |
|---|---|---|---|---|---|---|
| W1 | 156 / +82 | 134 / -1,304 | 88 / -262 | 69% vs 72% | no (-0.25) | avoids -23,085 |
| W2 | 156 / -196 | 136 / -1,104 | 88 / -821 | 78% vs 80% | no (0.14) | avoids -72,216 |
| W3 | 156 / -46 | 136 / -198 | 102 / +324 | 39% vs 45% | no (-1.24): RED better | gives up +33,021 |
| W4 | 156 / -188 | 136 / -239 | 102 / -633 | 62% vs 57% | no (1.24) | avoids -64,584 |
| W5 | 156 / -512 | 136 / -118 | 101 / +79 | 27% vs 18% | no (-1.29): RED better on average, more max-loss hits | gives up +7,977 |

What each role reads:
- **Statistician (strong evidence for this rule).** For no structure was RED significantly worse.
  - Staying out on RED would have avoided losses in W1, W2 and W4, but those structures lose in every colour, so
    staying out only shrinks a loss; it does not create profit.
  - For W3 and W5, staying out would have cost money: RED weeks pay more premium.
- **Volatility trader.** This is the classic trade-off. Unstable weeks carry fatter premiums, so a protected seller
  earns more on average then, while hitting the maximum loss more often (W5: 27% vs 18%). A "stay out when it's
  stormy" filter gives up exactly the premium that pays for the storms.
- **AMBER is descriptive only, and an observation, not a finding.** It was the worst bucket for the bought options
  (W1 -1,304, W2 -1,104). This was not pre-registered as a test and must not become a rule without a new trial.
- **Behavioural finance.** The owner's instinct ("warn me to stay out when unstable") is sound for survival and calm,
  but this data does not show it adds money for these structures. As a *risk* rule it caps exposure in crashes; as a
  *profit* rule it does nothing here.

## Crash behaviour, reported separately

**2020 (trades entered 17 Feb to 30 Apr 2020; 10 weeks).**
- The signal was RED from 28 Feb onwards, so it warned in time.
- But results inside the crash were mixed in both directions:
  - the bought put made +76,453 in the week of 6-12 March, and then -9,612, -8,195 and -7,782 in April;
  - the bear put spread made about +3,500 a week through March and lost about 3,000 a week in April;
  - the condor swung between -3,655 and +4,679.
- Staying out from 28 Feb would have skipped both the best and the worst weeks.

**2024 (the week containing 4 June 2024, election-result day).**
- RED on the decision day. The bought options were over the cap (not taken).
- The bull call spread made +2,506, the bear put spread lost -2,707, and the condor made +4,298. NIFTY's -5.9% fall
  on 4 June recovered by the 6 June expiry.
- The filter would have skipped a winning condor week.

## Caveats

- Close-proxy fills with a Rs 1 pad. Today's lot (65) and today's charges are applied to 2019-2023, as in experiment 1.
  P&L is pre-tax.
- Before Feb 2020 the expiry settlement is approximated by the NIFTY close.
- `max_loss` counts entry costs only. Settlement charges on in-the-money legs can push a realised loss up to about
  Rs 60 above it; this is immaterial to every result.
- "Gaps" are close-to-close moves; the data has no opening prices.
- The predictors were exposed (section 1 of the protocol), and that exposure could only flatter a pass. There is none.

## Proposed decisions

1. No weekly structure goes forward. Do not register W1-W5 in the playbook.
2. Do not use this RED rule as a profit filter. If the owner wants it as a **survival** warning (fewer trades in
   unstable weeks for peace of mind), that is a risk preference, not an edge, and should be labelled so.
3. This is the third independent "no edge" result on NIFTY options held for days or weeks:
   - experiment 1 (monthly protected premium);
   - response 92 (costs and proof horizon);
   - now weekly, in both directions.
   The honest reading (some evidence): **retail-sized, defined-risk NIFTY option trades with daily-close information
   have no edge we can find or prove.** The project's own rule says the tool shuts down if paper shows no net profit.
   The owner should weigh, now, whether to continue the strategy search at all, or to keep the tool as a risk and
   learning aid only.
4. If the search continues, it needs **new information**, not new filters on the same prices. Possible sources:
   intraday quotes, participant positioning (A8, once 20 days are measured), or company events for stock options.
   Each is a new registered study with its own frozen protocol.
