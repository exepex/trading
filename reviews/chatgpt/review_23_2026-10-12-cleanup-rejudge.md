# Review 23 — Clean-slate cleanup re-judge

**Date:** 2026-10-12  
**Judge:** ChatGPT  
**Repository:** `exepex/trading`  
**Cleanup:** `145a632`  
**Fix head reviewed:** `3643874`  
**Prior verdict:** Review 22 — FAIL (F1 should-fix, F2/F3 minor)

## Verdict: PASS

Review 22's only should-fix finding is closed. F2 and F3 are also fixed. I found no remaining active old-desk implementation in `fno/`, and the F1 cleanup did not change A4's recorder path or its `expiries -> chain -> quote_book` provider contract.

### Execution statement

I **could not execute** `pytest`, Ruff or `python tools/check_imports.py` myself because this environment exposes the repository through the GitHub connector rather than as a local checkout. I therefore do not present Claude's command output as my own. Response 28 reports:

- `python -m pytest -q` -> 164 passed
- `ruff check fno tests tools` -> all checks passed
- `ruff format --check fno tests tools` -> 63 files formatted
- `python tools/check_imports.py` -> clean: 70 files, 1 archival skipped
- focused cleanup/recorder tests -> 78 passed

My independent checks were static against commit `3643874`: commit diff, affected files, approved story contracts, and repository code search. The execution limitation remains explicit, but there is no unresolved code/design finding that warrants failing this re-judge.

## 1. F1 — CLOSED [strong evidence]

### Yahoo market-context stack is gone

The old stack identified in Review 22 is removed:

- `fno/providers/base.py:8-43` now exposes only `OptionChain`, `QuoteBook`, index identity, `expiries`, `chain` and `quote_book`. There is no `MarketContext`, `YAHOO_SYMBOLS` or `Provider.context()`.
- `fno/providers/public.py:31-55` now contains only the public NSE HTTP client; the Yahoo `daily_history/daily_closes`, index-context and VIX helpers are gone. `NSEProvider` at `:124-143` only implements `expiries` and `chain`.
- `fno/providers/groww.py:109-180` now has authentication plus `expiries`, `chain`, `quote_book`; its old `PublicData` dependency/context implementation is gone.
- `fno/providers/sample.py` retains only synthetic `expiries` and `chain`; its context generator is gone.
- `fno/models.py:1-90` contains `OptionQuote`, `QuoteBook` and `OptionChain`; `MarketContext` is gone.
- Repository code searches at the fix head returned no `MarketContext`, `historical_vol`, `atm_iv`, `fno.live`, `fno.backtest` or Yahoo references under active `fno/`.

### Remaining pre-built functions have named new-system justification

I checked the specific exceptions Response 28 names:

- `fno.analytics.bs_greeks` (`analytics.py:32-55`) is justified by C2: `docs/stories/C-code-roles.md:59-65` requires delta/vega exposure and Black-Scholes stress repricing. It is reasonable to have the pricing primitive before C2's caller is implemented.
- `fno/accounting/ledgers.py` explicitly implements C1; `docs/stories/C-code-roles.md:9-42` names that module and C1 is already built.
- `fno/research_data/events.py:1-74` implements A6; `docs/stories/A-data-foundation.md:258-295` names it and its point-in-time event rules.
- `fno/research_engine/ledger.py:1-138` implements B4; `docs/stories/B-research-engine.md:176-205` names its `register/require_registered/mark_run/count` contract.

The rest of the surviving core is directly used by retained CLI/A4/storage/research components or is the data-model/API surface they invoke. Section 9b records the deliberate pre-built story exceptions at `docs/CLEAN_SLATE_DESIGN.md:224-232`.

### Removing `historical_vol` is correct [strong evidence]

Yes. B1 does **not** specify the removed helper's demeaned sample-volatility formula. The approved definition is explicit at `docs/stories/B-research-engine.md:24-29`: realised volatility is **root mean square of the last 20 daily log returns, not demeaned**, annualised by sqrt(252), requiring 21 closes.

Keeping a generic function with different semantics would create a high risk of accidentally implementing B1 incorrectly. B1 should implement its exact feature definition when built.

### Removing `atm_iv` is correct [strong evidence]

Yes. B1 specifies ATM IV construction itself: select the nearest listed ATM strike with a deterministic tie rule; use each traded leg's daily close; solve each leg through `fno.analytics.implied_vol`; require both legs (`docs/stories/B-research-engine.md:24-29`). The removed `atm_iv(chain)` was a today's-chain convenience metric, not B1's point-in-time daily-file feature and not section 12's future 30-day ATM estimator.

The primitive B1 actually needs, `implied_vol`, remains at `fno/analytics.py:58-72`.

**F1 status: CLOSED. No blocking/should-fix residue.**

## 2. F2 — CLOSED [strong evidence]

`research/2026-10-12-backtest/README.md:14-24` clearly says replay runs only at the pre-cleanup commit in a separate worktree. The command section now explicitly distinguishes:

- `:30-31` — replay: “legacy worktree root only ... fails on main”
- `:32-33` — `cost_table.py`: “current main root”

There is no longer an instruction that implies the archival replay runs on current main.

**F2 status: CLOSED.**

## 3. F3 — CLOSED [strong evidence]

The A4 story now matches the actual recorder:

- `docs/stories/A-data-foundation.md:167-168` specifies timestamped immutable attempt paths.
- `:169-174` lists the actual 22 columns and explicitly says there is no `quote_age_seconds`.
- `:175-182` documents retries, canonical marker and metadata sidecar.
- `:186-204` matches the validity, retry, no-order and partial-failure behaviour.

These correspond to `fno/quotes/recorder.py`'s existing `COLUMNS`, path, canonical and metadata implementation. The fix changed documentation, not recorder code.

**F3 status: CLOSED.**

## 4. A4 regression check — PASS [strong evidence]

The F1 removals did not touch `fno/composition.py`, `fno/quotes/recorder.py`, `fno/quotes/expiry_listing.py`, or `fno/storage/wiring.py` in the `145a632..3643874` fix diff.

The current path is intact:

1. `fno/composition.py:12-17` selects the recorder's independent `quotes.provider`, quote store and NSE-file expiry fallback.
2. `Provider` still requires `expiries` and `chain`, and retains `quote_book` at `fno/providers/base.py:31-42`.
3. `GrowwProvider.expiries` remains at `fno/providers/groww.py:146-164`.
4. `GrowwProvider.chain` remains at `:166-170`.
5. `GrowwProvider.quote_book` remains at `:172-179`.
6. Public NSE fallback still provides `expiries`/`chain` at `fno/providers/public.py:124-143`.
7. The late-December expiry fallback remains `NseDailyFileExpiries` at `fno/quotes/expiry_listing.py:32-54`.

Removing Yahoo/context code therefore does not narrow or alter the recorder's market-data path. Response 28 additionally reports the byte-for-byte recorder baseline still passes; I could inspect the unchanged recorder path but could not execute that test myself.

## 5. Hunt for remaining old-desk code

**No new finding.**

I searched current code for the key old namespaces and artifacts. No active `fno.live`, `fno.backtest`, Yahoo market-context, `MarketContext`, `historical_vol`, or `atm_iv` reference remains. The old replay remains intentionally archival under `research/2026-10-12-backtest/` and is pinned to the legacy commit; that is evidence preservation, not runnable desk code.

The remaining NSE public provider, Groww provider, option-chain models, pricing/IV primitives, raw-storage stack, accounting/event/trial-ledger components and A4 recorder all have current command/story purposes.

One wording artifact is not a cleanup defect: `fno/storage/wiring.py:1-2` still says “the live desk's is fno/live/services.py” in its module docstring. That path no longer exists. This is stale documentation in code and should eventually say `fno/composition.py`, but it does not create a dead import or execution path. **Severity: minor.** It does not prevent PASS under `docs/JUDGE.md`, which fails only on blocking or should-fix findings.

## Findings summary

- **Blocking:** none.
- **Should fix:** none.
- **Minor:** 1 — stale docstring in `fno/storage/wiring.py:1-2` mentions removed `fno/live/services.py`; update to `fno/composition.py` opportunistically.

## Final verdict

# PASS

Review 22 F1-F3 are closed. The cleanup now meets the clean-slate intent without changing A4's recorder contract. The one remaining observation is documentation-only and does not justify another cleanup failure.
