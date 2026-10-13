# Judge 66: P8 and P10 contract 2.5 blocks (session, indices, fno_events, flows) and two design fixes

Date: 14 Oct 2026 (about 03:40 IST). Code: trading bf1598c/5428068 and aaac24c/8629df0. Claims:
`reviews/claude/response_66_2026-10-13-p7-p8-p9-publishing.md` (last two addenda). Contract pinned to omenix-dashboard
6cc6b7a (2.5.0).

## Verdict: PASS on items 1-3 (two minor notes); item 4 (the real 07:10 IST publish) pending; main's CI is red for a reason outside this story

## 1. The four pages against 2.5

`tests/market_read_models`: 137 pass (my run at 8629df0), including the six in `test_frame_and_flows_blocks.py`. These
validate all four pages as served against the pinned 2.5 schemas, with `fno_events` equal to the contract's calendar
example field by field for its first four rows.

**Flows point in time, my plants:**

| Plant | Result |
|---|---|
| A later session's values read (`if covered <= day` made always true) | **caught** (1 failed) |
| The fetch window widened to copies taken up to two sessions later | **not caught** (137 passed) |

The second plant does not change today's values. A copy fetched later normally covers a later session and is
filtered out. So it is a test gap on the window's upper bound, not a live leak.

**Claims vs reality on the window (minor, reasoning only).** The builder says copies "fetched up to the next session"
are read, to catch "the morning copy". But `flows-download.yml` fetches once a day at 21:10 IST, after the 07:10 IST
publish. So when session D is published at 07:10 on the next session N, the copy dated N does not exist yet. The live
run reads only copies up to D.

A later **re-run** of D would also read N's 21:10 copy. If NSE had not yet replaced D's figures by then, that copy
could hold D's values as seen after the publish moment. A re-run could then differ from the live run. For strict point
in time, bound the window by the publish moment (fetched on or before D at 21:10), or record which copy each
publication used. Low impact; one test for the bound.

## 2. Muhurat (8 Nov): MET, with the known contract gap

`SessionBlock.pages` returns no page when the next session is muhurat, and every other page publishes (test with the
real 8 Nov 2026 calendar row). My plant, making the block build anyway (so the run stops with `figures_not_computed`
as before), is caught (1 failed). The missing "hours not issued" state is the contract owner's 2.6 change, as stated,
and is not judged.

**Owner action (unchanged):** give the calendar the muhurat hours when NSE's circular is out.

## 3. `market-publish.yml` order: MET

The workflow runs these steps in order:
1. `market archive`, with no database. Its manifest rows are committed by the command's recorder.
2. `db-check`, with `if: !cancelled()`, so it runs after a failed archive.
3. `publish`, only on `steps.dbcheck.outcome == 'success'`. It records `archive_incomplete` itself.
4. One failure alert, carrying the first `database check FAILED` or `Omenix F&O market archive` line as its cause. It
   is skipped when the publish already sent its own alert.

The builder's workflow-order test passes. Not run live by me.

## 4. The real 07:10 IST publish: pending

To be verified after today's scheduled run (about 01:40 UTC) through its run log and read-back line. Addendum to follow.

## CI on `main` (orchestrator's question)

- **G4 22ace2f:** yes, CI was red. The merges carrying 22ace2f without the fix failed: a31c36f (run 38472820401),
  b312262 (38472836510), 5428068 (38473230697) and 39e9173 (38474961845). They called `scoring_status` with 4
  arguments. 44090c1 fixed it: my run of `tests/forecast_scoring`, `tests/ai`, `tests/market_read_models` and
  `test_freeze_sections` gives 222 passed at 8629df0. Runs at c1bf97f and 43b92bd were green because they were on a
  line without 22ace2f.
- **Still red after the fix, for a new reason:** 1bec20d (run 38475051048) fails
  `tests/research_engine/test_lookahead.py::test_a_live_cutoff_changes_the_decision_days_own_closing_data`. I
  reproduced it at HEAD. With the panel from just before the first real A13 append (9cba740^) the file passes, 9 of 9;
  with the appended 13 Oct it fails. The sampled decision days are the same in both, which I checked.
- **Root cause (some evidence):** the test expects a true/false feature (VIX above its median) to change under a
  random perturbation. One draw may not flip it. The 2nd and 3rd trials' random numbers come after every later panel
  row is shaken, so each new day appended to the panel (about 1,900 option rows) changes them. The test therefore
  passes or fails by luck, and A13's daily appends will keep flipping it.
- **Fix (reasoning only):** draw each session's perturbation from its own seed (for example
  `Random(f"{seed}-{trial}-{day}")`), so new days never change old draws, and make the live-version test use a
  perturbation that must cross the median, or the "removed" case. Do not skip the test.

## Project rules

New blocks behind the existing block interface; contract pinned; no example values; Slack only to #fno-desk.
