# FL1 report design v8: two editions, separate plain charts, no bands and no bars

Written by the designer session, 21 Oct 2026, after the owner rejected the fan chart (congested; the forecast, the
close and the gap could not be read; the colours did not say how big a miss was or which way). The orchestrator's
rebuild brief is followed block for block. Every number is read from the builder's PageView (`pageview.py`); the
pages compute only differences (close minus middle), percentages of those, and shares. Reasoning only unless marked.

## One key, once, at the top of each page

"✓ Correct = closed inside 'most likely' (1 day in 2). ⚠ Close call = outside 'most likely' but inside 'almost
certainly' (9 days in 10). ✗ Missed = outside 'almost certainly'. The gap says how far and which way: + closed
higher than the forecast middle, − lower."

## Evening, about 20:05 IST (`fl1-evening.html`), one page, both indices one after the other, one chart per card

1. **Result card**: three big numbers in a row, "Forecast middle 22,972 (most likely 22,840–23,090)" · "Actual close
   23,146" · "Gap +174 pts (+0.76%)", then the result chip and one plain line ("Closed 63 pts above the most-likely
   range, inside 'almost certainly'"), then 2 reason lines ("context, not cause").
2. **Chart 1, forecast vs actual close, last 30 days**: two lines only, the forecast middle (dashed blue) and the
   actual close (solid black), a dot per day coloured by the result, the last value of each line written, a title per
   day (date, forecast, actual, gap) for hover, gridlines every 100 (NIFTY) or 250 (BANKNIFTY) with numbers.
3. **Chart 2, how far off, last 30 days**: the gap (actual minus forecast middle) in points, one dot per day joined
   by a thin line, a zero line, and dashed step lines on each side for the edges of "most likely" (blue) and
   "almost certainly" (grey), which vary by day. Above zero = closed higher than forecast. Every miss and the last
   day written with its signed gap ("+369", "−381"), so a red dot says how big and which way.
4. **Day by day, last 10 sessions**: Date | Forecast middle | Most likely | Almost certainly | Actual close | Gap pts |
   Gap % | Result | Reason; gaps coloured by sign, numbers right-aligned; the table scrolls inside its box on a phone.
5. **Right vs wrong**: the counts WITH percentages for the last 30 trading days and for the month, then the month
   calendar (Mon–Fri, one rounded cell per trading day with ✓/⚠/✗).
6. **Reliability trend**, unchanged: the rolling 20-day share inside "almost certainly", target 90%, warning zone
   below 80%, the state word (steady / watch).
7. **When it was wrong, last 30 days** (date, gap, reason) and the compact **levels and flows** table (example values
   until the builder wires FL1-1d's levels).

## Morning, 08:50 IST (`fl1-morning.html`), one page, both indices

1. The key, then the **global cues** strip (example values until A17 is wired; "not out yet" and "not available"
   written as plain words, as the builder's SectionView status will say).
2. Per index: the three big numbers (most likely, almost certainly, forecast middle with the 3-day range under it),
   then **chart 1's style over the last 10 days** with today's forecast added as one labelled point on the right and
   its two ranges as a labelled vertical line (thick blue = most likely, thin grey = almost certainly), the five
   numbers written beside it.
3. "Why this forecast": 3 key points, context-labelled (VIX is context, never "used": no G13b method reads it).
4. The reliability chip: "Inside 'almost certainly' 25 of 30 (✓ correct 12 · ⚠ close call 13) · watch", coloured by
   the trend's state.

## Layout and checks

Spacious: one chart per row, never two charts in one box; 13.5 px body, 11 px chart labels; the dashboard's tokens.
On a phone (under 560 px) every chart is drawn a second time at the card's width (338 px) with fewer dates and
numbers-only forecast labels, and CSS shows that drawing, so nothing is cropped; the day table scrolls inside its box.

Rendered with the pre-installed Chromium through Playwright at 2x, both editions at 1100 and 390 px: 0 px sideways
overflow, no console errors, no external request. Found and fixed in review: the last-value labels over the forecast
range line (now left of the last point, the higher one above and the lower one below), the gap chart's side words
over the miss labels (moved into the subtitle), the day table wrapping its numbers (nowrap), the phone forecast
labels clipped (numbers only on the phone).

Data notes: the dump is a 15:45 issue for 19 Oct, so the morning shows the forecast for Wed 21 Oct with the 3 pm
price as "last close" and the evening shows the last scored session, Fri 16 Oct; live, the builder's FL1-1d
PageView gives each edition its own issue. Miss reasons exist for the last 7 days; the builder is asked to keep 30.
