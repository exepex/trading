# Response 74: story E2, the common market pack and book-private packs (builder's claims for the judge)

Story: `docs/stories/E-paper-desk.md` E2. Builder: Claude, 14 Oct 2026. Branch `story/e2-market-pack` (nothing on
`main` until the judge passes it). Research and paper only: nothing here places, modifies or cancels orders.

## 0. The verdict in two lines

The common market pack and Book 1's private pack are built, hashed and written once by `python -m fno desk pack`.
The common pack holds market data only. Every item carries its source and availability time, and anything after the
15:00 cutoff is refused by name. Rebuilding from committed inputs gives the same bytes even after later downloads.
The private packs of books 2 and 3 use the same builder; their CLI waits for D4 and D5.

## 1. Design

| Part | File | Job |
|---|---|---|
| Source contract | `fno/desk/pack_items.py` | `PackItem` (name, value, source, available_at); `admit` refuses an item after the cutoff or with no time, listing name, time and reason; canonical JSON and SHA-256 |
| Inputs (interface `CommonInput`) | `pack_inputs.py`, `snapshot_inputs.py`, `reference_inputs.py` | A4 snapshot, the session (A7), official closes (A10/O6) and events (A6) |
| Common pack | `common_pack.py` | admits items, adds provenance and the opportunity set; refuses the finished pack if it names any book or `journal/` |
| Opportunity set | `opportunity_set.py` | D2's `OpportunityFinder` (DRY) over the versions approved as of the start of the day, plus `no_trade` |
| Private pack | `private_pack.py` | the book's own files (path, SHA-256, text) from its allowed folders only (table below) |
| Store | `pack_store.py` | `journal/packs/<date>/common.json` and `journal/<book>/packs/<date>/private.json`, each with a `.sha256` in `sha256sum` form; write-once; temporary file then rename |
| Wiring, CLI | `pack_wiring.py` (new composition root, added to CLAUDE.md), `pack_cli.py` | `python -m fno desk pack [--day]` writes the common pack and Book 1's private pack and prints both hashes |

What each common-pack input provides:

| Input | Items | Available at |
|---|---|---|
| A4 snapshot (same dataset E4 fills from) | each option row: bid, ask, sizes, validity, spot | the row's `response_received_at` |
| | India VIX | the later of NSE's timestamp and the capture's first request |
| | futures (the monthly expiries) | the first request |
| | provenance: snapshot ID, CSV and meta SHA-256 | |
| Session | the day's NSE session kind | |
| Official closes | the last 260 before the day | each at 15:30 of its own day |
| | provenance: the SHA-256 of the rows supplied | |
| Events | announced on or before the day, dated on or after it | the end of the announcement day, because an announcement has a date but no time; so one made on the day itself is refused |

Private pack folders (`ALLOWED_FOLDERS`):

| Book | Folders |
|---|---|
| Book 1 | `journal/book1_rules/`, `playbook/` |
| Book 2 | `journal/book2_hybrid/`, `playbook/` (its envelope will live beside the playbook, D4) |
| Book 3 | `journal/book3_ai/`, `book3/` (D5) |

A file is taken only if it **resolves** inside one of its book's allowed folders, so a link or `..` into another book
is refused. The book's own `packs/` folder and dot files (the account's `.lock` lease, which holds host and process)
are left out.

**Rebuilds give the same bytes.** Inputs offer only what existed as of the day:
- closes strictly before the day;
- events announced by then;
- the opportunity set from registry rows dated before the day;
- no build time in the pack;
- no whole-file calendar hash, which changes when a new year is added.

So the judge's "rebuild one day's packs from committed inputs and compare hashes" holds after later downloads, and a
test proves it.

## 2. Claims per acceptance criterion (`tests/packs/`)

| # | Criterion | Tests |
|---|---|---|
| 1 | No field from any `journal/<book>/` path in the common pack | `test_a_planted_position_never_reaches_the_common_pack` (planted marker absent, no `journal/`, no book name); `test_a_pack_naming_a_book_or_journal_path_is_refused` (the leak guard refuses); `test_the_pack_holds_market_items_with_source_and_time` (fixed top-level schema) |
| 2 | A private pack never holds another book's data (each pair) | `test_a_private_pack_never_holds_another_books_data` (all 6 ordered pairs, markers in accounts, decisions, `book3/`), `test_a_link_into_another_book_is_refused`, `test_packs_and_dot_files_stay_out`, `test_book_1_reads_its_account_decisions_and_the_playbook_book_3_reads_book3` |
| 3 | Twice from the same inputs: byte-identical, same hash | `test_building_twice_gives_byte_identical_packs`, `test_private_packs_are_byte_identical_when_built_twice`, `test_later_closes_and_announcements_do_not_change_a_rebuilt_pack`, `test_the_store_writes_once_with_a_checkable_hash` |
| 4 | Input after the cutoff refused with its name | `test_an_input_after_the_cutoff_is_refused_by_name` (15:00:01), `test_a_quote_and_vix_observed_after_15_00_are_refused_by_name` (on a copy of the committed golden A4 snapshot), `test_an_event_announced_on_the_day_is_refused_one_announced_before_is_kept` |
| 5 | Common opportunity set equals a hand computation | `test_the_opportunity_set_matches_a_hand_computation`: on 13 Oct 2026 the 23 Nov expiry enters a 30-41 day window (41 days; 42 on the session before), exit on Monday 2 Nov. A 30-45 window opened earlier, so no opportunity today; a version approved on the day counts from the next session. Also `test_nothing_approved_leaves_only_no_trade` |

Wiring on the real repository: `test_pack_wiring.py`. `tests/packs`: 26 tests.

## 3. Mutation checks: 11 of 11 caught (bytecode caching off)

| Mutation | Caught by |
|---|---|
| cutoff moved to 15:59 | `test_an_input_after_the_cutoff_is_refused_by_name` |
| leak guard off | `test_a_pack_naming_a_book_or_journal_path_is_refused` |
| resolve-inside check off | `test_a_link_into_another_book_is_refused` |
| own packs folder not excluded | `test_packs_and_dot_files_stay_out` |
| dot files not excluded | `test_packs_and_dot_files_stay_out` |
| approval counted on the day (`<=`) | `test_the_opportunity_set_matches_a_hand_computation` |
| all closes, not before the day | `test_later_closes_and_announcements_do_not_change_a_rebuilt_pack` |
| later announcements offered | same |
| announcement at 00:00, not end of day | `test_an_event_announced_on_the_day_is_refused_...` |
| write-once check off | `test_the_store_writes_once_with_a_checkable_hash` |
| VIX time ignores NSE's timestamp | `test_a_quote_and_vix_observed_after_15_00_are_refused_by_name` |

## 4. Limits and decisions to confirm, said plainly

1. **Approvals take effect from the next session** in the common opportunity set (registry rows dated before the
   day). This keeps rebuilds stable. D2 (Book 1's evaluation) reads the current playbook, so a version approved during
   a session could be evaluated by D2 that day but be missing from the common set until the next. To align, either D2
   uses the same "as of the start of the day" rule, or approvals are always dated for the next session. I recommend
   the first (reasoning only); a D2 change goes to the judge separately.
2. **Committing is left to the daily run** (E3/O1's timetable). `desk pack` writes and prints; it does not commit.
3. **No A4 snapshot is committed on `main` yet** (the recorder's first runs are today). The tests use the committed
   golden snapshot of G1 v2 (case A). On the real repository, 13 Oct's common pack says `snapshot_id: null` in its
   provenance and has no option items.
4. **Quotes come from Groww's dataset** (the one E4 fills from), not the NSE dataset recorded beside it. The
   side-by-side comparison (owner's decision of 13 Oct) decides any switch: one line in `pack_wiring.py`.
5. **Books 2 and 3**: the builder and the separation tests cover them now. The CLI packs Book 1 only until D4 and D5
   define the envelope and constitution files.
6. **Judge's note on the real `ShadowBooks`** (D2): it is not built in E2. Whoever builds it (E5) must prove the shadow
   account writes only inside its declared folder. I have noted this for that story.
7. Not a pack field: closes use `fno/forecast/closes_source.py` (frozen G1 code, imported, not changed).

## Addendum 1 (14 Oct 2026): judge 72's findings, all accepted and fixed

The judge's 14 plants found 9 gaps in my tests; the code was right in each place, the tests did not guard it.

1. **Must-fix 1, opportunity-set status (criterion 5).**
   `test_only_versions_paper_at_the_start_of_the_day_are_offered` has four versions:
   - a registered research version;
   - a version approved and then paused before the day;
   - a version approved on the day;
   - a version approved before the day.
   Only the last is offered, plus `no_trade`. Plants P6 (earliest row wins) and P14 (status ignored) now fail it.
2. **Must-fix 2, point in time (criterion 4).**
   - `test_a_quote_received_after_15_00_and_an_untimed_vix_are_refused`: a request sent at 14:59:59 whose response
     arrived at 15:00:01 is "after the cutoff" (P3). VIX with no NSE time, or an unreadable one, is "no availability
     time" (P4).
   - `test_an_item_at_exactly_the_cutoff_is_kept` (P1).
3. **Must-fix 3, never freeze an empty pack.**
   - A recorded session day (regular or special) with no canonical A4 snapshot is refused: "no canonical A4 snapshot
     for <day> (<session> session): nothing written". `desk pack` exits 2 and writes nothing.
   - A closed day, or a muhurat-only evening the recorder never records, still gets its session-only pack.
   - Test: `test_a_session_day_without_its_snapshot_is_refused_and_a_closed_day_is_packed`.
   - On the real repository, 13 Oct is now refused (`test_the_app_refuses_a_session_day_without_its_snapshot`), and
     the wiring test builds a Saturday.
   - **Run order this implies for E3/O1:** pack only after the canonical A4 snapshot is committed. A failed recorder
     means no pack, so no book decides on an empty market.
4. **Should-fix, one test each:**
   - P2: `test_two_items_with_one_name_are_refused`;
   - P7: `test_past_events_are_not_offered`;
   - P9: `test_the_last_260_closes_before_the_day_are_kept`;
   - P10: `test_a_journal_path_alone_is_refused`;
   - P13: `test_the_provenance_names_the_snapshot_files_by_hash`.

**Checks:**
- All 11 of the judge's plants that the tests missed, plus my "empty pack frozen" mutation, are caught now: each
  re-applied, `tests/packs` run, then reverted.
- `tests/packs`: 37 tests.
- Full suite on the tree merged with `main`: 2316 passed.

**Answers to the judge's information points:**
- Book 1's pack will hold Book 2's envelope files once D4 adds them to `playbook/`; they are frozen rules, not state.
  D4's claims should state it.
- Events without `announced_on` are dropped before admission. The real file's three such rows all predate 13 Oct.
- The Groww routine's 13 Oct result (no snapshot committed) is reported to the orchestrator as a separate problem.

## Addendum 2 (14 Oct 2026): one rule for "approved at the start of the day"

After D2's start-of-day change merged (a0a8eef), the opportunity set reads `Playbook.status_on(day)`, the same rule
D2 uses. E2's own copy (`approved_on`) is removed.

The common pack's playbook input is now D1's loader itself. `Playbook` carries the registry rows, so the
`registry_rows()` interface and `LoadedPlaybook` adapter are gone.

A version paused during the day stays in the common set, as judge 72 accepted; Book 1's gate drops it at once
(judge 74). The status tests in `test_pack_contract.py` are unchanged and pass.
