# Response 229: answer to ChatGPT review 132 (R3 code part A, shadow accounts and Book 1 isolation)

Reviewed: `story/r3-shadow-accounts`, code at `b73fb49e` (judge 210 addendum 2 PASS). ChatGPT: PARTIAL, acceptable to
merge part A. All four points are accepted. Part A is merged; the conditions below gate part B and Test B.

1. **No contamination of Book 1 in part A: ACCEPT.** Part B repeats the with/without comparison after real shadow
   orders and fills exist, covering C2, C4, E6, S2, S3 and Book 1's actual ledger. That comparison gates part B's merge.
2. **`shadow_<id>.json` naming: ACCEPT.** `RecordClash` refuses collisions, and the `shadow_` prefix can never be a
   valid book-version name. Known limit: a reader that treats every `*.json` file in a run as a book record would
   misread a shadow record. The Book 1 reader has the mode guard. No compatibility layer is added.
3. **The two book-only readers (`book1_orders._stored_action`, `recorded_c4`): ACCEPT as a part-B activation
   condition.** Before any shadow order is written, both readers take an explicit mode and account. A test plants a
   book record and a shadow record with the same ID and proves each reader selects only its own. A missing shadow
   record fails closed and never falls back to Book 1.
4. **Test B readiness: ACCEPT (code checked: `fno/budget/stop_rule_tracker.py:41` tests only whether a path exists).**
   - At Test B's integration, readiness comes from resolved shadow closed-trade records, after the normal E2c download,
     checked against the registered trial requirements; it never comes from whether a folder exists.
   - Zero resolved shadows stays `undecided/no_economic_test`, never NO.
   - A review that runs before the download reports "data not loaded".
   No new Drive API or service is added. This is not a part-A blocker, because Test B is not computed yet.

Next: the R3 builder carries points 1, 3 and 4 into part B's story text and tests; the judge checks them there.
