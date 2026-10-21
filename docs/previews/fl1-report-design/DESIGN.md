# FL1 report design v7: two editions, one page each, three graphs

Written by the designer session, 21 Oct 2026, after the owner's verdict on the wireframe (DESK_DECISIONS c3231785):
the structure stands, the graphs come back, the forecast cycle is two editions. Every number is drawn from the
builder's PageView (`pageview.py`); nothing is computed here but the owner's three-colour rule and the outward
rounding to 10. Reasoning only unless marked.

## The chart set is fixed (owner, 21 Oct: "sometimes horizontal, sometimes vertical ... change randomly")

One visual language in both editions, no bars anywhere: the **fan chart** (a light corridor = "almost certainly", a
darker corridor = "most likely", a black line = the actual close, a dot per day coloured by the result, the last
value and every miss written), the **reliability trend** line and the **month calendar**.

**Evening, about 20:05 IST, one page, both indices side by side** (`fl1-evening.html`):
1. Result card, no chart: ✓ Correct / ⚠ Close call / ✗ Missed, forecast vs close, and 2 reason lines ("context,
   not cause, until a cue feeds the forecaster").
2. "Last 30 days · forecast vs actual": the fan chart over 30 trading dates, gridlines every 100 (NIFTY) or 250
   (BANKNIFTY), a number on every gridline when they are 13 px apart and on every second one otherwise (the
   subtitle says which), the last value and each miss written in its colour.
3. "This month · right vs wrong": a Mon-Fri calendar grid, one rounded cell per trading day with its date number,
   coloured by the result with its glyph; closed weekdays grey, the future dashed; the counts in big type above.
4. "Reliability trend": the rolling 20-day share inside "almost certainly" (the builder's rolling_90 for the shown
   method), a dashed target line at 90%, a shaded warning zone below 80%, the last value written; the state word
   ("steady" at 80% or more, else "watch") is the drift and fluctuation detector.
5. "When it was wrong · last 30 days": date, how far outside, the reason (reasons exist for the last 7 days; the
   builder is asked to keep 30).
6. Levels and flows, the compact table (example values until wired).

**Morning, 08:50 IST, one page, both indices side by side** (`fl1-morning.html`):
1. The global cues strip (example values until A17 is wired).
2. Per index: today's forecast in big type (most likely; almost certainly, middle and the 3-day range in one line),
   then the SAME fan chart over the last 10 days with today's corridor extending to the right behind a dashed edge,
   the high, middle and low written.
3. "Why this forecast": 3 key points, context-labelled.
4. The reliability chip: "Right 25 of 30 · watch" (the 30-day light's count and the trend's state).

One definition of "right" everywhere: inside "almost certainly"; the three result words are ✓ correct, ⚠ close call,
✗ missed on both pages, in the key, the calendar counts and the reliability chip ("Inside 'almost certainly' 25 of 30
(✓ correct 12 · ⚠ close call 13) · watch", coloured by the trend's state). The reasons heading follows the result
("Why it was correct", "Why a close call", "Why it missed"). The middle guess rounds to 10 in text and on the chart.
A written value never sits on another or on the line: miss labels go to the side away from the neighbouring closes,
stack away from the line when two meet, and stay inside the plot; dates are counted back from the last day.

On a phone (under 560 px) every chart is drawn a second time at the card's width (322 px) with fewer numbers and
dates, and CSS shows that drawing instead of the desktop one, so the right edge (today's corridor, the last values)
is always visible; nothing scrolls or crops.

Rendered at 1100 and 390 px (2x): 0 px overflow, no console errors, no requests. Found and fixed in review: 24
axis numbers 9 px apart on the 30-day chart (now every second gridline), the last value clipped at the right edge
(the CSS anchor overrode the attribute), the trend labels over the line (moved left), the warning label washed out
by the zone's opacity rule.

## Earlier v7 notes (kept for the record)

Each edition is ONE page with one header and one footer: NIFTY and BANKNIFTY side by side from 760 px (the picture is
drawn at 1100 px wide, 2x) and stacked on a phone. Each index card carries 2-4 **reason lines**: the morning "Why
this forecast" (what option prices imply, the overnight context, the day's calendar) and the evening "Why it was
right / wrong" (how far the close moved from the middle guess against the range's width, the miss reason from our
data on a red day, the overnight context). Honesty rule on the label: "context, not cause, until a cue feeds the
forecaster"; lines not yet in the PageView are example text marked as such.

**A. Morning, 08:50 IST: "Today's forecast"** (`fl1-morning.html`). First a compact **global cues** strip (US closes,
US 10-year, USD/INR, Brent with its print date; GIFT Nifty, Asia and Europe marked "coming" until A17e and A22), drawn
with example values labelled as such until the builder wires A17. Then per index: the forecast for today's close in
large type ("most likely"), the "almost certainly" range and the middle under it, then **graph 1**: the range on a
horizontal scale with a hairline every 50 points for NIFTY (100 for BANKNIFTY), a number on every edge (most likely
in bold above the bar, almost certainly in grey below, the middle in the accent) and the last close as a marker with
its value. A thinner second row on the same scale is the 3-day outlook. Then the 30-day light. No OI tables: the
levels, flows and contracts live in the attached details file.

**B. Evening, about 20:05 IST: "Was today's forecast right?"** (`fl1-evening.html`), checked against today's
official close read after 15:30, when today's OI, PCR and FII/DII flows also exist. Per index: a big chip
(✓ Correct inside "most likely", ⚠ Close call inside "almost certainly" only, ✗ Missed outside both), the forecast
range and the actual close in one line, the reason on a red day; **graph 2**: today's range on the scale with the
close marked in the result colour and written; **graph 3**: the last 10 sessions, one column per day (pale = almost
certainly, dark = most likely) with a dot where it closed, coloured by the result and written beside it, and three
rows under the dates with every day's forecast high, close and low. Then the light with the wrong days' dates, and
a compact **levels and flows** table (biggest call and put OI, PCR from → to, max pain, FII and DII cash, FII index
futures net), small, below the graphs, with example values labelled as such until wired.

## Why these forms

- **One idea per graph.** Graph 1 answers "where will it close"; graph 2 "was it inside"; graph 3 "how has it been
  going". No chart carries more than one range family and one marker per day.
- **Every number visible.** Each range edge, middle and close is written next to its mark; graph 3 repeats the
  high, close and low in aligned rows so the reader never estimates from the axis.
- **Gridlines every 50 for NIFTY** (the owner's ask); every 100 for BANKNIFTY because its ranges are about twice as
  wide, so 50 would be 35 hairlines on one bar. The axis writes a number only where numbers stay 72 px apart, so
  labels never touch; the card subtitle states the step.
- **Horizontal scale for one day, columns for ten days.** A single range reads best as a bar on a ruler (the
  dashboard's own range bar, and the brokers' "zone" convention); ten days read best as columns with a dot, where
  "dot inside the dark block" is one glance.
- **Type and space from the references**: 13.5 px body, 11 px chart labels, 24 px only for the headline range, one
  accent for the ranges, green/amber/red only for the result and always with a glyph and a word.
- **Example values, never a guess as a fact**: the cues strip and the levels table are not in the PageView yet, so
  the preview shows example numbers under a label that says so (the dashboard's own rule for states the data does
  not yet have). The builder replaces them with A17's cues and the chain and flow read models.
- **Mock dates**: the dump is a 15:45 issue for 19 Oct, so the morning edition shows the forecast for Wed 21 Oct
  with the 3 pm price as "last close", and the evening edition shows the last scored session, Fri 16 Oct. Live, the
  morning takes the sealed forecast for the day and the previous official close; the evening takes the day's
  official close once NSE archives it (the match lags one day: owner, 21 Oct).

## Checked

Rendered with the pre-installed Chromium through Playwright at 2x, both editions at 1100 and 390 px (the picture
at 1100): 0 px sideways overflow (at phone width each graph scrolls inside its card at 480 px so its type stays 11 px), no console errors,
no external request. Read test: each graph answers its question in one or two seconds; each edition is two cards
and reads in under 30 seconds. Collisions found and fixed in review: BANKNIFTY axis numbers (now spaced
automatically), the close marker's label over the high label (now under the bar), two neighbouring close labels in
graph 3 (now flipped to the free side).
