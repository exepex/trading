# Review 115 — E2c paper fills and accounts moved to Drive

**Reviewed:** `story/e2c-fills-to-drive` at **fecb99fc**; Response 161, E2c story, Claude Response 150 (including judge-159 answer), Judge 159 and addendum 1, and Review 105. **Reviewer:** ChatGPT, independent second reviewer under quality rule 9. **Overall: PARTIAL — the five-file recovery fix and public/private split are sound for the tested normal path; one normal-path stop-state error needs correction before merge.** Evidence labels follow `AGENTS.md`. Judge's 5,887-test run and 503 probes are reported evidence, not independently rerun here.

## Q1 — Drive 503, restart, overlapping runs, and push order: PARTIAL

**ACCEPT the upload order for entry recovery — strong evidence (code and judge's planted failures).** `fno/desk/private_files.py:ACCOUNT_FILES` uploads `desk_fills.csv`, `cash_ledger.csv`, `positions.json`, `equity_history.csv`, `desk_events.csv` in that order. A ledger fill without a desk fill can crash the reader; an `opened` event without its ledger fill can falsely tell the retry that entry completed. Uploading desk fills before ledger and the event last avoids both known failures. Judge 159 addendum 1 planted a 503 at each of the five uploads and reran in a fresh container: four ledger fills, four desk rows, one opened event and a readable position. This is stronger than simply trusting the builder's claim.

**PARTIAL on overall state correctness — strong evidence from code.** `DriveAccountSync.write` performs the private upload through the journal context and **then** calls `GitCommitter.commit(write_daily_totals(...))`. If Drive succeeded but Git fails, the private account has already changed and the public totals remain stale until a successful retry. The failure should alert (Git `CommitFailed`) and the next run's idempotent replay should reconcile it; this is a temporary, alerted inconsistency, not a silent money change. Add no transaction coordinator. Confirm one integration test for “Drive succeeds, Git push rejected, fresh-container rerun, totals reconcile” in the next normal failure suite.

**Known limit — reasoning only:** two concurrent daily-run containers could overwrite each other's Drive version because the lock is local. Only one daily routine is configured. Do not build distributed locking for a case that is not running.

## Q2 — Public reconstruction of fill/mark/cash: ACCEPT for current public artifacts (strong evidence for file placement; some evidence for cross-file coverage)

`private_files.py` keeps five account files and `private.json` in Drive; `daily_totals.py:COLUMNS` exposes only date, closed equity, open/closed trade counts and fill count. The builder's two-day fixture and judge's scan found no individual fill, quote, mid, open cash or marked-equity value in the committed paths. A worked result: initial closed equity ₹2,000,000.00, closed trade net −₹513.64 => published ₹1,999,486.36, with zero open and one closed trade; it does **not** reveal the two bid/ask quotes used on different snapshots. This closes Review 105's concrete `bid=2×mid−ask` path, because neither same-contract ask nor its marked mid is public from the account.

**Scope limitation — reasoning only:** this is not a proof that every future public output is non-reconstructive; the E2c story deliberately leaves E2b's derived decision mids in D3/C4 records and the signed-in dashboard can still display private marks. The test must continue scanning **all public committed files**, not just `journal/<book>/account/`, whenever a new publisher is added. No new privacy infrastructure now.

## Q3 — Block entries after missed exits, first day: PARTIAL (strong evidence)

**ACCEPT** the rule that a prior session without an `exits` step blocks new entries while today's exits still run. A failed Drive download before any run-log step is a real case: judge 159 reproduced the original bypass and addendum 1 verified the fix. The first-ever session must be allowed to open when no earlier run exists; otherwise a new paper book can never start.

**Remaining normal-path defect:** `fno/desk/daily_steps.py:review_exits` catches failures for **each book**, records `{reviewed: false, error: ...}`, and returns a completed **`exits` step**. The next day's `_stopped_before_exits` guard checks whether the step exists, not whether the book's exit review actually succeeded. Consequently a normal Drive failure during a book's exit can produce an `exits` step containing `reviewed: false`; tomorrow's new entries are allowed even though yesterday's risk-reducing exits were not reviewed. This is precisely the operational risk Review 105 point 3 intended to address, and it can change a trade and a stop decision.

**Exact small fix before merge:** in the existing next-day guard, treat a previous `exits` step with any book `reviewed: false` (or a `waiting` due to no valid snapshot) as an incomplete exit review, and block new entries until a successful subsequent exit review. The current day still attempts exits. Test: yesterday's Drive 503 in one book's `_review_book`, an `exits` step is logged with `reviewed: false`, today must open zero new positions and issue one alert. Do not add a separate watchdog.

## Q4 — What must change before merge? PARTIAL

**Required:** the one next-day guard correction in Q3. It affects actual new entries following a known class of Drive/exit failure. **Non-blocking:** confirm Git-after-Drive retry totals reconciliation; ensure the nine opening account files are uploaded or verified before `git rm --cached`; run `account show book1_rules` from a fresh checkout after migration. Keep the first-session exception. No real-order functionality is introduced.

## Financial-role cross-check

**Mathematician/statistician/quant modeller:** missing exits and stale totals alter the observed P&L denominator and selection of trading days; record unavailable days. **F&O/options/volatility trader and microstructure/execution:** missed exit review can leave risk overnight; no invented fill on retry. **Risk manager/portfolio/head of desk:** a completed log step is not equivalent to completed risk reduction; block new exposure until review succeeds. **Market research/macro/derivatives flow/equity/investment banking:** market events do not justify overriding an unresolved exit. **Regulation:** no real broker orders and private quote retention remains separate from public reporting. **Behavioural finance:** don't present a missed review as a safe NO TRADE. **Tax/cost accountant:** reconcile ledger charges and closed-equity totals after interrupted commits. **Data/backtesting engineer/red team:** test partial Drive upload, per-book exit failure, restart and public-value reconstruction.

## Final verdict

**PARTIAL / CHANGES REQUIRED before merge:** accept the five-file push order, the 503 recovery evidence and the privacy migration. Fix the **existing-step-but-failed-exit** case using the current guard and one regression test. This is a normal operational failure that can allow new paper trades while exits were not reviewed; it merits a change under the owner's simplicity rule. No broader redesign.
