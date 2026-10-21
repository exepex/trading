# FL1 report design v6 (designer's preview, branch `story/fl1-report-design`)

The owner rejected v4 (cluttered) and v5 (overview not on top, no values on the chart). This folder is v6: same data,
same words, the owner's layout. Rationale in `DESIGN.md`. Design only: the FL1 builder wires it to the real records and
to Slack; nothing under `fno/` is touched.

| File | What it is |
|---|---|
| `DESIGN.md` | What was cut, what the one chart per index is, why each element exists |
| `fl1-report-picture.html` | The picture in the message: the overview strip and one 8-day line chart per index, 600 px wide at 2x, no script |
| `fl1-report-details.html` | The attached file: the same, the chart over 30 days with zoom, the 3-day forecast, why it missed, every day in numbers, every method, the contracts proposal, the checks |
| `slack-message.txt` | The 3 text lines, unchanged from v4 |
| `data_v4.json` | The data every page is built from (below) |
| `build.py`, `linechart.py`, `contracts.py`, `report.css`, `zoom.js` | The generator: `python build.py` rewrites the HTML files. Standard library only |

No PNG is committed (the record scan refuses binary files). To draw the picture:
`/opt/pw-browsers/chromium --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=600,1700
--force-device-scale-factor=2 --screenshot=picture.png file://$PWD/fl1-report-picture.html`.

## Where the data comes from

Real back-fill data (G13b), report day Mon 19 Oct 2026, the same as v4's preview:
- the forecast numbers, today's closes, the misses and their reasons, the method scores, the ✓/✗ grids and the
  stricter checks are copied from v4's text;
- the 30 daily ranges and closes behind the chart are **recovered from v4's chart coordinates** (v4 embedded them
  only as SVG points), so each may be off by up to about 20 index points. They agree with v4's facts: 25 of 30 and
  28 of 30 right, 15 Oct 61 points above, 13 Oct 67 points above. The builder draws from the real records.

Paper research only, never an order.
