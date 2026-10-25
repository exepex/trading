# Judge 663: REC1d text amendment (the 08:50 and 20:05 sections), story/rec1d-sections at ccc71f331 (judge J, 1 of 2, round 1)

**FAIL** (text), lane 1: 1 should-fix, 2 minor. Markdown only: `docs/stories/REC1-recommender.md` (+39). Doc-reading
tests on the head: 932 passed, 13 xfailed.

## The orchestrator's checks
| Check | Verdict | My evidence |
|---|---|---|
| 08:50 shows the standing answer and the checks | MET | Item 3: the latest record before today, labelled "standing" with its day (plant (c) `<` vs `<=`); the latest checks in `check_text`'s words; "no recommendation recorded yet" on an empty history |
| 20:05 shows today's two answers and the fixed line | MET | Item 4: REC1b's words without the receipt part; the fixed "tonight's check runs after this edition" line; a session with no record named, with the run log's status |
| Each section under its own flag, never switching the other's | NOT MET | S1 |
| Both editions byte-identical with both off | MET in the text | Item 2 and plant (a); with S1 the cases are four, not one |
| A section failure never stops the edition | MET | Item 1 renders each section isolated with its own `failure_alert`; plants (b) and (d) |
| The privacy rule is the recommender's own | MET | Item 5: no strike, price or strategy internal, only REC1b's and REC1c's allowed words, no hash |

## Findings
**S1 (should fix) The school's flag switches the recommender's section.**
- Item 2 shows the section "only with `school.reports` on, and from `daily.live_from.recommend`".
- The code it plugs into confirms the coupling: `build_school_maker` returns the plain maker when
  `school_settings(config).reports` is false (`fno/school/reports/wiring.py:37-38`). So `extra=` sections hung on it
  vanish whenever the school's reports are off.
- The owner turned `school.reports` on today (`config.yaml:249`). If it is turned off again, say for a school fault,
  the recommender's answers would leave both editions too. That breaks the rule that neither flag switches the
  other's section.
- Fix:
  - The recommender's sections are added by their own wrapper in the composition root (`page_wiring.py`), outside
    `build_school_maker`, gated only by `daily.live_from.recommend`.
  - The school's maker keeps only its own flag.
  - Criterion (a) becomes the four flag pairs. Off/off is byte-identical to today. School-on/recommender-off is
    byte-identical to today's school-on output. School-off/recommender-on shows the recommender's sections only.
    On/on shows both, the school's first.
  - Plant: the recommender's section gated by `school.reports`.

**m1 (minor) "Check missing" catches only a day never checked.** Item 3 defines it as "a recorded day with no check
file dated after it". A day still open whose check did not run on the previous session (a failed evening routine) has
older check files, so it is not named. Define it as: a recorded day that was not final before the previous session
and has no check file dated that session. Also say "the previous session's evening" rather than "last evening", for
Mondays and holidays.

**m2 (minor)** Item 1 still waits for the orchestrator's yes on the placement, and for the FL1 owner's agreement to
the `page_wiring.py` change. Write both in before the code round. After S1's fix that call is the one place the
recommender's wrapper is wired.

## Plants
None (a text round). For the code round: S1's flag swap; m1's missed evening not named; and (a)-(e) as listed.

## Notes
- I did not coordinate with judge K.
