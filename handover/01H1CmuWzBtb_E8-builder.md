# Handover: E8 builder (owner-timing fills), and E8a

## (a) Identity

- **Session:** `session_01H1CmuWzBtbtjzoQNJUz2Dz`.
- **Role:** builder of story E8, owner-timing fills (issue #109). Also built E8a, the fill-timing study.
- **Branch:** `story/e8-code-part1`, head `d05508bb` before this handover file. The file's own commit follows it on the
  same branch.
- **Work register:** row E8 (and row E8a, done).

## (b) Done and merged to main

- **E8a, the fill-timing study:** merged `0b3b07cf`, judge 179 addendum 1 PASS. A live follow-up after 20 A16
  sessions is still to come.
- **E8 story text:** merged `78a51301` (judge 193 addendum 6). Revision 2 is at `fd3a0344` (on main).
- **Response 228:** the orchestrator's answer to ChatGPT review 128. It is on main (`75c77cfc`) and accepts all six
  points.
- **Judge 203 addenda 1-4:** part 1a PASS; part 1b PASS at `b79dee94` (addendum 3), which still stands (addendum 4).

## (c) Done but not merged: `story/e8-code-part1` at `d05508bb`

- **Code part 1 (1a + 1b):**
  - the clock, A16 snapshot adapter, availability seals, pending entries and exits, the verdict account at R = 60,
    C2's fill-day check, the exit alert, the daily step `owner_timing_fills` and the live switch;
  - the package `fno/desk/owner_timing/` (24 files);
  - tests in `tests/desk_owner_timing/` (19 files) and `tests/timetable/test_owner_timing_block.py`;
  - hook lines, all agreed with their owners (O1 `014zYLf1`, E4/E2c `0134MoC6`): `fno/desk/entries.py`, `exits.py`,
    `exit_timing.py`, `daily_run.py`, `daily_steps.py`, `daily_wiring.py`, `wiring.py`, `fno/daily/wiring.py` and
    `fno/constants_operations.py`.
- **Judge state:** PASS on the code (judge 203 addendum 3, head `b79dee94`). The owner-timing code has not changed
  since that head.
- **ChatGPT review 128:** PARTIAL. All six points were accepted in response 228.
- **The delta after review 128 is NOT judged yet.** It is described in `reviews/claude/response_280_e8-part1-review-128-delta.md`:
  - `tests/desk_owner_timing/test_waiting_exit_risk.py` (point 5: a waiting exit's risk is counted next morning);
  - `tests/desk_owner_timing/test_live_boundary.py` (point 6: the live boundary, the E4 pending exit across the live
    date, and the prior-day order);
  - a two-copy test in `test_mark_snapshots.py` (A16 always wins over a cheaper A4 copy);
  - "Part 2's report" in `docs/stories/E8-owner-timing-fills.md`;
  - two merges of main.
- **Gates at `d05508bb`** (merged with main as of 16 Oct, about 22:30 IST):
  - ruff: clean;
  - check_imports: clean;
  - pytest: 8,122 passed and 18 xfailed.
- **`tools/check_numbers.py`:** fails on one item that is not mine, `judge_308_f4_story_text.md` addendum 308.308. It
  fails the same way on main itself.
- **Numbers claimed** with the tool: response 280, plus 207 and 128 claimed exactly (those two files existed before
  O12).
- **Main has moved:** main is now 289 commits ahead of this branch.

## (d) In progress

Nothing is uncommitted. The next steps, in order:
1. **Merge main again** (`git pull --no-rebase origin main` into the branch), then run the full gates.
2. **O11's E8 xfail** (`tests/e2e_acceptance/test_expected_missing.py`, `@missing("E8")`) asserts
   `"owner_timing" in load_app_config()["desk"]`. E8's switch is `daily.live_from.owner_timing_fills`, not
   `desk.owner_timing`, so that xfail would stay red-free (still failing) after the merge.
   - The orchestrator asked: turn it into a real check in this branch, the way D3, D4, D5 and O1 were done (judge 306
     addenda). Replace it with a check that `VERDICT_REACTION_MINUTES == 60`, that `OWNER_TIMING_STEP` is in
     `DAILY_RUN_STEPS`, and that `owner_timing_fills` is in `fno/daily/wiring.LIVE_STEPS`. Ask the O11 builder
     (`session_01FWkBH4zNAEFSEpjUzVEgnd`) first.
   - S1 item 14 also names `desk.owner_timing.live` for the freezer. That is a mismatch: E8 uses
     `daily.live_from.owner_timing_fills`. Agree one key with the S1 owner (`0185gR5D`) before the freeze.
3. **Addendum to response 228** (orchestrator, 16 Oct): state the agreed correction in the story and as a response
   addendum (claim a number). The correction: from the live date, an E4 pending exit still open is alerted and
   finished under E8, and legs E4 already closed are never closed again. It is already tested in
   `test_live_boundary.py::test_an_e4_exit_waiting_across_the_live_date_is_alerted_and_finished_once`.
4. **Send the delta to the judge:** judge D (`session_01Pb8z2koLuxty7mbujFpgZa`), unless judge C is free. Point it at
   response 280.
5. **After the PASS, merge to main yourself:** pull, run the full gates on the exact merged tree, then push. Then
   update the E8 row in WORK_REGISTER and the conversation log.

## (e) Reviews and judging

- **Judge 203** (judge C):
  - addendum 2 FAILED at `65ec0b05`: the E4c/E4d checks were missing at the due mark. This was fixed.
  - addenda 3 and 4 PASS.
- **ChatGPT review 128:** PARTIAL. All points were accepted (response 228). The open findings are covered by the
  delta in (c), which is not yet judged.

## (f) Agreements and waiting items

- **Hook owners:** the hooks were agreed with O1 (`014zYLf1`) and with E4/E2c/E4c (`0134MoC6`). The E4c builder drops
  `OUTCOME_MISSED` and imports `outcomes.MISSED_REASONS` (9 reasons).
- **Waiting on E8:** R3 part B (`0145TfSw`) needs a one-line `_fills` change after both stories merge. The O11 replay
  and E6b's code (shared `ExecutionOpportunities`) also wait on E8.
- **Going live is an owner decision row.** `daily.live_from.owner_timing_fills` defaults to none, so E8 is off.
- **Owner setup still pending:** A16's 15-minute recorder routine. The 60-minute fill needs it live.

## (g) Risks and known limits

- A16 records only the near-month future, so a further-month expiry gets "missed, no future for that expiry".
- A day with no snapshot or exit review orders no exit. The book stays exposed, with no backdated exit.
- If the alert record's write fails after Slack accepted the post, the exit alert can be posted twice.
- The STR1 "E8" gate at `fno/constants.py:107` is untouched.
- `build_exit_desk` signs in to Drive twice per run.
- Part 2 is not built: the R = 5 and R = 30 views, the `e4_1515` view, and `TimingReport` (which uses E6b's
  `ExecutionOpportunities`).
- S1 must list E8's package in `frozen_files` (prose rule, explicit paths at the freeze).

## (h) The successor's first three actions

1. Check out `story/e8-code-part1` and merge main into it. Run `ruff check fno tests tools`,
   `python tools/check_imports.py` and `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -n auto`.
2. Turn O11's E8 xfail into a real check (agree it with the O11 builder), and write the response 228 addendum with a
   claimed number.
3. Send response 280 and the new head to judge D through the orchestrator. Merge after the PASS.
