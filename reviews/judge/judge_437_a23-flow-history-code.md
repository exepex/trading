# Judge 437: A23 FII/DII flow history, code (story/a23-flow-history @ 446a18a9), for response 305

Judge F (independent). Story `docs/stories/A23-flow-history.md` (text PASS, judge 429 add. 1-2), claims
`reviews/claude/response_305_a23-code.md`. Lane 1 (NSE, NSDL, Drive, a workflow). Labels: **strong**, **some**,
**reasoning only**.

## Verdict: PASS for the code, with a merge condition: the back-fill evidence comes back to me before the merge

## Gates (mine, at 446a18a9)

| Gate | Result |
|---|---|
| pytest `-n auto` | **2 failed, 9068 passed, 17 xfailed** |
| `tests/test_fingerprints.py::test_every_raw_dataset_has_a_committed_manifest_in_one_folder` | expected: the two new datasets have no manifest rows until the back-fill (the builder's stated sequencing, no exemption) |
| `tests/playbook/test_activation_gate.py::...[research-STR1b-2]` | **not A23's: a flake.** It passes alone 2 of 2 on A23's head and 2 of 2 on main; it failed only under the parallel run, where that file took 34.9 s. Reported to the orchestrator |
| ruff, ruff format (1677), `check_imports.py`, record scan (7363) | clean |

## Planted mutations (mine, in a separate copy; `tests/flow_history`, 60 tests)

| # | Plant | Caught |
|---|---|---|
| 1 | rewritten boundary `<` → `<=` (written exactly at 09:15:00 would count as rewritten) | yes |
| 2 | a missing `Last-Modified` not flagged as rewritten | yes (2) |
| 3 | NSDL pace 10 s → 9 s | yes (2) |
| 4 | NSDL tries per month 2 → 3 | yes (2) |

## Criteria (code read, tests and plants)

| # | Status |
|---|---|
| 1 Readers: 2019 and 2026 FII-statistics layouts (xlrd 2.0.2, pinned), per-index rows checked against the group within 2 contracts (A8's measure; one real 1-contract miss on 12 Jan 2026); participant volume through A8's reader | MET |
| 2 Point in time: next session; holiday and muhurat stepped over; written at 09:15:00 not rewritten, 09:15:01 rewritten; unknown flagged | MET (plants 1, 2) |
| 2b Rewritten share | pending, from the back-fill |
| 3 Back-fill: A9's librarian, resumable, manifest rows | pending, from the back-fill |
| 4 Daily: `flow-history.yml` 21:30 and 07:15 IST every day, on capture-watch, fallback step `if: ${{ failure() }}`, quiet when each step spoke (judge 359's pattern); O8 rows due 09:00 the next day | MET |
| 5 No value in the repository: manifests, receipts and write-time logs only | MET |
| 6 Real sample | pending, from the back-fill |
| 7 NSDL: readers on the 2019 and 2026 layouts, at least 10 s apart, one retry, resume, no value in lines, alerts or receipts; only the flow-history package names the NSDL table; requests identify as `RESEARCH_USER_AGENT` (an honest identity, row 281 kept rule 2) | MET (plants 3, 4) |

Choices beyond the text, all accepted:
- the sweep's baseline, with an unanswered write time waiting for the next run (never "unknown" for ever);
- O8's 09:00 next-calendar-day deadline, stricter than the text;
- NSDL totals and derivatives not kept;
- the `flows` command name.

Both datasets join `DATED_SOURCES`, so A7's coverage check, A11's revision sweep (the question from my judge 429 add.
1) and the NSE retry policy cover them.

## Merge condition

After the back-fills, before merging, send me:
- the commit with the manifest rows and write-time logs;
- the claims addendum with criterion 2b (rewritten count and share per dataset), criterion 3 (counts, first and last
  sessions, coverage gaps) and criterion 6 (the first back-filled month and the first daily run);
- a full suite where the fingerprint test passes.
I check that addendum, then the merge may go.

## For the owner (not A23's)

P8's dashboard already shows NSDL's latest daily FPI figure. Under row 281 that is fine only if the dashboard is
private ("never in a public place"). If anyone else can see it, the owner decides.

## Addendum 1: the back-fill's refused files, fix at story/a23-volume-fix @ cff14b5e (on the A23 branch)

**Verdict: PASS for the fix. The builder may re-run `data-librarian participant-volume` for 15 Sep 2021, 14 Oct
2022 and 18 Oct 2022 on cff14b5e.** Judge 437's merge condition stands: the back-fill manifest commit, the claims
addendum and a full suite with the fingerprint test green, all sent for my check.

The builder's report so far [as reported, not yet checked by me]:
- NSDL: 93 months, 0 failed, no real figure found in the receipts commit or the run log.
- Participant volume: 1,931 of 1,935 sessions archived. The content check refused 4 files; the builder found the root
  cause of each.

| Item | Change | My check | Result |
|---|---|---|---|
| Stray unnamed sum rows under TOTAL on 3 days | `read_participant_volume` drops body rows whose first cell is empty, then runs A8's reader unchanged; the content check uses it | Plant: unnamed rows kept: 1 failed. Plant: a named row ("Client") dropped: 7 failed. So the five named rows must still pass every identity, and a real participant row cannot be lost silently [strong] | **Accepted** |
| 18 Mar 2019, fractional contract counts (sixths) | a sourced row in `exceptions.csv`; not archived, not in the table | read. Refusing a file that gives fractional contracts is right; guessing a rounding would invent data | **Accepted, with a minor** |

Gates on cff14b5e: **9073 passed, 1 failed**: `test_every_raw_dataset_has_a_committed_manifest_in_one_folder`, the
expected failure until the back-fill's manifests are committed (judge 437). Ruff, ruff format (1678),
`check_imports.py` and the record scan (7551) are clean.

**Minor.**
- `build_file_exceptions` says the file lists sessions NSE "never published a file for", but 18 Mar 2019's file
  exists and is refused for its content. Say so in the reason (it does), and either widen that docstring or give
  refused-content days their own kind, so a coverage reader does not count it as "NSE published nothing".
- Removing the row fails no test (plant 3: 66 passed). Add a test that the participant-volume coverage expects that
  day excused.
