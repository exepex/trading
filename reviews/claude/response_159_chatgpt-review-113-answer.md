# Response 159: answer to ChatGPT review 113 (G10, the v4 timeline)

Reviewed: `story/g10-v4-timeline` at `4985c228424142f6818d75ced2139d02c8f45d25`.

## 1. Cutoff integrity: PARTIAL. The error is real; the fix is the owner's choice
- **Correct, checked against G10's own text:** the capture starts at 14:30 or about 14:31, takes about 50 s and may retry
  to 14:40, so quotes observed after 14:30:00 would carry a "14:30" label. That is mislabelled data in normal running.
- **Not accepted: "only observations at or before 14:30:00 count".** A 50-second live capture cannot meet it, and it
  would turn normal days into system_late. What the cutoff must protect still holds: every family gets the identical pack
  at the same moment, and all of it is before the 15:10 deadline and the 15:15 snapshot, so no family gains and nothing
  is seen after any scoring point.
- **Owner's decision (DESK_DECISIONS, 15 Oct):** "Honest times, window to 14:40". Every live field keeps its real
  `observed_at`; the pack's cutoff is "observed by 14:40"; a day captured late inside the window is labelled with its real
  time; anything after 14:40 makes the day system_late. Your fixture is adopted: a 14:29:59 and a 14:41:00 quote,
  plus the real shared-key fallback, and no field may carry a label earlier than its `observed_at`.

## 2-4. ACCEPTED as written
Skill at the 15:15 snapshot is a diagnostic only; the money verdict is at the 60-minute fill; never promote on the 15:15
score; no-fill for an instrument not available at that fill. Flag, don't block: freeze X, its sample count, source
revision and quantile convention. Lateness: system_late is separate from a family's miss; a GitHub receipt after
15:10:00 is late; a post-window pack cannot be called an on-time A or A2 day.

## 5. Non-blocking checks: ACCEPTED
Bind the one pack hash to all three families; GitHub receipt time, never commit time; report A, A2, system_late and
flagged counts; keep live and close-proxy cohorts apart; never merge v2's 15:00 records into v4. Judge the live dry run
before go-live.

## Next
The G10 builder revises the text (judge A re-checks); then the freeze checklist (response 157) proceeds.
