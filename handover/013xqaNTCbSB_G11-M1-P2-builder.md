# Handover: session 013xqaNTCbSBytKgqpfaYFqZ (builder: G11, M1, P2a-h screens, P11)

Written 21 Oct 2026 on the owner's handover order (orchestrator, 16 Oct 22:39 UTC, received 21 Oct). Everything is on
GitHub; nothing stays only in the container.

## (a) Identity

- Session: `session_013xqaNTCbSBytKgqpfaYFqZ`. Role: builder, reporting to the orchestrator
  (`session_01VG1RqxLFUVdvvPuMRYZtDH`).
- Owns, per `docs/WORK_REGISTER.md`:
  - G11, the AI books on protocol v4, including `fno/ai`'s v4 changes;
  - M1, the market weather as a scored forecaster, `fno/weather/`;
  - P2a-h, the F&O screen pages in `fno/market_read_models/`;
  - P11, the per-page hold.
- Branches and heads, 21 Oct:
  - `story/g11-ai-books-v4` at `96573db1a57a2bb84c271b78a810f7bf10580517`: G11 round 2b part 1, not judged. This
    handover file is added on top of it.
  - `story/p2c-paper-books` at `0ae25471`: P2c, judge 248 PASS part 1, unmerged. Held by the owner's UI pause; the
    main steward confirmed on 21 Oct that it stays held.
  - `story/p2f-card` was not built. P2f is deferred (response 246).

## (b) Done and merged to main

- **G11 round 1:** `fno/ai/v4_rows.py`. Every settled AI book-day becomes one G7-schema row per question, and every
  failure is a named miss. Judge 275 PASS, merged at `866f4069`/`7c1a9734`. It is switched off: no caller on main.
- **M1 record folders:** `fno/weather/folders.py record_folders()` for O1's commits. Judge 273 PASS, merged at
  `c9863fe2`.
- **M1 at the calendar's end:** unknown events are said, and v0's not-scored reason is named (response 245), at
  `a7a91d65`, merged.
- **P2b**, the forecast lab page (`story/p2b-forecast-lab` 8ea526cb), merged.
- **P11**, the per-page hold (PageHeld, the page_holds page, contract 2.13.0), merged. Judges 251 add. 2 (text) and
  the code PASS are in the register row.
- **P2a and the 2.10 pages:** judges 218, 221, 231; cd069a74.
- **Withdrawn, moved to F8c:** response 258, my round 2a run-timing. F8c (0134MoC6) merged it with my
  `BookUsageRecorder`, credited; main 3ab941dd.

## (c) Done but not merged

1. **G11 round 2b part 1**, `story/g11-ai-books-v4` at 96573db1. Its claim for judge B is
   `reviews/claude/response_282_g11-round-2b-v4-fire-collect.md`; read it first. **Not sent to judge B**: the
   handover order and the owner's 21 Oct phase-1 scope freeze came first. G11 is not in phase 1, and the v4 freeze
   is stopped.
   - **Built:** the v4 input (`v4_input.py`, `v4_book_inputs.py`) and the 64 KiB pointer (`v4_pointer.py`); prompts
     v2 (`agents/forecast/book*_v2.md`), registered as protocol-v4 versions; `ai fire --protocol v4`
     (`v4_fire.py`); `ai collect --protocol v4` (`v4_collect.py`, `v4_settle.py`); `run_terms.py`, threaded
     through F1/G5's chain with the v2 default.
   - **Gates** on the merged tree (main 6603fab0): 8036 passed, 18 xfailed; ruff, format and check_imports clean.
     `check_numbers` failed only because the 282 claim row lives on main, not on the branch; the tool says to run it
     on main.
   - G10 (b1), `story/g10-part2b-release`, is merged into this branch, so landing this branch lands (b1). Judge 282
     addendum 3 ("g10-part2b-merge-without-g11") may have released (b1) to merge alone; check it.
   - Design and decisions: `reviews/claude/response_272_g11-round-2b-design.md` and its addenda 1-3. The
     orchestrator confirmed the design on 16 Oct.
2. **P2c**, paper books, `story/p2c-paper-books` 0ae25471. Judge 248 PASS part 1. Held under the UI pause.

## (d) In progress

Nothing is uncommitted. Open G11 steps, in order:
1. **Step 7, the book side of v4.** `brief` accepts the v4 pointer (`parse_v4_pointer`) and prints its input.
   `seal` and `reveal` use `V4_TERMS` paths and times, with labels from `v4_labels(input)` and the envelope from
   `v4_envelope(input)`.
   - It waits for F1t's refactor of `fno/ai/book.py` (F1t, `session_01PLbKH15BXYucP6cT9xtoxK`, said they would
     extract after F8c merged; F8c is merged).
   - Files: `fno/ai/book.py`, `__main__.py`, `book_wiring.py`.
2. **Round 2c**, mine by the orchestrator's ruling of 16 Oct. Add default-preserving parameters to
   `fno/ai/stop_rule.py` (`breached_days`: the window's session days) and to the transcript-audit draw
   (`audit_plan.fired_sessions`, `transcript_audit.TranscriptAudits`: the folder). Then pass `V4_TERMS` from
   `scoring_gate.scoring_status`. F1t builds on mine. Until 2c lands:
   - every on-time v4 day stays "awaiting audit" (the safe direction: never scored clean);
   - the stop rule cannot stop a v4 book.
3. **Rows carry `pack_sha256`.** R2/G7's column is on main now. In `v4_rows.v4_rows`, pass
   `pack_sha256=day.pack_sha256` to `records.record`, and add a test.
4. **O11's replay check.** Replace the strict xfail
   `tests/e2e_acceptance/test_expected_missing.py::test_the_ai_books_answer_the_v4_questions_on_the_recorded_day`
   with a real check before G11 merges (orchestrator, 16 Oct; O11 builder `session_01FWkBH4zNAEFSEpjUzVEgnd`).
5. **Round 3**, after the v4 freeze: ledger rows registering `book2_hybrid_v2` (hybrid) and `book3_ai_v2`
   (ai_team) for V6a and V6b, with `effective_start`.

## (e) Reviews and judging

I judged nothing. Judge verdicts on my work:
- 244 and 248 (P2c: FAILs fixed, then PASS part 1);
- 251 (P11 text, addenda);
- 255 (digits in hold reasons, fixed);
- 257 add. 1 (wiring untested, fixed);
- 273 PASS (M1 folders);
- 275 PASS (G11 round 1, with two conditions):
  - the round 2 writer calls the pack guard: done, `check_pack_binding` with tests;
  - v4_rows goes on the freeze list: done, R2/G7's response 250 line 9 hashes v4_rows.py, scoring_gate.py,
    outcome.py, stop_rule.py, and fire.py once it writes the flag.

## (f) Open questions and agreements

**Agreed with the A16/G8/G10 builder** (`session_01VK88LxJvV1Gi7Wbr3D4fzp`):
- v4-fire.yml runs `python -m fno ai fire --protocol v4 --day <today>` and commits `research/forecasts/ai_v4`. The
  test pinning that path is `test_the_fire_log_is_in_the_folder_v4_fire_yml_commits`.
- The pack guard is keyed by book, and the book comes from the same `BookVersion` that names the folder.
- `build_slot_registry()` (made public in G8's wiring) is the one registry for scoring, the look and the fire.
- G10's publisher writes `system_late` for every scored session without a pack, with a catch-up. That is (b2),
  which is stopped by the scope freeze.
- At the freeze, forecast-capture.yml drops the v2 AI steps and adds `--protocol v4` to the collect line (theirs).

**Agreed with R2/G7** (`0185gR5DmoDh2zBAvgRU4CEB`):
- the freeze-list entries above;
- the registered names `book2_hybrid_v2` / `book3_ai_v2` (response 250 line 1);
- the structured stop-rule flag instead of the text prefix (done in v4_rows).

**F8c** (`0134MoC6f7aAJVcHRBiyATo6`) owns the timing capture, merged. **F1t** keeps STOPPED's name and text, and
refactors book.py after F8c. **T1c** (`0145TfSwzmpk6MBrH92f5h4G`) reads M1's weather record; field names agreed.
**G13** (`01UkTaDeTRF9ksDgQB9cTU5C`) edits nothing in fno/ai; it imports the book ids.

**Waiting on:**
- F1t's parameter names and timing for the shared seams (asked 16 Oct, no answer; the orchestrator then gave me
  round 2c);
- the orchestrator's confirmation of the order in response 282.

## (g) Risks and things not to miss

1. **M1's stale method hash** (R2/G7's response 250 **line 10**, assigned to me, not fixed). The committed back-fill
   rows carry `2495d512`; the tree computes another hash.
   - Strong evidence, checked 16 Oct: a full re-run gave identical values, statuses and input hashes on all 9,636
     rows. Only the hash differs.
   - Fix at the v4 freeze: regenerate the back-fill on the frozen code in the freeze commit, and add a gate test
     that every committed row's `method_sha256` equals the tree's.
   - It is stopped with the freeze under the phase-1 scope.
2. **Prompt v2 hashes are registered.** Any edit to `agents/forecast/book*_v2.md` before G11 lands must update its
   hash in `fno/ai/versions.py` in the same commit. After it lands, a change is a v3.
3. **Urgent, found 21 Oct: main now sets `daily.live_from.forecasts_v4: "2026-10-22"`** (owner, 21 Oct, response 299
   item 15) for G7's rule forecasts in O1.
   - On main this is safe, because G11 round 2b is not there and the v2 AI fire has no v4 switch.
   - But on `story/g11-ai-books-v4`, `ai fire --protocol v4` and the v2 AI stop both key on that same date. **Never
     merge the branch as it is:** the books would be fired with a pointer their routine cannot read (step 7 is
     missing), and the v2 AI run would stop.
   - Fix before any merge: give the AI books their own go-live key (for example `ai.v4_live_from`, an allowed key in
     `fno/config.py`), separate from O1's `forecasts_v4`. That is a design change the judge must see. Set it only
     after step 7 and round 2c land.
4. `fno/constants.py` is at 346 of its 350-line limit; new constants go elsewhere (`constants_operations.py` holds
   `ROUTINE_POINTER_MAX_BYTES`).
5. **M1's US-move flag lags a day on the Nasdaq-100 side** (A17/A17e builder 01MBnbVU, response 298, 21 Oct; strong
   evidence: Nasdaq's API publishes the close late, so the 03:41 IST copy lacks the previous US close).
   - Impact is low: `fno/weather/drivers.py` `us_move_flag` feeds only the private Drive record
     (`capture.py:47`). The public record shows the placeholder `US_PUBLIC`, and neither the probabilities nor the
     colour use it.
   - `drivers.py` is not in M1's `METHOD_FILES`, so a fix moves no method hash.
   - Recommended fix (b): read the Nasdaq-100 through A17e's `build_index_reader()`, which uses Nasdaq's value where
     it has the date and Yahoo's ^NDX otherwise. A17e's builder offered a small helper for the previous close. It is
     not started, because of the phase-1 freeze and the handover.
   - Weather goes live on 22 Oct (`daily.live_from.weather`).
6. The 64 KiB pointer cap is not yet confirmed against the routine API's real limit (F1t's story says to confirm it
   before go-live). A full input measured 20,713 bytes.

## (h) First three actions for the successor

1. Read `reviews/claude/response_282_g11-round-2b-v4-fire-collect.md` and response 272's addenda. Then check with the
   orchestrator or main steward whether G11 stays parked under the 21 Oct phase-1 scope freeze. If it does, update
   the G11 row in `docs/WORK_REGISTER.md` to "parked by the scope freeze; branch at 96573db1" and stop there.
2. If (b1) is to merge alone (judge 282 add. 3), tell the G10 builder that G11 no longer blocks it. Their condition
   was that the v4 fire land first, and v4-fire.yml would only call `--protocol v4` once G11 lands. A run before that
   fails visibly with "invalid choice" and fires nothing.
3. When G11 resumes:
   - merge main into `story/g11-ai-books-v4` (expect conflicts in CLAUDE.md, the register and the README; keep both
     sides);
   - pass `pack_sha256` into the rows (item d.3);
   - build round 2c, then step 7;
   - turn the O11 xfail into a real check;
   - run the full gates and send response 282 (updated) to judge B.
