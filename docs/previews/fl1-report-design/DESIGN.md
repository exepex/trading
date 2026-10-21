# FL1 report design v6: the rationale

Written by the designer session, 21 Oct 2026, after the owner rejected v5 (the overview was not on top, the
columns had no values, 500-point gridlines were too coarse, "make it just line, numbers on top"). The data and words
are v4's; the layout is the owner's v6 brief, relayed by the orchestrator. Reasoning only unless marked.

## The page, top to bottom

1. **At a glance** (5 to 10 seconds), one block per index, like a broker's morning note:
   - the 30-day light as a pill (`Good: 25 of 30 days`, word and colour);
   - **Today's call**: the "most likely" range forecast the session before, the close, and a chip:
     green `✓ Correct` = inside "most likely", amber `⚠ Close call` = inside "almost certainly" only,
     red `✗ Missed` = outside both; one grey line says which range held; on a red day one line gives the reason;
   - **Next**: the date, "most likely" in large bold, "almost certainly" after it.
2. **One line chart per index** (the picture shows the last 8 trading days, the attached file 30):
   - three lines: the forecast **high** and **low** (the edges of "most likely", accent colour) and the **actual
     close** (ink, thicker); each close has a dot coloured green, amber or red by the rule above;
   - **numbers on top**: the close is written at every point; the high and low are written at the first point, the
     last point and on every red day (the brief's "ends and misses"); under the dates, three aligned rows give
     **every** day's high, close (coloured by its result) and low, so every value on the graph is readable even
     where the lines cross;
   - **gridlines every 100 points for NIFTY**. For BANKNIFTY every 250: its 8-day span is about 2,000 points, so
     100-point lines would be 20 lines 15 px apart with 11 px labels (unreadable); 250 gives 9 lines 33 px apart.
     The card's subtitle states the step;
   - the **forecast zone** on the right: the lines continue dashed into a tinted zone to the next day's high, middle
     and low, each written with its word;
   - a key, then `Last 30 days: 12 ✓ correct · 13 ⚠ close call · 5 ✗ missed (dates)`.
3. **Details** (attached file only): the 3-day forecast, "why it missed" for the last 7 days, every day in numbers
   (now with the three-colour result), every method in collapsed sections, the words in numbers, the system card.
4. **Contracts**: v6's mock (a normal fit with a per-day check per contract) was withdrawn on 21 Oct after the G13
   builder's facts: the chances are the market's own (1 − cdf for calls, cdf for puts, from G13's per-strike
   record), and the check is a calibration table across past expiries, never a per-day tick per contract. The
   wireframe's block 7 carries the corrected form.

## Why these choices

- **Overview first, detail below**: the owner's rule. The picture is the overview strip plus the two charts; nothing
  in the picture needs the attached file to be understood.
- **8 days in the picture, not 10**: at 600 px wide each day gets 48 px, enough for an 11.5 px bold close label and the
  value rows without overlap; 10 days gave 38 px and labels collided (tried, rejected in self-review).
- **Value rows under the chart rather than 24 labels inside it**: the three lines cross often (each day's range is
  centred on the previous close, the close moves on), so labelling high, low and close at every point inside the
  plot overlapped in every render. The rows carry every number, aligned with its date; the plot keeps the close at
  every point and the high and low where they matter.
- **Colours**: the dashboard tokens (exepex/omenix-dashboard `design/system/tokens.css`): accent `#5a5ee6` for the
  forecast lines and zone, ink `#4b465c` for the close, green `#15803d`, amber `#e07b00`, red `#dc2626` for the
  result, always with a glyph (✓ ⚠ ✗) and a word. The dataviz validator passes the set; amber and red carry glyphs
  so the tritan pair never relies on colour.
- **Type**: 16 px body, 20 px headline numbers in the overview, 12 px dates, 10.5 px the smallest (the value rows).
  Smaller than v5 because the owner asked for every number on the graph; the picture is drawn at 2x.

## Checked

Rendered with the pre-installed Chromium through Playwright at 2x: the picture at 600 and 390 px, the attached file
at 1100 and 390 px. No sideways overflow (the 30-day chart scrolls inside its card and zooms), no console errors, no
external request. Looked at every render: no label over another label, every value in the rows readable.

Data: every number is read from the builder's real PageView dump (`pageview-2026-10-19.json`, the production
PageBuilder on G13b's back-fill) through `pageview.py`, which only formats dates and renames bands. The builder's
PageRenderer calls `render_picture(page_view)` and `render_details(page_view)`.

Honest limits: the headline ranges round outward to 10 (the builder's rule); the timeline in the dump ends at the session before the issue day (16 Oct), so the
overview's "call" row shows that day until the builder adds today's close as the last outcome.
