# E3 fills by book: the daily run's fill result keyed by book

**Owner and lane:** builder session_01B3RARTgoiGJwBKXRCgGRe8 (orchestrator, 25 Oct 2026: "yes, you fix it"; E3's
original owner is out of reach). Lane 1 (it is the record of fills), one judge. It must land before Book 2's live
switch is set; with only Book 1 live there is no collision.

**Why (strong evidence: O11's replay of 16 Oct with Book 2 live, story F5):** E3's `fills` step keyed each trade's
result by its trade ID alone (`fno/desk/daily_steps.py`). The trade ID is `<day>-<opportunity_id>`, so Book 1 and Book 2
taking the same opportunity (the normal follow-the-rule day) wrote one key. Both accounts filled 4 legs; the run log kept
one line. Account records and alerts were right; the run log and anything reading it lost a book.

**The change:**
- The result is `{book: {"trades": {trade_id: entry}}}`. A book that opens nothing keeps its book-level
  `{"outcome", "reason"}` (blocked, or its orders refused), as before. A book with no order adds no key.
- One reader, `fno/desk/fill_results.py` (`trade_entries`, `trade_fills`, `book_refusals`), reads both the new shape
  and the old flat one. The step's own count of written trades and every test read through it. Nothing recorded is
  rewritten: the seven committed run logs (17-24 Oct) hold empty or missing fill results.
- Book 1's future logs change only in the key: each entry's values are the same.

## Claims

1. Two books on one trade ID keep both lines (`tests/desk/test_fill_results.py`).
2. An old flat Book 1 log reads the same as its new shape through the reader, including book refusals and step-level
   fields (same file).
3. Book 1's line on the recorded day of 16 Oct (O11's replay, real quotes) is exactly
   `{book1_rules: {"trades": {trade_id: {outcome, reason, snapshot_id, sha256}}}}`, the same values as before
   (`tests/e2e_acceptance/test_replay_day.py`).
4. The public run log needs no change: it recurses into the nested dicts, and book names are listed words.
5. **Not checked (outside this session's repository scope):** whether the dashboard (`exepex/omenix-dashboard`) reads
   `fills` from the run logs. If it does, it must read both shapes; the reader here is the rule to copy.
