# Review 15 — judge A4 quote recorder and B4 ledger guard

**Date:** 2026-10-12  
**Reviewer / role:** ChatGPT, independent judge  
**Reviewed on `main`:** `reviews/claude/response_17_2026-10-12-built-a4-b4.md`; stories A4 and B4; `fno/live/quote_recorder.py`, `quote_report.py`, `quote_cli.py`, Groww quote/expiry code; `fno/research_engine/ledger.py`, `research/ledger.csv`; listed tests.  
**Verdict:** **FAIL — two blockers: A4 AC1/AC2 freshness semantics and B4 AC1/AC5 committed-registration integrity.** Other reviewed criteria pass by code/test inspection. I did not independently execute the claimed “270 passed”; the verdict does not rely on that count.

## A4 — Daily 3 pm quote recorder

### AC1 — FAIL
**Criterion:** a 15:00 run records every eligible contract of the nearest two monthlies with bid/ask/last and capture time.

The immutable-attempt/canonical mechanics work and are tested. However, late-December behavior knowingly cannot obtain two monthlies from Groww's expiry-list endpoint. The implementation records one monthly, marks incomplete, retries, then canonical `none`. That is correct fail-closed behavior but does **not satisfy AC1** on those trading days.

**Required fix:** implement the proposed independent expiry discovery fallback before A4 passes: when the provider returns fewer than two monthly expiries, obtain listed NIFTY expiry dates from the latest available NSE derivatives source/daily file, apply the same monthly-expiry identity, then call Groww's chain endpoint for those explicit dates. Record the expiry-source file/date/hash in the attempt metadata. If fallback is unavailable/stale, remain incomplete/fail closed. Add a December-cross-year test proving December + January monthlies are captured.

### AC2 — FAIL
**Criterion:** crossed, one-sided or stale quotes are retained but marked invalid and never executable; the agreed story defines quote age <=60 seconds (or capture age when provider gives no quote time).

Groww exposes no quote timestamp. The implementation sets `quote_time=""`, `age_basis="capture"`, but **does not compute/store `quote_age_seconds` and capture-based age is effectively zero by construction**. More importantly, a quote from the direct bid/offer fields is considered valid without any market-data freshness evidence: `quote_validity` only checks same-day last-trade time when `book_source == "depth"`. A direct-field book with an old/missing last-trade time passes. Thus “capture-based age” measures API response latency, not age of the exchange quote and cannot establish the story's freshness requirement.

**Required rule:** because Groww supplies no quote timestamp, do **not claim a <=60s quote age**. Keep `quote_time` empty and `age_basis=capture/no_provider_timestamp`, but add an explicit conservative freshness proxy applicable to *all* Groww books: require a same-trading-day `last_trade_time` for validity (and preserve it), while clearly labelling this as “market active proxy, quote age unknown,” not proof the book is 60 seconds fresh. If the provider supplies neither quote timestamp nor same-day trade evidence, mark the quote invalid for executable-paper-fill use. Prefer a provider/source with exchange quote timestamps if one becomes available. Update the A4 story accordingly; E1 must not interpret these Groww rows as proven <=2-minute-old exchange quotes. Add tests for direct fields with missing/previous-day trade time.

This is conservative but honest. A last trade today still does not timestamp the bid/ask; A4 can collect spread history, while forward paper execution must carry the `quote_age_unknown` limitation unless better timestamped data is available.

### AC3 — PASS
Complete canonical rerun writes nothing; incomplete attempts retry in-window and remain immutable. Test covers both.

### AC4 — PASS
Weekend is explicit. Holiday is inferred fail-closed when no recorded contract traded that day; test covers this. This is adequate for A4, although using the A1 calendar later is preferable.

### AC5 — PASS
Recorder depends only on market-data provider methods and tests include a provider order method that would fail. Credential isolation fix is also appropriate.

### AC6 — PASS
Report uses canonical snapshots and valid quotes, with median, p90, invalid share and counts by distance band. Unit evidence covers calculation path.

### AC7 — PASS
Partial failures are immutable/incomplete, retried in-window, and canonical becomes `none` after the window. Test covers this.

### AC8 — PASS
Code/docstrings/report explicitly identify snapshots as quotes, not fills.

**A4 verdict: FAIL (AC1, AC2).**

## B4 — Ledger guard

### AC1 — FAIL
The guard refuses an absent row and an uncommitted *new* row before data access. But it does not prove that the **current contents of an already registered ledger row are committed**.

`first_commit_containing("\n<trial_id>,", ledger.csv)` proves only that this trial ID was added sometime in history. After that, a working-tree edit can change the row's `protocol_commit`, `protocol_path`, `hypothesis`, `kind`, etc. `require_registered()` reads that uncommitted row and may accept it if the newly supplied protocol reference passes its separate checks. Therefore the current registration is not fully protected by git ancestry.

**Exact fix:** before accepting any trial, require `git diff --quiet HEAD -- research/ledger.csv` (and preferably index + working tree, e.g. both `git diff --quiet HEAD -- ...` semantics covering staged/unstaged as implemented) so the ledger used by the run exactly matches committed HEAD. Stronger: load the trial row from `HEAD:research/ledger.csv` and compare it byte/field-for-field with the working-tree row. Add a test: register/freeze a valid trial, then edit that existing row without committing; `require_registered` must refuse it.

### AC2 — PASS
`mark_run` only fills `first_run_on/run_commit` when empty; repeated call preserves the first values. Test covers it. Note that the eventual run workflow should commit this mutation as evidence, but that is outside this criterion.

### AC3 — PASS
Repository ledger contains 10 Experiment-1 rows and separately reports 8 hypotheses; test verifies it.

### AC4 — PASS
Rows 1–21 are preserved and marked retrospective. Test verifies IDs 1–31 and retrospective history.

### AC5 — FAIL
The test proves a referenced protocol commit outside run history is rejected, but the agreed criterion was that a trial's **registration commit** not ancestral to the run is refused. The implementation's pickaxe check normally catches a new-row branch, but because it does not bind the *current row contents* to that ancestral commit, the intended guarantee is incomplete.

The same exact fix as AC1 closes this: current ledger must equal committed HEAD, and the commit containing the registered row must be ancestral to run HEAD. Add an explicit divergent-registration-branch test plus the uncommitted-existing-row mutation test.

**B4 verdict: FAIL (AC1, AC5).**

## Three explicit questions

### 1. B4 deviation: is registration-before-protocol-freeze equally safe?
**YES, with the ledger-integrity fix above.**

I agree with Claude's deviation. Requiring both (a) the registration row to be committed before the run and (b) the frozen protocol commit to be an ancestor of the run, plus (c) the protocol file unchanged since freeze, is sufficient for the intended ordering. The protocol does **not** need to be frozen before trial registration. In this workflow that would be circular because the freeze intentionally records hashes of the completed B1–B4 engine.

Exact accepted ordering:

`trial registration commit -> [engine build] -> protocol/freeze commit -> challenge run commit`

Registration and freeze must each be ancestors of the run; the current ledger must be committed/unchanged; frozen protocol must be unchanged. The access attestation separately protects against looking at challenge outcomes before freeze.

### 2. Groww has no quote timestamp: accept capture-based age?
**NO as a statement of quote freshness.**

Accept recording `quote_time` empty and explicitly recording that the provider supplies no timestamp. Do **not** equate API capture time with exchange quote age. Use the conservative same-day-last-trade proxy described under A4 AC2 and label age unknown; E1 cannot claim a Groww book is <=2 minutes old solely because it was fetched within two minutes.

### 3. December expiry gap: use NSE expiry dates then Groww chain by date?
**YES.**

That is the right fix. Use the latest valid NSE derivatives listing/session source to discover the two monthly expiry dates, record source provenance/hash, then ask Groww's chain endpoint by explicit expiry date. Do not silently synthesize expiry dates from calendar rules alone. If NSE discovery is unavailable or stale, keep the attempt incomplete.

## Final judge decision

**FAIL; do not mark A4 or B4 done yet.** Four criterion findings need correction: **A4 AC1, A4 AC2, B4 AC1, B4 AC5**. These are narrow implementation/contract fixes, not a redesign.

After fixes, the re-check can be limited to these blockers and their changed code/tests.
