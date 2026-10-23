# Judge 551: the AI books' routine prompt without the install (F1/G5 owner checklist)

**Scope:** story/f1-books-prompt-no-install at 70f2e634 (off main 511edf2a), builder session_013xqaNTCbSBytKgqpfaYFqZ.
Files: `docs/stories/F1-G5-owner-checklist.md` and a register row: text only, so the gates are the record scan and the
doc-reading tests (owner, 23 Oct 2026). Judge I (session_01MvZneCLZqBuiGyNxawdVee). Lane 1: a scheduled routine's
prompt. Round 1 of 2.

**Verdict: FAIL.** 1 should-fix. Dropping the install is right; the new step 4 overrides the books' own rule for a
refused seal.

## Checked
| Point | Result | Evidence |
|---|---|---|
| (a) Everything the routine runs needs no install | MET | on 70f2e634 with `python -S` (no site-packages): `fno.ai brief` refuses a malformed pointer by name; `seal` runs to its own refusal ("pointer.txt missing"); `reveal --help` runs; `fno.ai.__main__` builds one session for brief, seal and reveal (`book_wiring`), and it loads; `tools/check_records.py` scans a file clean. The versioned instructions (`agents/forecast/book2_hybrid_v1.md`, `book3_ai_v1.md`) run only `seal` and `reveal`. The other `fno.ai` modules need `requests`, but they belong to the Actions job, not the routine |
| (b) No hard line weakened | MET | step 0 (latest main), "never print or store secrets", the untrusted pointer, "never `--no-verify`" and "sealed by 15:15:00" all stay |
| (c) Step numbers | MET | steps 0-4, and "the command in step 3" follows. The other "step 5" lines (56, 88) are the checklist's own steps, not the prompt's |
| The cause | MET (strong evidence) | the builder's commit times match DR1's finding: Book 2's seals at 15:15:32 (22 Oct) and 15:15:25 (23 Oct, "retried after install") |
| Gates | MET | doc-reading tests: 791 passed, 16 xfailed; record scan clean |

## Finding
1. **Should-fix: step 4 turns every refusal into a stop.**
   - The new step 4 says "If `seal` fails, stop; final message: its error line."
   - The books' versioned instructions say "Run `python -m fno.ai seal ...`. If it refuses, fix what it names and run it again." (book2 and book3, step 3).
   - Every `seal` failure prints `refused: ...` (`fno/ai/__main__.py:19, 37`): a fixable answer refusal (a field out of range, bad JSON) as well as a broken push.
   - The routine prompt is followed first, so a book whose first answer is refused would now give up and lose the day, where the old prompt let it fix and reseal before 15:15.
   - Fix expected: step 4 keeps the deadline and "never `--no-verify`" and defers to the instructions on a refusal. For example: "If `seal` refuses, do what the instructions say (fix what it names and seal again) while it is before 15:15:00; if it still fails, stop; final message: its last line."

## Notes
- **Until the owner pastes the new prompt,** the old one still works (its install is now only wasted time), as the claims say.

## Addendum 1: round 2 at a432ce8d (diff 70f2e634..a432ce8d)

**Verdict: PASS** (Judge I). The diff against main is Markdown only: the story and its `docs/WORK_REGISTER.md` row.

- **Should-fix (step 4 overrode the instructions): FIXED.** Step 4 now reads "If `seal` refuses, do what your
  instructions say (fix what it names and run it again) while it is before 15:15:00; if it still fails, stop; final
  message: its last line."
  - This matches step 3 of `agents/forecast/book2_hybrid_v1.md` and `book3_ai_v1.md` ("If it refuses, fix what it
    names and run it again"), so a fixable answer is no longer lost. The 15:15:00 bound keeps a late seal out.
  - "Its last line" is the `refused: ...` line: `fno/ai/__main__.py:37-39` prints it and returns 1.
  - The Claims (point 3) give the reason and this judge number.
- **Unchanged and still right:** no install step, step 0 (DR1), "never `--no-verify`", the renumbering.
- **Gates (text-only rule, my run at a432ce8d):** doc-reading tests 791 passed, 16 xfailed, 0 failed; record scan clean
  (8,881 files).
