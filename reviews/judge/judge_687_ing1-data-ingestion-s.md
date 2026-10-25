# Judge 687: ING1 data ingestion as a separate part (design), judge S (2 of 2)

Branch `story/ing1-data-ingestion` at `6988fc3e2`, `docs/stories/ING1-data-ingestion.md` (479 lines) plus one
WORK_REGISTER row. **FAIL, lane 1** (2 blocking, 4 should fix, 3 minor). Design only, so I read it and checked its
facts against the code and git history myself.

## Criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | The inventory matches the code (file:line) and misses no capture | PARTLY | The 27 workflows are all placed. The cited lines check out (`constants_operations.py:69-97`, `quote_parts.py:7-8, 80-84`, `runner.py:58-76`, `v4_part.py:27-35`, `config.yaml:210-216`, `execution_capture.py:37`). It misses the system's own NSE fetches (B1) and `lab release-check` |
| 2 | The migration never loses a session's data | NOT MET | B2 |
| 3 | No second writer of a write-once record | PARTLY | The owner key and `RawFileConflict` stop it. The system's fetch-and-archive (B1) and a flip set by wall clock (S1) do not |
| 4 | Reuses O14's retry unchanged | MET | Section 4.4 matches O14 section 4 (own loops are not wrapped) and section 5 (no sign-in retry) |
| 5 | Keeps GW1's limits and quiet windows | PARTLY | The quiet windows are kept. The budget does not add up (S2) |
| 6 | Each step can be proven on a real session | MET | K10, plus a rehearsal and a watched first session for each Class G step (6.1) |
| 7 | Two judges for every removal | MET | Section 6.2 and its closing paragraph |
| 8 | Under 500 lines, one owning document, links not restating | MET | 479 lines; O14, DR1 and GW1 are linked, not restated |

## Findings

1. **Blocking: the system already fetches and archives NSE files itself, and the design misses it.**
   - What happens: `RawFileLibrary.get` reads the stores first, then fetches from NSE and `put`s the file in Drive
     (`fno/storage/raw_library.py:52-60`, built by `storage/wiring.py:151-157`).
   - Who uses it: system roots build it through `build_nse_fo_library()`, at `desk/wiring.py:45` (ExitDesk's
     settlement: money), `forecast_v4_rules/pack_wiring.py:93,167`, `scoreboard/wiring.py:116`,
     `role_value/wiring.py:64`, `checks/wiring.py:126` and `itm_chance/wiring.py:51`. `forecast_lab/page_wiring.py:76`
     does the same for participant OI.
   - A capture missing from the inventory: `lab release-check` (`forecast_lab/wiring.py:75-87`) polls NSE for the
     bhavcopy and FII/DII release times from the evening routine. It is in neither the inventory nor M8.
   - What is wrong in the text as a result: summary item 6 ("the only place where the system starts a capture") is
     false. K2 only looks for Groww and recorder names, so it would pass all of these. "One owner per dataset-day" is
     already broken for the F&O and OI datasets. `raw_library.py:3` (24 Oct) already says a reader must use
     `StoredFilesLibrary`.
   - Fix expected: list them as M-findings. Widen K2 to cover `RawFileLibrary` with a live source and
     `build_nse_*_library` / `build_nse_source` in system packages. Add a step that moves each system reader to
     `StoredFilesLibrary` with the 4.5 not-ready stop; the desk's part is money, so two judges. Put `release-check` in
     the inventory and give it a host.
2. **Blocking: a Class G swap day can lose the session's data.**
   - With the key set to `job`, the old path refuses (K3). If the new routine never starts, nothing records the 3 pm,
     v4 or E3 quotes.
   - The only guard is a witness "2 minutes before the window" (6.3). It follows `recorder-watch.yml`'s pattern, which
     runs on Actions' cron. The story itself calls that cron 4-5 h late (4.3), and `recorder-watch.yml:5` calls it
     "best effort", so the alert cannot come in time.
   - The hand run that 6.3 relies on for a routine that never started is the builder's own reading of the owner's
     market-hours rule ("reasoning only").
   - Fix expected: keep both hosts scheduled and let a per-dataset-day git claim decide who takes the capture (first
     push wins, as `intraday/claims.py:1-7`). The key names the primary; the standby takes over only when no claim
     exists by T-x. That gives exactly one taker and no lost day. Prove it with a planted no-start in a rehearsal.
     Put the hand-run reading to the owner as a question.
3. **Should fix: the ownership flip goes by wall clock, not by dataset-day.**
   - The flip lands between 16:40 and 08:00 and each path reads the key when it starts (6.1). Actions jobs start 4-5 h
     late and run overnight (`nse-margins` 03:30, `fo-masters` 06:00, `index-closes` 07:41), so a run that started
     before the flip and a job that starts after it can both be owner of the same day.
   - Fix expected: key the owner by session date (`ingest.owner.<dataset>: {job_from: <day>}`) so every path agrees
     on every day.
4. **Should fix: the Groww budget does not add up.**
   - 21+5+1+4+2 = 33, not 38. The 38 needs the rerun's 10 children (`groww_sign_in.py:8-11`).
   - O14 already gets 129 once the next morning's 08:36 run falls inside the rolling 24 hours (`O14-retry-policy.md:
     132-133`). K7's cap of 130 then leaves about 1 try, and I10's C9 alone needs 3 tries (`TRIES_A_DAY`). So I10
     cannot pass K7 as written.
   - "The school's 4 slots" look like C20's probe slots, which I10 then counts again as new.
   - Fix expected: line up with O14's figure, count tries, state the room left for I10, and make it an owner question
     if it does not fit.
5. **Should fix: the import inventory is short.** Summary item 4 says "three places". Also found:
   - `capture_probes/wiring.py:79-81` imports `school`;
   - `storage/receipt_publisher.py:10` imports `research_engine`;
   - `storage/content_checks.py:9-12` and `filings/wiring.py:12` import `market_read_models`;
   - `record_store/wiring.py:64` imports `daily.alerts` (outside M10's list).
   An allow-list that starts as "today's M-list" (I1) would be wrong on its first run. `boundary.py` must also say
   whether `storage` and `providers` are ingestion, shared or system; `storage` holds the fetching library.
6. **Should fix: C5's double writer is already settled by git history.**
   - The workflow committed only on 14 and 15 Oct (`13a6c8c01`, `fe695efcb`, at 19:35 and 19:13 IST). Every session
     since 16 Oct was committed by the daily run (`2ec7c6e6d` to `d5a247530`).
   - So the workflow has recorded nothing for 6 sessions, M15 is strong evidence, and afternoon lateness can be
     measured. I4's 5-session measurement is not needed.
   - Fix expected: use these facts, shorten I4, and say whether Actions can host any tight window at all.
7. **Minor: health gaps.** The gap list omits C6: the indices and weeklies have no row in `health/expectations.py:68-96`.
8. **Minor: I1's lane.** `ingest.owner.*` keys decide which path captures, so I1 is lane 1, as section 7 item 7
   already says; the step table puts it in lane 2.
9. **Minor: `fno/alerts/` already exists.** It holds `sender.py` and others; say "add `reported.py` to the existing
   package".

## Plants

None. This is a design with no code to mutate.

## Notes

- I fetched the full history (`--unshallow`) for finding 6.
- To claim my number I printed the tail of `reviews/judge/README.md`, and it showed Judge R's row 686. I saw it after
  my findings were formed and did not use it. I checked none of R's points myself, and none is in this verdict.
