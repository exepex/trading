# What the 15:45 report is for: a user-needs brief (no design yet)

Written as the reader: the owner, a beginner in F&O, who opens Slack on a phone at about 15:45, for about 30
seconds, once a trading day. Two previews were rejected because they answered questions this reader does not ask.
This brief fixes the questions first. Numbers below are real (G13b's back-fill, up to 21 Oct 2026); none of it is
advice.

## Why the report exists

- **Its purpose today is to learn, not to trade.** It shows one forecast a day and, over time, whether that kind of
  forecast can be trusted. Only once it has proved itself might it help with a real decision, such as how far away
  to place an option. Until then it is a research record.
- **The feeling it should leave:** "I know roughly where NIFTY and BANKNIFTY should close next, I know whether this
  has been right lately, nothing is broken, and I don't need to do anything."
- **What it must never do:** look like a tip, or make a quiet day look alarming.

## The five questions the reader asks, in their own words

1. "Where will NIFTY (and BANKNIFTY) probably close tomorrow?"
2. "How sure is it?"
3. "Has it been right lately?"
4. "Is anything broken?" This means the system (data late, report not made), not the market.
5. "Should I do anything?" Today the answer is always "No, this is research only", and the report says so once.

## The first line the reader sees

> **NIFTY tomorrow (Wed 21 Oct): most likely 22,750 to 23,000. Right 25 of the last 30 days.** 🟢

One line per index answers questions 1 and 3 together. Everything else is below it, or one tap away in the attached
file.

## Every element on the rejected pages: does it answer a question?

| Element (v1 / v2) | Question it answers | Keep? | What a beginner will misread |
|---|---|---|---|
| Today's price | 1 (the starting point) | keep, small | nothing |
| "50% band" / "90% band" | 1 and 2, in jargon | **replace with words**: "most likely" and "almost certainly" | "50%" reads as "half right" or as a coin flip |
| The 3-session range | nobody asked | details only | a second range doubles the reading for no daily use |
| Band chart for today | 1 | maybe, as one simple bar | small bars with ticks need explaining |
| 30-day timeline | 3, for someone who reads charts | **one small picture at most**, or details | to a beginner, many crosses on a line look like a crash |
| Hit grid (methods × days) | 3 per method | **details only** | 100+ ticks and crosses read as "11 problems" |
| Drift banner with method names | 4, but about the market, not the system | **replace** with one traffic light and one plain sentence | "11 problems" read as a broken system when the market was just jumpier |
| Method names (implied, rv20...) | nobody asked | details only | meaningless names |
| "Direction: coin flip so far" | 5, sort of | keep as one short line: "It cannot tell up from down yet" | "coin flip" can read as "50% chance of profit" |
| Trust meter (0 of 60 days) | 2 | merge into the reliability line | "0 of 60" reads as "broken" |
| Score strips, error points | nobody, daily | details only | numbers without meaning |
| Seal checks, alerts | 4 | keep only when something is wrong, as one red line | lines saying all is fine add noise |

## Plain-language replacements (real numbers, 19 to 21 Oct)

- **Range:** "Tomorrow NIFTY will most likely close between 22,750 and 23,000. It almost certainly stays between
  22,540 and 23,190." Here "most likely" means 1 day in 2 and "almost certainly" means 9 days in 10. The
  percentages appear only in the details.
- **Reliability:** "Right 25 of the last 30 days" for NIFTY, where right means the close was inside the "almost
  certainly" range. For BANKNIFTY it was 28 of 30. One traffic light (some evidence: exact binomial, for a method
  that is right 9 days in 10):
  - 🟢 25 or more: a sound method falls below that 18% of the time;
  - 🟡 24;
  - 🔴 23 or fewer: only 3% by chance, so it is worth a look.
- **Is anything broken:** only when true, one line: "⚠️ Today's forecast is missing: data arrived late". Otherwise
  nothing, or one green tick: "All systems normal".
- **Should I do anything:** one fixed line: "Research only. Not a trade tip."
- **Lately the market moved more than expected** (the v2 banner's real finding): "NIFTY moved more than expected
  lately (5 misses in 30 days)". That is a fact about the market, shown inside the reliability line, not as a
  problem list.

## Pros and cons

- **Less information:** the reader understands it in 30 seconds and comes back daily. The cost is that the expert
  view (methods, coverage, drift) moves to the attached file. Recommended (reasoning only): the owner's words.
- **One method shown, "the best so far":** simple. The con: today it is only the best on history, not proven live.
  The page says "not yet proven" once, in the details.
- **Showing BANKNIFTY too:** it doubles the reading. Ask the owner.
- **Daily versus weekly:** daily makes a habit, but most days the message will be "same as yesterday". A weekly
  look at reliability might teach more. Ask the owner.
- **Risk:** plain words like "almost certainly" can feel stronger than they are. On history, "almost certainly"
  failed about 1 day in 11 (NIFTY 91% right over 1,909 days), and the details say so.

## Questions for the owner

1. Is "learn whether these forecasts can be trusted" the right purpose for now? Or do you want the report to point
   at a decision, such as how far away to place an option, once it is proven?
2. Both indices, or NIFTY only?
3. Tomorrow only, or also "in 3 days"?
4. Are "most likely" (1 day in 2) and "almost certainly" (9 days in 10) the right words? Do you also want the
   percentages shown?
5. Should "right" mean inside the "almost certainly" range, as above?
6. Traffic light thresholds: green at 25 or more of 30, red at 23 or fewer. Are those right?
7. A picture in Slack, or just three lines of text with the full page attached?
8. Daily at 15:45, or daily plus a weekly "how reliable was it" summary?
