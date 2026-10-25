# Judge 661: F5 code, Book 2 (story/f5-code @ 6e5c882da, PR #160, on F6 e805c6466 and F1t), judge B (2 of 2), round 1 of 2

**FAIL (1 blocking, 1 minor; everything judged otherwise MET). Lane 1** (Book 2's paper trades: a money piece). I did
not read judge I. On the exact head: ruff, format (2,765), imports (2,894) and record scan (9,448) clean; **17,512
passed, 1 skipped, 12 xfailed** (token kept).

| Check | Result | My evidence |
|---|---|---|
| 632 B1: paused versions never tradable | MET | `Book2Playbook.approved_on` = D1's `approved_on(day)` (`paper` at the start and through the day) plus `shadow_on(day)` still `research` through the day, minus Book 2's pauses (`fno/playbook/book2_playbook.py`). Plants (approved by status incl. `paused`: 36 failed; research not checked through the day: 1) caught |
| 632 B2: research loss stops | MET | `fno/book2/pauses.py`, a `Review` in E6's step, on Book 2's own closed trades only (plant "other books counted" caught). Single loss `<= -cap`, cumulative `<= -CUMULATIVE_CAPS x cap`, E6's constant imported; both boundary plants caught; a paused version leaves `Book2Playbook` (plant caught) |
| 632.1 m1: append-only, never back-dated | MET, with m1 below | `ResearchPauses.rows()` refuses a file not starting with its committed text and any back-dated row; `append` refuses back-dating. Both plants caught |
| SF1: no shadow twice | MET | `Book2Playbook.shadow_on` returns nothing; plant (shadows back) 39 failed |
| Book 1 unchanged | MET | `PlaybookSnapshot` builds `Book2Playbook` only when `paused` is set, and `book2_paused` and `book2_rule_defaults` are written only for Book 2; the four committed Book 1 `inputs.json` round-trip byte-identical on this head (my run); plant "Book 1 gets Book2Playbook" (11 failed, 7 errors) caught. `CandidateBuilder.build` now loops over `at_terms`, with the same messages |
| Labels | MET | F5's own refusal (criterion 15) plus F1t's; run-level `strategy_status` (a run with any research pick reads "not yet passed": conservative) |
| 1 open trade | MET | D2's allocator (unchanged rule, per version, Book 2's own records) and again in C4 (`unproven_check`, `validity_envelope.py`), counting trades passed earlier the same day. Plants: off by one (2), check dropped (3) caught |
| C4 fails closed | MET | `version_counts` None fails `unproven` (plant caught); the envelope's registered hash is checked, and no rule default fails |
| Q12 (no-trade threshold binds paper only) | as built, owner pending | one function `binds_paper` (`fno/book2/evaluation.py:24`), used for the default and for the selection; (B) is that function returning `True`. Without it D2 refuses every research candidate. The text says it plainly; no owner row on main yet, so the merge waits for the owner, not for me |
| Live switch | MET | `daily.live_from.book2_hybrid: null`; the text says NoJudge blocks Book 2 every day until F4 lands |

## Findings

1. **Blocking B1: the head does not merge with main.** My trial merge into origin/main 9b511a706 conflicts in
   `fno/daily/wiring.py`, `fno/daily/reason_codes.py`, `config.yaml` (main's `recommend` key against this branch's
   `book2_hybrid`/`book3_ai` keys and the `ai_books` timetable block), `tests/daily/test_day_run.py` and
   `tests/health/test_desk_and_data_checks.py` (main's `recommend` step against `ai_fire`/`ai_collect`). Fix: merge
   main, keep both sides, rerun the full gates. The resolved daily wiring is lane-1 code, so it is judged again.
2. **Minor m1: a committed edit of `research_pauses.csv` is not caught.** `rows()` compares the file with its *last*
   committed text, so a rewritten row that was itself committed passes. Compare with the file's history (each
   committed version a prefix of the next, as the git log gives), or state that a hand edit is lane 1 and caught in
   review only.

## Plants

13 planted on the exact head, 13 caught (each named above).

## Addendum 1

**Merge re-check at story/f5-code `da5808026` (main merged through F1t `f0cad75ce` and F6 `e5fefd8ac`): B1 MET;
verdict still FAIL, now 1 should-fix (new, my round-1 miss) and the open m1. Still round 1 of 2.**

| Check | Result | My evidence |
|---|---|---|
| B1: merge with main | MET | `git merge-tree` of origin/main `30f1e6839` and the head: clean. Main's side kept: `recommend` in `LIVE_STEPS` and `daily.live_from`, `SCHOOL_STEP` and REC1b's templates in `reason_codes.py`; F1t's `ai_fire`/`ai_collect`, `ai_books` and the AI keys added beside them |
| F5 code unchanged | MET | F5's own delta from its merge base, file by file, is identical in round 1 and now except `docs/stories/F5-book2.md` (Claims 3: the D4 ruling, text only) and one expected step-list string in `tests/health/test_desk_and_data_checks.py` (now with `recommend`) |
| Full gates, trial merge with main `30f1e6839` (token kept) | MET | ruff, format (2,834), imports (2,989), record scan (9,582), numbers clean; **18,099 passed, 1 skipped, 12 xfailed** |
| Plants on the merged wiring | 2 of 4 caught | `recommend` dropped from `LIVE_STEPS`: 2 failed (caught). Three survived the daily, book2, playbook, checks and health tests: `ai_collect` templates dropped (F1t's code, not F5's; for F1t's judges), and the two F5 plants below, which also pass the **full suite** (18,099 passed each) |

**S1, should-fix (F5, `fno/daily/wiring.py:81-95`):** nothing pins that Book 2's research pauses run in the daily
run. Plant 1: `book2_reviews` always returns `()`, so on a Book 2 live day the review is never built and **no
research-loss stop (632 B2) ever fires**. Plant 2: `book2_review_paths` returns `()`, so a pause row is written but
not committed by the reviews step, and the cloud container loses it. Both pass all 18,099 tests. My round-1 B2 MET
rested on `Book2ResearchPauses` and its tests, not on this wiring; I did not plant here in round 1. Fix: a daily-run
test with `daily.live_from.book2_hybrid` set that shows the pauses review in the step and `PAUSES_FILE` among its
committed paths, and neither when Book 2 is not live. Nothing is live yet (`book2_hybrid: null`), so no record is
affected today.

**m1 (open, as agreed for round 2):** `ResearchPauses.rows()` compares only with the last committed text, so a
committed edit of an earlier row passes.

Next round (2 of 2, the last): S1 with its test, m1, then the full gates and these plants again.
