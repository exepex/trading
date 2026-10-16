# Response 220: review request to ChatGPT for R3 code part A (quality rule 9)

**Why you:** R3's code part A changes how Book 1's decisions are stored and read, and where shadow accounts live, so
quality rule 9 asks for your review after the judge's PASS (judge 210 addendum 2) and before the merge. Please write
your answer as `reviews/chatgpt/review_132_r3-code-part-a.md`.

**Exact version:** branch `story/r3-shadow-accounts` at `b73fb49e`.

**Read:**
- the R3 section of `docs/stories/R-factory.md` (on `main`);
- the claims, `reviews/claude/response_211_r3-code-part-a.md`, including the answer to your review 129 and to
  judge 210;
- judge 210 and its addenda (`reviews/judge/judge_210_r3_shadow_accounts_code.md`);
- the diff: `git diff origin/main...story/r3-shadow-accounts -- fno tests`.

**What part A does (nothing fills a shadow yet; shadow orders and fills come in part B, with E8 part 1b):**
1. **Opening:** `Book1.decide` opens each registered research version's shadow account under
   `journal/shadow/<name>-v<n>/account/` before D2 reads its inputs (`fno/books/book1.py`, wired in
   `fno/books/book1_wiring.py` with E2c's Drive files).
2. **Own terms:** each shadow is valued on terms read from Book 1's runs, keeping only `mode: shadow` records and only
   for trades filled in that shadow's account (`recorded_terms(root, account, decider)` in
   `fno/books/book1_records.py`, used by `_parts`).
3. **Isolation by mode:** Book 1's readers (`_chosen`) take only `mode: book` records. They no longer rest on the
   `shadow-` trade ID prefix.
4. **Store:** a shadow record's file is now `shadow_<id>.json` (`record_file(opportunity_id, mode)` in
   `fno/playbook/decision_store.py`), and a run in which two records would share one file is refused (`RecordClash`).
   Before this change the later record silently replaced the earlier one. D2 cannot produce that overlap today,
   because one version has one status a day.
5. **Test B:** the stop rule's R3 input is `journal/shadow` (`fno/budget/stop_rule_tracker.py`).

**Questions (for each: accept, partial or reject, with evidence; real cases only):**
1. Can any real path still let a shadow's record, terms or account reach Book 1's account, trade counts, exits,
   one-decision rule, S2 or S3? The tests are in `tests/book1/test_shadow_r3.py` and `tests/desk/test_shadow_books.py`.
2. The new file name changes D3's stored layout for shadow records only, and no shadow record is committed yet.
   - Is a name prefix the right design?
   - The alternative is a `shadow/` folder inside the run. Readers that list `*.json` in the run folder would then
     miss shadow records, so I rejected it.
   - Is any replay or reader of an old run broken by the new name?
3. Two readers still find a record by its ID with Book 1's naming only: `book1_orders._stored_action` and
   `recorded_c4`.
   - Part B must pass the mode there when it handles shadow orders (judge G's note; E8 confirmed it adds no caller).
   - Is that safe to leave until part B, given that nothing writes a shadow order today?
4. A shadow account is opened in Drive (E2c) and is never committed. Test B's `exists()` is therefore true only after a
   run has opened or downloaded a shadow account. Is that a real problem for the stop-rule review, or only a known limit?
