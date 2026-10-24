# FL1-1c preview v4: the 15:45 report

v1 and v2 were rejected. v3 was "way better"; v4 adds the owner's changes, as relayed by the orchestrator on
21 Oct 2026.

| File | What it is |
|---|---|
| `slack-message.txt` | The 3 text lines, exactly as the message shows them (unchanged from v3) |
| `fl1-report-picture.html` | The picture in the message (drawn 600 px wide at 2x, static) |
| `fl1-report-details.html` | The attached file: the same chart, with zoom, plus the exact numbers and every method |

No PNG is committed (the record scan refuses binary files). To draw the picture, run
`/opt/pw-browsers/chromium --headless=new --no-sandbox --disable-gpu --hide-scrollbars --window-size=600,4000
--force-device-scale-factor=2 --screenshot=picture.png file://$PWD/fl1-report-picture.html`.

## What changed from v3

1. **Dates on all 30 boxes:** two rows of 15, each with the day and month.
2. **One big graph per index**, the main visual:
   - "most likely" as a shaded ribbon, its middle guess as a thin dashed line, "almost certainly" as a faint outer
     ribbon, each as forecast the session before;
   - the actual close as a line, with a green tick or red cross on each close;
   - at the right edge, the next trading day's and the 3-day forecasts, labelled "forecast <date>", with the
     "most likely" upper, middle and lower numbers, and the "almost certainly" edges in grey;
   - a labelled Y axis (every 200 points for NIFTY, every 500 for BANKNIFTY), on a taller chart.
3. **Zoom in the attached file only:** mouse wheel or trackpad zooms at the pointer, drag moves, pinch on a phone,
   and a double click resets. It is a small inline script with no library and no request.
4. **"Last 7 trading days: why it missed":** for each miss, the date, how many points above or below
   "almost certainly", and a likely reason after the fact. A reason is shown only when a fact in our own data
   crosses its threshold, otherwise "no clear reason in our data":
   - India VIX up 10% or more on the day;
   - a scheduled event (RBI policy, Union Budget) since the last session;
   - a NIFTY F&O expiry day;
   - Brent oil or USD/INR moving 3% or 0.5% in the last print before the day.

   The details page says plainly what is not checked yet: overnight US moves (the US closes stay private until the
   owner approves a display), FII/DII flows (archived, not yet read here) and the opening gap (no index open price
   is held).
5. **Kept from v3:** the headline lines, the light, "All systems normal" and "Research only. Not a trade tip."
6. **One plain line under the legend:** "Most likely = a normal day's move (1 day in 2). Almost certainly = covers
   even a jumpy day (9 days in 10)."
7. **One signal:** the owner's 30-day light. The stricter 20-session checks are plain facts in the details, with
   no colour.

## Checked

Checked with Playwright on the pre-installed Chromium, at real viewport widths:
- the picture at 600 and 390 px, the details at 1100 and 390 px;
- no sideways scroll (the first 390 px run found 118 px of overflow from the date labels; fixed);
- no console errors;
- no external request;
- the wheel zoom changes the chart's view (1,000 to 549 units wide).

## Synthetic numbers, not market data

The preview files use made-up numbers: a seeded random walk from 25,000 (NIFTY) and 55,000 (BANKNIFTY), with each
method's band a fixed multiple of a 0.85% daily move. They contain no market data and no G13b record (judge 434
should-fix 4: every data file, fetched or derived, lives in Drive). The real-data check of v4 (report day 19 Oct,
G13b's back-fill) is described in response 301; its numbers are not kept here.

The preview's report day is Fri 23 Oct; the record line shows "(27 back-tested)" because only the last 3 synthetic
days are marked live (judge 434 should-fix 1).

Paper research only, never an order.
