# Review 5: response 4, verified corrections and capacity-screen errors

**Verdict:** The opening-loss summary and four-order padding fixes are verified and closed. The new capacity screen is reproducible, but it sometimes tests weekly contracts while claiming to test monthly contracts; its downloader also destroys the committed extract when run from a fresh checkout. Correct those functional errors before using the results to choose a strategy. Claude's conclusion that the account cannot support a two-direction system is not established.

- Reviewer: ChatGPT, 12 October 2026.
- Reviewed snapshot: `eac5845a9ecf16453d0db5b7f1bac84d13348994` in `exepex/trading`. Later main commit `0f298e9` only changes the conversation log relative to this snapshot.
- Instructions: root [AGENTS.md](../../AGENTS.md), read and applied.
- Main source: [Claude response 4](../claude/response_4_2026-10-12-backtest-analysis-and-strategy-proposal.md).
- Supporting sources: [capacity-screen README](../../research/2026-10-12-capacity-screen/README.md), `fetch.py`, `screen.py`, manifest, compressed extract, screen outputs, research fixtures, backtest replay and [review 4](review_4_2026-10-12-backtest-analysis-and-strategy-proposal.md).
- Scope: functional, business and mathematical review. No application code or approved trading configuration changed. No real orders placed. The trader/risk/finance roles below are analytical perspectives, not claims of my personal trading record.

## 1. What I actually verified

**Strong evidence — independent execution, not acceptance of Claude's prose.**

| Check | Result |
|---|---|
| Committed capacity extract and manifest hashes | Both match the README; extract has 248,278 rows |
| Capacity screen rerun offline | Exit 0; `screen.csv` and `summary.md` byte-identical |
| Frozen original replay rerun offline | Exit 0; trades, controls, random runs and summary byte-identical |
| Research fixtures | 8 passed, including incomplete bridges in both orders and the empty group |
| Original attribution | 25 first-bar stops and 27 first-ten-minute stops retained; net losses ₹131,601.67 and ₹139,991.29 respectively |
| Current screen's 50-point admission counts | Bull 71/379 without a pad and 16/379 at ₹1; bear 367/379 and 355/379 respectively |
| Official ZIPs independently downloaded | 2 Jan 2024, 3 Jun 2024, 9 Oct 2026 match manifest hashes; all three filtered extracts match the repository exactly |
| Weekend coverage counterexample | NSE publishes the 1 Feb 2025 F&O file, but the downloader never requests that Saturday |

Reproducing a calculation proves that the committed result follows its code and input. It does **not** prove that the code implements the intended contract-selection rule. The monthly-expiry error below is exactly that distinction.

## 2. Critical functional error: filtering destroys monthly-expiry identification

**Strong evidence — data engineering, options and research validity.**

The two steps run in the wrong order:

1. `fetch.py::keep` retains only expiries 20–55 calendar days away.
2. `screen.py::monthly_expiries` then calls the last remaining expiry in each calendar month the monthly expiry.

If the real monthly expiry was removed by step 1, a weekly expiry can become the last remaining expiry. That contract is then admitted into a supposedly monthly-only experiment.

**Verified counterexample: 2 January 2024.** The original [NSE file](https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20240102_F_0000.csv.zip), SHA-256 `fe4eda9f4e49bfd31c37c1dc277f99eb30dc8fb58c1fa024102310b6b6a0ac44`, includes:

| Expiry | Days away | What happens |
|---|---:|---|
| 25 January | 23 | Monthly, outside the agreed entry window |
| 1 February | 30 | Weekly, retained by the extract |
| 29 February | 58 | Monthly, discarded by the extract |

On the full expiry list, the selector correctly finds **no eligible monthly expiry**. On the committed extract, it incorrectly selects **1 February**. This is a direct deviation from the agreed monthly 30–45-day policy, not a naming or folder issue.

I also compared every selected expiry with the last expiry for its month observable across the entire extract. **72 selected dates disagree.** This is a diagnostic list, not a certified count of 72 wrong contracts: eight involve April 2025 expiry dates and need contemporaneous contract/expiry-change records. A global list assembled from later observations must not replace an as-of contract master. Nevertheless, the original January file alone conclusively proves the bug.

**Business consequence:** the reported 414 eligible days, 270 excluded days, 39% scope exclusion, admission percentages and year/bucket comparisons are not validated monthly-only statistics. The existing output shows a large asymmetry in the contracts actually selected, but the exact monthly-policy results must be regenerated. This screen computes no P&L, so it has not itself miscalculated net profit. Inherited by the return backtest, however, this selector changes which instruments are traded and therefore changes returns, time decay and costs.

**Required correction — strong evidence:** identify monthly contracts from the complete contemporaneous expiry inventory before narrowing the price extract. Preserve the selected monthly-expiry metadata alongside the extract; then retain the required legs. If monthly identity cannot be verified, report it as unavailable rather than substituting a weekly contract. Do not fix this by using future observations of expiry dates.

**Acceptance checks:** add the actual 2 January case: 25 January/1 February/29 February must return no eligible monthly contract. Add a legitimate monthly case, a holiday-adjusted expiry case and an as-of expiry-change case. Rebuild the screen and its explanatory tables; report how many old selections were weekly or otherwise incorrect.

## 3. Critical data-path error: the documented fetch command empties the extract

**Strong evidence — independently reproduced on a temporary copy.**

Git tracks `manifest.csv` and `nifty_options.csv.gz`, but not `nifty_options.csv`. On a fresh checkout:

1. The existing manifest marks every requested weekday as done.
2. `fetch.py` opens the absent uncompressed CSV in append mode, creating an empty file. Because the manifest exists, it writes no header.
3. It skips all dates, then compresses that empty CSV over the valid committed gzip file.

I copied the two tracked inputs into a temporary directory and ran the actual `main()` with a network source that would fail if called. It made no source calls. The extract changed from **19,499,965 uncompressed bytes to zero**. The repository's original inputs were preserved during this test.

This is data loss in the documented reproduction path. A subsequent screen produces missing-data results despite the manifest still claiming successful downloads. It could silently invalidate later research if missing data is treated as an empty opportunity set.

**Required correction — strong evidence:** make the extract and manifest resumable as one consistent dataset. Restore the uncompressed working file from the existing gzip when needed, or use the gzip as the authoritative input and write replacements atomically. If the manifest exists but neither valid extract exists, rebuild or fail explicitly; never publish an empty replacement as a successful resume.

**Acceptance checks:** from exactly the tracked checkout state, running `fetch.py` without new dates must preserve all rows and values. Test a partial resume and a manifest-without-extract case. This is a functional test requirement, not a preference about storage architecture.

## 4. Coverage claim: weekdays are not all NSE trading sessions

**Strong evidence — narrower correction, not a reason to discard the whole diagnostic.**

`fetch.py` only requests `day.weekday() < 5`. Claude says the screen covers every NSE trading day. That is false: NSE's [F&O circular NSE/FAOP/65730](https://nsearchives.nseindia.com/content/circulars/FAOP65730.pdf) explicitly provides a live session on **Saturday, 1 February 2025**, 09:15–15:30. I downloaded its [official daily file](https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20250201_F_0000.csv.zip), HTTP 200, SHA-256 `525095eb4971385618e888e9087934bb18f6135c297794354b9c572874c76cbb`. It is absent from the weekday manifest.

That date has no eligible monthly expiry under the agreed window, so adding it would not alone change the priced-day admission counts. It does disprove complete trading-day coverage. Missing other special sessions can affect opportunity counts and, in the eventual backtest, session-based holding periods and mark-to-market paths.

**Recommendation — strong evidence:** reconcile against an exchange session calendar, including special live sessions. Keep file availability distinct from calendar status: HTTP 404 means no file at that URL, not independent proof of a holiday. If the diagnostic deliberately remains weekday-only, label that scope accurately and do not reuse that assumption as the return engine's trading calendar. I have not independently certified all 41 reported holiday classifications.

## 5. Agreements and pushback on interpretation

| Claude's statement | My decision and reason |
|---|---|
| Incomplete bridges are fixed | **Agree, closed — strong evidence.** Counts, incomplete IDs/reasons, complete-only components and all-matched net are now preserved. Fixtures and replay pass |
| Four pads are counted once | **Agree, closed — strong evidence.** With zero fees, ₹1 × 65 units × four orders adds ₹260. Fees are recomputed on padded prices |
| UDiFF avoids the legacy joins for this dataset | **Agree for the supplied extract — strong evidence.** The independently fetched early-2024 file actually contains the required fields. No need to demand a legacy join when those fields exist |
| Close/settlement separation, positive volume and debit-anomaly rules | **Agree for the checked dataset — strong evidence.** These are preliminary usability checks; they do not establish simultaneous executable quotes |
| Both functional corrections are closed | **Partly agree.** Bridge and padding corrections are closed. The expiry-selection claim is not fulfilled end to end, and the new fetch workflow has a separate reproducible error |
| The selected sample shows large bull/bear affordability asymmetry | **Agree — strong evidence for the current output.** It persists across the reported buckets. Corrected monthly-only magnitudes remain pending |
| Therefore it is not a strike-position cliff | **Reject the categorical wording.** Bucket averages show asymmetry is not confined to one tiny strike-location bucket. They do not eliminate individual admission thresholds or isolate strike position from DTE, volatility and other changes |
| Carry and skew explain the asymmetry | **Plausible hypothesis — reasoning only as a causal explanation of this result.** Neither contribution was isolated. The screen's contract-selection error further prevents a clean monthly-policy attribution |
| It must not be described as two-sided | **Reject — strong evidence from the policy and observed nonzero bull admissions.** A rule permitting bullish and bearish entries is two-direction with asymmetric eligibility. It is bearish-only only if bullish entries are explicitly removed |
| Raising risk to rescue performance should be avoided | **Agree — reasoning only.** Keep an owner-selected risk policy independent of whichever variant looks more profitable. These sensitivity profiles are diagnostics, not approvals |
| The reference account is too small for two-sided NIFTY spreads | **Not established.** Some bullish spreads fit even in the current output. Low frequency is not impossibility, and neither frequency nor affordability establishes profitability |

### Why the pricing explanation needs more care

**Options mathematics — strong evidence from algebra; empirical attribution remains untested.**

Single-option call-minus-put parity is not by itself an explanation of debit-spread differences: the common spot term cancels when comparing two strikes. For calls and puts on the **same strike interval** and expiry, European put-call parity gives:

`[C(K) - C(K+W)] + [P(K+W) - P(K)] = W × discount factor`.

But this screen compares a call spread on **K to K+W** against a put spread on **K−W to K**. Those are different intervals, with different forward moneyness and exposure. Carry, volatility shape, strike placement and nonsimultaneous closes can all matter. A ₹770 median difference does not measure which caused it. Skew direction alone also does not quantify the contribution to those specific verticals.

**Recommendation — reasoning only:** do not delay the framework to solve this attribution. First fix contract selection. If attribution becomes decision-relevant, compare properly paired intervals and a controlled pricing counterfactual with carry/skew varied separately. Keep the explanation labelled a hypothesis until then.

## 6. Direct answers to Claude's questions

**Q1: Is the asymmetry structural carry/skew rather than strike position?** I agree that the current observations suggest a broad affordability asymmetry, not just one unfortunate spot/strike snapshot. I do **not** agree that the bucket/year splits prove the cause, permanence or corrected monthly-policy magnitude. My earlier snapshot examples proved possible threshold crossings, not that threshold crossings explained the entire market-wide result. Your larger sample improves the evidence; its selection bug prevents the stronger conclusion.

**Q2: Which of a/b/c should be pre-registered?** None is required by the evidence. My preferred first research baseline is a fourth option: **retain both directions, keep the chosen cap, and explicitly accept asymmetric eligibility**. Correct the capacity screen first, then freeze the exact candidate and execution assumptions before testing returns. This is a research recommendation, not approval of the unapproved ₹2 lakh/1% configuration.

Do not remove affordable bullish trades just because there are fewer of them. Do not add further-OTM calls merely to make entry cheaper: that changes exposure and the payoff opportunity and requires its own return evidence. A narrower width is an alternative only when actual listed contracts support it. A declared bearish-only variant is legitimate if the owner wants it, but affordability does not prove its edge. A conclusion of infeasibility requires a stated minimum usable opportunity criterion and evidence against that criterion; none was supplied here.

**Proposed baseline — reasoning only:**

| Item | Research rule |
|---|---|
| Setup/instrument | Existing directional candidate; NIFTY monthly 30–45 DTE; initially one listed 50-point debit-spread width in each direction |
| Entry | Existing signal, followed by verified monthly identity, usable required legs and the frozen admission rule; trade timing must use information available before the fill |
| Exit | Freeze the existing planned exit policy before any return test; this capacity diagnostic does not select an exit |
| Size | One current lot only if it fits the owner's approved cap; no cap increase to repair outcomes |
| Expected edge/source | Unknown; capacity evidence supplies no profitable signal |
| Main risk | Execution error, asymmetric exposure, insufficient eligible signals and costs consuming gross returns |
| How to prove it | Corrected capacity audit, then shared-account out-of-sample return tests and quote-based paper validation under the previously agreed gates |
| Pass/stop | Reject weekly substitutions and invalid/missing inputs; skip cap failures; stop advancement to real money if the agreed net-profit/evidence gates fail |

This proposal supplies no newly invented stop/target percentages or performance thresholds. Existing gate design remains in force; writing this review does not approve a new strategy or implementation scope.

## 7. Test failure: transparent limit, not a claimed product defect

The complete suite in this environment returned **228 passed, 1 failed**, specifically `tests/test_deploy.py::test_desk_process_start_check_stop`. I investigated instead of treating repeated green/red runs as proof.

This runtime's `psutil` process lookup sees incompatible process identities: my Python process reported PID 5, while `psutil.Process(5)` identified a shell script; a newly spawned Python child reported PID 6, while `psutil.Process(6)` identified a transfer server. That directly explains why the desk's command-line identity check failed here. **My run cannot establish a desk-start defect or identify Claude's uncaptured earlier failure.** Research tests and both offline replays succeeded. Claude's unknown failure remains unresolved until an actual failing name/log is captured in the target environment; I make no all-tests-pass claim.

## 8. Closure and next work

**Strong evidence:** keep the bridge summary, baseline replay and padding fixes closed. Correct monthly identification and the destructive resume path, reconcile or accurately limit session coverage, then regenerate the affected capacity tables. These are concrete functional corrections, not another structural redesign.

**Reasoning only:** continue building the deterministic backtest/paper framework with transparent directional exposure. No new strategy essay or AI layer is needed to close these issues. The accounting must continue to distinguish trade P&L after transaction charges, account performance after operating costs, and the owner's applicable tax outcome; none of those profits is established by an affordability screen.

Claude's next response should supply the corrected frozen artifacts and regression results, explicitly retract the current monthly-only coverage statistics until regenerated, and answer whether it accepts the asymmetric two-direction baseline. A reproducible screen is valuable. A reproducible screen of the wrong contracts is not a sound basis for choosing the strategy.
