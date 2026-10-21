# Handover: A16 / G8 / G10 builder (session 01VK88LxJvV1Gi7Wbr3D4fzp)

Written 21 Oct 2026 for the owner's handover order (orchestrator, 16 Oct night). Everything here is on GitHub;
nothing is left only in a container.

## (a) Identity

- **Session:** `session_01VK88LxJvV1Gi7Wbr3D4fzp`. Builder under the orchestrator (`session_01VG1RqxLFUVdvvPuMRYZtDH`).
- **Owns:**
  - **A16:** the 15-minute quote recorder: `fno/intraday/`, the mark observer port and group, void share, trial reports.
  - **G8:** protocol v4 scoring, comparisons and looks: `fno/forecast_scoring/v4/`, including `days.py`,
    `cutoff_moves.py`, `reconcile.py`, `outcomes.py` and `g7_series.py`.
  - **G10:** the v4 day's clock, labels and pack: part 1 is merged; part 2 is `fno/v4_pack/` plus `.github/workflows/v4-fire.yml`.
- **Branches and head SHAs:**

| Branch | Head | What |
|---|---|---|
| `story/g10-part2b-release` | `81311283` | G10 part 2 (b1): release record, verified reader, 15:10 deadline, v4-fire.yml; the A2 drop |
| `story/g10-part2b-pack` | `7cab92b0` (this file is committed on top) | (b1) plus WIP (b2): capture source and pack builder |
| `story/a16-observer-group` | `6de320d2` | ObserverGroup: several mark observers, each isolated and time-limited |

## (b) Done and merged to `main`

| Work | Merge | Verdict |
|---|---|---|
| G8 V7 shared rule (`story/g8-v7-shared-rule`) | 16 Oct, `a5acc809` | judge 267 PASS |
| A16 mark observer port (`story/a16-mark-observer`) | 16 Oct, `c41ce209` | judge 265 add. 1 PASS |
| A16 void-share start (`story/a16-void-share-start`) | 16 Oct | judge 270 add. 1 PASS |
| G8 "VIX close missing" line (`story/g8-vix-missing-line`, `cc026608`) | 16 Oct, `1c9a8762` | judge 272 PASS |
| G10 part 2 text (`story/g10-part2-text`, `df5dcf35`) | 16 Oct, `8f9f16e4` | judge 274 add. 1 PASS |
| G10 part 2 (a): `fno/v4_pack` format, canonical SHA, guard, `V4_LATEST_FIRE` (`df9432e9`) | 16 Oct, `8321d73f` | judge 277 PASS |
| Earlier (before 16 Oct): G8 look reconciliation `83a5ee7a` (judge 211 add. 1-2), G10 part 1, the stored flag, cohorts | on main | PASS |

## (c) Done but not merged

1. **`story/g10-part2b-release` at `81311283`.** Contains (b1) and the A2 drop.
   - **What it holds:**
     - `fno/v4_pack/release.py`: `ReleaseRecord`, `publish`, `ReleasedPacks` and `NotReleased`.
     - `fno/v4_pack/commitment.py`: `CommitmentTimes`, `GitHubCommitmentTimes` and `on_time` at 15:10:00.
     - `fno/v4_pack/wiring.py`.
     - `.github/workflows/v4-fire.yml`: starts only on a push of `receipts/data/v4/days/**`, no cron; runs
       `ai fire --protocol v4 --day <today IST>`, then commits and pushes the fire log `research/forecasts/ai_v4`.
     - The A2 label removed everywhere (constants, `days.py`, `DayCounts`, codec, story text).
   - **Verdicts:** judge 282 FAIL, fixed; then 282.1 PASS (be7322b1) and 282.2 PASS (81311283, A2 drop).
   - **Merge conditions (judge B):**
     - merge only **after G11's v4 fire (`ai fire --protocol v4`) is on main**; it is not, as of 21 Oct
       (`fno/ai/run_terms.py` is absent on main);
     - G11's test pins the fire log under `research/forecasts/ai_v4/`;
     - pull, then the full suite on the merged tree. Main has moved about five days, so expect conflicts in
       `CLAUDE.md` and `docs/WORK_REGISTER.md`.
   - **Freeze dependency:** `fno/forecast_scoring/v4/days.py` and `fno/constants.py` change here, and `days.py` is
     byte-checked at the v4 freeze. **This must land before the freeze** (the R2/G7 builder now runs the freeze:
     response 287).
2. **`story/a16-observer-group` at `6de320d2`.** It sits with **judge D** (`session_01Pb8z2koLuxty7mbujFpgZa`); no
   verdict was found on main as of 21 Oct.
   - **What it does:** `ObserverGroup([(observer, limit_seconds), ...])` runs each member in its own daemon thread,
     joined for at most its limit (0 < limit <= 300 s). A failure or time-out is named by class
     (`MembersFailed.names`), and a failing member never skips the next one.
   - **Wiring:** `fno/intraday/wiring.py` has `_observers()` (empty now). LM1's member goes first at
     `MONITOR_TIME_LIMIT_SECONDS = 90.0`, then A21's at 10 s.
   - **Gates:** 7949 passed.

## (d) In progress: G10 part 2 (b2), `story/g10-part2b-pack` at `7cab92b0`

- **Built, tests pass** (62 in `tests/v4_pack`; full suite 7986 passed, 18 xfailed, on 21 Oct):
  - `fno/v4_pack/capture.py`: `StoredV4Capture(store, dataset).capture(day)` reads the canonical marker, the sidecar
    and the Drive quote rows of A4e's `groww/derivatives/quote-snapshots-v4`, the same way as `fno/quotes/compare.py`.
  - `fno/v4_pack/builder.py`: `PackBuilder(iv_rule, iv_method, clock).build(day, capture) -> Built(pack | None, reasons)`.
    - An `A` pack needs all of: `clock_status == clock_ok`; every field inside 14:30:00-14:40:00 IST; `e` = the
      nearest monthly future strictly after the day; `levels_received_at` in the window, used for VIX and the
      futures; spot from `e`'s chain entry; `e`'s valid two-sided ATM call and put; IV30 by G1 v2's live rule
      (`LiveAtmIvMinusRealised.atm_implied_vol_points` plus `interpolate_30d`).
    - Only valid rows enter the chain. Black-76 needs the future's traded volume (fixed in `7cab92b0`).
  - `codec.capture_window(day)` is shared by the codec and the builder; `Iv30.value` is in volatility points.
- **Not built (the next steps):**
  1. **Publish command with catch-up,** e.g. `python -m fno v4 release [--day]`:
     - (i) for every scored session from `daily.live_from.forecasts_v4` to yesterday with **no release record in
       Drive**, write `publish(store, d, None)` (system_late). Judge 282.2's condition: decide "no record" from
       Drive (DataStore and receipts), never the checkout. On a write-once refusal (`RawFileConflict`), fail by
       name; never overwrite, never crash.
     - (ii) today: build from `StoredV4Capture`, `publish`.
     - (iii) commit the receipts with `build_receipt_committer()`, pushed with the routine's own credentials (that
       push starts `v4-fire.yml`).
  2. **Wiring** in `fno/v4_pack/wiring.py`:
     - the capture store is `build_drive_only_quote_store(QUOTES_FOLDER, dataset="groww/derivatives/quote-snapshots-v4")`;
     - `iv_method` = `"g1_v2_live_atm_iv30/sha256:<hash of fno/research_engine/live_features.py + fno/forecast/iv30.py>"`;
     - the IV rule is `LiveAtmIvMinusRealised(CUTOFF, cfg["risk_free_rate"], Black76())`, as in `fno/forecast/baseline_wiring.py:68`.
  3. **Routine step:** O1 owns `fno/daily/` and `DAILY_RUN_STEPS`; agree the step with O1. It needs `quotes record
     --window v4` at 14:30 and the release run right after 14:40, with the owner moving the routine start to 14:05.
  4. **Tests** for the catch-up, the command and a real A16-shaped row. Judge 277 asks to test on a real row: A16's
     14:30 row on 16 Oct was sent at 14:30:00.0004 and received at 14:30:00.753.
  5. **Story text, register row, judge B.** Lane 1.
- **Uncommitted:** nothing.

## (e) Reviews and judging

I judged nothing. Reviews I gave to other builders, all agreed:
- **A4e (A4 builder `01MKtUHByHsR9cNwaP5KhFYH`):**
  - the named window `--window v4` in its own dataset;
  - a clock check before and after the run;
  - receipt times for spot (per chain), and one upper-bound `levels_received_at` for VIX and the futures.
  - It merged after judges 278 and 281.
- **A14c:** `ReadOnlyGroww(client, allowed=...)` refuses `place_|modify_|cancel_|create_` names at construction.
- **G11 (`013xqaNTCbSBytKgqpfaYFqZ`):**
  - the pack guard is keyed by book (`book2_hybrid`, `book3_ai`), with the book taken from the same BookVersion
    that names the folder;
  - rows go in `v4/<book>_v2/`;
  - `build_slot_registry()` rename accepted.
- **G13:** reads the 3 pm chains only, never the v4 pack.
- **R2/G7:** the `pack_sha256` column (tolerant read, empty for G7 and M1).

## (f) Open questions and agreements

- **Orchestrator rulings (DESK_DECISIONS, 16 Oct):**
  - the 14:30 capture is an **extra** capture beside 14:55 (option A);
  - **A2 is dropped**;
  - the docs-only drift rule for merges.
- **G11:**
  - (b1) merges after G11's v4 fire;
  - at the freeze, forecast-capture.yml's change (removing the v2 AI steps, adding `--protocol v4` to collect) is
    this builder's;
  - F8c already added the `accounting/ai_usage.csv` line; don't duplicate it.
- **A21 (`01XFXpbkyixX7SuXeQCp5EnX`) asked for its receipts to ride A16's mark commit.** My proposal (not built):
  members declare `committed_paths`, and the recorder makes a **second, separate commit** after its own, so a
  member's file can never block the ledger push. Build it after judge D passes the group. Also warn A21 that
  `research/ops/capture_errors.csv` can lose a row on `-X theirs`.
- **LM1 (`012eM7Ti8ZaSVowgyMkgoGmM`):** 90 s limit, first in `_observers()`.
- **Dry run (G10 criterion 6):** a 14:30 dry run beside A16's 14:30 mark, measuring the Groww load. It needs live
  read-only Groww; any permission refusal goes to the orchestrator for the owner.

## (g) Risks and things not to miss

- **The freeze:** `days.py` and `constants.py` from `story/g10-part2b-release` must be on main before the v4 freeze,
  or the freeze pins A2.
- **M1's method hash** covers `fno/forecast_v4/terms.py`. Any terms change before the freeze moves it; after M1 pins,
  don't touch terms.
- **v4-fire.yml** calls `ai fire --protocol v4`; until G11 lands, a run would fail with "invalid choice". Nothing
  pushes a release receipt until (b2) runs, so it can't trigger early.
- **No release record** for a session blocks every look until the catch-up writes system_late. The catch-up is
  essential (G11's finding).
- **The receipt path** is `receipts/data/v4/days/<YYYY>/<date>.json.sha256` (O9's `data` area), not `receipts/v4/...`.
- **`StoredV4Capture`** returns None on a missing sidecar or CSV. A4b's store raises `RawQuoteMissing`,
  `RawQuoteHashMismatch` or `RawQuoteStoreUnavailable` on Drive problems. Those currently propagate; decide whether
  the release run names them and writes system_late after 14:40.
- **A16 trial:** day 1 (16 Oct) does not count (the owner's decision). The void-share count starts at the first
  session with a recorded previous session.

## (h) The successor's first three actions

1. Ask judge D (`01Pb8z2k`) for the verdict on `story/a16-observer-group` at `6de320d2`. On PASS: pull main, merge,
   run the full suite on the exact tree, push. Then tell LM1 and A21.
2. Check whether G11's v4 fire is on main (`fno/ai/run_terms.py`). When it is, merge `story/g10-part2b-release`
   with the full suite. **Before the v4 freeze in any case:** if G11 slips, ask the orchestrator and judge B about
   merging (b1) earlier, since the A2 drop must not miss the freeze.
3. Finish (b2) on `story/g10-part2b-pack`: the publish and catch-up command (judge 282.2's Drive-only rule), the
   wiring, tests, story text and register row, then judge B. Agree the routine step with O1.

## Update, 21 Oct 2026 evening (after the restart; phase-1 scope freeze from the owner)

- **Merged to main at `d4e2a454`:**
  - G10 part 2b: (b1) and the A2 drop, judges 282.1-282.3. It merged **without** `v4-fire.yml` and
    `tests/v4_pack/test_fire_workflow.py` (judge 282.3); those stay on `story/g10-part2b-release` until G11's v4 fire
    lands.
  - ObserverGroup: judge 405 PASS, judge D.
  - Gates: 8132 passed, with exactly main's two known failures, which the steward fixes on `story/main-green`.
- **Judge D's conditions for the observer group (not built; paused):**
  - (1) members write files atomically;
  - (2) skip a member whose previous call is still alive;
  - (3) cap the sum of limits when a third member comes.
- **G10 PROTOCOL_v4 edits:** `story/g10-protocol-edits` at `73394828`. Judge 411 FAILed on one should-fix (the
  deadline was not pinned). It is fixed, and each table row is now matched to its terms constant. It's back with judge
  B. R2/G7 builds the rest of the freeze text on top of it, once the freeze resumes.
- **(b2):** `story/g10-part2b-pack`, this branch, is done and with judge B but **paused** (phase 1).
  - `fno/v4_pack/capture.py`, `builder.py` and `release_run.py`, plus the `python -m fno v4-pack release` command and
    its wiring.
  - "No record" is decided by Drive; a write-once refusal is named and never overwrites anything.
  - `capture-watch.yml` lists `v4-fire`. That must merge only together with `v4-fire.yml`, after G11.
  - The O1 routine step is not to be asked for until phase 1 ends.
- **Dropped:** `fix/g8-v1-series-test`. The steward's `story/main-green` fixes the same test more strictly.
- **BANKNIFTY in A16 (paused by the freeze; measurement kept for later).** Read-only, 21 Oct 20:00 IST, strong
  evidence:
  - NIFTY: 2 chains (27 Oct, 3 Nov), 110 contracts each within 6%, so **220 quotes a mark**, about 45-50 s at 5 calls
    a second.
  - BANKNIFTY: monthly only (27 Oct, 23 Nov, 29 Dec). Spot 54,977, 132 contracts per chain within 6%, so **264 more
    quotes**, about 55 s more.
  - The owner's widened universe (DESK_DECISIONS 21 Oct: every expiry up to 3 months, ±10% strikes, three futures) is
    larger still and was not measured.
  - The risk is 14:30, when A4e's v4 capture (about 190 quotes, no pacer) shares the key: about 680 calls in ten
    minutes.
  - A16 hard-codes NIFTY in `groww_source.py` and `expiry_plan.py`, so BANKNIFTY means making the underlying a
    parameter. NIFTY's rows must stay byte-for-byte unchanged, because they are frozen for v4.
- **Scratch script used:** a read-only count through `ReadOnlyGroww`. It is not committed; it is easy to redo with
  `listed_expiries` and `parse_groww_chain` from `fno/providers/groww.py`.
- **Protocol edits at `a831e2ce`:** judge 411's notes are done as well. The quantile convention is tested against
  `research/forecasts/v4_moved_after_cutoff.json`, and my long prose lines are wrapped. It's back with judge B.
- **FL1's needs for BANKNIFTY in phase 2 (FL1-2, from about 3-5 Nov):**
  - The owner's universe: every expiry up to 3 months, ±10%, plus the futures. FL1's fallback, if the load doesn't
    fit, is the two nearest monthlies at ±6%, which needs the owner's yes.
  - Marks to keep: 09:30 (entries), the hourly marks from 10:15, 15:15 (exits) and 15:30.
  - The future and the index level at each mark.
  - Measure the ±10%, 3-month load first.
