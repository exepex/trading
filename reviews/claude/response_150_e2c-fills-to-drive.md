# Response 150: story E2c, per-contract paper fills, marks and equity history in Drive (story text for the judge)

Builder: Claude. Branch `story/e2c-fills-to-drive`, from `main`. Story text only, under the owner's rule "keep the
design simple" (real paths only). Sources:
- the owner's decision of 15 Oct 2026 ("A: move to Drive");
- ChatGPT review 105, points 1 and 3;
- the orchestrator's response 131.

**Renamed from response 148** (orchestrator, 15 Oct): 148 is G9's claims on `main`. Judge 148's file still says
"response 148" for E2c and is left as it is; it means this file.

## What the story does (docs/stories/E-paper-desk.md, "E2c")

- **Drive:** every paper file that names a contract's price, and every mark, is kept in Drive through A4b's store.
  That is the cash ledger, the desk's fills and events, positions, equity history and scoreboard B.
- **Public:** the repository keeps `journal/<book>/daily_totals.csv` only: date, closed equity, open and closed trade
  counts, and the fill count.
- **One writer:** `DriveAccountSync` replaces `GitAccountSync` behind E3's `AccountSync` port. The daily run is the
  only account writer.
- **Blocked entries:** a session whose run log has no `exits` step blocks the next session's new entries, with one
  alert (review 105 point 3).

## Facts checked in code (strong evidence unless marked)

| Fact | Where |
|---|---|
| Account files committed today hold only the opening rows (no fill yet) | `git ls-files journal`; `journal/book1_rules/account/cash_ledger.csv` |
| The cash ledger holds contract, quoted and fill price per fill | `fno/books/fills.py` `LEDGER_COLUMNS` |
| Equity history holds daily marked equity | `fno/books/account.py:32` `EQUITY_COLUMNS` |
| Home's read model publishes a book's marked equity | `fno/market_read_models/home_inputs.py:50-55` |
| The dashboard contract plans each book's marked `value`, and each open trade's `mark_value` and `unrealised`, as public | `contracts/omenix-dashboard/api/schemas/fno-paper-trades.yaml` |
| The scheduled routine starts in a fresh container, so a stop is seen only in the committed run log | reasoning (how the scheduled sessions run) |

## Answer to judge 148

| Finding | Accepted? | Change |
|---|---|---|
| Ruling: the dashboard read model is not public | **accepted** (I had checked it too: `PostgresPublisher` on `FNO_DB_URL`; the only GitHub commit is `PublicationInputsFile`, provenance hashes only) | The dashboard-contract bullet and criterion 6 are dropped. A Known-limits line says no later job may commit these fields to a public repository |
| Must-fix 1: the committed private packs would copy the downloaded account files every day | **accepted (strong: `private_pack.py`, `daily_steps.py:85`, `pack_store.py:28`)** | I chose the simpler option: `private.json` goes to Drive beside the account, and only its `.sha256` stays public (D3 records the pack's hash already). Leaving the account text out of the pack would change what the books read. The private packs are added to criterion 1's scan |
| Should-fix 1: daily readers missing | **accepted** | Named: the daily run, Book 1 with its pack, C4's `LedgerAccounts` (its cutoff filter keeps replays valid on the Drive copy), T1's card, E6, scoreboard B, Home, E1's account command and the shadow books. One shared download runs at the start of each run or command |

## Code round (for judge B; then ChatGPT, rule 9)

Built from the PASSed text (c62ef47, judge 148 add. 1), rebased onto current `main`. Simple design, owner's rule.

**What changed**
- `fno/desk/private_files.py` (new): `PrivateFiles` keeps each account's five files (ledger, equity history,
  positions, desk fills, desk events) and the books' `private.json` in Drive through A4b's `IndexFileStore`
  (`DriveIndexStore`, area `paper`). It has one shared `download(day)`, `pull_account`/`push_account` for the writer,
  and the one-time `move_accounts()`. Any Drive failure is raised as `PrivateFilesUnavailable`, a `CommitFailed`, so
  E3's one handler alerts and stops the run.
- `fno/desk/drive_sync.py` (new): `DriveAccountSync` replaces `GitAccountSync`. Under the lock it pulls, applies and
  pushes (`open_account_writer(files=...)`), then commits `journal/<book>/daily_totals.csv`.
- `fno/books/daily_totals.py` (new): the five public columns, one row per IST date with a ledger row.
- `fno/desk/git_sync.py`: `GitAccountSync`, `CheckoutNotDedicated` and the reset logic are removed (one writer, no
  merge). `GitCommitter` is unchanged.
- The daily run downloads after its recovery step. The fills step opens nothing, with one alert, when the last
  session's run log has steps but no `exits` (and no `skipped`) step.
- The pack step pushes `private.json` to Drive and commits the common pack plus every `.sha256`.
- Readers download first: `desk book1` (with the day's private pack), `desk scorecard`, `scoreboard b` (its board is
  written locally, git-ignored, and pushed to Drive), `market publish` (Home), `card daily`, `account init/top-up/show`
  and `desk pack`. `fno/cli.py` turns `PrivateFilesUnavailable` into one line, `stopped: ...`, and exit 1.
- `.gitignore`: `journal/*/account/`, `journal/shadow/*/account/`, `journal/*/packs/*/private.json` and
  `research/scoreboards/B/`.
- New command `python -m fno account move-to-drive`.

**Claims per criterion** (tests in `tests/timetable/test_fills_to_drive.py`, `test_private_readers.py`,
`tests/desk/test_private_files.py`):
1. The test runs two fixture days end to end: the pack step (real `PrivatePackBuilder`, `PackStore`) on 14 Oct, t1 and
   b1 opened, then t1 closed on 16 Oct, each day in a fresh container.
   - It scans every committed path for every fill, quoted and mid price, every ledger amount and every open-book cash.
     It finds nothing, and no committed path is an account file or a `private.json`.
   - The scan's sensitivity is checked on the ledger itself (more than 10 hits).
   - Excluded: a flat book's cash, which equals its closed equity by definition (the public column).
2. Book 1's rows, checked by hand: `2026-10-14,2000000.00,1,0,4` and `2026-10-16,1999486.36,0,1,4`. The closed trade's
   net is Rs -513.64 in the run log, and the Drive ledger's amounts also sum to 1999486.36.
3. Eight readers, each compared before and after `fresh_container` plus `download`:
   - the account itself;
   - Book 1's C2 view, its trade counts and its private pack;
   - C4's `LedgerAccounts`;
   - T1's status lines;
   - E6 and scoreboard B's record seam (`paper_accounts` and `DeskRecords`);
   - Home's `BooksReader`.
   Six commands are also checked: each stops on a Drive failure before its builder runs.
4. When a Drive write of an account file fails (503), the run stops at `step fills` with one alert ("could not be
   written") and no fills commit. The rerun later the same day, in a fresh container, fills once: Drive holds 4 legs.
5. Run both ways: with 13 Oct's log stopped after `versions`, 14 Oct opens nothing, sends one alert naming 13 Oct, and
   still runs its exits. With no stop, t1 opens and no alert is sent.

**Where I differ from the text (please rule)**
- Drive path: `paper/journal/<book>/account/...`. Each file keeps its whole repository path, rather than
  `paper/<book>/account/`, so one rule covers accounts, packs and scoreboard B (`research/scoreboards/B/`). Reasoning
  only. Stripping `journal/` is a few lines if you want it.
- T1's card now reads `positions.json` from the downloaded copy (`DownloadedRecords`), which is the one exception to
  T1 criterion 5 ("committed records only"). The text asks for exactly this. The card still hashes what it used.
- Criterion 3 for E6 and scoreboard B is tested at their record-reading seam, not a full board build (the board needs
  the playbook and snapshots, which the fixture does not have). Both commands are tested to download before they build.

**Known limits (honest)**
- Shadow accounts are found by their folder under `journal/shadow/`, which is now git-ignored. Today nothing in
  production starts a shadow account (`start_shadow_books` has no caller), so no data is lost now. The story that
  wires shadow starts must list them from a committed source (the playbook registry), or a fresh container will miss
  them.
- `daily_totals.csv` is written when a book's account is written. A book never written has its file only from the move
  command.
- `market publish` now needs the four `FNO_GDRIVE_*` settings. `market-publish.yml` already has them. Without them
  it stops with one line rather than publishing books from a stale copy.
- The two-runs-at-once race on Drive stays as written in the story.

**Merge steps for the orchestrator (in order)**
1. Merge, then run `python -m fno account move-to-drive` with the Drive settings. Each file prints "uploaded" (or
   "already in Drive"), and each book's `daily_totals.csv` is written. On any "REFUSED" line, stop and ask the owner.
2. Commit the `daily_totals.csv` files.
3. In a separate commit: `git rm -r --cached journal/*/account` (the history keeps only the opening and top-up rows).

## Answer to judge 159 (code FAIL at 7823796c)

| Finding | Accepted? | Change |
|---|---|---|
| **Blocking 1:** a push that stops after the ledger leaves Drive half-written, and every rerun crashes (`IndexError`, `status.py:60`) | **Accepted. Reproduced, and the root cause is the push order.** **The suggested order ("ledger last") is rejected, with evidence.** With the events pushed before the ledger, a 503 on the ledger leaves Drive with the "opened" event and no ledger fill. The rerun's `EntryDesk.enter` sees the event, returns the recorded outcome and applies nothing (`entries.py:117-119`). The book then shows 0 fills in its ledger and 4 desk rows: silently wrong cash, with no crash and no alert. I ran the new test under that order: 3 of 9 fail (`assert 0 == 4`, ledger fills) | Order (`private_files.ACCOUNT_FILES`): desk fills, ledger, positions, equity history, desk events. The events are the entry's "done" marker, so they go last. The ledger never reaches Drive without its desk rows. Both fill files are idempotent by fill ID, and `IdempotentCsvLog.append` accepts an identical row (checked). Positions and equity history are rebuilt from the ledger. **Test:** a 503 on each of the five files in turn (parametrized). Each stops the run with one alert and commits nothing. A fresh-container rerun then opens t1, runs the exits, and leaves Drive with 4 ledger fills, 4 desk rows, one "opened" event and a readable open position. Under the old order and under "ledger last", 3 of the file's 9 tests fail (3 of the 5 file cases) |
| **Should-fix 1:** a stop at the download or recovery does not block the next session | **Accepted** | `_stopped_before_exits`: a last session with no log blocks once an earlier log exists (the desk's first day is never blocked). `RunLog.days` lists the logged days. **Test:** 12 Oct logged, 13 Oct stops at the download (Drive token expired), 14 Oct's fills are blocked with one alert naming 13 Oct, and its exits run. Plants: never blocking fails 1 test; blocking without an earlier log fails 20 |
| The response 148 rename | done in dce63510 | none |
| Note 1: one row per date with a ledger row | accepted | Story table and criterion 2 say so |
| Note 2: the Status line | accepted | Updated |
| Note 3: `market publish --local` needs Drive | accepted | Added to Known limits |
| Deviation 1: the Drive path | accepted by the judge | The Scope line now says `paper/journal/<book>/account/` |
| Merge-step additions (a) nine lines, (b) nothing else tracked | noted | For the orchestrator at merge |

## ChatGPT review 115 (PARTIAL, one required fix; the orchestrator's brief)

**Checked in the code first (strong evidence):** `daily_steps.review_exits` catches one book's failure, including a
Drive 503 (`PrivateFilesUnavailable`), logs `{reviewed: False, error}` and still completes the step. The old guard only
checked that `exits` was in the log. The finding is real.

**What changed:**
- `DailyRun._unreviewed(day)` returns each book whose exits the last session did not review, with why:
  - no log while an earlier one exists: every book;
  - a log without `exits`: every book;
  - an `exits` step: each book with an `error` or a non-empty `waiting`.
- `DeskSteps.fill` takes that map. A blocked book records "not filled" with the reason, one alert names every
  blocked book, and the other books fill.

**Per book, not the whole desk:** the run log keeps each book's exit result, and the fill step already works book by
book. Books never share money or positions (E1 firewall), so one book's unreviewed exits say nothing about another
book's risk. A stop before the exits step, or before any step, still blocks every book, because then no book's
exits were reviewed.

**The orchestrator's refinement (`waiting == []` blocks nothing):** I checked it against `ExitDesk.due_exits` and
`_review_book` and agree with it. The doubt I found, reasoning only: with no snapshot, an open trade's price-based
exits (stop, profit) are not checked that day, and `waiting` lists only exits due without prices (time rules or
ordered exits). I still keep the rule:
- the next session's fills need a valid snapshot (`NO_SNAPSHOT`), and its exits review that same snapshot in the same
  run;
- blocking on every no-snapshot day with any open trade would stop entries on every data gap, a cost with no
  matching risk once the next snapshot is valid.

If the owner wants price exits re-checked before any new entry, that is an order change in E3 (exits before fills),
a design decision and not part of this fix.

**Tests** (`tests/timetable/test_fills_to_drive.py`):
- Book 1's exit review fails on a Drive 503 on 13 Oct. On 14 Oct Book 1 opens nothing and Book 2 opens b1. One
  alert names Book 1 only. The exits run, and Book 1 is reviewed again.
- 16 Oct has no snapshot. Book 1's t1 time exit is due and held up, so on 19 Oct Book 1 opens nothing (t5 not filled)
  while Book 2 (`waiting == []`) opens b5.
- Review 115's non-blocking item, added because it is small: Book 1's fill reaches Drive and the commit of its
  totals is rejected. A fresh container (no unpushed totals, no marker) reruns, fills nothing twice, commits the
  totals, and they equal `daily_totals` of the Drive account.
- Plants:
  - an error ignored (1 test fails);
  - a held-up exit ignored (1 fails);
  - any `reviewed: False` blocking (1 fails: the no-snapshot day with nothing due);
  - a whole-desk block (2 fail).
- Kept: the first-session exception. No distributed lock: a single routine is a known limit.
