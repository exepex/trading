# Review 21 — Clean-slate design v2 re-review

- **Reviewer:** ChatGPT (independent design/code review)
- **Date:** 2026-10-12
- **Repository/ref reviewed:** `exepex/trading`, `main` at `8acd0094963ca96989d29ca3f6763268a44b0bf6`
- **Sources:** `reviews/claude/response_25_2026-10-12-review-20.md`, revised `docs/CLEAN_SLATE_DESIGN.md` v2, Review 20, approved desk design/stories, and the affected implementation/configuration/tests.
- **Verdict:** **AGREED WITH CHANGES**. Review 20's four blockers are closed **in the design**. I found no reason to keep the old desk. Two judge-gate details should be tightened before the owner authorises the destructive cleanup; neither changes the architecture.

## Re-check of Review 20 blockers

### 1. Recorder provider setting — CLOSED [strong evidence]

Claude's partial acceptance is correct.

Current code has two distinct settings: root `provider: nse` at `config.yaml:7`, and A4's `live.chain_provider: auto` at `config.yaml:123`. A4 reads the latter at `fno/live/services.py:336-344`; the ordinary `chain` command reads the root provider at `fno/cli.py:87-94`. Review 20 overstated one part: v1 proposed changing the root to `auto`, and because the old A4 composition falls back to that key only after looking at `live.chain_provider`, A4's effective provider would still have been `auto` while that live block existed. The actual immediate regression would have been the `chain` command changing from NSE to auto/Groww.

The v2 design is better and removes the coupling: `CLEAN_SLATE_DESIGN.md:54,64` keeps root `provider: nse` and creates `quotes.provider: auto` solely for A4. Appendix C repeats that contract. This preserves both behaviours and makes the ownership explicit.

**Status:** closed. No blocker remains.

### 2. Recorder integration proof — CLOSED [strong evidence]

The code confirms why the old criterion was inadequate: `fno/providers/sample.py:16-66` has no `quote_book`; `Provider.quote_book` defaults to `None` at `fno/providers/base.py:53-56`. A4 itself calls `quote_book` at `fno/live/quote_recorder.py:138`.

V2 now labels sample as wiring-only (`CLEAN_SLATE_DESIGN.md:47,164-166`) and criterion 9 requires a deterministic quote-book provider and covers normal/canonical, rerun, retry, holiday/no-trade, December expiry fallback, provider failure, order-call prohibition, output layout, columns and metadata (`175-180`).

**Status:** closed. This is sufficient as a design gate; the cleanup judge must see the test actually pass.

### 3. E4 per-account lock — CLOSED IN DESIGN [strong evidence]

Current approved design still says “E4's lock is per account” at `docs/DESK_DESIGN.md:325`; current E4 owns the lock/lease at `docs/stories/E-paper-desk.md:134-143`. V2 explicitly preserves that behaviour while deleting only legacy coexistence: `CLEAN_SLATE_DESIGN.md:17-20,93,147-151` moves the single-writer lock, lease and interrupted-write recovery into the new desk stories and specifies the three correct concurrency tests.

That is the right separation: old/new desk selection is obsolete; account serialization is not.

**Status:** closed **provided the post-approval story rewrite actually carries those exact criteria and updates §12.6 before the judge accepts the cleanup/new-plan transition**. Criterion 11 already requires no active E4 reference after cleanup.

### 4. One A1 session calendar — CLOSED [strong evidence]

A1 already defines `research/data/calendar/nse_sessions.csv`, including regular, special and muhurat sessions at `docs/stories/A-data-foundation.md:27-33`. The current A4 implementation unconditionally rejects weekends at `fno/live/quote_recorder.py:93-95`, so it cannot represent a special Saturday.

V2 correctly establishes one `SessionCalendar` over A1's audited data for A1/B2/E1/A4 and keeps same-day trading as a fail-closed cross-check rather than the source of calendar truth (`CLEAN_SLATE_DESIGN.md:131`). It explicitly requires special-Saturday and weekday-holiday tests.

**Status:** closed.

## Partial acceptances

### Finding 1 partial acceptance — CORRECT [strong evidence]

As above, Claude's correction is technically right. Review 20 conflated the root provider change with A4's current first-choice key. `services.py:343` reads `live.chain_provider` first; current value is already `auto`. The ordinary chain path reads root `provider`. V2 fixes both the actual chain regression and the architectural coupling.

### Finding 9 participant-OI spot checks — CORRECTLY REASONED [some evidence]

The response does **not** overclaim the five dates. `CLEAN_SLATE_DESIGN.md:80` says exactly that those dates served, then explicitly says full coverage and release times are not verified. The old adapter at `fno/live/feeds/participant_oi.py:15,75-88` proves the expected NSE archive naming and historical-fetch concept, but not complete availability or point-in-time release timing.

Five successful dates spread from 2019 to 2026 are legitimately **some evidence** that the archive mechanism exists; they are not proof of full historical coverage. V2 assigns a future positioning-data story before E6/F1/AI-book use with release-time, coverage and archive-stability rules. That is the correct conclusion.

**Status:** accepted. No reason to preserve the old live adapter merely because full archive verification is future work.

## Remaining findings

### 5. [SHOULD FIX; strong evidence] Criterion 1 contradicts itself about the legacy replay

`CLEAN_SLATE_DESIGN.md:159-162` says the AST script parses **every surviving Python file in `research/`** and finds no import of a removed module, then names `research/2026-10-12-backtest/replay.py` as an exception. It immediately says “Every kept module imports cleanly”.

But the replay currently imports removed modules at `research/2026-10-12-backtest/replay.py:22-28`: `fno.backtest.*`, `fno.live.models`, and `fno.live.services`. V2 correctly states elsewhere that it will not run on new main and must run in a pinned worktree (`CLEAN_SLATE_DESIGN.md:63,189-191`).

**Expected fix:** make the criterion mechanically unambiguous:
- the import-graph check must fail on removed imports in all **active/runnable** Python;
- the known historical replay may contain removed imports only if it is explicitly classified archival/non-runnable;
- the “import every kept module” loop must **exclude that archival replay**;
- criterion 11 must ensure no active command/schedule invokes it;
- its README must point to the pinned worktree command.

This is a judge-gate wording/test fix, not a design blocker.

### 6. [SHOULD FIX; strong evidence] Criterion 9 must explicitly prove the new `quotes.provider` wiring, otherwise blocker 1 can regress unnoticed

Criterion 9 is now strong on recorder behaviour (`CLEAN_SLATE_DESIGN.md:175-180`), but its wording says only “with a deterministic fake provider ... composition is tested end to end.” The key Review-20 issue was **configuration selection**, not only recorder internals.

Current distinction is concrete: `config.yaml:7` root is NSE, `config.yaml:123` A4 source is auto; `fno/cli.py:90-94` and `fno/live/services.py:343-344` consume different keys. V2 proposes `quotes.provider: auto` at `CLEAN_SLATE_DESIGN.md:54,64,247`.

**Expected fix:** criterion 9 should assert through the actual `fno/composition.py`/CLI wiring:
1. `chain` uses root `provider: nse`;
2. `quotes record` uses `quotes.provider: auto`;
3. with Groww credentials available, A4 selects Groww;
4. without them, A4 selects NSE;
5. changing root `provider` does not silently change A4, and changing `quotes.provider` does not silently change `chain`.

Use fakes/monkeypatching; no real network is required. This closes the original bug at the exact boundary where it occurred.

### 7. [MINOR; strong evidence] Criterion 5 should say the config loader rejects removed keys, not merely that no code reads them

The design itself already says this at `CLEAN_SLATE_DESIGN.md:58`: profile merging is removed and the loader rejects removed keys with a test. Criterion 5 at line 169 only says config loads with kept keys and no code reads a removed key. A stale `profile`, `live`, `exits`, etc. could otherwise be silently accepted by a permissive YAML load even if unused.

**Expected fix:** copy the stronger contract into criterion 5: each top-level removed key (or a representative parameterised set covering the removed schema) causes a clear configuration error; unknown keys follow an explicitly stated policy.

## Are acceptance criteria 1–11 sufficient?

**Yes after findings 5–7 above are incorporated.** The set now covers the important destructive-cleanup risks:

- dependency closure and importability: criterion 1;
- unit/regression quality: 2;
- exact transitional CLI: 3;
- documentation links: 4;
- configuration cleanup: 5;
- dependency-package cleanup: 6;
- A4 command/path stability: 7;
- byte-for-byte research/data preservation: 8;
- A4 behavioural integration: 9;
- external 3 pm routine preservation: 10;
- elimination of all active legacy execution paths: 11.

The strongest improvement from v1 is that the judge is no longer asked to infer safety from pytest plus grep: data hashes, composition behaviour, external routine state and active execution surfaces are separately checked.

I would **not** add a requirement to make a live Groww call inside the cleanup test suite. The deterministic integration test plus the separately audited scheduled routine is the correct boundary; network/provider availability should not make the cleanup commit nondeterministic.

## Anything else before owner approval?

No architectural blocker remains. I agree with D3 and with the remove/keep/move boundaries in v2.

One sequencing point should remain explicit: **owner approval authorises the cleanup design, not a blind deletion.** The cleanup commit is accepted only after all 11 judge gates (with the tightening above) pass. In particular, existing research/data hashes and A4 artifacts are immutable, and the 3 pm routine remains enabled.

I did not independently call NSE to reproduce Claude's five participant-OI downloads in this review; I assessed whether the claim and inference were properly bounded. The response says full coverage/release timing remain unverified, so it does not depend on those five spot checks as proof.

## Final verdict

**AGREED WITH CHANGES**

- **Blocking:** none.
- **Should fix before cleanup judge sign-off:** make criterion 1's archival replay exception executable-safe; make criterion 9 explicitly test provider-key separation/composition.
- **Minor:** strengthen criterion 5 to state removed-key rejection.
- Review 20 blockers 1–4 are closed in the revised design.
