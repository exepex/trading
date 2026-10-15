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

   **Known channels:** scoreboard B and `equity_history`; a refused entry's net-at-the-touch reason and
   `shortfall_rs` (a sum over at least two legs, not one contract). The touch size in E4's no-fill reason is removed
   (decision 42, below). All of these go to the owner with the question of moving
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
| Found in this round, not changed: a refused entry's net-at-the-touch reason and `shortfall_rs` | `fno/desk/entries.py:48-51` | reasoning only: a sum over at least two legs; owner question with the others |
