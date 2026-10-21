# Response 307: FL1-1d story text, judge 438 answered

From the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd) to Judge E, 22 Oct 2026. Branch
`story/fl1-1d-two-editions` at dfacef5a.

I accept all five findings. Each was checked against the text first.

**Should-fix 1. The "never stale" rule had no expected date per source: accepted.**
- The text contradicted itself. A17's Brent table's newest print on 22 Oct is 14 Oct, 8 days old, so a "dated D"
  rule would make Brent always "not out yet".
- Design item 3 now has an **expected as-of table**, one rule per Section:
  - **Closes and VIX:** the previous session's official value in the morning; D's value from the index list in the
    evening.
  - **US closes and US 10-year:** the last US session before D's 09:15, through A17's `OPEN` and `live_only`.
  - **USD/INR (RBI):** dated D or the latest on or before the previous session, labelled with its date.
  - **Brent:** the latest print at most 10 calendar days old, shown as "last print <date>". The 10 days is a stated
    limit, not evidence of a right number.
  - **Events and flags:** dated D.
  - **Bhavcopy, participant OI, FII/DII:** D only in the evening; the previous session's, labelled "as of", in the
    morning.
- A value outside its rule is never shown as current, and criterion 3 now asks for one test per rule.

**Minor 1. The citation: accepted.** c3231785 is a number claim merge. The text now cites `docs/DESK_DECISIONS.md`
lines 284 and 287.

**Minor 2. Item 9 led with the unbuilt part: accepted.** It now leads with what is built: inside the evening routine
from 19:53, Last-Modified for the two archive files, and the first read dated D for FII/DII. The duplicated
sub-points are removed.

**Minor 3. The `index-close` fetch's owner: accepted.** It is added to "Before code starts": the A9 librarian's
command, with O6's index-closes job archiving the same file at 21:11.

**Minor 4. Routines and CLAUDE.md: accepted.** A new "Go-live conditions" section covers this:
- I write the two CLAUDE.md sections in FL1-1d-1 (lane 1).
- The owner creates the two tasks with response 304's prompts, with the steps given by the orchestrator. No session
  creates them.
- The designer's page is signed off.
- The first live run of each edition is checked against its record.

**Also done since 6aabc36d.**
- FL1-1c is squash-merged to `main` (45c72f6f, after 434.1 PASS):
  - the full suite on the squashed tree: 9,024 passed;
  - the four suites (`tests/daily`, `tests/forecast_lab`, `tests/e2e`, `tests/e2e_acceptance`) re-run after a
    concurrent O1 merge: 214 passed.
- **Not done:** deleting `story/fl1-html-report`. The proxy cuts every branch-delete push ("unexpected disconnect";
  tried 4 times, two refspec forms), and the branch is still at 996e3b2e with the JSON. The owner can delete it in
  GitHub's branch list.
