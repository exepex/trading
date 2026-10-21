# FL1 report design v5: the rationale

Written by the designer session (21 Oct 2026) after the owner rejected v1 to v4 as cluttered and not understandable.
v4's data, wording and content stay; only the picture changes. Reasoning only unless marked otherwise.

## What failed in v4, in one sentence each

- **One jagged ribbon chart for 30 days.** Each day's range was forecast the session before, so the ribbon jumps every
  day and the eye reads 30 zig-zags, two shaded bands, a dashed line, a solid line and 30 ticks at once.
- **Thirteen gridlines and six date ticks** that line up with nothing the reader cares about.
- **A grid of 30 tiny boxes** with 9.5 px dates under the chart: a second copy of the same 30 answers.
- **A seven-item legend** that wrapped onto two lines, so the reader had to learn seven marks before reading.
- **Type too small for a phone**: 11 px axis labels and 13 px body in a picture that Slack shrinks to about 0.6.

## The rule for v5: one question, one element, nothing twice

The reader is a beginner with a phone, 30 seconds, five questions (USER_NEEDS.md). Every element on the page answers
exactly one of them, in order, and nothing is shown twice.

| Element | Question it answers | Why this form |
|---|---|---|
| `NIFTY · closed today at 22,871` | the starting point | small, one line |
| Light pill `Good: right 25 of the last 30 days` | 3 and 4 | the only coloured badge; its word is always written, never colour alone (dashboard rule) |
| `most likely 22,750 – 23,000`, 26 px bold | 1 and 2 | the single biggest thing on the page; "almost certainly" under it at 17 px |
| The same for "in 3 trading days", smaller | 1 and 2 | the owner asked for both horizons; smaller so it never competes with tomorrow |
| **One chart: 10 columns, 2 forecast columns** | 3, with a date on every day, and 1 on the right | below |
| `Wrong on 5 of the last 30 trading days: 15 Oct, 13 Oct, 8 Oct, 28 Sep, 24 Sep.` | 3, with dates for the other 20 days | one sentence replaces the 30-box grid: the right days are "every other day" |
| `Why it missed · last 7 trading days` | 3, the reason | two plain bullets, as in v4 |
| `✓ All systems normal · Research only. Not a trade tip.` | 4 and 5 | one line, once, at the bottom |

Cut from the picture: the middle-guess dashed line, the 30-day timeline, the ✓/✗ date grid, the "It cannot tell up
from down yet" line (details only), the method names, the percentages. Everything cut is in the details file.

## The chart: a column per trading day

For each of the last 10 trading days, one vertical column shows **the range forecast the session before** (pale =
"almost certainly", solid = "most likely") and **a dot where the index closed**. A dot inside the pale column was a
right day; a dot outside is drawn red. Under each column: the date on two lines (14 px day, 12 px month) and a
green ✓ or red ✗. To the right, on a light "future" panel, the same column shape for **next day** and **in 3 days**,
with the five numbers written beside each (upper and lower "most likely" in bold, the middle in the accent colour,
the "almost certainly" edges in grey). So the reader checks one day in one glance: "was the dot inside the box?"

Why columns, not ribbons: each day is an independent forecast, so a shape per day is the honest form; the eye never
has to follow a line. Why 10 days in the picture and 30 in the details: at 600 px wide, 10 columns leave 40 px each,
enough for a 14 px date and a 17 px mark with air between; 30 columns would need 11 px type (v4's mistake). Why no
numbers on past columns: a number on every point is noise (dataviz rule: label selectively); the exact numbers are a
table in the details file. Why only three or four gridlines: round steps (every 500 points for NIFTY, every 1,000 for
BANKNIFTY) and hairline, solid, so the columns stay the loudest thing.

## Colours, type, spacing

- **Two colours plus two status colours**, all from the dashboard's design system (exepex/omenix-dashboard,
  `design/system/tokens.css`): the accent `#5a5ee6` for every range (45% for "most likely", 14% for "almost
  certainly"), the ink `#4b465c` for the close and all text, green `#15803d` only for ✓ and the light, red `#dc2626`
  only for ✗ and the light. The dataviz validator passes the three (adjacent ΔE 8.6 deutan, 30.5 normal); red and
  green also carry a glyph and a word, never colour alone.
- **Type**: 16 px body, 26 px headline number, 14 px chart labels, 12 px smallest (the month under a date). v4's
  smallest was 9.5 px.
- **Layout**: the dashboard's page grey `#f7f7f9`, white cards with its soft shadow and 4 px corners, 16 px gutters,
  one card per index, generous space between blocks. No legend box: a one-line key under the chart (two swatches, a
  dot and the two marks), then the one sentence that defines the words.

## What the two files are

- `fl1-report-picture.html`: the static picture, drawn at 600 px wide (2x) for the Slack message. No script.
  It is 1,786 px tall for both indices. **Recommendation:** post one picture per index
  (`fl1-report-picture-nifty.html`, `fl1-report-picture-banknifty.html`, about 600 × 990 each): Slack's phone
  preview crops a tall image, and a picture per index keeps the headline numbers and the whole chart in the first
  preview. The combined picture is kept for the case the owner prefers one image.
- `fl1-report-details.html`: the attached file. The same cards with the chart over 30 days (zoom with the mouse wheel
  or pinch, drag to move, double-tap to reset; it also scrolls sideways on a phone), a table of every day in numbers,
  the exact forecast numbers, every method's ✓/✗ by day and its scores in collapsed sections "for the curious", the
  words in numbers, the stricter checks, seal checks and alerts. Self-contained: no request, no CDN, one small inline
  script.

## Checked

Rendered with the pre-installed Chromium through Playwright at 2x: the picture at 600 and 390 px, the details at
1100 and 390 px, with every collapsed section opened as well. No sideways overflow at any width (one 73 px overflow
from the score table at 390 px was found and fixed), no console errors, no external request. Looked at every render:
no label overlaps another, the smallest type is 12 px, the five questions read top to bottom.

Honest limits: the numbers behind the 30 columns were recovered from v4's chart coordinates (see README.md), so a
value may be off by up to about 20 points; the builder draws from the real records. Rounding of the headline ranges to
the nearest 10 is the designer's choice for readability; the builder decides the final rounding rule.
