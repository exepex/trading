# Response 149: story A17d, FBIL's USD/INR table moves to Drive (build claims)

Branch `story/a17d-fbil-drive`. Story text: judge 162 PASS (1c6700f4); new order: judge 162 addendum 1. The owner's
decision is dated 15 Oct 2026 (`docs/DESK_DECISIONS.md`). Rule 9 does not apply: no money path. Evidence labels:
**strong** means a test or a real run.

## What changed

| Commit | Change |
|---|---|
| 7d2e647f (code) | `FbilUsdInrSource.private = True`. `OVERLAP_FIELDS = ("date", "kind")`: a public row never holds a rate. Fixtures use made-up FBIL rates (`test_sources.py`, `test_as_of_checks.py`). New test `test_fbil_is_private_and_its_table_and_revisions_go_to_drive_never_to_the_repository`. The committed-files test lists `usdinr_fbil` as private. Docs: global-cues README, A17/A17b lines marked superseded, the docstrings, `fno/storage/README.md` |
| cd29c930 (removal) | `research/data/global-cues/usdinr_fbil.csv` removed. FBIL's 171 rows leave `checks/gaps.csv` (now in Drive's `usdinr_fbil/checks`). The `overlap_usdinr.csv` header is now `date,kind`. Both check files were rewritten by `global-cues check` code, not by hand |

The copy log `research/data/manifests/global-cues/usdinr_fbil.csv` stays: paths, URLs, SHA-256 values and sizes.

## Migration (rule 6, real run, 15 Oct 2026; strong)

The order is judge 162 addendum 1: adopt and compare before the merge, then the removal on the branch.

1. Adopt the full-history copy, from the branch code:
   `global-cues adopt --cue usdinr_fbil --from 2018-07-10 --to 2026-10-15 --copy fbil/.../061631_reference-rates_20180710_20261015.json`
   ```
usdinr_fbil: 1981 dates added, 0 revisions logged, last 2026-10-07
USD/INR RBI against FBIL: 1086 dates compared, no difference
   ```
   Exit 0.
2. Adopt the top-up copy, `.../061749_reference-rates_20260906_20261015.json` (`--from 2026-09-06`):
   ```
usdinr_fbil: 0 dates added, 0 revisions logged, last 2026-10-07
   ```
   Exit 0.
3. Comparison. This is a one-off script that reads the file with `git show origin/main:research/data/global-cues/usdinr_fbil.csv`;
   its last change on origin/main is **d359fc3e6e386e4037dca6df468540212075c617**. It prints counts and SHA-256 values
   only.
   - On every column, as written: **not equal**. Values, `source_sha256`, dates and `provenance` match on all 1,981
     rows. `first_seen_at` differs on all 1,981 rows: the fill stamped `06:16:31.010317`, while adopt stamps the
     copy's path time, `06:16:31`. The path carries whole seconds; this is the same rule as the US-close adoption.
   - With `first_seen_at` cut to the second on both sides:
     ```
repository rows 1981 SHA-256 3dc8f54da2491feab79efd44a51649f97cb5d7fb6083c8227e60b4fcec67ca2b
Drive rows      1981 SHA-256 3dc8f54da2491feab79efd44a51649f97cb5d7fb6083c8227e60b4fcec67ca2b
EQUAL with first_seen_at to the second
largest first_seen_at gap (s): 0.010317
     ```

**A deviation from criterion 5 ("equal SHA-256 values"), stated plainly.** The Drive table's `first_seen_at` is
10.3 ms earlier than the old file's on every row. This is within the copy's own fetch second; no `provenance` label
changes (all `backfilled`, values first usable on later sessions). I accepted it rather than write a table by hand,
for these reasons:
- adopt is A17's own path, with Drive's creation-time check;
- the alternative is a one-off row writer, a new path for one use;
- by the owner's "keep the design simple", a 10 ms difference changes no decision.

The judge may rule otherwise.

## Criteria

| # | Claim | Evidence |
|---|---|---|
| 1 | FBIL is private. Its rows and revisions go to Drive's `derived/global-cues/usdinr_fbil/`, none to the repository. `build_tables(include_private=False)` has no `usdinr_fbil` | new test over a local-folder Drive (rows, plus a revision). Real: the adopt above. **Strong** |
| 2 | The overlap check names dates, never rates | `test_rbi_and_fbil_differences_are_listed_on_the_dates_both_publish_without_a_rate`; the committed header `date,kind`. **Strong** |
| 3 | A committed FBIL table, revision row or gap row fails CI | planted, one at a time: `usdinr_fbil.csv`, a `revisions.csv` row and a `gaps.csv` row each fail `test_no_private_cue_has_a_table_or_values_in_the_repository`. **Strong** |
| 4 | No test fixture holds a real FBIL rate | the two fixtures now use made-up rates (labelled). **Strong** |
| 5 | Real run | above, with the `first_seen_at` deviation stated |
| 6 | Gates | see the message to the orchestrator (full suite, ruff, imports) |

**Mutations, all caught:**
- private flag off;
- overlap rows carry rates;
- overlap columns carry rates.

**Before the merge (judge 162 addendum 1):** `git log origin/main -- research/data/global-cues/usdinr_fbil.csv` must
still show d359fc3e as the last change. If it shows a later commit, I adopt the newer copy and compare again.

**After the merge:** the next `global-cues fill` (none is scheduled) writes FBIL's new rows to Drive only.
