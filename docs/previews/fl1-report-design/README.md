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
| `pageview-2026-10-19.json` | The builder's real PageView dump (story/fl1-html-report cf452764): every page is built from it |
| `pageview.py` | Reads a PageView (dataclasses or the JSON dump) into plain values; `render_picture(pv)` and `render_details(pv)` for the builder's PageRenderer |
| `build.py`, `linechart.py`, `contracts.py`, `report.css`, `zoom.js` | The generator: `python build.py` rewrites the HTML files from the dump. Standard library only |

No PNG is committed (the record scan refuses binary files). To draw the picture:
`/opt/pw-browsers/chromium --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=600,1700
--force-device-scale-factor=2 --screenshot=picture.png file://$PWD/fl1-report-picture.html`.

## Where the data comes from

The builder's real PageView dump (`pageview-2026-10-19.json`, from the production PageBuilder on G13b's back-fill,
with the 19 Oct 3 pm record as the day's issue). The pages draw its values and never compute a forecast number;
`pageview.py` formats dates, renames bands and orders lists. The contracts card is the one exception: a mock from a
normal fit, labelled "proposal, data to confirm".

Paper research only, never an order.
