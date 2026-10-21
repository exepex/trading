# Response 288: story FL1, the forecast lab and daily reports (story text for Judge E)

Builder session_01FWkBH4zNAEFSEpjUzVEgnd. Story: `docs/stories/FL1-forecast-lab.md` on `story/fl1-forecast-lab`.

## Claims, each with its check

1. G13b and A22 have no text, branch or code on 21 Oct (`git ls-remote`, WORK_REGISTER, DESK_DECISIONS row 262).
2. G13 is unmerged (judge 310 FAIL); its branch forecasts NIFTY only at h1, h5 and two expiry horizons, 7 levels,
   from the 3 pm chain (`fno/price_distribution/constants.py` on `story/g13-price-distribution`).
3. A16 records NIFTY only (`fno/intraday/expiry_plan.py: UNDERLYING = "NIFTY"`, 6% band); BANKNIFTY options exist
   only in A4c's 3 pm chain. Lab positions are therefore NIFTY only for now.
4. E8's mark reader (`IntradayMarkSnapshots`) is on `story/e8-code-part1` only; FL1 waits for it, no second reader.
5. `fno/constants.py` has 345 lines, so the two channel IDs go in `fno/forecast_lab/constants.py`.

## Owner's answers (21 Oct, DESK_DECISIONS row 264), now in the text

1. The 08:45 post waits for A22: FL1 runs 09:30 and 15:45; the 08:45 slot is FL1d.
2. top_n = 10.
3. A16 is extended to BANKNIFTY (A16 builder 01VK88Lx): BANKNIFTY positions are part FL1b2, behind that dependency.

## Owner's later decisions (21 Oct, "Lab universe, report times and phasing"), now in the text

FL1 is two parts: FL1-1, the 15:45 report with ranges, the match report and the end-of-day contract tracking of every
NIFTY and BANKNIFTY contract (phase 1); FL1-2, the 09:15 report with the top 10 candidates and paper fills at the 09:30
mark (phase 2). Judge 403's three fixes are kept and timed for the 09:15 report. The 09:30 fills post to #fno-intraday
(an intraday event the owner can act on; #fno-forecast keeps two fixed posts a day).
