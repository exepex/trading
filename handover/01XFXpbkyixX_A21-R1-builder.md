# Handover: builder session 01XFXpbkyixX7SuXeQCp5EnX (R1 factory, A21 rates and first-seen; formerly F&O screens lead)

Written 21 Oct 2026, after the orchestrator's handover order of 16 Oct (this session was stopped then). The owner froze
scope to phase 1 on 21 Oct (DESK_DECISIONS), and A21 is parked. Nothing below is merged by this session: I never merge
to `main`.

## (a) Identity

- Session `session_01XFXpbkyixX7SuXeQCp5EnX`. Roles: F&O screens lead (dashboard contract and mockups, stopped by the
  owner 16 Oct), then R1 builder (the strategy factory), then A21 builder (rates and same-day first-seen).
- Branches and heads (all pushed):
  - `story/a21-rates-first-seen` at `5ae76881`: A21 story text.
  - `story/a21-rates-code` at `6cc00168`: A21 part 1, the rates code; built on O10's branch `story/o10-capture-health`.
  - `story/a21-announcements` at the commit carrying this file: A21 part 2, WIP; built on part 1 plus
    `story/a16-observer-group`.
  - Merged earlier: `story/r1-factory-text`, `story/r1a-records`, `story/r1b-screens`, `story/r1c-shadows`.

## (b) Done and merged to main

- **R1, the factory's code, complete:**
  - R1 text: judge 259 PASS (86368061).
  - R1a records: judge 261 PASS (29a0707a).
  - R1b screens: judge 266 addendum 1 PASS (9a20155a).
  - R1c shadows and Holm: judge 271 addendum 1 PASS (136b77c4).
  - All four merged by the orchestrator.
  - R1c added `fno/playbook/measurement.py`, `fno/factory/registered_shadows.py`, `fno/factory/gate_log.py` and
    `fno/budget/stop_rule_tracker.py` to S1's frozen_files (S1 owner's wording, BG1 owner agreed), with a pin test
    `tests/evaluation/test_factory_constants_pinned.py`.
- **Dashboard (exepex/omenix-dashboard), stopped by the owner:**
  - Contract 2.8.0 to 2.13.0 merged (last d53cefe, page_holds; judge 255 add. 1).
  - F&O mockups 37 and 39-46 are in `design/mockups/`.

## (c) Done but not merged

- **A21 story text:** `story/a21-rates-first-seen` 5ae76881, judge 355 addendum 1 PASS (judged at 94cda4a8; only
  merges and the claims number changed since). Not merged.
- **A21 part 1 (rates):** `story/a21-rates-code` 6cc00168, **judge 402 FAIL**, one should-fix.
  - The CLI's exit 1 when the alert was NOT sent is untested: add CLI tests where NOT_SENT exits 1 and SENT exits 0.
  - Merge condition: the merged capture-watch list must hold global-cues, vix-history and rates-daily, and the merged
    tree must pass `tools/check_numbers.py`.
  - Claims: `reviews/claude/response_274_a21-rates-part1.md` (number reserved under O12's list).

## (d) In progress (WIP, committed and pushed)

**A21 part 2 (`story/a21-announcements`).** Files: `fno/announcements_live/` (source, rows, day_state, mark_parts,
poller, reading, wiring, cli, constants), `tests/announcements_live/` (24 tests), the member line in
`fno/intraday/wiring.py` `_observers()` (LazyAnnouncementsPoller at 10 s), A16's two tests updated to expect that
member, `fno/rates/failures.py` (job parameter, `has`), `fno/cli.py`, `.gitignore`. A dry run on live NSE recorded
384 items, and a second process read them back and added none.

**Not judged. A review agent found blocking issues, all open:**
1. **Blocking:** nothing commits the poller's receipts and O10 rows from inside A16's routine, so each new fire would
   re-record items with later times and repeat once-a-day alerts. A16's owner proposed (16 Oct 12:59 UTC) a
   `committed_paths` class attribute on MarkObserver and a second, separate commit after A16's own. It is not built.
   Their question is open: capture_errors.csv is merged with `-X theirs`, so rows could be dropped; consider a per-run
   error file.
2. **Blocking:** A16's catch-up rows make the poller poll past marks. Poll only when the mark is the current one.
3. **Should fix:** a thread cut off at the time limit can race the next. Drive writes have no timeout, and the
   seen-set load syncs the whole month; sync only today.
4. **Should fix:** `store_failed` alerts at every mark. A store failure writes no poll row. The lazy build can race.
5. **Tests missing:** the real poller under the group's limit, the catch-up rows, `DriveDayState`'s day filter, the
   paths commit, and "not a trading day" output on a closed day.
6. **Minor:** the raw file name has no run_id; `SourceCoolingOff` is mapped as `unreachable`; the 3 s read timeout is
   per read; `DayState.kinds()` is dead code.

## (e) Reviews and judging

No judging by me. Self-review agents ran on A21 part 1 (8 findings, all fixed before judge 402) and part 2 (the open
list above).

## (f) Open questions and agreements

- **A21 boundaries:**
  - A12 has no owner; the orchestrator agreed A21 adds a new package and changes no A12 file.
  - A19's owner confirmed there is no overlap.
- **A16's owner (01VK88Lx):** agreed the ObserverGroup conditions (5 s GET, 10 s per member, coverage list, the
  routine's network allowance as a Known limit). The `committed_paths` proposal waits on judge D's PASS of the group.
- **LM1's builder (012eM7Ti):** goes first in the group at 90 s, so A21's poll can start up to 90 s after a mark.
- **D2f (shadow isolation in `fno/playbook/evaluate.py:52-59`):** assigned to me by the orchestrator on 16 Oct. Not
  started. It needs agreement with O2's builder (014zYLf18PgCzR7YoHs1X5Dp, who keeps an xfail), lane 1, judge D, and
  must land before the first paper approval.
- **Handed over:** G11 to 013xqaNT (confirmed); LM1 to 012eM7Ti.
- **Owner, 16 Oct:** "don't design the screen. you can finish backend development which is not tied to UI because I
  didn't like UI mockups" (DESK_DECISIONS row by the orchestrator). The F&O mockups are not approved. The W3 builder's
  built screens follow them, and the orchestrator holds them for the owner's call. The owner's review page (an
  artifact) holds no verdicts.

## (g) Risks and gaps

- **The 6.5% rate:** config's `risk_free_rate` (6.5%) and S6's 5.5% placeholder differ from RBI's real 91-day T-bill
  of 5.7281% (14 Oct auction) and the repo rate of 5.50%. G13 and S6 switch only through their owners.
- **A21 part 1 depends on O10:** it is built on O10's unmerged branch and must merge after it.
- **A21 part 2 must not merge as it is (d).**
- **Live runs:** no live Drive or Slack run of A21 was made; this session has those credentials, and a live run
  writes to the owner's Drive and posts to #fno-desk.

## (h) First three actions for a successor

1. Read DESK_DECISIONS of 21 Oct (scope frozen to phase 1). If A21 stays parked, leave all three branches as they are,
   and tell the main steward (01KS9xBc) and the orchestrator that they are preserved at the heads above.
2. If D2f is in phase 1 (shadow isolation before the first paper approval), start it: agree with O2's builder, write
   the story text, then lane 1 with judge D.
3. If A21 resumes:
   - fix judge 402's SF1 (CLI exit-code tests) on `story/a21-rates-code`;
   - rebase it onto `main` after O10 merges, and check the capture-watch list;
   - only then take up part 2's blocking items with A16's owner.
