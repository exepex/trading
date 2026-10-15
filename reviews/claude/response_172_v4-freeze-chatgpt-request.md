# Response 172: review request to ChatGPT for the protocol v4 freeze plan (quality rule 9)

**Why you:** the v4 freeze fixes every rule that decides a v4 forecast's score and verdict, and the stop-rule review
(May 2027) reads them. Quality rule 9 asks for your review after the judge's PASS (judge 177 addendum 1) and before
the owner decides. Nothing is frozen yet; this is the plan.

**Exact version:** branch `freeze/v4-checklist` at `3e3fd30250aa324d22a05b6f2f97029ada0dfd36` (the version the judge passed; this request file is added on top).
**Read:** `reviews/claude/response_157_v4-freeze-checklist.md` (the plan, with "Revision 1"); judges 177 and 177
addendum 1; `research/forecasts/PROTOCOL_v4.md` and `PROTOCOL_v4_calibration.md` (drafts); story G10 in
`docs/stories/G-forecasts.md` (merged); your review 113 and our response 159; G9 (`fno/forecast_v4/misses.py`);
`docs/DESK_DECISIONS.md` rows of 15 Oct 2026 named in response 157.
**Answer in:** `reviews/chatgpt/review_119_v4-freeze.md`, with a README line.

## Questions (please answer each with ACCEPT, CHANGE or REJECT and your evidence)

1. **What is frozen and what is not.** The record byte-checks the protocol, its calibration part and tables, every file
   of `fno/forecast_v4/`, `fno/forecast_v4_rules/` (G7), `fno/forecast_scoring/v4/` (G8), G4's `scores.py`, A16's
   four RV files, M1's `METHOD_FILES` and the golden fixture; it records but does not check `fno/constants.py`,
   `fno/desk/settlement.py`, the calendar module, `implied_vol.py`, `rv_table.py`, `iv30.py` and the rest of
   `fno/weather/`. Is any file that can change a v4 baseline, outcome, pairing, threshold or verdict left only
   "recorded", or outside both lists? Is anything checked that should stay free?
2. **V1 pinned to A16's method.** V1's outcome and its intraday baselines will read only A16 rows of method
   `rv-quote-15m-v1`, and A16's RV arithmetic and void rule are byte-checked. Is that enough so that a new A16 sampling
   method (A16's own rule above 5% void sessions) cannot change V1's record, and nothing more is needed?
3. **The day's clock (G10).** The pack holds quotes received 14:30:00-14:40:00, each with its real receipt time; one
   SHA-256 for every family; a 15:10:00 deadline on GitHub's receipt time; the 15:15 common snapshot; `A`, `A2` or
   `system_late` per day. Does the freeze plan carry every one of these into the frozen text and code, and is anything
   left to an implementation choice that could change a result?
4. **Late and missed forecasts.** `system_late` days are out for every family; a commitment received after 15:10 is a
   miss; G9's caps (10% of baseline days, 10% of baseline 2% days) make a member "undecided, operations"; misses count
   from the day after the freeze for a forecaster already started, else from its first live forecast; only live rows
   of later days count after the freeze. Can a family gain by being late, by missing chosen days, or by starting late?
5. **Look-ahead.** Is there any path by which a forecast could be scored, paired or thresholded using data first seen
   after its own cutoff: the back-fills (G7 `f891d9b`, M1 `6b7eaba`, disclosed and never counted), the EOD IV30 proxy
   in the premium ratio, the regime and crash-share inputs (outcome-side by design), or the slot registrations (ledger
   rows appended before a slot's first counted forecast)?

Owner's simplicity rule (15 Oct): please count only paths that happen in this system's normal running; anything else
at most one line.
