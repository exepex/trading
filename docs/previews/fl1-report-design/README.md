# FL1 report design: signed off at d8f0440 (owner, 21 Oct 2026; DESK_DECISIONS 11ef1b23)

The owner signed off the report design at commit d8f0440: two editions, separate plain charts, no shaded bands and
no bars. The design is frozen at that commit: no visual change unless the owner asks. The FL1 builder wires it
(story FL1-1d) from the files in the first table. Rationale in `DESIGN.md`; research in `REFERENCES.md`. Design only: the FL1 builder wires it to the real records and
to Slack; nothing under `fno/` is touched.

## The signed-off design (d8f0440)

| File | What it is |
|---|---|
| `fl1-morning.html` | Edition A, 08:50 IST: the key, the cues strip, per index the three big numbers, chart 1 over 10 days with today's forecast on the right, why this forecast, the reliability chip |
| `fl1-evening.html` | Edition B, 20:05 IST: the key, per index the result card, chart 1 (forecast vs close), chart 2 (how far off), the day-by-day table, the counts with percentages and the calendar, the reliability trend, when it was wrong, levels and flows |
| `editions.py` | Builds both pages: `python editions.py` rewrites them from the PageView dump next to it |
| `blocks.py` | The result card, the day-by-day table, the counts with percentages, the misses table |
| `twolines.py` | Chart 1: forecast middle (dashed) vs actual close (solid); the morning variant with today's forecast |
| `gapchart.py` | Chart 2: the gap in points per day, zero line, dashed step lines for the range edges |
| `trendchart.py` | The reliability trend (rolling 20-day share inside "almost certainly", target, warning zone) |
| `calendar_grid.py` | The month calendar of results |
| `editions.css` | The look: the dashboard's tokens, one chart per card, phone drawings under 560 px |
| `pageview.py` | Reads the builder's PageView (dataclasses or JSON) into the plain values the pages draw |
| `linechart.py` | Shared number formats (outward rounding to 10) and the three-colour result rule |
| `pageview-2026-10-19.json` | The builder's real PageView dump the preview is built from |
| `DESIGN.md` | The rationale, block by block |
| `REFERENCES.md` | The research: five broker notes, conventions, editions, the content table with availability |

## Kept for reference only (superseded, not part of the sign-off)

| File | What it is |
|---|---|
| `wireframe.html` | The v7 wireframe the owner approved the structure of |
| `fl1-report-details.html`, `fl1-report-picture.html`, `build.py`, `report.css`, `zoom.js` | v6's attached details file and picture (rejected look); the details file still shows the method grids, scores and checks that an attached file may carry |
| `slack-message.txt` | v4's three text lines (superseded by the two editions) |

No PNG is committed (the record scan refuses binary files). To draw an edition at the width the builder posts:
`/opt/pw-browsers/chromium --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=1100,5000
--force-device-scale-factor=2 --screenshot=evening.png file://$PWD/fl1-evening.html` (trim the empty bottom).

## Where the data comes from

The builder's real PageView dump (`pageview-2026-10-19.json`, from the production PageBuilder on G13b's back-fill,
with the 19 Oct 3 pm record as the day's issue). The pages draw its values and never compute a forecast number;
`pageview.py` formats dates, renames bands and orders lists.

Paper research only, never an order.
