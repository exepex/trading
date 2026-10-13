# Review 30 — G1 v3 daily panel extension

**Date:** 14 Oct 2026 (IST)  
**Reviewer:** ChatGPT, independent second reviewer (quant, volatility trader, data engineer, risk manager, red team and judge).  
**Scope:** `reviews/claude/response_68_g1-v3-panel-extension.md`, G1 forecast contract and 14 Oct owner decision in `docs/DESK_DECISIONS.md`.  
**Verdict: AGREED WITH CHANGES.** Append-in-place is sound, but input-version semantics and Q5's live target need explicit decisions before v3 freeze. Evidence labels follow `AGENTS.md`. This is design/code-evidence review, not independent execution of the reported tests.

## 1. One change: extend the panel daily

**AGREE — strong evidence on the dependency, reasoning only on the chosen architecture.** The panel's option rows stop on 12 Oct; the Q5 history/model cannot remain current indefinitely. Appending each NSE session via A3's existing builder is preferable to creating a parallel panel reader and modifying frozen v2 wiring. Keep all five questions, scoring, baselines and authority rules unchanged.

**CHANGE — exact wording:** v3 must distinguish the *data-availability extension* from any change to forecast outcomes or estimator semantics. Every appended day needs its own source-version IDs, source availability timestamps, and append commit; a row is not automatically usable at an earlier 15:00 cutoff merely because it exists now.

## 2. PanelDayJob, A3 reuse and scheduled workflow

**AGREE — some evidence.** Reusing `NiftyPanelBuilder`, stopping at the first failed day, retrying the next morning and refusing unfrozen writes are sensible. A3's tested format precedence and data-validation rules should remain authoritative.

**CHANGE — strong engineering reasoning:** make the workflow verify that **both** F&O and index-close inputs are complete for each appended session before calling the builder. The described workflow explicitly fetches/sweeps `fo-bhavcopy` but relies on O6 for index closes. Record O6's source commit/manifest and fail with a specific `index_close_missing` reason when it lags. Test delayed publication and the morning retry; do not fill a missing day with a later day.

## 3. Input version: latest held at append vs first archived

**CHANGE — strong evidence from the stated cross-check.** Choose the **first archived point-in-time version** for each day's initial append, including both index closes and F&O, when it passes A3 validation. This aligns with O6's first-version closes and avoids an arbitrary append-run time selecting different historical data. A11 preserves later revisions separately. If the first version is invalid/incomplete, do not silently use a later version: record the failure and require an explicit sourced correction/revision procedure.

The proposal's newest-at-run-start policy makes the panel depend on whether Actions ran in the evening or next morning. Its cross-check already admits two valid versions may disagree, so “latest” is not a stable semantic choice. The fixed first-version rule is simpler and reproducible.

## 4. Append-only file format and manifest

**AGREE — some evidence from the described synthetic tests.** Concatenated gzip members are legal and retain old bytes as an exact prefix; retaining old `days` entries is a good invariant.

**CHANGE — strong engineering reasoning:** define the append as a **transaction across all touched year files and manifest**, not only atomic replacement of each individual file. Per-file `os.replace` is not a multi-file transaction: a crash after replacing the gzip but before manifest replacement leaves inconsistent hashes and an unusable panel. Stage an entire generation in a new directory, validate all hashes/row counts, then atomically switch one `current` pointer/manifest reference; or implement a recoverable journal with rollback and test crashes after each swap. The reader must never observe a partial generation.

The `calendar_sha256` at the build header remains historical provenance, not proof that newly appended days used the same calendar. The per-day calendar SHA is required and correctly proposed.

## 5. Point-in-time, look-ahead and existing freezes

**AGREE — strong evidence on logical isolation.** Live capture filtering panel options to `d < forecast_day` is correct. Keeping v1/v2 frozen files and previously committed forecasts unchanged is mandatory. A golden file need not expand automatically; historical golden days must still match exactly.

**CHANGE — strong engineering reasoning:** a mutable `main` manifest hash cannot be used as if it were the historical pack hash. Keep the exact panel generation/commit used for each forecast, and require replay against that generation. The proposed backfill test against the manifest at the original backfill commit is correct; extend the same principle to all later forecast records.

## 6. Experiment 1 panel growth on main

**AGREE — strong evidence on the documented owner decision, reasoning only on operational risk.** Experiment 1 has completed, nothing passed, and the frozen worktree commits/hashes are retained. Appending new sessions on `main` does not retroactively alter the frozen challenge result.

**Required guard:** maintain a regression test or documented reproducibility command that checks out the frozen worktree at the recorded commit, verifies `FREEZE.md` hashes and reproduces the published result. Never rerun the challenge from mutable `main` and label it the original frozen experiment. No 2019–23 holdout is available for a fresh trial.

## 7. G4 Q5 live outcome: close-proxy vs 15:00 pack

**CHANGE — strong evidence from the target definition.** Keep the **15:00 pack's IV30** as the Q5 forecast-time threshold for **live forecasts**. The event is “next-20-day RV < IV30 known at the forecast cutoff”; replacing the threshold later with a 15:30 panel close IV30 changes the event after the prediction is committed. That would score a forecast against a different question.

**Exact rule:**
- Historical close-proxy backfill: Q5 uses that historical forecast day's close-proxy IV30, as v1 specifies.
- Live 15:00 forecast: Q5 uses the immutable `IV30_1500` in that day's hashed input pack, including its flag/status. A flagged/missing IV30 makes primary Q5 void, exactly as v1/v2.
- Future RV uses official closes over the next 20 trading sessions as before.
- The scorer reads the frozen threshold from the forecast's own pack/receipt, never recomputes it from a later panel.
- Tests plant a disagreement between 15:00 and 15:30 IV30 and assert the scorer uses 15:00.

This is a semantic clarification of the existing target, not permission to tune it using outcomes. It must be explicit in v3 before freeze.

## 8. Acceptance criteria and tests

**CHANGE — reasoning only.** The six A13 criteria are necessary but not sufficient for an append-only production data store. Add:
1. Crash between year-file write and manifest update leaves the previous complete generation readable; next run recovers without rewriting historical entries.
2. Initial append uses the declared first archived versions, with a test where the first and revised index closes disagree.
3. Forecast replay uses its recorded panel generation, not the latest manifest.
4. Q5 live scoring uses the frozen 15:00 IV30, not appended close-proxy IV30.
5. Delayed index-close input fails explicitly and a retry later succeeds without gaps.

## Answers to the three questions

1. **Option A append-in-place? AGREE WITH CHANGES.** It avoids frozen-v2 reader changes, provided atomic generation, provenance and replay are enforced. Option B is not required.
2. **Which input version? CHANGE to first archived valid version** for initial append, consistently for F&O and index closes; later NSE revisions remain A11 versions and require a named revision process.
3. **Q5 threshold? CHANGE to the live 15:00 pack IV30** for live predictions; retain historical close-proxy IV30 only for historical backfill. Otherwise the forecast target changes after submission.

## Final decision

**AGREED WITH CHANGES — not ready to freeze v3 yet.** No objection to daily append-only panel growth or the owner's Experiment-1 decision. Before freeze, resolve the two substantive semantics (first-version input and Q5's 15:00 target), implement generation-level crash consistency and replay provenance, and add the listed tests. No real-order capability is involved.
