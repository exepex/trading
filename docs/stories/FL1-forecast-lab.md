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
  2. **A22 pre-open data** (GIFT Nifty, NSE pre-open) has no text. Until it exists, an 08:45 forecast knows nothing
     the 15:45 forecast of the evening before did not. FL1 then reposts that sealed forecast as "pre-open: no new
     input" and never re-forecasts.
  3. **BANKNIFTY has no intraday quotes.** A16 records NIFTY within 6% only; BANKNIFTY options exist only in A4c's
     3 pm chain. So lab positions are **NIFTY only** until A16 (or a new recorder) covers BANKNIFTY. BANKNIFTY ranges
     are still forecast and scored, against NSE's archived all-index close files.
- E8's bid/ask reader for A16 marks (`IntradayMarkSnapshots`) is only on E8's branch. FL1 reuses it after E8 merges
  and never writes a second one.

## Scope

In:
- one command `python -m fno lab <slot>` for the slots `pre_open` (08:45), `open` (09:30) and `close` (15:45), each
  run by its own Claude routine that the owner creates, with the exact prompts and a CLAUDE.md section;
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
| Forecasts | G13b's sealed records (Drive write-once, O9 receipts), read through G13b's reader | a seal-time check per slot: pre_open before 09:15, open before 09:45, close before the next session's 09:15 |
| Positions (09:30) | E8's `IntradayMarkSnapshots.at(day, 09:30)`; E4's `price_leg` (fills at the touch, checks size); `Fill.priced` and C1's charges; C4's defined-risk shapes; R3's shadow-account layout for a research account | `RangeRanker`: for each defined-risk candidate (verticals and condors on the next weekly and monthly NIFTY expiries within A16's 6% band), the expected payoff at its horizon under the sealed 5-95% quantiles (linear between quantiles, flat tails at the 5% and 95% levels, stated as a modelling choice), minus entry and exit costs at bid/ask. Ranked by expected net per rupee of maximum loss; top N (config `lab.top_n`, default 10). One lab account `journal/lab/account/`, never in scoreboards A or B |
| Exits | the same mark reader; every exit is fixed at entry: the 15:15 mark of N+1, or of N+3 if the horizon is N+3 | `LabExits` (time exit only: no stops, so no stop the lab cannot enforce) |
| 15:45 match report | G13's `quantile_score`, `share_inside`; the post-mortem's section pattern and once-only publish (LR1 `Publisher` posts once and records a marker) | `MatchReport` sections: forecasts vs the close (inside the 25-75% and 5-95% bands, direction of the median, quantile score), each baseline the same way, positions' paper P&L after costs at the 15:30 mark (exit value at bid for long legs, ask for short ones), the running scoreboard and the trust line, then the next day's sealed forecasts |
| Hourly line | A16's `MarkObserver.after_mark` (no new routine; an observer failure never stops A16) | `HourlyLine` at 10:15, 11:15, ..., 15:15: NIFTY against today's sealed band, open lab positions' marked P&L |
| Slack | `SlackChannelAlerts(token, channel)` (same bot token); alerts stay on `build_alert_sender` (#fno-desk) | `FNO_FORECAST_CHANNEL_ID` and `FNO_INTRADAY_CHANNEL_ID` (the IDs the owner created on 21 Oct, passed by the orchestrator; they enter the repository only in FL1a's code, with the scan change, because the scan refuses them until then) in a new `fno/forecast_lab/constants.py` (`fno/constants.py` is at 345 of 350 lines), imported into the record scan's `ALLOWED_VALUES` |

Routing: #fno-forecast gets the 08:45 post, the 09:30 post with the top positions, and the 15:45 match report with the
next day's forecasts. #fno-intraday gets the hourly lines. #fno-desk keeps every alert (a failed slot, a missing
forecast, a refused seal) and the T1 card.

Records: lab fills, positions and marks are written like the books' private records (E2c: Drive, never the public
repository). Each slot's report text is written once with its SHA-256 (O9 receipt) before it is posted, so a rerun
posts nothing twice.

## Build order (each part its own judged branch)

| Part | Delivers | Waits for |
|---|---|---|
| FL1a | channels, record-scan allowance and its test, CLAUDE.md routing line, `lab` command with the three slots, routine prompts, the match report on G13's NIFTY h1 rows (labelled "h1 = N+1"), the trust line | G13 merge |
| FL1b | the lab: ranker, research account, 09:30 fills, time exits, P&L in the report, hourly line | E8 merge (mark reader) |
| FL1c | N+0 and N+3, BANKNIFTY ranges, three seals a day | G13b |
| FL1d | the pre-open forecast with new information | A22 |

## Acceptance criteria

1. On a closed day every slot prints "not a trading day" and posts nothing.
2. A forecast sealed after its slot's cutoff is never posted as that slot's forecast; the refusal is alerted to
   #fno-desk and recorded.
3. The 15:45 report scores only forecasts sealed before the outcome's session opened. Its scores equal G13's
   `quantile_score` and `share_inside` on the same rows (test on fixed rows).
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
   names it (FL1a-FL1d).
10. Gates as in CLAUDE.md; no file over 350 lines.

## Judge verifies

Run the slots on fixed records for a session day, a closed day and a rerun. Read the ranker against its stated
modelling choice, and check that costs are on both legs of every trade. Plant a seal after its cutoff and see it
refused and alerted. Check that the scan refuses a fourth channel ID.
