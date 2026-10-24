# Response 301: FL1-1c production pieces (builder's claims, for Judge E)

Builder: session_01FWkBH4zNAEFSEpjUzVEgnd. Branch `story/fl1-html-report`, head named in the message to the judge.
Story text: `docs/stories/FL1-forecast-lab.md`, section FL1-1c. Owner decisions: DESK_DECISIONS f21a8966 and 194aa8b3
(the user-needs brief's answers), and 21 Oct (FII/DII flows yes; global markets as a set, not the US alone).

**Out of scope here: the visual design.** The designer's session owns it (story/fl1-report-design, owner sign-off
first). These pieces draw with an interim renderer behind a port (`page/render.py`); the signed-off design replaces
it with one class and one line in `page_wiring.py`. `daily.live_from.lab_close` stays null.

## What is built

| Piece | Files | What it does |
|---|---|---|
| Page model and builder | `page/model.py`, `page/builder.py` | Every number the page shows, from live sources (today's written issue through FL1's `RangeSource`, G13b's scored history, the facts, the regular sessions) |
| G13b history | `g13b_history.py` | G13b's own score rows with the band each scored; for one method, horizon and target day, live wins over 3 pm back-fill, which wins over end-of-day back-fill (nothing counts twice) |
| Plain words | `page/plain.py` | The 3 lines, "most likely" and "almost certainly", outward rounding to 10 points, "tomorrow" only when true, the 30-day light (green 25+, amber 24, red 23 or fewer) |
| Reasons and facts | `page/reasons.py`, `page/facts.py` | Each of the last 7 sessions' misses with "likely reason (after the fact)" only from facts crossing stated limits (below), else "no clear reason in our data"; global markets and the opening gap listed as not checked |
| Stricter checks | `page/drift.py`, `page/history.py` | 20-session coverage limits, as facts in the details, with no colour (the owner's one signal is the 30-day light) |
| Delivery | `delivery.py` | One Slack message to #fno-forecast with the text, the picture and the details file (files upload v2) |
| Maker | `maker.py` | The text, picture and file from one page model; a picture failure sends the text and the file with one alert |
| Records | `records.py`, `written.py` | The whole message and both files in one write-once Drive record (base64), so a rerun posts exactly what was made |
| Lab close | `lab_close.py`, `wiring.py`, `page_wiring.py` | FL1-1's seal checks and coverage (unchanged, judged) decide the alerts; the maker decides the message; FL1-1's check lines go to the details page |

The reason limits:
- India VIX up 10% or more on the day;
- an RBI policy decision or Union Budget since the last session;
- a NIFTY F&O expiry day;
- Brent 3% or more, or USD/INR 0.5% or more, in the last print before the day;
- an FII or DII net cash flow of Rs 4,000 crore or more on the day, **only when it pushes the way of the miss**.

## Decisions to check, with their evidence

1. **Direction-aware flows.**
   - The fact: on 15 Oct NIFTY closed 56 points above its range while FIIs sold Rs 5,285 crore. A
     non-directional rule offered that selling as the reason for a rise. Now: "no clear reason in our data".
   - Evidence: strong (real data, the smoke run, a test).
   - The Rs 4,000 crore limit is reasoning only: on the 6 archived sessions the FII nets were between Rs 1,000 and
     5,300 crore.
2. **A double post fixed.**
   - In merged FL1-1, T1's poster returns "not sent, no readable ts" when Slack accepted a post but gave no
     timestamp. That outcome lacks the may-have-posted words, so a rerun would have posted again.
   - The new `Delivery` carries `may_have_posted` explicitly: a lost answer to the last upload call is marked and
     never retried; a refused connection is retried.
   - Tests: `test_a_lost_answer_to_the_last_call_may_have_posted_and_a_refused_connection_did_not`, plus FL1-1's
     maybe-posted test, now on `Delivery`.
3. **Today's issue is shown once written, whatever its seal.**
   - The seal is GitHub's push time, read from its activity log, which can lag at 15:45. Calling a just-written
     issue "missing" would be a false alarm.
   - Seals are for scoring (no look-ahead), and FL1-1's seal checks still judge them.
   - Only a missing record is a system problem.
4. **One write-once record for the message and both files.** Writing the files and the report separately would let
   a crash between them make a rerun rebuild different files and hit a write-once conflict.
5. **implied as the method when no history exists yet.** This is the owner's named choice, and what the history
   picks today.

## Tests and checks

- **26 new tests** in `tests/forecast_lab/`, and FL1-1's 38 kept green with the new fakes. The O11 replay now runs
  the real maker and poster path on the recorded day, with a fixed camera.
- **My mutation run:** 13 planted, 13 caught:
  - flow direction;
  - the VIX limit;
  - live preference;
  - a silent missing issue;
  - the best method by maximum error;
  - a swallowed picture failure;
  - maybe-posted not marked;
  - a lost answer not marked as maybe-posted;
  - inward rounding;
  - "tomorrow" always;
  - amber wrong;
  - files not posted;
  - facts after the report day.
- **Smoke run on real data,** for 21 Oct, with G13b's real reader and P8's real flows: the picture is 1200 × 3351 px
  and the details file 113 KB. "Today's forecast is missing" is correct, because live issues start 22 Oct.
- **Gates on the merged tree:** listed in the message to the judge.

## Known limits

- The interim drawing is not the owner's design.
- Expiry days come from the NIFTY options panel only, so BANKNIFTY's own expiries are not separate.
- Reading the panel costs about 0.3 s a year.
- A real Slack upload has not been made: a test post is never made. The upload calls follow Slack's documented
  three-step flow and are tested against a fake session.
