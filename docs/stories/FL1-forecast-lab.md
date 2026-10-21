# FL1. Forecast lab and daily reports: sealed ranges, paper positions, the match report

**Lane 1** (a new story; Slack channels and a record-scan change). Owner session: session_01FWkBH4zNAEFSEpjUzVEgnd.
Orchestrator: session_01VG1RqxLFUVdvvPuMRYZtDH. Judge E (session_01HkXMVPDEqVsmJZtghFrGzM). Response 288.

## Why (owner, 21 Oct 2026, DESK_DECISIONS row 262)

"my focus point is to validate that the forecasting and price prediction engine works as expected, and so that I can
make a decision whether to trust it or not." The owner wants three things. First, forecasts before the open, after the
first 15 minutes, and after the close. Second, a report matching them against the close. Third, a lab of the top
10-20 paper positions. All of it goes to two new Slack channels, for NIFTY and BANKNIFTY, at N+1 and at most N+3.

## What the owner must hear first (evidence labels as in CLAUDE.md)

- **No live forecaster has beaten its base rate yet** [strong: back-fill Briers equal base rates]. Next-day index
  direction is close to a coin flip [strong], so FL1 reports ranges first and direction second.
- **Trust is counted in trading days, not positions** [strong]. 10-20 NIFTY positions on one day are one correlated
  bet, not 20 samples. Range calibration needs about 60 trading days. A trading edge needs 6-12 months, and costs of
  Rs 800-940 a four-leg trade have so far eaten every edge found [strong: experiment 1, E8a]. Every report prints this
  rule with the day count.
- **Three inputs FL1 needs do not exist yet** [strong, read on main 21 Oct]:
  1. **G13b** (ranges at N+0, N+1 and N+3 for NIFTY and BANKNIFTY, sealed three times a day) has no text and no code.
     G13 itself is unmerged (judge 310 FAIL, fixes on its branch), and it covers NIFTY only, h1/h5/expiry horizons, 7
     levels and the 3 pm chain only.
  2. **A22 pre-open data** (GIFT Nifty, NSE pre-open; A20 builder 013u1Ac2) has no text. Until it is live, an 08:45
     forecast knows nothing the 15:45 forecast of the evening before did not, so **FL1 runs 09:30 and 15:45 only**;
     the 08:45 slot starts with A22's first live day (owner, DESK_DECISIONS row 264).
  3. **BANKNIFTY has no intraday quotes yet.** A16 records NIFTY within 6% only. The owner chose to extend A16 to
     BANKNIFTY (row 264; A16 builder 01VK88Lx, Groww load measured first). Until that is live, lab positions are NIFTY
     only. BANKNIFTY ranges are still forecast (G13b, G13 builder 01UkTaDe) and scored against NSE's archived
     all-index close files.
- E8's bid/ask reader for A16 marks (`IntradayMarkSnapshots`) is only on E8's branch. FL1 reuses it after E8 merges
  and never writes a second one.

## Scope

In:
- one command `python -m fno lab <slot>` for the slots `open` (09:30) and `close` (15:45), each run by its own
  Claude routine that the owner creates, with the exact prompts and a CLAUDE.md section. `pre_open` (08:45) is added
  in FL1d, with A22;
- sealing: the run calls G13b's record command for its slot and refuses to post a forecast whose seal is after its
  cutoff;
- the lab's paper positions at 09:30 and their exits;
- the 15:45 match report and running scoreboard;
- the hourly #fno-intraday line;
- the two channel IDs.

Out: building forecasters or baselines (G13b), pre-open data (A22), BANKNIFTY intraday quotes, real orders (never),
UI, a second desk, a second fill reader, AI calls.

## Design (reuse first; new code only where nothing exists)

| Part | Reuses | New |
|---|---|---|
| Slots and timing | O1's `Alerted` step rule (recorded and alerted once, the run goes on); the A7 calendar (a closed day prints "not a trading day") | `fno/forecast_lab/` package and its wiring `fno/forecast_lab/wiring.py`; `lab` CLI |
| Forecasts | G13b's sealed records: one JSON per (underlying, issue 0930 or 1545, day), write-once in Drive with an O9 receipt, quantiles q05-q95 and `p_up` per forecaster and horizon. FL1 reads them only through G13b's reader port (`RangeForecasts.sealed(underlying, day, issue)`), never by path. The 1545 issue has no N0 | a seal-time check per slot on `sealed_at`, the receipt's commit time on `main` (never the self-reported `issued_at`): the 09:30 issue before 09:45, the 15:45 issue before the next session's 09:15 (08:45, from FL1d: before 09:15) |
| Positions (09:30) | E8's `IntradayMarkSnapshots.at(day, 09:30)` and `DueFill.price(order, DueMark(day, 09:30))` (ask to buy, bid to sell, size checked, all legs or none, E4c and E4d checks, C1 charges through E4's `FillMaker`; a miss is `Missed(reason, copy)`); C4's defined-risk shapes; R3's shadow-account layout for a research account | `RangeRanker`: for each defined-risk candidate (verticals and condors on the next weekly and monthly NIFTY expiries within A16's 6% band), the expected payoff at its horizon under the sealed 5-95% quantiles (linear between quantiles, flat tails at the 5% and 95% levels, stated as a modelling choice), minus entry and exit costs at bid/ask. Ranked by expected net per rupee of maximum loss; the top 10 (owner, row 264; config `lab.top_n`). The entry rule is one new `EntryRange` class, `RankedPrice`: a position fills only at the touch the ranker priced on the same 09:30 copy, or better (there is no C2 approval in the lab). One lab account `journal/lab/account/`, never in scoreboards A or B |
| Exits | E8's `OwnerTimingExits` (shorts first, protection last; a leg without a valid quote waits for the next mark; past the last expiry, E7's settlement); every exit is fixed at entry: the 15:15 mark of N+1, or of N+3 if the horizon is N+3 | one `FillClock` strategy beside E8's `OwnerTimingClock` (a fixed session offset and time), written by E8's builder in E8's module (one builder per function); time exit only, so no stop the lab cannot enforce |
| 15:45 match report | G13b's scores (quantile score, 25-75 and 5-95 band coverage, `p_up` Brier per forecaster, horizon and issue) and its outcome closes (NSE's official index close), read and never recomputed; the post-mortem's section pattern and once-only publish (LR1 `Publisher` posts once and records a marker) | `MatchReport` sections: forecasts vs the close (inside the 25-75% and 5-95% bands, direction of the median, quantile score), each baseline the same way, positions' paper P&L after costs at the 15:30 mark (exit value at bid for long legs, ask for short ones), the running scoreboard and the trust line, then the next day's sealed forecasts |
| Hourly line | A16's `MarkObserver.after_mark` (no new routine; an observer failure never stops A16) | `HourlyLine` at 10:15, 11:15, ..., 15:15: NIFTY against today's sealed band, open lab positions' marked P&L |
| Slack | `SlackChannelAlerts(token, channel)` (same bot token); alerts stay on `build_alert_sender` (#fno-desk) | `FNO_FORECAST_CHANNEL_ID` and `FNO_INTRADAY_CHANNEL_ID` (the IDs the owner created on 21 Oct, passed by the orchestrator; they enter the repository only in FL1a's code, with the scan change, because the scan refuses them until then) in a new `fno/forecast_lab/constants.py` (`fno/constants.py` is at 345 of 350 lines), imported into the record scan's `ALLOWED_VALUES` |

Routing: #fno-forecast gets the 09:30 post with the top positions (and the 08:45 post from FL1d), and the 15:45 match report with the
next day's forecasts. #fno-intraday gets the hourly lines. #fno-desk keeps every alert (a failed slot, a missing
forecast, a refused seal) and the T1 card.

Records: lab fills, positions and marks are written like the books' private records (E2c: Drive, never the public
repository). Each slot's report text is written once with its SHA-256 (O9 receipt) before it is posted, so a rerun
posts nothing twice.

## Build order (each part its own judged branch)

| Part | Delivers | Waits for |
|---|---|---|
| FL1a | channels, record-scan allowance and its test, CLAUDE.md routing line, `lab` command with the three slots, routine prompts, the match report on G13's NIFTY h1 rows (labelled "h1 = N+1"), the trust line | G13 merge |
| FL1b | the lab on NIFTY: ranker, research account, 09:30 fills, time exits, P&L in the report, hourly line | E8 merge (mark reader) |
| FL1b2 | BANKNIFTY lab positions and hourly line | A16's BANKNIFTY marks |
| FL1c | N+0 and N+3, BANKNIFTY ranges, three seals a day | G13b |
| FL1d | the 08:45 slot and its routine, with A22's inputs | A22 live |

## Acceptance criteria

1. On a closed day every slot prints "not a trading day" and posts nothing.
2. A forecast sealed after its slot's cutoff is never posted as that slot's forecast; the refusal is alerted to
   #fno-desk and recorded.
3. The 15:45 report shows only forecasts sealed before their cutoff, scored by G13b's scorer (its numbers, never
   recomputed); a test on fixed rows checks that the report's numbers equal G13b's scores.
4. The trust line shows the trading-day count against 60 (calibration) and against 6-12 months (edge), every day.
5. A rerun of a slot posts nothing a second time (the posted marker), and its records are byte-identical.
6. Lab positions are defined-risk only (C4's shapes). Each is filled at the 09:30 mark's touch with C1 charges, or
   recorded "not filled" with its reason (missing quote, size, invalid). None appears in scoreboards A or B or in a
   book's account.
7. Every exit is the time exit fixed at entry; a position past its exit mark is closed at the next valid mark and the
   delay is reported.
8. Only #fno-desk, #fno-forecast and #fno-intraday IDs pass the record scan (test). The bot's membership in both new
   channels is checked with one read-only `conversations.info` call in setup; there is never a test post.
9. O11's replay covers the 15:45 report and the lab on its recorded day. Until each part lands, its O11 strict xfail
   names it (FL1a, FL1b, FL1b2, FL1c, FL1d).
10. Gates as in CLAUDE.md; no file over 350 lines.

## Judge verifies

Run the slots on fixed records for a session day, a closed day and a rerun. Read the ranker against its stated
modelling choice, and check that costs are on both legs of every trade. Plant a seal after its cutoff and see it
refused and alerted. Check that the scan refuses a fourth channel ID.
