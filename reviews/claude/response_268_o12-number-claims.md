# Response 268: story O12, one central place to claim file numbers (builder's claims)

Branch `story/o12-number-claims`, lane 1 (tools/, CI, rule documents). Story text: `docs/stories/O12-number-claims.md`
(commit 3a4684aa, pushed first per quality rule 1). Builder session_01KS9xBc14DGACR9QrS6Acdq. Number 268 is
the orchestrator's reservation (reviews/claude/README.md, acb57e21). The registry carries the orchestrator's
reservations as rows named `<prefix>_<n>_*.md`: responses 260-270 and judges 300-399 not yet written (judges E and F
number from those ranges until the merge). Each row registers its file when it lands, and the tool hands none of them
out, so a judge still writing from its range cannot clash with a tool claim; new judge numbers start at 400.

## Design check (the orchestrator's proposal, validated)

Accepted in full, with five changes found by testing and by the self-review (all reasoning plus the tests below):
1. **The seed is pinned.** Seeded `existing` rows may repeat a number, so a later seeded row could hide a clash (the
   first draft's "seeded rows first" rule did not stop it). The SHA-256 of each category's seeded rows lives in
   `fno/numbering/seed_pins.json`; changing it is a code change (lane 1).
2. **A claim counts files on `main`, not only rows**, so a file written the old way is never handed out again.
3. **Only a lost race is retried.** Git's `[rejected] (fetch first)`/non-fast-forward and, found by the four-thread
   test, the server's `cannot lock ref ... failed to update ref` when two pushes arrive together. Any other refusal
   (access, protection, network, hook) stops at once with git's own words.
4. **Addenda are a fourth series** (`judge-addendum`, number `<report>.<k>`): judge 98 and judge 122 each hold two
   addendum sections with one number (3 and 4).
5. **The judge-number convention ends.** Judges are at 274 and responses at 253, so "judge number = response number"
   is often taken; `docs/JUDGE.md` says so.

Integers in a registry against timestamps or UUIDs: in the story text. In short, the registry keeps "judge 270 add. 2"
readable and makes a clash impossible, not just unlikely; the cost is one push (about 2 s) per claim.

**Not a pre-commit hook or a branch gate**: a story branch does not carry its claim row (it is on `main`), so a
branch-local check would refuse correct work. CI runs it on every push to `main` and on PRs (merge ref).

## Criteria

| # | Code | Test (fails when the code is broken: mutation) |
|---|---|---|
| 1 | `numbers/*.csv`, `fno/numbering/seed.py`, `seed_pin.py` | `test_check.py::test_the_seed_registers_history_once_with_its_duplicates_and_pins_it`; 1,023 rows from main (merged after d7f2b737), plus 102 reservation rows (responses 260-270 not yet written, 268 being this file; judges 300-399 not yet written); duplicates: response 66, judges 233-235, addenda 98.3, 122.4, 233.1 |
| 2 | `fno/numbering/claim.py`, `git_main.py` | `test_claim.py` (exact free and taken, file without a row, report not on main, 10 refusals); M6, M9, M11, M16 |
| 3 | `claim.py:claim`, `git_main.py:commit_and_push` | two-clone race, four clones in threads, retries exhausted, server hook refusal; M1, M12, M13 |
| 4 | `git_main.py:main_copy` | caller's branch and staged file unchanged; one worktree left after success and failure; M5 |
| 5 | `fno/numbering/check.py` | `test_check.py` (17 cases: no row, renamed, shared, seeded repeat, pin changed first or last, misnamed, `###`, fenced, malformed rows, header); M3, M4, M7, M10, M14, M15 |
| 6 | `checks.yml` (last step, `if: always()`), `tools/ci_scope.sh` | `test_ci_scope.py::test_a_number_claim_is_lane_3_and_the_number_check_runs_on_every_push`; M17 |
| 7 | `CLAUDE.md`, `AGENTS.md`, `docs/JUDGE.md`, three READMEs, `numbers/README.md` | read by the judge (text) |

Planted mutations: 17 of 17 caught (`tests/numbering`, `tests/test_ci_scope.py`). M13 is caught by the four-thread
race, which depends on timing: it was caught in my run but is not guaranteed in every run.

## Gates (main d7f2b737 merged in, head after this file)

`pytest -q -n auto`: 7,790 passed. `ruff check` and `ruff format --check`: clean. `check_imports.py`: clean (1,495
files). `check_records.py`: clean (6,726 files). `check_numbers.py`: clean.

## Real output (a local bare copy of this branch as `origin`, record-scan hook on; not the real `main`)

```
$ claim_number.py claude-response o12-claims --session session_A &  claim_number.py claude-response other-work --session session_B
claimed: claude-response 254 -> response_254_other-work.md
claimed: claude-response 255 -> response_255_o12-claims.md
$ claim_number.py judge-addendum round-2 --session session_A --report 270
claimed: judge-addendum 270.2 -> round-2
$ claim_number.py judge-report x --session session_A --number 233
number claim: NOT claimed (judge-report 233 is already taken)
$ echo x > reviews/claude/response_66_again.md; check_numbers.py
reviews/claude/response_66_again.md: number 66 has no row in numbers/claude-response.csv
numbers/claude-response.csv: number 66 is used 3 times (response_66_2026-10-13-p7-p8-p9-publishing.md, response_66_again.md, response_66_g4.md); only seeded history may repeat a number
number check: FAILED, 2 problem(s); claim numbers with tools/claim_number.py (docs/stories/O12)
```

## Self-review (quality rule 3)

One independent review agent (correctness and silent failures) found 2 blocking, 7 should-fix and 9 minor issues.
- **Fixed:** the number check ran before the record scan, so a red number check would skip the record scan. It now
  runs last with `if: always()`.
- **Fixed:** a re-seed could hide a clash (now pinned).
- **Fixed:** a claim ignored files on main.
- **Fixed:** every push failure was treated as a lost race.
- **Fixed:** the judge convention was impossible to follow.
- **Fixed:** CLAUDE.md made the check a branch gate.
- **Fixed:** the manual path said "pull", which can merge two rows with one number.
- **Fixed:** `###` and fenced addendum headings.
- **Fixed:** misnamed files.
- **Fixed:** BOM, blank lines and empty-file headers.
- **Fixed:** malformed rows crashed a claim.
- **Fixed:** the session `existing` was accepted.
- **Fixed:** stamps were checked loosely.
- **Fixed:** the pause now comes before the re-fetch.
- **Fixed:** a temporary folder leaked on a failed worktree add.
- **Fixed:** duplicate finding lines.
- **Fixed:** line wraps.

Kept, with reasons:
- Unnumbered `## Addendum` headings are outside the series (14 old ones). An addendum must carry its number. A judge who writes an unnumbered one escapes the check: say so if you want them refused.
- The tests run with `core.hooksPath=/dev/null`. The real hook ran in the sample above, and a refused commit stops the claim with `GitFailed`.
- Two claims at once from the same checkout race on its `origin/main` ref lock and stop loudly.
- A push the server accepted but whose reply was lost leaves an orphan row (a wasted number, never a clash).
- The tool refreshes the caller's `origin/main` ref (stated in `git_main.py`).

## For the merger

Run `python tools/check_numbers.py --seed` on the merged tree (files keep landing on `main`), read the rows it adds
(`git diff numbers/ fno/numbering/seed_pins.json`), then the gates. Reservation rows still without a file stay as they are.

## Addendum 1: judge 354 (FAIL, 1 should-fix, docs only)

- **SF1 accepted.** The manual claim reset the claimant's own checkout, which wipes uncommitted work and moves the
  branch off unpushed commits. All four documents (`numbers/README.md`, `AGENTS.md`, `CLAUDE.md`,
  `reviews/chatgpt/README.md`) and the story text now claim from a separate copy of `main`: a worktree
  (`git worktree add --detach ../claim origin/main`), a fresh clone, or GitHub's editor. The reset happens only in that
  copy. GitHub's editor refuses a stale save the same way a push is refused.
- **Minor 1 accepted:** new test `test_a_claimed_row_reusing_a_number_seeded_once_fails`. The judge's mutation
  (`seeded_count[number] < 1`) now fails it: 1 failed, 56 passed. Reverted, 57 passed.
- **Minor 2 accepted:** `numbers/README.md` and the story now say that a claimed row edited or deleted before its file
  exists is not seen by the check; git history shows it.
- **Minor 3 not in O12:** the record-scan steps are skipped after a failed pytest step. That behaviour predates O12; it
  is for a separate change, as the judge says.
