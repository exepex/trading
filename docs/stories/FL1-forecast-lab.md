# FL1. Forecast lab and daily reports: sealed ranges, the match report, paper positions

**Lane 1** (a new story; Slack channels and a record-scan change). Owner session: session_01FWkBH4zNAEFSEpjUzVEgnd.
Orchestrator: session_01VG1RqxLFUVdvvPuMRYZtDH. Judge E (session_01HkXMVPDEqVsmJZtghFrGzM). Response 288.
Two parts, each its own judged branch, so part 1 merges alone (owner, DESK_DECISIONS 21 Oct, "Lab universe, report
times and phasing"): **FL1-1, the 15:45 report** (phase 1, about 28-30 Oct) and **FL1-2, the 09:15 report and paper
positions** (phase 2, about 3-5 Nov). The dates are the owner's targets [reasoning only].

## Why (owner, 21 Oct 2026, DESK_DECISIONS rows 262-264 and "Lab universe")

"my focus point is to validate that the forecasting and price prediction engine works as expected, and so that I can
make a decision whether to trust it or not." And: "I'd like to track all positions of Nifty and Bank Nifty, like all
the weekly and monthly call and put options ... for now we focus on 9:15 and 15:45 report".

## What the owner must hear first (evidence labels as in CLAUDE.md)

- **No live forecaster has beaten its base rate yet** [strong: back-fill Briers equal base rates]. Next-day index
  direction is close to a coin flip [strong], so FL1 reports ranges first and direction second.
- **Trust is counted in trading days, not positions or contracts** [strong]. Ten NIFTY positions, or every contract of
  one day, form one correlated outcome, not many samples. Range calibration needs about 60 trading days; a trading edge
  needs 6-12 months. Costs of Rs 800-940 a four-leg trade have so far eaten every edge found [strong: experiment 1,
  E8a]. Every report prints this rule with the day count.
- **Inputs FL1 reads but does not build** [strong, read on main 21 Oct]:
  - **G13b** (ranges for NIFTY and BANKNIFTY at today's close, N+1 and N+3): story text pending with the G13 builder
    (01UkTaDe). Its base, G13, is unmerged (judge 310 FAIL, fixes on its branch).
  - **A22 pre-open data** (NSE's 09:00-09:08 pre-open price, GIFT Nifty, US closes): the A20 builder (013u1Ac2); no
    text yet. FL1-2 waits for it.
  - **Intraday quotes for the lab universe** (every listed expiry up to three months, strikes within 10%, the futures,
    NIFTY and BANKNIFTY): an extension of A16 (A16 builder 01VK88Lx, Groww load measured first). Today A16 records
    NIFTY within 6% only. BANKNIFTY has no weekly options since SEBI's November 2024 rule, so its universe is monthlies.
  - **E8's mark reader and fills** (`story/e8-code-part1`, with the judge). FL1-2 waits for E8's merge and never
    writes a second fill reader.

## Scope

In:
- the command `python -m fno lab close` (FL1-1), run as O1's last daily step, and `python -m fno lab open` (FL1-2),
  run by a morning routine (its design with the O1 builder in phase 2; the owner creates it, with its exact prompt and
  a CLAUDE.md section);
- the two reports and where they go;
- the end-of-day tracking and scoring of every NIFTY and BANKNIFTY contract;
- the lab's paper positions, their fills and exits (FL1-2);
- the two channel IDs and the record-scan allowance.

Out: forecasters, baselines and their scores (G13b); pre-open data (A22); intraday capture of the universe (A16);
real orders (never); UI; a second desk; a second fill reader; AI calls.

## FL1-1: the 15:45 report (phase 1)

| Part | Reuses | New |
|---|---|---|
| Slot and timing | O1's daily run: `lab_close` is its last step, after `candles`, through `NotBefore(15:45)` and `Alerted`, with a `daily.live_from` date (agreed with the O1 builder): no new routine and no new prompt, so the 14:33 routine runs it; the A7 calendar (a closed day records `skipped`) | `fno/forecast_lab/` and its wiring `fno/forecast_lab/wiring.py`; the `lab close` command (O1 runs it as a child process); one step name in `DAILY_RUN_STEPS` and one line in `fno/daily/wiring.py` |
| Forecasts | G13b's sealed records (one JSON per underlying, issue and day, write-once in Drive with an O9 receipt), read only through G13b's reader port `RangeForecasts.sealed(underlying, day, issue)`, never by path | the seal check on `sealed_at`, the GitHub push time of the issue's receipt (O8's push evidence; never a commit date, which the committer's clock sets, and never the self-reported `issued_at`; no push evidence means `late`, never assumed sealed): the 15:45 issue must be sealed before the next session's 09:15 |
| Match report | G13b's scores (quantile score, 25-75 and 5-95 band coverage, `p_up` Brier, per forecaster, horizon and issue) and its outcome closes (NSE's official index close), read and never recomputed; LR1's section pattern and once-only `Publisher` | `MatchReport` sections: each forecast whose target is today against today's close (inside the 25-75 and 5-95 bands, direction of the median, quantile score); each baseline the same way; the running scoreboard and the trust line; then the next session's sealed N+1 and N+3 ranges |
| Contract universe (FL1-1b) | NSE's F&O bhavcopy (A1's archive, the A13 job's reader); Black-76 (`fno/research_engine/implied_vol.py`); G13's quantile scorer | `ContractTracker`: see below |
| Slack | `SlackChannelAlerts(token, channel)` with the same bot token; alerts stay on `build_alert_sender` (#fno-desk) | `FNO_FORECAST_CHANNEL_ID` and `FNO_INTRADAY_CHANNEL_ID` (the IDs the owner created on 21 Oct, passed by the orchestrator; they enter the repository only in FL1-1's code, with the scan change, because the scan refuses them until then) in `fno/forecast_lab/constants.py` (`fno/constants.py` is at 345 of 350 lines), imported into the record scan's `ALLOWED_VALUES` |

**Contract tracking and scoring: part FL1-1b, after FL1-1 merges** (scope freeze, orchestrator 21 Oct: phase 1 is the
15:45 report and the match report; contract scoring needs nothing beyond G13b phase 1 but is not needed to start).
Every NIFTY and BANKNIFTY contract in day d's bhavcopy is tracked: calls, puts and futures, all expiries. The rule
(judge 403.3):
- **Prices are `ClsPric`**, NSE's closing price, never `SttlmPric` (for an untraded option NSE's settlement is a
  theoretical price). A contract counts as **traded** on a day only if its `TtlNbOfTxsExctd` (number of trades) is
  above zero.
- **Only contracts traded on d get a band.** Their implied volatility comes from d's close with Black-76 on the
  same-expiry future's close, or, without one, on the index close times exp(rate x years) (stated). Each band is
  repriced at each of the 15:45 issue's N+1 quantiles of the index, holding that volatility (sticky strike), one session
  closer to expiry. This ignores changes in implied volatility, and the report says so.
- **A future's band keeps its basis:** each quantile times the future's d close divided by the index's d close.
- **Only contracts traded on N+1 are scored**, against N+1's `ClsPric`. The rest are counted as "not scored: untraded
  on d" or "not scored: untraded on N+1", by moneyness bucket and expiry, never dropped silently.
- NSE publishes the bhavcopy in the evening, so a band for day N+1 is scored in the 15:45 report of N+2 (stated).
- Scores: 25-75 and 5-95 coverage, quantile score in rupees, by moneyness bucket and expiry, with the implied range
  as the baseline. The report shows summaries; the full table is a write-once Drive record.

Routing: #fno-forecast gets the 15:45 report. #fno-desk keeps every alert (a failed run, a missing or late forecast, a
missing bhavcopy) and the T1 card.

## FL1-2: the 09:15 report and paper positions (phase 2)

**The 09:15 report** (`lab open`, its routine starting after NSE's pre-open ends at 09:08). It posts G13b's 09:15 issue,
built from A22's inputs, which must be sealed before 09:15: ranges for today's close, N+1 and N+3, NIFTY and BANKNIFTY.
It also posts the top 10 candidates. A 09:15 issue not sealed by 09:15 is never posted as the day's forecast and opens
no position: "not taken: forecast sealed late", alerted.

**The 09:30 fills go to #fno-intraday**, one post right after the fill mark, and the 15:45 report repeats them in one
summary line. Reason: a fill is an intraday event the owner can still act on at 09:30, and #fno-forecast stays at two
fixed posts a day, 09:15 and 15:45.

| Part | Reuses | New |
|---|---|---|
| Fills | E8's `IntradayMarkSnapshots.at(day, mark)` and `DueFill.price(order, DueMark(day, mark))`: ask to buy, bid to sell, size checked, all legs or none, E4c and E4d checks, C1 charges through E4's `FillMaker`; a miss is `Missed(reason, copy)` | one `EntryRange` class `RankedPrice` (rule 5) |
| Exits | E8's `OwnerTimingExits` on its `RetryingClock`, with E8's `SessionOffsetClock` (written by E8's builder, 3c30e5d0): shorts first, protection last; a leg without a valid quote waits for the next mark; past the last expiry, E7's settlement | none |
| Account | R3's shadow-account layout | one lab account `journal/lab/account/`, never in scoreboards A or B or a book's account; records like E2c's (Drive, never the public repository) |
| Hourly line | A16's `MarkObserver.after_mark` (no new routine; an observer failure never stops A16) | `HourlyLine` at 10:15, 11:15, ..., 15:15 in #fno-intraday: each underlying against today's sealed band, open lab positions' marked P&L |

### The lab's rules (judge 403, timed for the 09:15 report)

1. **No look-ahead.** Candidates are ranked on the 09:15 issue only once it is sealed, priced on the previous
   session's last valid A16 mark (the newest prices the forecast could see), and filled at the 09:30 mark. That mark
   comes after the seal, so the forecast never saw the fill's prices. A seal later than 09:15 opens nothing (above).
2. **One named forecaster per lab version, fixed before any result.** `lab_v1` trades **`rv20`**, G13b's
   realised-volatility range, against option prices: a realised-against-implied test (the variance risk premium, which
   experiment 1 found eaten by costs). The option-implied range is **never** a picking source: its expected payoff
   against the same options' prices is about zero by construction, so its top 10 would be picked by noise and costs.
   It stays a baseline. Changing the forecaster is a new lab version (`lab.version`, `lab.forecaster`), never chosen by
   recent scores. Every report names the picking forecaster and version.
3. **Tails reach every wing.** The payoff expectation uses the forecast's quantiles as a distribution, linear in price
   between adjacent quantiles from q05 to q95. Below q05 and above q95 it uses G13's anchored lognormal tail rule,
   applied to the forecast. Each tail carries exactly its 5% mass from its anchor, with
   sigma = (ln q95 - ln q05) / (2 x 1.645) over the horizon, running to zero and to infinity, so every wing is reached.
   Expectations are exact: payoffs are piecewise-linear, with closed-form lognormal partial expectations in the tails.
4. **Ranking and size.** Candidates are verticals and condors (C4's defined-risk shapes) on the universe's expiries,
   **one lot each**. The score is expected net (expected payoff minus entry and exit costs at bid and ask, with C1
   charges) per rupee of maximum loss. Only positive expected nets qualify, and the top 10 are taken (owner, row 264;
   `lab.top_n`).
5. **Entry rule (`RankedPrice`).** A position fills at the 09:30 touch only if its expected net, recomputed at that
   touch, is still positive; otherwise it is "missed, price moved".
6. **Exits and horizon.** Every exit is fixed at entry: `SessionOffsetClock(1 or 3, 15:15, calendar)` from the entry
   session, with retries on later marks. The forecast's target is the 15:30 close; the exit is the 15:15 mark, the last
   one a fill can rely on. The report states this mismatch, scoring the forecast at the close and the position at its
   exit.
7. **Winner's curse shown.** The 15:45 report keeps, by rank 1 to 10, expected net at entry against realised net after
   exit.

## Records and reruns (both parts)

Each run's report text is written once in Drive with its SHA-256 (O9 receipt) before it is posted, so a rerun posts
nothing twice. Lab fills, positions and marks are private records (E2c's pattern).

## Acceptance criteria

FL1-1:
1. On a closed day `lab close` prints "not a trading day" and posts nothing; as O1's step it runs only after
   `candles`, never before 15:45, and a failure is recorded in the run log and alerted once.
2. A forecast sealed after its cutoff is never shown as that issue's forecast; the refusal is recorded and alerted
   to #fno-desk.
3. The report's forecast scores equal G13b's scores on fixed rows (read, never recomputed).
4. The trust line shows the trading-day count against 60 (calibration) and against 6-12 months (edge), every day.
5. A rerun posts nothing a second time, and its records are byte-identical.
6. (FL1-1b) Contract tracking covers every NIFTY and BANKNIFTY contract in a fixed bhavcopy (count checked). Bands
   follow the stated sticky-strike rule (a golden contract checked by hand); a future's band keeps its basis. A
   contract untraded on d or on N+1 is counted "not scored: untraded" by bucket, never scored on a stale or
   theoretical price (test with one untraded option each way). A missing bhavcopy is alerted and scored later, never
   skipped silently.
7. Only #fno-desk, #fno-forecast and #fno-intraday IDs pass the record scan (test). The bot's membership in both new
   channels is checked with one read-only `conversations.info` call in setup, never a test post.
8. O11's replay covers `lab close` on its recorded day; until FL1-1 lands, its strict xfail names it.

FL1-2:
9. A 09:15 issue sealed after 09:15 opens no position: "not taken: forecast sealed late", alerted. Candidates are never
   priced on a mark the forecast saw after its seal, and are filled at the 09:30 mark.
10. Only the configured forecaster ranks, never the implied range, and every report names it.
11. A short condor with its wing beyond q95 gets a lower expected net than flat tails would give, by the closed-form
    tail loss (test).
12. Positions are defined-risk, one lot each. Each is filled with C1 charges, or recorded "not filled" or "missed,
    price moved" with its reason. None appears in scoreboards A or B or a book's account.
13. Every exit is the time exit fixed at entry; a position past its exit mark closes at the next valid mark, and the
    delay is reported.
14. O11's replay covers `lab open` and the fills; until FL1-2 lands, its strict xfail names it.

Both: gates as in CLAUDE.md; no file over 350 lines.

## Judge verifies

Run `lab close` on fixed records for a session day, a closed day and a rerun. Plant a late seal and see it refused and
alerted. Check one contract's band by hand. Check that the scan refuses a fourth channel ID. For FL1-2, read the ranker
against rules 1-7, check costs on both legs of every trade, and check the condor tail test.
