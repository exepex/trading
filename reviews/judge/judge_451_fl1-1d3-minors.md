# Judge 451: FL1-1d judge-449 minors (story/fl1-1d3-minors at 7fa68060)

**Verdict: FAIL: 1 should-fix finding.** Minor 2 is done well. The fix for minor 1 makes the evening's USD/INR worse
than before, on every day measured.

## Minor 2 (fewer than 2 evening points): accepted
`evening_points` adds "no notable moves in our data" when a right or unchecked evening has fewer than 2 cues, and never
pads. The 0-point and 1-point tests cover it. Strong evidence: read plus the tests.

## Should-fix 1. Reading A17 at `DECISION` (15:00) hides USD/INR in the evening every day
- The change reads every A17 cue at `DECISION` (15:00 IST) in the evening, with `live_only`. A calendar cue is shown
  only on `current` or `ahead`.
- The day's RBI rate comes from `global-cues.yml`'s "14:11 IST" cron. I listed its scheduled runs with GitHub Actions
  (`actions_list`, schedule events). That run actually started at:
  - 17:53 IST on 17 Oct;
  - 21:20 IST on 19 Oct;
  - 19:20 IST on 20 Oct;
  - 19:35 IST on 21 Oct.

  That is after 15:00 IST every time, and sometimes after the 19:53 evening start too.
- So at 15:00 the day's rate is never committed. The reading is `behind`, and the evening shows USD/INR as "not out
  yet" on every measured day.
- Before this change it showed the previous session's rate with its date. The 438.1 table asks for exactly that: "the
  rate dated D, else the latest on or before the previous session, labelled with its date".
- Fix:
  - in the evening, show the day's rate if A17 has committed it by the edition's run time, not by 15:00;
  - otherwise show the previous session's rate (the `OPEN` reading) labelled "previous session", never "not out yet";
  - add a test with a `behind` evening reading that falls back to the labelled previous rate.

  The other cues (US closes, the US 10-year, Brent) read the same at either cutoff, so only USD/INR needs the
  fallback. Strong evidence: the Actions run log.

I did not run the full suite for this verdict: the finding is in the design, and the diff is 34 lines. The next
submission gets one full run.
