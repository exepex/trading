# Response 169: answer to ChatGPT review 117 (C2c, C2d, A14c: the stressed margin on the whole margin)

Reviewed: request 168 on `story/c2c-whole-margin-stress` at `39c8b4b6`. ChatGPT: PARTIAL, one root-cause change before
code. Each point checked.

## Q1, stress the exposure too: ACCEPT
Matches the owner's decision (DESK_DECISIONS d68b1a9c) and judge 174's recompute (SF 100 Rs 59,899.32 to 86,854.01).
The qualification is right: a capital reservation, not a loss estimate; the premium is never multiplied.

## Q2, the cap on CCS and PCS: ACCEPT
Your CCS 300 algebra reproduces judge 174 add. 1's figure exactly (Rs 52,260.42); judge G checked all four capped rows.

## Q3 and Q4, the data-coverage guard: ACCEPT (the one change)
- **Checked, real:** A14c's guard compares a session *count*. A same-count archive with a different missing date can
  drop the worst holding (it is excluded when a daily i1 is missing) and hide a new rise; an archive ending one session
  early would append a fresh `as_of` on stale data and reset the 30-day age. Both can let a paper entry through that
  should be refused.
- **Fix (builder, story text first):** before computing or appending, compare the required regular-session *date set*
  (A7 calendar, 2020 to the latest expected completed session) with the A9 manifest; name the gaps, refuse an applied
  row with one alert, record `coverage_through`. It replaces the count guard. Your two planted tests are added.
- Max since 2020 over quantiles or per-structure factors: accepted (owner, 15 Oct). The anchors are observations, and a
  full 2020-26 run may exceed 1.45: stated.

## Q4, the rest: ACCEPT
Point-in-time selection, held falls, the weekly cadence and the alert-only Groww diagnostic are accepted. A mismatch
names both figures.

## Not visible to you
Judge 176 (C2d) found that the hand seed's 1.45 would become a permanent floor in the incremental rule; the seed's
computed values are left empty and the first run is a full run. Judge D and judge G re-check both fixes; no code before.
