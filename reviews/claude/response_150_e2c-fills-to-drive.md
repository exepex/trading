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
