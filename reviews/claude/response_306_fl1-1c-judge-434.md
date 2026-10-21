# Response 306: FL1-1c production, judge 434 answered

From the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd) to Judge E, 22 Oct 2026. Branch `story/fl1-html-report`.

I accept all four should-fix findings and all three minors. For each one I checked the code first.

## Should-fix

1. **The record counts back-tested days as if they were live: accepted.**
   - **Check:** `builder._index` takes the last 30 N1 points from `G13bHistory`. That source falls back to back-fill
     wherever no live row exists, and `record_words` did not say so.
   - **Fix:** `IndexView.backtested` counts the back-fill points in the window. The record now reads "right 26 of
     the last 30 days (26 back-tested)" until the window is all live. The same function writes the Slack line and
     the picture's light label, so both carry the count.
   - **Light:** I kept the light as it is; the owner decides whether it becomes "Too few live days". The details page
     already marks live days (underlined in the grid, a filled dot on the chart).
   - **Tests:**
     - `test_back_tested_days_are_said_in_the_record_until_the_window_is_all_live`;
     - the builder test `test_the_record_counts_the_back_tested_days_in_its_window`: 30 scored, 26 back-tested,
       4 live.
     - A mutation setting `backtested=0` is caught.
2. **The history pools method versions: accepted.**
   - **Check:** G13b's records and score rows both carry `method_sha256`. My `_records` key `(label, day)` also
     dropped `issue`.
   - **Fix:** only the current version counts. The current version is the one behind the newest record, with live
     winning over back-fill on the same day.
     - Score rows of any other version are dropped.
     - Bands are keyed `(label, day, issue)` within the current version only.
     - So two versions are never pooled, and a band is never paired with another version's score.
   - **Tests:** three, with two versions:
     - an old-version back-fill and a new-version live record;
     - every row of the old version;
     - the same back-fill day rebuilt by both versions, with the old one read last.
   - **Mutations:** 3 of 3 caught (no score filter, no band filter, live not preferred for "current").
   - **Consequence, stated plainly:** at G13b's first method change, the page's record restarts from that version's
     own rows. This is honest, but the light will read "Too few days" until G13b back-fills the new version.
3. **Pillow is undeclared: accepted.**
   - **Fix:** `Pillow>=10.0` is now in `requirements.txt`, which `tools/routine_setup.sh` installs. A failed install
     stops setup loudly.
   - **Partial push-back:** I did not add `PIL` to O7's hard import probe (`modules="numpy, requests, yaml"`, owned
     by O7). A missing Pillow costs only the picture, with its alert, and the text and the details file still post.
     Making it a whole-routine stop would turn a degraded report into no report, and the 3 pm quotes would stop
     too. If you still want it in the probe, that is O7's file and its owner's decision.
4. **8,443 lines of derived data in the repository: accepted.**
   - **Fix:**
     - `pageview-2026-10-19.json` is removed. Nothing read it, and the designer works from the page model's code.
     - The three preview files are regenerated from **synthetic** numbers: a seeded random walk with made-up bands,
       labelled "Preview: synthetic numbers, not market data". They go through the real `PageBuilder` and
       renderers.
     - The README says so.
   - **History:** the file stays in this branch's commit history (2ed6405e). I will merge this story to `main` as
     one squashed commit, so `main`'s history never carries it. Rewriting the pushed branch is not needed for that.
     Please say if you want the branch itself rewritten.

## Minors

1. **The two survivors: tests added.**
   - Q2: an unreadable (non-JSON) answer to `completeUploadExternal` is may-have-posted, never retried. A mutation
     that drops `ValueError` from `LOST_ANSWER` is caught.
   - Q10: a score whose target is the report day itself never enters the history. A mutation from `<` to `<=` is
     caught.
2. **The headline method is picked on the history it is scored on: wording fixed.** The details now say "lowest error
   on its own history, the same days it is scored on". The selector question stays with IL.
3. **Response 301's "a refused connection is retried": corrected here.**
   - Only `ConnectTimeout` (no connection made) is "not posted" and may be retried by a rerun.
   - `ConnectionError`, including a refused or reset connection, counts as may-have-posted and is never retried.
     That is conservative, because the connection may have dropped after Slack received the request.

## Gates (on the branch merged with `main` at fc50a995, one run)

- Tests: 9,024 passed, 17 xfailed.
- Lint and format: `ruff check` clean; `ruff format --check` shows 1,687 files formatted.
- Other checks: `check_imports` clean; record scan clean (7,385 files).
- Mutations for this round: 6 of 6 caught (3 for versions, 1 for back-tested, Q2 and Q10).

`lab_close` stays null. The orchestrator confirms that the report waits for the owner's sign-off of the designer's
two-edition page. FL1-1d (the two editions, responses 303 and 304) builds on this branch after your verdict.
