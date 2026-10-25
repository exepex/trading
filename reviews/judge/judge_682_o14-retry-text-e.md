# Judge 682: O14 story text, one retry policy for failed commands (story/o14-retry-policy @ 912cb521f), judge E

**FAIL (round 1 of 2; 2 should-fix, 3 minor). Lane 1** (it decides whether a record-writing step runs again, and
it calls outside services; judge 1 of 2). Judge E, own session; judge F's verdict not read. Text only (208 lines).

## Checked and met

- **The owner's words** (section 1) are quoted exactly from DESK_DECISIONS e3bbbdfeb. The gap list maps each part.
- **Section 2's facts, read in code:**
  - `COMMAND_LIMIT_SECONDS` is 600 (`fno/daily/steps.py:24`);
  - GW1a's worst case is "38 x 3 = 114 tries, under Groww's 150 per 24 hours" (`groww_sign_in.py:11`);
  - A16's slot is the mark plus 120 s (A16 story line 148), and A16 runs as its own Claude routine, so it is rightly
    in scope.
- **The design pattern:** one `RetryPolicy` interface with one strategy, wired in the composition roots. The numbers
  are 30 s doubling to an 8-minute cap, 5 retries, ±20% seeded jitter, and the short policy for A16 and A22.
- **No double capture:** the quote parts, the pack and the snapshot are left to their own loops.
- **Classification:** the step's own error classes, and decision 44's run stops stay final.
- **One escalation alert** carrying class names only.
- **The owner questions are fair and honest:** fills kept final, the school kept, exits and marks put to the owner
  with evidence.
- **The quiet-hours rule** (CLAUDE.md "How to work", judge 680.3): O14's retries are the scheduled routine's own, and a
  hand rerun stays only after an escalation. Consistent.
- **Gates:** record scan clean (9,544 files); doc-reading tests 963 passed, 13 xfailed, 0 failed.

## Findings

**Should-fix 1. The deadline rule looks only at the retried step's own deadline. The daily run is one thread, so a
retry can push a later timed step past its deadline.**
- `DAILY_RUN_STEPS` runs `book1` after the 14:58 pack and before `snapshot` and `fills` (15:15, `fills_by` 15:20).
  It also runs `reviews` and `card` before `premium_ranges` (sealed by 15:30) and the school (never after 15:25).
- Section 4 gives `book1` and these steps "the end of the run" as their deadline. Up to 15.5 minutes of waits, plus
  each attempt's run time (up to 600 s), would then cost the day its fills, the school slot or G13d's issue.
- **That is a money step lost to a retry of a step before it.** And "the step's expected run time" in the rule is
  never defined.
- Fix:
  - a step's retry deadline is the earliest of its own deadline and the latest start of every later timed step
    (`fills_by`, `SLOT_LAST_START`, 15:30, the 15:12 v4 check);
  - `book1`'s own deadline is the desk's decision deadline;
  - define the expected run time (for example the step's last measured time, else `COMMAND_LIMIT_SECONDS`);
  - add a criterion with a plant: `book1` failing at 15:05 must not delay `fills` past `fills_by`.

**Should-fix 2. The Groww sign-in budget leaves no margin, and the circuit cannot see a child's failure.**
- Groww's limit is "150 requests per 24 hours" (the 22 Oct probe file, line 111): a rolling window. 114 plus 12 x 3 =
  150 exactly, and a bad afternoon's sign-ins still count at the next morning's 08:36 pre-open.
- The circuit is "shared by every caller in the process", but the daily run's Groww retries are child processes. The
  parent learns a child's failure only from its exit and output.
- So it is not said how a child's sign-in failure or 429 opens the parent's Groww circuit, which section 5 needs for
  "no retry may start a new sign-in".
- Fix:
  - classify a child's Groww error class from its own last line (class names are already public) into the parent's
    circuit;
  - set the budget below the limit, for example 8 processes with a stated margin, or count sign-ins rather than
    processes;
  - add a criterion with a plant: a child's sign-in failure, then no further Groww child that day.

**Minor 1.** Criterion 8 removes step 2b. It should also update the quiet-hours clause in CLAUDE.md "How to work" and
AGENTS.md ("step 2b's once-only rerun holds until O14 replaces it") in the same change, so neither names a removed step.

**Minor 2.** "The end of the run otherwise" is not a deadline the policy can read. Name each step's real one, or
"16:00, `close_recheck`'s start", per should-fix 1.

**Minor 3.** Section 6 makes `card` not safe until a test shows one post. Say the same for every step that posts to
Slack (`recommend`, the editions): a Slack post is the one write that is not write-once.
