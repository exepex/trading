# Response 211: R3 code, part A (build order A): claims (for the judge)

**Branch:** `story/r3-shadow-accounts` (from `main`). **Story text:** `docs/stories/R-factory.md`, R3 (judge 208
addendum 1 PASS). Owner's decision 2 A: account opening, own terms and the Test B path now; fills with E8 part 1b; B0's
registration after this merges. Lane 1.

| # | Claim | Evidence |
|---|---|---|
| 1 | Book 1's run opens each research version's shadow account before D2 reads its inputs (criterion 1). | `fno/books/book1.py` `decide` calls `open_shadows(shadow_on(day), day)` before `inputs.day`; `test_shadow_accounts_are_opened_before_d2_reads_its_inputs`. Mutation (call removed) fails it. |
| 2 | An account already opened is never reset. | Strong: the opener is the existing `start_shadow_books`. Under the account lock, `open_account_writer` pulls the account from Drive (E2c `files`) before `writer.start`, which opens only a never-started account (`tests/desk/test_shadow_books.py`: a second call opens nothing). `cmd_book1` passes its shared download into `build_book1`. |
| 3 | Each shadow is valued on its own terms; Book 1's terms never reach a shadow (criterion 2). | `opening_runs`, `opening_trades` and `recorded_terms` take `decider`; the shadow books get `recorded_terms(account, decider=Book 1)`; `test_each_account_takes_only_its_own_records_and_terms`. |
| 4 | Book 1's readers take no shadow record, and the isolation does not rest on the `shadow-` prefix (criterion 9, E5's readers). | `_chosen` keeps a record only if its `mode` matches the reader. Two tests: same-day with and without a shadow; and a wrong-mode record with a matching id. Mutation (mode check removed) fails the second. |
| 5 | Test B's R3 input points at the shadow accounts (criterion 7). | `fno/budget/stop_rule_tracker.py` `SHADOW_ACCOUNTS = journal/shadow`; zero shadows still give "undecided" (`fno/forecast_v4/stop_rule.py`, unchanged). |
| 6 | Nothing fills a shadow yet (criterion 6). | No fill code added; shadow orders and fills are E8 part 1b's. |
| 7 | E6, S2 and S3's Book 1 views are unchanged (criterion 9, the rest). | S3: tested. `test_s3_book1_actions_are_unchanged_by_a_shadow_on_the_same_day` builds scoreboard A (`MatchedDays`, `action_of`, on `main` since 91c54f88) with and without a shadow record in Book 1's run, and Book 1's action rows are equal (S3's own `test_a_shadow_candidate_outside_the_common_set_never_appears` agrees). E6's Book 1 section and S2's Book 1 board: strong, from reading the code. They read Book 1's own account (`journal/book1_rules/account/`), which R3 never writes. |

**Gates:** `pytest -q -n auto` 6,792 passed; `ruff check`, `ruff format --check`, `check_imports` and `check_records` are
clean.

**Known limit:** on a fresh checkout, `journal/shadow/` holds no committed files: accounts are kept in Drive (E2c). So
Test B's `exists()` is true only after a run has opened or downloaded a shadow.

## Code-round answer to ChatGPT review 129 (via response 214): accepted, with two parts pushed back on evidence

| Review 129 asks | Answer | Evidence |
|---|---|---|
| Same session, one Book 1 trade and one shadow trade with different terms | ACCEPT | `test_book1_s_readers_and_account_are_identical_with_a_real_same_day_shadow`: Book 1's real D2 run decides one session with a paper version and a research version (width 50 against Book 1's 100). It asserts both modes are recorded and the widths differ. |
| Book 1's opening trades, decided exits, counts, one-decision finder, account files identical with or without the shadow | ACCEPT, one part PARTIAL | All equal, the account files byte for byte. **The finder's run documents are not byte-identical by design:** D2 records the shadow books in `inputs.json` so the run can be replayed (`fno/playbook/decision_inputs.py`, `RecordingShadowBooks`). The test therefore compares what the one-decision rule uses: which runs exist, and where (`run_id`, `place`). |
| E6 section | ACCEPT through its input | E6's Book 1 section reads only Book 1's account (`strategy_records(account, DeskRecords, charges)`), which the test compares byte for byte. Calling E6 directly on this fixture fails on the fixture's minimal fill rows (no units), not on a shadow. |
| S2 and S3 boards | ACCEPT | S3: `test_s3_book1_actions_are_unchanged_by_a_shadow_on_the_same_day`. S2: `test_s2_book1_section_is_identical_with_a_shadow_record_in_book1_s_run`, on S2's own fixture, with a shadow record inside Book 1's run, because S2 feeds every record of a run into D6's segments (`entry_decisions.py`). Book 1's S2 section is equal. |
| Overlapping opportunity IDs | REJECT, as impossible | An `opportunity_id` is `<name>-v<n>:<expiry>`, with no mode in it (`fno/playbook/opportunities.py`). A version is a book opportunity only at `paper` and a shadow only at `research`, never both on one day. D2's store keeps one file per id (`decision_store.py`, `record_file`). My own first probe "showed" an S3 leak only because the fixture's shadow record overwrote Book 1's file; I retracted it to the S3/S6 builder. |
| A shadow trade ID not starting `shadow-`, still isolated by mode | ACCEPT | `test_a_record_of_the_wrong_mode_is_never_taken_even_with_a_matching_id` uses the ids `same` and `other`. Mutation: removing the mode check fails it. |
| Conflicting caps: refuse only the shadow | ACCEPT, already covered | `tests/playbook/test_evaluate.py::test_shadow_and_book_never_share_slots`: the shadow's own book is full, so the shadow gets `SHADOW_NO_TRADE` ("slot:") while Book 1 is chosen. New for R3's own change: `test_a_shadow_with_an_open_trade_is_valued_on_its_own_terms_never_book_1s`, where terms lacking the shadow's trade raise `RiskInputError` (the old crash) and its own terms load. |

**Gates:** `pytest -q -n auto` 6,796 passed; ruff, format, imports and the record scan are clean.

## Answer to judge 210 (FAIL, finding 1) and the orchestrator's store fix

| Ask | Answer | Evidence (strong: each test fails under the judge's mutation, run by me) |
|---|---|---|
| `_parts` gives a shadow book only its own trade's terms | ACCEPT, tested | `tests/desk/test_shadow_books.py::test_book1_s_parts_give_each_shadow_book_its_own_trade_terms`: one Book 1 trade (`b1`) and one shadow trade (`t1`) opened by E4's desk, both recorded in Book 1's run. `_parts` gives Book 1 `b1` and the shadow `t1`. Mutation `shadow_terms = lambda account: terms` fails it with `RiskInputError` (`book_view.py:38`). |
| `build_book1` wires the opener | ACCEPT, tested | `tests/book1/test_shadow_r3.py::test_book1_as_the_app_builds_it_opens_a_registered_research_version_s_account`: the app's `build_book1(cfg, root)`, only the playbook and run finder replaced; `decide` opens `journal/shadow/cand-v1/account`, then stops at the inputs (no packs). Mutation (opener not passed) fails it on the folder assertion. |
| Tracker's R3 path | ACCEPT, tested | `tests/budget/test_stop_rule_tracker.py::test_test_b_reads_resolved_shadow_trades_from_the_shadow_accounts_folder`: the path is `journal/shadow`, and it exists once E6 opens an account. Mutation (path dropped) fails it. |
| Notes 1 and 2 | AGREE | E6 and S2 with/without tests go with part B (E8's fills). The S3 test is a guard that passes partly by construction. |
| Store: keep shadow records apart, both survive an overlapping ID | ACCEPT, built | `record_file(opportunity_id, mode)`: a shadow record is `shadow_<id>.json`. Version names are `[a-z0-9-]` only (`schema.py` `NAME_PATTERN`), so it never matches a book name. `DecisionStore.write` now refuses a run (`RecordClash`, nothing written) if two records would still share a file, instead of keeping the later one silently. The replay names fresh records the same way (`decision_run.py`). Test: `tests/decisions/test_records.py::test_a_book_and_a_shadow_record_of_one_opportunity_both_survive_and_a_true_clash_is_refused`. Its shadow-case replay test still passes. |

**What the store fix changes in practice** (reasoning plus code reading): today nothing. D2 cannot make the overlap:
- `status_on` gives a version one status a day;
- `approved_on` (paper) and `shadow_on` (research) are therefore disjoint;
- `evaluation.chosen` holds Book 1's choices only (`outcomes.py:71`), so the order replay (`book1_orders._stored_action`, book name) never reads a shadow file.

The fix makes the overlap impossible at the store too, so a later change cannot reopen it silently. No shadow record is committed yet, so no stored run changes name. Two readers stay book-only: `book1_orders` and `recorded_c4` (by `order.decision_id`). Part B's shadow orders must pass the mode (Known limit for E8 part 1b).

**Gates:** see the push message to the orchestrator.
