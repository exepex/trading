# Judge 622: MS-P1j3, the school runner's first-seal cutoff, text and code (story/ms-p1j3-first-seal-cutoff @ e6bb4c2ac; text 81eeefb4a, code a1c4a1fe9), judge E

**PASS (round 1 of 2, text and code in one round). Lane 1** (decides whether a session is recorded; judge 2 of 2).
Judge E, own session; judge F's verdict not read. The tip adds only a Claims line to the code (`git diff 17ed4bad7
e6bb4c2ac`: the story, +4).

## Text (rule 1)

It answers the condition judges 607 and 608 set: a manual `school run` after the close made a first seal whose
every fill law 6 then refused. The owner switched the school on (DESK_DECISIONS 25 Oct, row 343 item 1, which names
this condition). Criteria 1-4 are testable with good, bad, boundary and empty cases. The gap list holds. The runbook
line is plain.

## Criteria (code)

| # | Criterion | Result | My evidence |
|---|---|---|---|
| 1 cutoff | MET | `SchoolFleet._too_late_to_seal` returns `FIRST_SEAL_TOO_LATE` (a `FLEET_STOPPED` status, so `school run` exits 1). It is checked after the sealed-session branch and before `settle_expired` (`runner.py:98-100`), so nothing is settled, sealed, filled or counted. My P1 (refusal removed): 5 failed. P8 (not a "stopped:" status): 4 failed |
| 2 boundary | MET | `started <= datetime.combine(session, 15:25, IST)` compares full aware datetimes, so another zone is compared in IST and a later day is refused. P2 (`<`): 3 failed. P5 (the session's 15:25 taken in the clock's own zone): 1 failed. P6 (time of day only, so a later day passes): 1 failed |
| 2b the start decides | MET | `started` is read before `plan_slot`; the `SlowReading` test pins it |
| 3 untouched | MET | RECORD only: P3 (mode test dropped) 27 failed, since the simulator's practice runs `RunMode.REPLAY` at 15:30 (`practice/runner.py:48`). A sealed session reruns as before. P4 (the check before the sealed branch): 2 failed. Nothing scheduled returns first. Production's clock is `IstClock` (`now_ist`, `school/wiring.py:41-43`), so a REH1 rehearsal is judged on the replay clock. Only `school run` without `--replay` is RECORD (`cli.py:45-49`) |
| 4 one value | MET | `SCHOOL_STARTS_BY = SLOT_LAST_START`; the test asserts identity. P9 (the daily step's own equal value): caught |
| Gates | MET | Trial merge 5d8200de3 with origin/main 97b16e4f7: ruff clean, format clean (2,631 files), imports clean (2,760 files), record scan clean (9,266 files). Full suite with the token kept: **16,557 passed, 14 xfailed, 0 failed** |

## Plants

9 planted, 8 caught. P7 (a second check after `settle_expired`) changes nothing, as the first check returns earlier:
it was a no-op by construction, not a survivor. Each was run alone on `tests/school/fleet`, `tests/school/simulator`,
`tests/daily/test_starts_by.py` and `tests/e2e/test_school_step.py` (442 tests), and restored after.

## Findings

None blocking, none should-fix, none minor.

## Notes

- The stated few-second boundary (a daily step started at 15:24:59 whose child reads its clock after 15:25:00) fails
  closed: both refuse, both alert, nothing is sealed. Accepted.
- The condition of 607 is met: the switch commit may follow this merge.
