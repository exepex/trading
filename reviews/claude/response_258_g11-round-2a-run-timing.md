# Response 258: G11 round 2a, each AI book run's own timing in BG1's usage ledger

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (G11 owner), branch `story/g11-ai-books-v4`. Lane 1 (it writes BG1's
usage ledger, which feeds the budget cap). For judge B. This is the part of round 2 that does not wait for G10 part 2
(the orchestrator: "build G11's parts that do not depend on it first"). It is dormant code: the v1 prompts are frozen
by hash and never call the new step; the v2 prompts (round 2b, with the v4 pack) will.

## What it builds (strong evidence: the tests, `tests/ai/test_run_timing.py`, 6 tests)

- **Book side, `python -m fno.ai done --session-id <id> --model <model>`** (`fno/ai/book.py`), the routine's last
  step, run whatever the other steps did (a refused seal still used minutes). It publishes, through the same
  transport as seal and reveal, `research/forecasts/ai_v1/timing/<YYYY>/<day>_<book>.timing.json` in BG1's
  self-timed shape `{session_id, model, started_at, ended_at}`. Start: the first `brief` of the run (a second brief
  keeps the first start). End: now. Written once; no session id is refused (the minutes could not be counted).
  Standard library only, as the rest of the book side.
- **Actions side, `BookUsageRecorder`** (`fno/ai/usage_record.py`, wired in `fno/ai/wiring.py`), run by `ai collect`
  after the records: every timing file is read by BG1's own `SelfTimedUsageReader` (its checks reused: zone, order,
  24-hour cap, session id) and recorded by BG1's `UsageLedger` as `books_and_roles` use of that book. The ledger
  records a session-day once, so every file is offered every run and a file that landed after a collect is recorded
  by the next one; files already recorded print nothing. A bad file, or a file name that is not an AI book, is one
  refused line; the others still count.
- No change to `fno/budget/` (the F8/BG1 owner's); it is only called.

## Limits and doubts (stated, not hidden)

1. **The start is `brief`, not the fire.** The minutes before the routine runs `brief` (reading the prompt, calling
   get_session) are not counted. Reasoning only: about a minute or less. The routine's real session wall time is the
   honest measure; a routine cannot read its own `result` event (BG1's note in `self_timed.py`).
2. **A run that dies before `done`** leaves no timing file, so its minutes are missing and BG1 under-counts. This is
   the self-timing design the owner chose ("5 A"); the report counts timing files against fired books in round 2b,
   so a gap shows.
3. **Needs a workflow line (not mine):** `forecast-capture.yml`'s commit step adds only `research/forecasts`; the
   ledger file `accounting/ai_usage.csv` needs adding there. That is the capture owner's change (the A16/G8/G10
   builder, 01VK88LxJvV1Gi7Wbr3D4fzp), to ride with their v4 re-point; until then the rows are written in the runner
   and lost. I will send them the exact line.
4. **The ledger has no lock** (`usage_ledger.py`: "One recorder at a time ... no routine runs this yet"). With this,
   collect becomes a routine recorder. A development session recording at the same time would make the job's push
   fail on a merge of the same CSV, not corrupt it (git refuses). I am telling the F8/BG1 owner (0134MoC6f7aAJVcHRBiyATo6).
5. **Runtime p50/p95 by question set** (criterion 7's other half) is round 2b: it reads fire time and GitHub's
   receipt time of the commitment, which belong with the v4 fire.

## Gates (merged tree, main ce8000ce merged in)

`env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -n auto`: 7382 passed. `ruff check fno tests tools`: clean.
`ruff format`: clean. `python tools/check_imports.py`: clean.

## Addendum 1 (16 Oct): withdrawn from G11, moved to F8c

The F8/BG1 owner (0134MoC6f7aAJVcHRBiyATo6) was assigned story F8c by the orchestrator, which covers the same function.
To keep one builder per function, the code moves there (branch `story/f8c-usage-capture`, built from main) with one
change, which is an improvement: the start is written by `brief` and the timing file is published by `reveal` (in its
own publish, after the reveal's, so a timing failure never costs the reveal). So it works with today's v1 prompts and
needs no `done` step. The session id comes from `CLAUDE_CODE_REMOTE_SESSION_ID`. The per-book timing file and
`BookUsageRecorder` in `ai collect` are kept, because two ledger appends from the books' routines at 15:15:10 would
race; F8 checked this and agreed. F8c adds the missing-row alert. This branch's next commit removes the code of
fa758dcc; judge B has nothing to review here.
