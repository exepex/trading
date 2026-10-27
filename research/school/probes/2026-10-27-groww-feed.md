# Groww feed probe (story A16h), Tue 27 Oct 2026

Read-only probe of Groww's streaming feed (`GrowwFeed`). It ran through `ReadOnlyFeed` and `ReadOnlyGroww`, on main
with the TLS fix (judge 499 addendum 9). Counts and times only; no price and no raw answer is kept. Evidence labels:
**strong evidence**, **some evidence**, **reasoning only**.

## What ran, and what did not

| Plan | Window (IST) | Ran? |
|---|---|---|
| coverage | 10:20-10:40 | **No.** The builder session's worker was restarted; the scheduled check-in reached it only at 15:49. |
| alongside | 14:30-15:20 | **No**, for the same reason. Its gate would have passed: A16's 10:30 and 10:45 marks were good. |
| ramp (after the close) | 15:45-16:15 | **Yes:** 15:50:45-15:55:39. The A16b candles step ended ok at 15:33:20. |

Earlier evidence used below: the owner's one-minute dry run on Fri 23 Oct, 15:17:02-15:18:09, on the same code path.
It covered 5 instruments: the NIFTY and BANKNIFTY index values and three NIFTY 27 Oct options
(`conversations/2026-10-23.md`).

## Answers

**(1) Coverage.** Not answered for the full set. The coverage plan did not run.
- *Strong evidence* (23 Oct dry run, in market hours): LTP streams for NIFTY monthly options (83-87 ticks a minute
  each), and index values stream for NIFTY (299 a minute) and BANKNIFTY (251 a minute).
- After the close (the 27 Oct ramp), the four index values kept ticking at 4.3-5.0 a second. None of the 2,996
  option and future subscriptions ticked. *Reasoning only:* no trading after 15:30 means no new LTP, so this says
  nothing about coverage in market hours.
- Market depth, FINNIFTY, MIDCPNIFTY, NIFTY weeklies and futures in market hours: **untested**.

**(2) Subscription limit.** "no limit up to 3000".
- *Strong evidence* that Groww accepted 3,000 subscriptions on one connection, after the close. Steps held: 50, 500,
  1,000, 1,500, 2,000, 3,000. Every topic was created, and the feed still answered after each step.
- So the documentation's "upto 1000" is not a hard refusal at 1,000.
- *Some evidence only* for market hours: the ramp ran after the close, when almost nothing ticks. Whether 3,000
  topics can be **served** while they tick is untested.
- The SDK printed one "Disconnected" line during the run; the run continued and the index ticks kept arriving.
- The ramp's highest step is 3,000, so a limit above 3,000 is not measured (the universe was 3,248).

**(3) Separate budget from REST.** **Untested.** The alongside plan did not run.
- *Some evidence* from the dry run: it ran 15:17:02-15:18:09 on 23 Oct, overlapping E3's 15:15 execution capture by
  32 s. That capture recorded 180/180 with no failures.
- One minute and five instruments prove nothing about a separate budget.
- Today's 3 pm captures (no feed running) were all complete with no failures.

**(4) Rate and latency.**
- Rate, *strong evidence* for these instruments and times:
  - index values about 4-5 a second (23 Oct in market hours and 27 Oct after the close);
  - NIFTY monthly option LTP about 1.4 a second (23 Oct, 15:17).
- Latency: **not measurable** from index ticks. The probe printed "latency: no exchange time in the ticks". Option
  LTP latency in market hours is untested.

## Two wording bugs in the probe's report (A16h code, not the data)

- **The stop line misleads.** When nothing failed, it reads "stopped: hard end time reached", even though the ramp
  finished all six steps at 15:55, before its 16:15 end.
- **The feed-type labels are wrong.** Each class is reported under every feed type that ticked. Only index values
  ticked, so options and futures appear as `[index_value]`; they were subscribed to LTP. The counts are right: those
  instruments had no ticks of any type.

## Separate finding the same day (A16, not the feed)

A16 marks are failing since GW1a's 60 s process-wide pause after a 429 (merged 25 Oct):
- 2 incomplete marks on 26 Oct and 6 on 27 Oct, against 0 on 23 Oct;
- every failed quote is `GrowwRateLimitPaused` (28-100 per mark);
- each pause starts 58-60 s after the mark.

Reported to the orchestrator for GW1's owner. No feed ran before 15:50 on 27 Oct, so the feed is not the cause.

## Still needed

A market-hours session for the **coverage** and **alongside** plans, and a **ramp-day** run (10:50-10:58) if the
limit under live ticks matters. Each needs a new date from the orchestrator or the owner.
