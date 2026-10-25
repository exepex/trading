# Judge 687: ING1 data ingestion as a separate part (design), judge S (2 of 2)

Branch `story/ing1-data-ingestion` at `6988fc3e2`. **FAIL, lane 1** (2 blocking, 4 should fix, 3 minor). Design only:
I read the text and checked its facts against the code and the git history.

## Criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Inventory matches the code, misses no capture | PARTLY | 27 workflows placed; cited lines right (`constants_operations.py:69-97`, `quote_parts.py:7-8,80-84`, `runner.py:58-76`, `v4_part.py:27-35`); misses B1 |
| 2 | Migration never loses a session's data | NOT MET | finding 2 |
| 3 | No second writer of a write-once record | PARTLY | key and `RawFileConflict` stop it; findings 1 and 3 do not |
| 4 | Reuses O14's retry unchanged | MET | 4.4 matches O14 sections 4 and 5 |
| 5 | Keeps GW1's limits and quiet windows | PARTLY | quiet windows kept; budget wrong (finding 4) |
| 6 | Each step provable on a real session | MET | K10; rehearsal plus a watched first session per Class G step |
| 7 | Two judges per removal; under 500 lines; links | MET | 6.2; 479 lines |

## Findings

1. **Blocking: the system already fetches NSE files and archives them in Drive; the design misses it.**
   `RawFileLibrary.get` falls back to NSE and `put`s the file (`storage/raw_library.py:52-60`, `storage/wiring.py:151-157`).
   Used by `desk/wiring.py:45` (ExitDesk settlement), `forecast_v4_rules/pack_wiring.py:93,167`,
   `scoreboard/wiring.py:116`, `role_value/wiring.py:64`, `checks/wiring.py:126`, `itm_chance/wiring.py:51` and
   `forecast_lab/page_wiring.py:76`. Also missed: `lab release-check` polls NSE (`forecast_lab/wiring.py:75-87`).
   Summary item 6 ("the only place") is false, and K2 (Groww names only) passes all of these. Fix: list them, widen K2,
   move each system reader to `StoredFilesLibrary` plus the 4.5 not-ready stop (desk: two judges), and host
   `release-check`.
2. **Blocking: a Class G swap day can lose the session.** Once the key says `job`, the old path refuses (K3). If the new
   routine does not start, the only guard is a witness "2 minutes before the window" (6.3) on Actions' cron, which 4.3
   itself says is 4-5 h late (`recorder-watch.yml:5`: "best effort"). The hand-run reading is "reasoning only". Fix:
   keep both hosts scheduled and let a dataset-day git claim decide (first push wins, `intraday/claims.py:1-7`): the
   standby takes over only with no claim by T-x. Prove it with a planted no-start in rehearsal; put the hand-run reading
   to the owner.
3. **Should fix: the flip goes by wall clock.** It lands 16:40-08:00 and is read when a path starts (6.1), but late
   overnight Actions runs (03:30, 06:00, 07:41) can span it, so two owners of one day are possible. Fix: key the owner
   by session date (`job_from: <day>`).
4. **Should fix: the Groww budget is wrong.** 21+5+1+4+2 = 33, not 38; 38 needs the rerun's 10
   (`groww_sign_in.py:8-11`). O14 already reaches 129 (`O14-retry-policy.md:132-133`), so K7's cap of 130 leaves about
   one try, and I10's C9 alone needs 3. "The school's 4 slots" may be C20's slots, counted twice. Fix: line up with O14,
   count tries, state I10's room, or ask the owner.
5. **Should fix: the import inventory is short** ("three places"). Also found: `capture_probes/wiring.py:79-81`
   imports `school`; `storage/receipt_publisher.py:10` imports `research_engine`; `storage/content_checks.py:9-12` and
   `filings/wiring.py:12` import `market_read_models`; `record_store/wiring.py:64` imports `daily.alerts`. I1's
   allow-list would be wrong on its first run. `boundary.py` must also place `storage` and `providers`.
6. **Should fix: C5's double writer is already settled by git.** The workflow committed only on 14 and 15 Oct
   (`13a6c8c01`, `fe695efcb`, at 19:35 and 19:13 IST); the daily run committed every session since 16 Oct (`2ec7c6e6d`
   to `d5a247530`). M15 is strong evidence; drop I4's 5-session measurement.
7. **Minor:** the gap list omits C6 (no indices or weeklies row in `health/expectations.py:68-96`).
8. **Minor:** I1 changes which path captures, so it is lane 1 (as section 7 item 7 says), not lane 2.
9. **Minor:** `fno/alerts/` already exists: say "add `reported.py` to it".

## Plants

None. A design has no code to mutate.

## Notes

- To claim my number I printed the tail of `reviews/judge/README.md`, which showed Judge R's row 686. I had already
  formed my findings, did not use it, and checked none of R's points.

## Addendum 1

Round 2 at `4caf44151` (497 lines). **FAIL, lane 1**: finding 2 is still partly open; every other finding is
fixed and checked. This was the last round, so the owner decides.

| # | Verdict | Evidence |
|---|---|---|
| 1 | Fixed | M17 and C22 added; summary item 6 corrected; K2 now walks every import and forbids `RawFileLibrary` and any NSE source in system code; I8b switches one root at a time |
| 2 | **Partly** | 6.3 adds a git claim plus a standby path, as asked. But 6.1 (lines 351-353) still says the old path "stays in code, not scheduled" and that rollback means "flip the key and restore the old routine line". A path that is not scheduled cannot stand by, so a no-start day is still lost; 6.3 (line 394) also still says "restorable by one key". Once the old path is removed, nothing covers a no-start and the text does not say so. The hand-run reading (line 277) is still the builder's reading, not an owner question. The died-after-claim lease has no planted test |
| 3 | Fixed | Owner key is now `job_from: <session date>`, set at least one session ahead |
| 4 | Fixed | 33 (38 with a rerun), then 129 and 135 with the planned jobs; limits 60 and 140 leave I10 room |
| 5 | Fixed | M10 lists the inverted imports; `boundary.py` lists a shared layer |
| 6 | Fixed | M15 rests on git history; I4 only removes the dead cron |
| 7-9 | Fixed | C6 in I3; I1 is lane 1; `fno/alerts/` is the existing package |

Fix that would close 2 (text only): in 6.1 and 6.3, the old path stays **scheduled** as the standby until its
removal; rollback is a later `legacy_from` date. State the cover after removal (it is today's risk, with the
Actions alert only as a second signal). Add owner question 4: may a routine that never started be run by hand in
market hours? Add a planted died-after-claim test to I7.

Re-checked at the builder's later tip `4c244b43a`, still round 2 (it crossed with this addendum). Finding 2's core
is now fixed: 6.1 (line 351) keeps the old path scheduled as the standby, gated by the claim, and 6.3 says that
with GitHub down neither path takes the window. **Still FAIL** on 2 should-fix and 1 minor, all text only:
- **Should fix:** the owner is still not asked whether a routine that never started may be run by hand in market
  hours (line 278 is the builder's reading of a hard rule).
- **Should fix:** nothing says what covers a no-start once the old path is removed (it is a single host again,
  today's risk).
- **Minor:** lines 353 and 395 still say "flip the key and restore the old routine line" and "restorable by one
  key"; they should match line 345 (a later `legacy_from` date).

Note for I7's judges: the died-after-claim lease must come with a planted test there. The owner decides.
