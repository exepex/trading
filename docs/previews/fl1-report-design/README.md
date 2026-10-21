# FL1 report design v7 (designer's preview, branch `story/fl1-report-design`)

The owner rejected v4 (cluttered), v5 (overview not on top, no values) and v6 (congested, big type, data missing),
then approved the wireframe's structure with the graphs back and two editions. This folder is v7. Rationale in
`DESIGN.md`; research in `REFERENCES.md`. Design only: the FL1 builder wires it to the real records and
to Slack; nothing under `fno/` is touched.

| File | What it is |
|---|---|
| `REFERENCES.md` | Research before v7: five broker notes opened, what their first screen carries, visual conventions, morning vs evening editions, our content proposal with data availability |
| `wireframe.html` | The v7 wireframe: layout only, plain boxes, 13.5 px body, two columns from 760 px |
| `DESIGN.md` | v7's rationale: the two editions and the three graphs |
| `fl1-morning.html` | Edition A, 08:50: one page, both indices side by side: cues strip, today's forecast, graph 1, why this forecast, the 3-day outlook, the light |
| `fl1-evening.html` | Edition B, 19:00: one page, both indices side by side: the verdict chip, why it was right or wrong, graph 2, graph 3, the light, levels and flows |
| `editions.py`, `rangechart.py`, `dotchart.py`, `editions.css` | The v7 generator: `python editions.py` rewrites both editions from the PageView dump |
| `fl1-report-picture.html` | v6's picture (rejected; kept until the builder wires v7) |
| `fl1-report-details.html` | v6's attached file (the 30-day chart with zoom, every day in numbers, every method, the checks); v7's details file follows the wireframe's blocks 4-8 once the editions are approved |
| `slack-message.txt` | The 3 text lines, unchanged from v4 |
| `pageview-2026-10-19.json` | The builder's real PageView dump (story/fl1-html-report cf452764): every page is built from it |
| `pageview.py` | Reads a PageView (dataclasses or the JSON dump) into plain values; `render_picture(pv)` and `render_details(pv)` for the builder's PageRenderer |
| `build.py`, `linechart.py`, `report.css`, `zoom.js` | v6's generator (`python build.py`); `linechart.py` also holds the shared number formats and the three-colour rule |

No PNG is committed (the record scan refuses binary files). To draw the picture:
`/opt/pw-browsers/chromium --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=600,1700
--force-device-scale-factor=2 --screenshot=picture.png file://$PWD/fl1-report-picture.html`.

## Where the data comes from

The builder's real PageView dump (`pageview-2026-10-19.json`, from the production PageBuilder on G13b's back-fill,
with the 19 Oct 3 pm record as the day's issue). The pages draw its values and never compute a forecast number;
`pageview.py` formats dates, renames bands and orders lists.

Paper research only, never an order.
