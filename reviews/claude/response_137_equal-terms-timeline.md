# Response 137: one timeline for every family (equal terms), proposal for the owner, the judge and ChatGPT

Owner, 15 Oct 2026: "all family strategies follow the same timeline otherwise they will work on different dataset and
due to different dataset & different execution time, the comparison will not be fair or not correct. so let's work on
a proper fix".

## What is true today (checked in the code, strong evidence)

- **Same data already:** every family's forecast reads one frozen pack per day (protocol v2 section 5), whose
  same-day fields count only if stamped by 15:00:00 IST. Book 1 and the baselines are published only after 15:15, so
  the AI books cannot read them first.
- **Same deadline already:** 15:15:00 IST for all (`GENERATION_DEADLINE`; the AI books by GitHub's push time).
- **Unequal in practice:** the capture job waits until 15:10 before it builds the pack and fires Books 2 and 3
  (`.github/workflows/forecast-capture.yml`, protocol v2 section 5), although the day's `.canonical` snapshot is final
  the moment it is written (`fno/quotes/recorder.py`: first complete attempt, written once), usually about 14:58.
  Rule books need seconds; the AI books get about 5 minutes, and on 15 Oct missed by 12 s. A family that misses the
  lock has no record that day, so the comparison silently loses days for one side.
- **Times are spread over several files:** recorder window (14:55-15:10), `GENERATION_DEADLINE` (15:15),
  `fno/ai/timing.py` (15:13, 15:15:10, 15:30), the capture's 15:10 wait, and E3's proposed timetable (15:12, 15:15,
  15:20). They agree today by hand, not by design.

## Proposal: five equal-terms rules, one timeline file

| Rule | Meaning | Change |
|---|---|---|
| E1 One input | One pack per day, hashed; every family's forecast and trade decision names that pack hash; scoring and the desk refuse any record built on another hash. | Add the hash check where missing (E2/E3 decisions). |
| E2 One release | The pack is released to all families at the same moment: as soon as the day's canonical snapshot is in (about 14:58), at the latest 15:10 (recorder retry days). All families are started at that moment; rule outputs stay unpublished until the lock. | Capture job: build and fire on the canonical snapshot instead of waiting until 15:10. The pack is identical either way (15:00 cutoff per field), so no data changes. |
| E3 One lock | 15:15:00 IST for every family's forecasts and decisions; nobody gets extra time; nothing after it counts. | None (kept). |
| E4 One execution | Every family's paper trade fills against the same 15:15 execution snapshot with the same fill model (E3/E4). | Write it into E3 as a rule, not a proposed time. |
| E5 Fair missing days | A missed lock never drops a day from a comparison. A missing forecast is scored as the no-skill base rate (the protocol's climatology baseline) and counted; a missing decision is NO TRADE (flat) and counted. Reports show each family's missed-day count. | Scoring (G4/G8) and scoreboard (S2) rule; must enter protocol v4 before its freeze. |

**One timeline file:** every time above lives in one place (`fno/timeline.py`, read by the recorder, the capture, the AI
books, the desk and scoring), with a test that no module defines its own copy. Changing a time then changes it for every
family at once.

## Trade-offs (said plainly)

- E2 gives the AI books about 15-17 minutes on normal days, but still about 5 on a recorder retry day. Keeping one
  fixed lock is simpler and fair; retry days should be rare once setup is fixed (story O7). Reasoning only.
- E5's choice: scoring a missed day as the base rate is fair and cannot be gamed. The alternative is comparing only
  days where both families have a record. That rewards a family that happens to miss hard days, and the misses come
  from timing problems that cannot be predicted, so they may still line up with busy days. Recommended: base rate.
- Protocol v2's 15:10 wait is frozen: changing it needs the judge and ChatGPT (rule 9). E5 must go into protocol v4
  before its freeze (the G6 notes), or the freeze locks in silent dropping.

## Asked of the owner

1. Approve E1-E5 and the one timeline file?
2. E5: score a missed forecast day as the base rate (recommended) or compare only common days?

Then: ChatGPT review of this file, a story on a `story/` branch, judge PASS, merge.
