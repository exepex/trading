# Response 118: E2b, only derived quote figures in the committed packs and desk records

Builder claims for the judge. Lane 1. Branch `story/e2b-derived-packs`. Story text: `docs/stories/E-paper-desk.md`,
section "E2b". Its first version passed judge 118 addendum 1 at `de28300`. The text has changed since, by the
orchestrator's decisions of 15 Oct (response 113), so the judge re-checks it with the code:
- exception 3;
- the known channels;
- the kept mids;
- one spot per recorded chain;
- the guard on staged files.

**Merge order:** after A4b (criterion 3 reads the 15:15 quote file from Drive), then ChatGPT (quality rule 9), then
the merge. Nothing here is live, posts anything, or places an order.

## Answer to judge 118 addendum 2 (FAIL on `b76be4f`: 2 should-fix, 3 minor)

| Item | Done | Where (code; tests; broken-code proof) |
|---|---|---|
| **SF1** A refusal during an account write left the fills applied but not committed, and escaped the steps' handling | **Accepted, design fixed** | `GitAccountSync.write` checks the whole index before `apply` (`_require_no_raw_quote_staged`, `fno/desk/git_sync.py`), so a refusal applies nothing. It is raised through `_stop` as `CheckoutNotDedicated`, an `AccountWriteRefused`, with one alert. `Git.staged()` is now the one source of "what the next commit carries" |
| | | Tests: `tests/timetable/test_git_sync.py` (`test_a_raw_quote_file_staged_earlier_refuses_the_write_before_anything_is_applied`, for a fill and an exit write: journal byte-identical, nothing committed, one alert); `tests/timetable/test_raw_quote_refusal_run.py` (the daily run: "not filled: the account write was refused ... before any fill was applied", book 2 still fills, the exit step still runs) |
| | | Mutations caught: the pre-apply check removed; the refusal raised as a plain `RawQuoteCommitRefused` |
| **SF2** M16 (narrow except) and M18 (one-sided quote) survived | **Accepted, tests added** | `tests/scorecard/test_touches.py`, through the real `RecordedExecutionSnapshots`: a corrupt sidecar (JSONDecodeError) gives one "touch unknown"; a one-sided quote gives one "touch unknown" while the other fill is still averaged (65 units, 0.5); a corrupt snapshot among good ones leaves the good ones averaged. M16 and M18 are now caught |
| Minor 1: "two" vs three exceptions | **Fixed** | story text |
| Minor 2: a chain with no rows had no `spot:` item | **Fixed** (a few lines) | The chain list is the sidecar's `expiries`, with the rows as the fallback for older sidecars such as the golden fixtures. A chain with no rows gets an item with no value at the capture's first request (`fno/desk/snapshot_inputs.py` `_spots`; `tests/packs/test_derived_pack.py::test_a_chain_the_sidecar_names_without_rows_gets_an_item_with_no_value`) |
| Minor 3: the guard is path-based; a staged deletion is refused | **Confirmed and stated** | Kept. An account commit should never carry a deletion of a raw quote file. A4b removes the old 14 Oct CSV in its own commit, made by its builder with `git rm` at its merge, never through `GitAccountSync` or the desk's `Git`. The story now says the guard is path-based because the desk's writers never copy or rename a raw file |
| For the merge check after A4b | **Planned** | `fno/scorecard/wiring.py` must read snapshots through A4b's hash-checked store, which is `build_quote_store()` once A4b is merged. Today it passes `root / QUOTES_FOLDER...` to `build_execution_snapshots(folder)`. After A4b, `build_execution_snapshots` builds on A4b's `build_quote_store(folder)`, so the store is swapped there with no change in E2b's wiring. I will re-check at the merge that the scorecard path reaches the Drive store, and keep one version of `execution_capture.py` (both stories commit only what the repository holds) |

## Decisions this story rests on

- **Option B (orchestrator for the owner).** Mid plus spread % gives bid and ask back exactly: 648 of 648 cases on
  0.05 ticks (strong evidence). So the committed pack holds no per-contract quote figure.
- **Fills.** The `quote_bid` and `quote_ask` columns are dropped. E6 reads the touch from the hash-checked snapshot.
  The fill price stays.
- **A commit guard** refuses raw Groww quote files.
- **Exceptions and channels found by the builder's reviews**, decided by the orchestrator:
  - exception 3 stands until a separate E4 story removes it;
  - scoreboard B's and `equity_history`'s marks are a known channel;
  - the 14:55 mids are kept;
  - C3 requires one spot per recorded chain.

## Claims

| # | Criterion | Code | Tests | Evidence |
|---|---|---|---|---|
| 1 | Pack schema 2: no `option:` item; no bid, ask or size field; no number equal to any row's bid or ask; `spot:<expiry>` per chain (known with the chain's first row; two spots refused; no spot kept as an item with no value); `quote_counts`; VIX, futures, hashes | `fno/desk/snapshot_inputs.py:36`, `:53`, `:69`; `fno/desk/common_pack.py:23` | `tests/packs/test_derived_pack.py:33`, `:44`, `:64`, `:77`, `:99`; `tests/packs/test_common_pack.py` (updated) | strong (5 mutations caught) |
| 2 | C3 gives the same results from `spot:` items. One spot per recorded chain: a blank or refused chain is named and fails | `fno/checks/market_checks.py:36-48` | `tests/checks/test_data_checks.py` (2% and 0.2% boundaries, through the updated `tests/checks/builders.py`), `:155` | strong (3 mutations caught) |
| 3 | No `quote_bid`/`quote_ask`. Only the three stated exceptions reveal both sides. E6's half-spread comes from the hash-checked snapshot and equals the old figure. "Touch unknown" is counted, printed and never zero. Settlements are left out | `fno/desk/records.py:31`; `fno/scorecard/touches.py:25`, `:40`, `:53`; `fno/scorecard/execution_costs.py`; `fno/scorecard/report.py:35`; `fno/scorecard/wiring.py` | `tests/desk/test_public_fills.py:43-121` (the equivalence test at `:121` reads E4's own rows through the real `RecordedExecutionSnapshots`); `tests/scorecard/test_touches.py:27-52` | strong (7 mutations caught). The equivalence on the real 14 Oct snapshot is also from review 1: old 6.164266304347825 = new, over 368 rows |
| 4 | The 15:15 capture commits its record and the sidecar, never the CSV; the record keeps both hashes | `fno/desk/execution_capture.py:49-52` | `tests/timetable/test_capture_commits.py:31` | strong (1 mutation caught) |
| 5 | The guard runs before git on the given paths (resolved: `.CSV`, `../` and symlinks caught), then on every staged file after the add, in every `Git.commit_paths` (the daily run's committer and the account sync). On a refusal the add is undone and nothing is committed | `fno/desk/commit_guard.py:21-32`; `fno/desk/git_sync.py:62-75`, `:108` | `tests/timetable/test_capture_commits.py:59`, `:64`, `:78`, `:82`, `:114`, `:122`, `:132` | strong (5 mutations caught) |
| 6 | E2's own criteria still hold on schema 2 | unchanged | `tests/packs/*` (all pass) | strong |
| 7 | No reader in `fno/` looks up an `option:` item; the AI books' pack reader is unchanged | — | `tests/packs/test_derived_pack.py:90` | strong |

**Mutations:** 22 planted, one at a time, each restored, and all 22 caught by the affected suites.
- One survived at first: a wrong valid count. It is caught now by `test_the_valid_count_counts_only_valid_rows`.
- One mutation was malformed in my first script; the corrected version is caught.

## Requirements map (quality rule 2)

The full map is in the story text. Summary:

| Requirement | Status |
|---|---|
| "8 A" packs: derived only | covered (criteria 1, 2) |
| "8 A" what E3 commits | covered (criteria 4, 5) |
| "8 A" AI books read the derived pack | covered (criterion 7: they read the derived forecast v2 pack) |
| "8 A" before the desk goes live | covered (criterion 5) |
| "6 A" Drive storage | out: A4b, merged first |
| E2 criteria 1-5 | criterion 6 |
| E4 criterion 1 (fill at ask or bid with the hash) | kept |
| E4 criterion 2 (unwind) | kept; exception 1 |
| E6 half-spread | criterion 3 |
| C3 2% and 0.2% rules, plus one spot per chain | criterion 2 |
| Other committed figures that could reveal a quote | stated: exceptions 1-3, known channels, kept mids |

## Self-review (quality rule 3): two independent agents on `92cf696`, then my fixes

| Finding | Severity | Response |
|---|---|---|
| R1 B1: the guard missed folders and pathspecs (git adds the CSVs inside) | blocking | **accepted, fixed**: the guard also checks every staged file after the add (tested on a real repository) |
| R1 B2 and R2-3: `git commit` takes the whole index, so a quote file staged earlier was committed | blocking | **accepted, fixed**, same change. Another writer's staged file is left staged, so later commits keep refusing (fails closed) |
| R1 m1 and R2-4: a corrupt snapshot crashed the scorecard | minor | **fixed**: one "touch unknown", never a crash |
| R1 m2: the scorecard ignored its `root` for quotes | minor | **fixed** |
| R1 m3: the quotes-folder path was defined twice | minor | **fixed**: one constant |
| R1 m4: no equivalence test through the real reader | minor | **added** |
| R1 m5: a two-spot chain retries until 15:10 | minor | **kept**: the outcome is right (no pack) |
| R2-1: a third way to reveal both sides (protection unverified at the opening snapshot closes there) | high | **accepted, pinned by a test**, listed as exception 3. A separate E4 story will refuse such entries (orchestrator) |
| R2-2: scoreboard B's (and `equity_history`'s) marks at the fill's snapshot give a bid back | high | **accepted as a known channel** (orchestrator): owner question, together with moving fills to Drive; no S2 change |
| R2-5: per-contract 14:55 mids in D3 inputs and C4 evidence | medium | **kept by decision**; stated in the story |
| R2-6: a chain without a spot skipped C3's agreement check (existed before E2b) | low | **fixed** (orchestrator's decision 4) |
| R2-7: the 3 pm routine still commits raw CSVs until A4b | context | out: A4b, merged first |
| R2 weak tests: the capture test read paths by order; the report test checked only 0; the opening-snapshot test passed for the wrong reason | — | **fixed**: by name; a nonzero count; one test for the time rule and one pinning exception 3 |

## Real output (quality rule 6)

These are the quote items of a schema-2 pack, made by the committed `SnapshotInput` from the committed 14 Oct
snapshot (`nifty_20261014_145500`), printed in a dry run with no pack written:

```
{"available_at": "2026-10-14T14:55:25.462843+05:30", "name": "spot:2026-10-27", "value": 22620.0, ...}
{"available_at": "2026-10-14T14:56:36.726874+05:30", "name": "spot:2026-11-23", "value": 22621.15, ...}
{"available_at": "2026-10-14T14:57:44.897739+05:30", "name": "quote_counts", "value": {"complete": true, "expected_contracts": 184, "recorded_contracts": 184, "valid_contracts": 184}, ...}
{"name": "india_vix", "value": 14.74, ...}
{"name": "future:2026-10-27", "value": {"last": 22650.0, "volume": 3118570}, ...}
{"name": "future:2026-11-23", "value": {"last": 22760.0, "volume": 312910}, ...}
{"name": "future:2026-12-29", "value": {"last": 22910.0, "volume": 106535}, ...}
provenance: {"csv_sha256": "9d9de08b...", "meta_sha256": "9bef6528...", "snapshot_id": "nifty_20261014_145500"}
```

That is 7 items in place of the 184 per-contract quote items before, and nothing per contract.

## Known limits (said plainly)

1. **Three exceptions in the fill rows:**
   - an unwound entry;
   - two accounts on opposite sides of one contract at one snapshot;
   - protection unverified at the opening snapshot.

   **Known channels:** scoreboard B and `equity_history`. The touch size in E4's no-fill reason (decision 42) and a
   refused entry's net-at-the-touch reason and `shortfall_rs` column (decision 45) are removed (below). All of these go to the owner with the question of moving
   paper fills, marks and scoreboard B to Drive.
2. Before A4b merges, the 15:15 quote CSV is not committed and lives only in the run's local folder, so E6 shows
   "touch unknown" on a fresh checkout. E2b merges after A4b for this reason.
3. A lock against two writers is not part of this story. The guard leaves another writer's staged file staged, so
   every later desk commit is refused until someone fixes the index (fail closed, by choice).
4. Hard links into the quote folder are not detected; a symlink is.

## What the judge should test hardest

- Scan a built pack for raw values, using a fixture with distinct prices.
- Commit a folder holding a quote CSV, and a CSV staged earlier, through the real `Git`.
- Recompute one half-spread from a snapshot by hand.
- Exception 3's test, and whether any other outcome reveals both sides.
- C3 with a blank chain, and with a spot refused at the cutoff.

## Decision 42: no touch size in the public reason

| What | Where | Evidence |
|---|---|---|
| E4's no-fill reason no longer carries the size shown at the touch: "not enough size at the touch for M units" | `fno/desk/pricing.py:19`, `:63` | strong |
| Test: the reason and the committed `desk_events.csv` row carry no size (size 64 against 65 units) | `tests/desk/test_entries.py:118-122` | strong: putting `size {size}` back fails it ("'64' is contained here") |
| Pending-exit reasons reuse the same leg reason, so they lose the size too | `fno/desk/exits.py:137` | strong (same text) |
| Found in this round: a refused entry's net-at-the-touch reason and `shortfall_rs` | removed by decision 45 (below) | strong |

## Answer to judge 118 addendum 3 (decision 44)

| Item | Accepted? | Fix | Tests | Evidence |
|---|---|---|---|---|
| New should-fix 1: the run's log commit hit the staged raw file first, with no alert | **accepted**. Reproduced with the real `GitCommitter` in a run: with the new catch removed (M1), the refusal escapes `DailyRun.run`. My earlier test used a fake committer, so it missed this | The committer port now raises one error, `CommitFailed` (`fno/desk/daily_ports.py`). `GitCommitter` turns any refusal or git failure into it (`fno/desk/git_sync.py:112-116`). `DailyRun._step` is the one place it is handled, whether it comes from the step's own commit or from a commit inside the step (`fno/desk/daily_run.py:83-94`): one alert through the same sender `_stop` uses (`steps.alerts`, the same object in the wiring), no later step, then `RunStopped`. `fno desk run` prints that line and returns 1 (`fno/books/book1_cli.py:39-43`) | `tests/timetable/test_commit_failure_run.py`, all with the real `GitCommitter` in a run unless noted: a staged raw file (one alert naming it; HEAD and origin unchanged; the run's own add undone); an unreachable origin; a push rejected three times (a pre-receive hook); a commit failing inside the snapshot step (fake committer); the command's exit code 1 and output line | strong. Plants caught: catch removed (M1); committer not wrapping (M2); no alert (M3); CLI not catching (M5); only the step's own commit caught (M6) |
| The judge's older case: a push rejected three times ends unalerted | covered at the same catch point | Its alert says "the commit stays local, unpushed". That commit then refuses every later account write until it is fixed by hand (fail closed, unchanged) | the rejected-push test above | strong |
| Minor 1, N4: `staged()` ignoring deletions survived | **accepted** | no code change; the claim now has its test | `tests/timetable/test_capture_commits.py:138` | strong: the N4 plant (`--diff-filter=d`) fails it |
| Decision 42 (the touch size in E4's reason) | done | commit 290a8a0, in this push | see "Decision 42" above | strong |

**Out, stated:** `fno desk book1`, Book 1's decision command, still ends in a traceback with no alert when its own
commit fails (`fno/books/book1.py:74`), as it did before E2b. That command is not the daily run, so it is listed as a
follow-up in the story's Out list.

## Decision 45: no entry figures in a refused entry's record

My earlier "a sum over at least two legs" was wrong as a defence: the playbook's STR1 structures include LC and LP
(`fno/constants.py:97`), which have a single leg. Accepted (strong):

| What | Where | Evidence |
|---|---|---|
| A refused entry's reason is the fixed text "entry_worse_than_approved: entry price at the touch worse than the approved limit"; no net, limit or shortfall figure | `fno/desk/entries.py` (`WORSE_THAN_APPROVED`, `worse_than_approved`) | strong |
| Schema change: `desk_events.csv` loses `shortfall_rs`; `EntryResult` and `DeskEvent` lose the field | `fno/desk/records.py` (`EVENT_COLUMNS`), `fno/desk/entries.py` | strong: nothing in `fno/` read it (grep), and no `desk_events.csv` is committed (`git ls-files`) |
| Tests: for a single-leg long call and for the iron fly, the reason is the fixed text with no digit, the row has exactly the new columns, and no column but names, day and hashes holds a digit | `tests/desk/test_entry_limit.py` (`assert_no_quote_figure` and its two tests) | strong: plants caught by both tests: the limit back in the reason (D1), the column back (D2), a figure in another column (D3) |
| The limit's own logic is still tested through outcomes: equal or better fills, a paisa worse refuses, the limit scales with lots (2 lots at a Rs 3 half-spread are refused though they beat a 1-lot limit) | `tests/desk/test_entry_limit.py` | strong |

**Out:** a Drive-only record of the figures for research is not built (nothing needs it today).

## Answer to judge 118 addendum 4 (decisions 47 and 48)

| Item | Accepted? | Fix | Tests | Evidence |
|---|---|---|---|---|
| Should-fix 1: after a stop, the rerun skipped the failed step and never committed its files | **accepted**. The gap is wider than the step's own commit: a commit that failed inside a step (D6's registry row, the 15:15 capture record) also left files no later run would commit. A rerun of the decisions step after the deadline would also have made every book late | `fno/desk/pending_commit.py`: `PendingCommitter` wraps the run's committer (wiring: `fno/desk/daily_wiring.py`). Before each commit it writes a git-ignored marker with the paths, their SHA-256 and the message, and removes it on success. `DailyRun.run` first calls `recover()` inside the same single handler: it commits the files exactly as recorded, or stops with an alert naming the changed file. No step is re-run | `tests/timetable/test_rerun_after_stop.py`, real `GitCommitter` and a bare origin: a stop at the pack (committed byte-identical; 1 build, 1 capture, 4 fills, a third run changes nothing); a stop at the decisions (1 collection; the no-decision file byte-identical; book 1 still on time); a tampered pending file (alert, nothing committed, no rebuild) | strong. Plants caught: recover does nothing (P1), no hash check (P2), run never recovers (P3), marker removed before the commit (P4) |
| The judge's question 1: a commit stuck local after a rejected push | **partly disagreed, with evidence**. The judge said the next successful commit pushes it. It did not when that commit had nothing new to commit: `commit_paths` returned False, so no push ran. That is exactly the recovery of an already-committed step | `GitCommitter` also pushes when `HEAD` is ahead of `origin/<branch>` (`fno/desk/git_sync.py`) | `test_a_push_rejected_every_time_is_pushed_by_the_rerun`: the exits step's push is rejected by a hook; the rerun's recovery pushes it | strong: plant P5 (push only a new commit) survived my first version of the test, so the test now rejects the last step's push |
| Minor 1: the alert text | **accepted** | "exits not reviewed today" for a stop before `exits`; "Fix: remove the cause, then rerun `fno desk run` (...)"; "; the rerun pushes the local commit" for a rejected push (`fno/desk/daily_run.py`) | the stop tests above | strong (plants P6, P7 caught) |
| Minor 2, decision 48: "net Rs X if closed now" in `exit_ordered` reasons | **accepted** | fixed texts `TARGET_REACHED` and `STOP_REACHED` (`fno/desk/exit_rules.py`) | `tests/desk/test_exits.py` exit-rule test: the `exit_ordered` reason equals the fixed text and has no digit | strong (plant D48 caught) |
| Minor 3: Book 1's command | noted by the orchestrator as a follow-up | none | none | none |

**Limits, said plainly:**
- A commit that failed inside a step (the capture's) means that step is not recorded, so the rerun runs it again. The
  15:15 capture then takes a second snapshot: both are committed, the fills read the latest, and no fill had been made
  before. Making the capture step itself resumable would change E3, so it is left as stated.
- The marker is local to one checkout. A rerun in a fresh container has no marker; the failed step's files are not in
  that checkout either, so nothing is committed by mistake. That run starts the day over from what was committed.

## Answer to judge 118 addendum 6 (decision 51)

| Item | Accepted? | Fix | Tests | Evidence |
|---|---|---|---|---|
| Should-fix 1: a push published files the guard never checked | **accepted** (the judge's probe put a raw file on origin) | (a) Before every push attempt, `RawQuoteGuard` checks `Git.unpushed_files()`, every file the push would change on origin. (b) Before the pull, `GitCommitter._refuse_stray` refuses any unpushed non-merge commit except the run's own, naming each commit's message and files. Both go through `CommitFailed`, so the one handler sends one alert. Account writes and the run share `Git.unpushed()`: account writes refuse any unpushed commit (unchanged), the run allows only its own (`fno/desk/git_sync.py`) | `tests/timetable/test_push_guard.py`, real git and a bare origin: a stray raw-file commit refused, origin unchanged, the alert names the file; the same with (b) switched off, so (a) alone refuses it; a stray commit without quotes; a stray copying the run's message but touching other files; the run's own stuck commit pushed after origin moved on, through a merge | strong. Plants caught: R1 (no pre-push guard), R2 (no stray refusal), R3 (own commit never recognised), R4 (merges counted as strays), R5 (own commit's files not checked; it survived until I added the copied-message test), R6 (recovery passes no own commit) |
| How (b) tells the run's own commit apart | | The pending marker: `recover()` passes its message as `own_unpushed`. A commit counts as the run's own only if its subject equals that message AND its files are within the marker's files | the copied-message test and the stuck-commit test | strong |
| A merge left by a retry's pull | found by me while building (b) | When origin moved on, the retry's pull creates a merge commit, and (b) would have refused the run's own recovery. Merges are skipped in (b): the commits a merge brings in are checked one by one, and its files by (a) | the stuck-commit test (a rerun with pushes still rejected leaves one merge unpushed; the next rerun pushes) | strong (R4) |
| Minor 1: the fresh-checkout rule | **accepted** | stated in story criterion 5, with the pre-A4b report gap | none (text) | the judge's reasoning, checked against `entries.py` and `daily_steps.py` |
| Minor 2: the capture window | **accepted** | "inside the execution window (after `fills_by`, C3 refuses it ...)" | none (text) | the judge's reading of `snapshot_checks.py` |
| Minor 3: plant Q5, `STILL_PENDING` | **accepted: removed** | Unreachable: `DailyRun.run` calls `recover()` before any step, and `PendingCommitter` is built only in the daily run's wiring and used only inside its steps. A failed commit stops the run. The docstring states that order | none | reasoning plus `grep`: the only users are `daily_wiring.py` and the tests |

**Changed test text:** the unreachable-origin test now expects "git fetch -q failed". The stray check fetches before
the pull, so the same cause is reported at the fetch.
