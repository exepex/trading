# Response 247: LM1 thresholds, the question for the owner (builder 012eM7Ti, 16 Oct 2026)

Sent to the orchestrator on 16 Oct to put to the owner (CLAUDE.md: everything for the other side is in the repository).
The LM1 story is `docs/stories/LM1-position-monitor.md` (judge 215 PASS). The handover from 01XFXpbk was agreed on 16 Oct. The script that measured the moves is below.


The monitor only sends alerts. It never opens, changes or closes a trade. Every value below is a starting setting (in
`config.yaml`, under `monitor`), and the owner can change any of them later.

Data used:
- NIFTY's 15-minute candles from Groww, read from the A16b archive in Drive and checked against their SHA-256: 1,668
  full sessions, 1 Jan 2020 to 14 Oct 2026.
- NSE's previous close (`warmup_closes.csv`).
- A16's first live day (16 Oct 2026, the 23 marks recorded so far).

Labels:
- **Strong evidence** means many years of data, tested.
- **Some evidence** means data exists but is thin.
- **Reasoning only** means no data.

## Key numbers

- **One 15-minute step** (how far NIFTY moves between two marks): typically 0.07%. It is 0.31% or more once in 20
  steps, and 0.54% or more once in 100.
- **One hour** (how far NIFTY moves in 60 minutes): typically 0.13%. It is 0.58% or more once in 20 hours, and 1.03%
  or more once in 100.
- **How often 0.5% moves happen:** a move of 0.5% or more happens in 7.2% of hours, and in 1.3% of 15-minute steps.

These are strong evidence (1,668 sessions).

## The questions

| # | Threshold | Proposed | Why | Cost of a false alarm | Cost of a miss | Label |
|---|---|---|---|---|---|---|
| 1 | Loss used: WARNING | 50% of the position's maximum loss | Design 4.2 and 6.5 | One message, no action | Late news of half a loss: at most Rs 5,000 on a Rs 10,000 trade | Reasoning only |
| 2 | Loss used: DANGER | 80% | Same | Same | At most Rs 2,000 more before the maximum loss is reached | Reasoning only |
| 3 | Short strike near (DANGER) | NIFTY within 0.5% of a short strike | 0.5% is about 125 points. NIFTY moves that far within an hour 7% of the time, so with the owner allowed 60 minutes to act, the alert usually comes before the strike is crossed | Repeats on a quiet day when the strike sits close | The strike is crossed with no warning beforehand | Strong evidence (the move sizes); the choice of 0.5% is reasoning |
| 4 | Big move (DANGER, one alert for the whole desk) | NIFTY at least 1.5% from the previous close | Design 4.2 | See below | A real stress day is not flagged | Strong evidence |
| 5 | Quotes stale (WARNING) | No good mark for 30 minutes (two missed marks) | Matches A16's 30-minute silence rule (`SILENT_AFTER`) | See below | Positions go unwatched without anyone knowing | Some evidence (one day) |
| 6 | Expiry near (WARNING) | Proposal: 09:30 mark on the session before expiry, and again on expiry day | NIFTY options settle in cash, so delivery risk applies only to stock options. A16 marks NIFTY only, so stock options cannot be marked yet | One message a week | An expiry-day position the owner forgot about | Reasoning only |
| 7 | Alert limits | One alert per condition per position per hour (one per hour for desk-wide conditions); after 10 DANGER alerts in a session, a summary every 30 minutes | Design 6.5 | n/a | n/a | Reasoning only |

### What the data says about the big-move alert (question 4)

A 1.5% move is not rare:

| Period | Sessions | Days a mark reached 1.5% from the previous close | Share |
|---|---|---|---|
| All years | 1,668 | 266 | 15.9% |
| 2020 | 248 | 85 | 34% |
| 2023 | 245 | 10 | 4% |
| 2024 | 245 | 22 | 9% |
| 2025 | 245 | 18 | 7% |
| 2026 (to 14 Oct) | 192 | 33 | 17% |

Other thresholds, all years:
- 1.0%: 34.7% of sessions.
- 2.0%: 7.4%.
- 2.5%: 4.1%.

Once a day crosses 1.5%, it usually stays there: 8 of the 26 marks at the median, and 26 of 26 for the top tenth. 61
of the 266 days had already crossed 1.5% at the 09:15 opening gap.

If the alert repeats every hour while the move lasts, a stress day sends up to about 6 identical DANGER alerts.

**Q4b:** after the first big-move alert, should the monitor alert again only when the move grows by another 0.5% (at 2.0%,
then 2.5%), instead of every hour? My recommendation is yes (reasoning only). An alert that repeats with no new
information trains the owner to ignore DANGER. Each new 0.5% step is new information.

### What A16's first live day says about stale quotes (question 5)

On 16 Oct, A16 recorded these marks:

| Status | Marks | When |
|---|---|---|
| Missed | 3 | 09:15 to 09:45 (the routine started late) |
| Good | 11 | |
| Incomplete | 9 | 6 of them had 73 to 87 of about 224 contracts failed; 3 had 1 failed |

The story's rule says only a good mark is checked. Under that rule, the run of incomplete marks from 12:00 to 12:30
would already have fired the stale WARNING. On a normal day, half of all marks would be "no check".

**Q5b:** should an incomplete mark still be checked for any position whose legs are all present on it? My recommendation is
yes (some evidence: one day). The NIFTY index level itself is good on those marks (index age 0.7 to 1.5 seconds), and
a leg that is missing already gives "cannot mark". Then only missed, failed or late marks would count as stale.

## What I do not know yet (reasoning only)

1. **Bid/ask marking.** Loss used is measured at bid/ask, the price the position could actually be closed at. Right
   after entry, a spread already shows a loss equal to the bid-ask cost. For a far out-of-the-money (OTM)
   defined-risk spread, that can be a noticeable share of the 50% line. I cannot measure this until a real position
   exists. The first 5 live sessions with a position will report it, as counts only.
2. **The short-strike threshold.** 0.5% is a single cut. A threshold based on standard deviations (for example 0.5
   of the hour's typical move) would adapt to VIX. I recommend keeping 0.5% fixed now (KISS) and reviewing it with the
   weekly replay's false-alarm share.
3. **Waiting checks.** The VIX +10% check and the weather check stay as "waits" until their data exists. They need no
   values now.

## Answer format

For each of questions 1 to 7, plus Q4b and Q5b, answer "accept" or give a new value.

## What each alert would say (examples; the wording follows the story's rules)

- "F&O monitor: information, no action. NIFTY is 1.6% below the previous close at 10:30. The paper record changes only at the next daily run's execution snapshot."
- "F&O monitor: review your position. Loss used 82% of maximum on <trade> at 13:15. The paper record changes only at the next daily run's execution snapshot." (No contract price. Index levels are allowed.)
- **VIX up 10% in a session:** not available yet. A16's mark has no intraday VIX, so nothing is built and no alert can fire.
- **Weather turned RED or AMBER intraday:** not available yet. M1 rates the weather once a session.

## Method (repeatable)

The 15-minute copies come from `research/data/manifests/groww-candles/nifty-15m.csv`. They were loaded with
`CandleArchive.load`, which checks each file's SHA-256. Each session's 26 levels come from `session_candles`: the
09:15 open, then the close of each candle. Sessions with a missing candle were left out, which leaves 1,668. The
previous close is NSE's `underlying` in `research/data/nifty-panel/warmup_closes.csv`, regular sessions only.

The 15-minute and 60-minute moves are absolute changes between levels 1 and 4 marks apart, within one session. The
replay over A16's live marks covers one day (16 Oct, `research/data/intraday/slots/2026/10/16/`).
