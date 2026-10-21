# FL1 report design v7: two editions, three graphs

Written by the designer session, 21 Oct 2026, after the owner's verdict on the wireframe (DESK_DECISIONS c3231785):
the structure stands, the graphs come back, the forecast cycle is two editions. Every number is drawn from the
builder's PageView (`pageview.py`); nothing is computed here but the owner's three-colour rule and the outward
rounding to 10. Reasoning only unless marked.

## The two editions

**A. Morning, 08:50 IST: "Today's forecast"** (`fl1-morning.html`). First a compact **global cues** strip (US closes,
US 10-year, USD/INR, Brent with its print date; GIFT Nifty, Asia and Europe marked "coming" until A17e and A22), drawn
with example values labelled as such until the builder wires A17. Then per index: the forecast for today's close in
large type ("most likely"), the "almost certainly" range and the middle under it, then **graph 1**: the range on a
horizontal scale with a hairline every 50 points for NIFTY (100 for BANKNIFTY), a number on every edge (most likely
in bold above the bar, almost certainly in grey below, the middle in the accent) and the last close as a marker with
its value. A thinner second row on the same scale is the 3-day outlook. Then the 30-day light. No OI tables: the
levels, flows and contracts live in the attached details file.

**B. Evening, about 19:00 IST: "Was today's forecast right?"** (`fl1-evening.html`), checked against today's
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

Rendered with the pre-installed Chromium through Playwright at 2x, both editions at 600 and 390 px: 0 px sideways
overflow (at phone width each graph scrolls inside its card at 520 px so its type stays 11 px), no console errors,
no external request. Read test: each graph answers its question in one or two seconds; each edition is two cards
and reads in under 30 seconds. Collisions found and fixed in review: BANKNIFTY axis numbers (now spaced
automatically), the close marker's label over the high label (now under the bar), two neighbouring close labels in
graph 3 (now flipped to the free side).
