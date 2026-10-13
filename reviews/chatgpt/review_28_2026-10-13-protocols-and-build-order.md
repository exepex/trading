# Review 28 — protocols and build order

Date: 13 Oct 2026  
Reviewer: ChatGPT, second reviewer  
Repository: exepex/trading, main

Overall verdict: CHANGE before either protocol is frozen and before BUILD_MAP is final. Experiment 1 v2.2 is substantively ready with one documentation tightening. G1 has good targets and estimators, but its 45-test confirmatory family is too broad for the stated three-book question and realistic six-month sample. The thin-slice idea is right, but runtime UI states and dependency order need corrections.

Evidence labels follow AGENTS.md: strong evidence = repository code/data/tests or mathematical identity; some evidence = measured but limited data; reasoning only = design judgement.

# 1. response_55 — Experiment 1 protocol v2.2

## Monthly-expiry identity

AGREE — strong evidence.

Use this rule: an option expiry is a NIFTY monthly expiry on day D iff a NIFTY index future with that same expiry is listed on D.

Judge 46 independently reports 60 challenge cycles, 12 per year for 2019-23, and 33 discovery cycles for 2024-26. That matches section 3's intended one opportunity per actual monthly contract. The old >50-day first-listing heuristic demonstrably admitted weeklies in the older regime: response 48 found 216 decision days instead of about 60.

Exact section 3 text I recommend:

> One opportunity per NIFTY monthly expiry. Point-in-time monthly identity on day D: an option expiry is monthly iff a NIFTY index future with the same expiry is listed on D. The rule uses listings available on D only. The measured pre-freeze cycle count is 60 for 2019-2023 and 33 for 2024-09 Oct 2026; these counts use dates/listings only, not outcomes.

Do not retain the 50-day rule as a fallback.

## Response 48 items 1-7

1. Black-76 F1 on the same-expiry NIFTY future: AGREE — strong evidence. The repository measurement is material: ATM 22,350 call/put IV differed by 0.04 vol points under Black-76 versus 2.00 under spot Black-Scholes. F1's sign drives P4/P5/P6/P8. Freeze the rule that the future itself must have traded; no settlement substitution.

2. C1 95th percentile nearest-rank index 9,499: AGREE — strong evidence. It is an exact reproducibility convention; equality remains a fail.

3. Exact NumPy draws, seed, shape/order and NumPy version: AGREE — strong evidence. A seed alone does not uniquely define the experiment.

4. Period by decision day, P&L/year by exit day: AGREE — reasoning only. It is coherent and must be fixed before results.

5. Drawdown, losing-run and win-rate definitions: AGREE — strong evidence for reproducibility. Keep zero P&L ending a losing run explicit.

6. P6 empty removed set fails; F2 warm-up: AGREE — strong evidence. An empty removed set sums to zero and cannot prove the event filter adds value. A10/judge 34 closes the F2 warm-up blocker.

7. Freeze recipe: AGREE — strong evidence. The protocol/freeze/ledger ancestry sequence is reproducible and consistent with B4.

## Long debit >= width = bad_prices

AGREE — strong evidence, mathematical identity.

For a long iron fly with wing width W, terminal gross payoff is capped at W per unit. If entry debit is >= W before charges and pads, positive terminal gross profit is impossible; after costs it is worse. Keep exit bound anomalies report-only and never silently repair prices.

## F1 minimum traded volume = 10 contracts

AGREE — some evidence.

Ten is not a scientifically proven liquidity threshold, but it is a defensible pre-freeze quality floor. The measured exclusions are: >0 loses 8/59 challenge days; >=10 loses 10/59; >=50 loses 21/59; >=100 loses 24/59. >=10 loses zero discovery days. It removes the most fragile 1-9-contract prints without deleting a third or more of the challenge, and it was selected from volume/listing counts rather than challenge P&L.

Exact rule: the thinner ATM call/put volume must be >=10 contracts. Below 10 means F1 = None; never substitute settlement.

## 30 Mar 2021 reader change

AGREE — strong evidence, with one required documentation change.

Restoring NSE's 30 Mar 2021 NIFTY/VIX closes before freeze is a legitimate data-reader correction. It can change trailing-close feature availability; no challenge P&L was viewed.

CHANGE required in the final v2.2 freeze/access record — strong evidence. Explicitly record:
1. the reader revision commit named by response 55;
2. that 30 Mar 2021 NIFTY/VIX closes became available;
3. that this changed feature availability for the 12 Apr 2021 decision cycle;
4. all challenge access since v2.1: listing-date counts and ATM volume/OI counts, with the statement that no challenge option price, feature value or P&L was computed/viewed.

Experiment 1 verdict: CHANGE only this documentation point, then AGREE to freeze. I do not reopen the accepted Black-76, C1, randomization, accounting-period, drawdown, P6, debit-width, F1-volume or futures-monthly conventions.

# 2. response_57 — G1 forecast protocol

## Targets

AGREE — reasoning only, with strong evidence that code/tests implement the written targets.

The five questions measure different things: direction; large move; realised-volatility regime change; VIX direction; and realised versus implied volatility. Q3 and Q5 are not duplicates.

Strict ties = no and simple return for Q2 are acceptable because they are frozen before outcomes.

## Trading days

AGREE — reasoning only.

Use the F&O project's A7/B1 convention consistently: special weekend sessions count; muhurat-only sessions are excluded. The dashboard's separate 250-session convention should be documented but does not justify changing this research protocol.

## IV30 interpolation

AGREE — strong evidence / standard construction.

Total-variance interpolation between monthly expiries is preferable to linear volatility interpolation. Reusing the Black-76 implementation shared with F1 is correct.

## IV30 single-expiry fallback

CHANGE — some evidence.

Flagged IV30 days should not enter Q5's primary inferential score. The protocol says Q5 is about 30-day ATM IV, while a single expiry nearest 30 is an approximation. 258/1,922 historical days, about 13%, are flagged and are concentrated in 2019-20, so the approximation is regime-dependent.

Exact rule:
- Q1/Q2 risk-neutral baseline may use flagged IV30 if the flag is carried and flagged/unflagged sensitivity is reported.
- Q5 primary outcome/comparison is void when IV30 is flagged or missing.
- Q5 on flagged fallback days is a separate descriptive sensitivity and never enters its confirmatory p-value.
- Keep the flag rate visible.

This gives up sample size honestly rather than mixing estimator error with forecast skill.

## Risk-neutral baseline

AGREE — reasoning only.

The lognormal risk-neutral baseline for Q1/Q2 is simple, reproducible and correctly labelled risk-neutral rather than real-world. Sparse historical far strikes make a smoothing-sensitive Breeden-Litzenberger density a poor first baseline. No risk-neutral baseline for Q3-Q5 is reasonable.

## Historical base rate

AGREE — reasoning only.

750 resolved earlier days, minimum 500, is conservative and point-in-time. The key anti-look-ahead condition is that the target was resolved before the forecast cutoff.

## Statistical baselines

AGREE — some evidence / reasoning only on model choice.

HAR-type RV and simple VIX mean reversion are defensible low-complexity baselines. Monthly refitting is a good compromise. The residual empirical distribution must remain training-window-only, as written.

## Book 1 = mean of two baselines

AGREE — reasoning only.

A fixed average is a legitimate rules-only ensemble. Continue to report each component separately so any ensemble benefit is visible.

## Brier, log score, calibration

AGREE — strong evidence for reproducibility.

Brier is the right primary binary-probability score. Clipped log score is useful descriptively and calibration is necessary to expose overconfidence.

## Multiplicity: 45 Holm tests

CHANGE — reasoning only, but important.

The 45-comparison family is valid but poorly matched to the practical question at the first six-month review. About 125 daily forecasts with 20-day overlapping targets contain only roughly six non-overlapping 20-day spans. The moving-block bootstrap acknowledges that dependence; it cannot create more independent information. Holm's first threshold over 45 tests is 0.05/45 = 0.00111. This is likely to make the protocol say "no significant difference" even for a practically useful book advantage.

Exact change: freeze two layers.

Primary confirmatory family — 10 tests, answering the book question:
- for each of five questions, Hybrid Book 2 vs Rules Book 1;
- for each of five questions, AI Book 3 vs Rules Book 1;
- same Brier difference, L=20 moving-block bootstrap, B=10,000 and centred two-sided p-value;
- Holm FWER 5% over these 10 tests;
- minimum 40 paired dates remains;
- no significance claim before six months remains.

Secondary/exploratory:
- Book 2 vs Book 3;
- each book vs each baseline;
- log score and calibration;
- report effect sizes and intervals, but do not call these version-1 confirmatory significant.

Book 1 vs base rate is not a sufficient primary family because it does not answer whether Hybrid or AI separates from Rules.

Even with 10 tests, six months can legitimately be inconclusive. Six months is the first review, not a deadline to choose a winner.

## Can G1 separate Rules, Hybrid and AI in a realistic number of days?

CHANGE / qualified answer — reasoning only.

It can detect a large difference within months, but it cannot promise a reliable ranking in about 125 days because targets overlap heavily. The current 45-test family makes separation especially unlikely. The proposed 10-test primary family aligns the inferential burden with the actual question, but inconclusive remains a valid six-month result.

Forecast significance must never promote a trading book; the protocol correctly says trade profit decides.

## Freeze and golden values

AGREE — strong evidence.

Judge 47's correction is right: freeze behavior/golden outputs, not shared-library bytes for months. Keep the IV30 flag in the golden contract because the primary Q5 rule above depends on it.

G1 verdict: CHANGE before freeze: (1) flagged IV30 days are descriptive only for Q5, and (2) replace the 45-test confirmatory family with the 10-test primary family above. Everything else can remain.

# 3. response_59 + docs/BUILD_MAP.md

## Question 1 — contract as the meeting point

CHANGE — strong engineering evidence / reasoning only on exact shape.

Contract-first is correct, but fields/types/examples/publisher are not enough to prevent drift. Every screen-block contract must also define:
- schema version and compatibility rule;
- required versus nullable fields;
- units/currency and enums;
- as_of, cutoff, built_at, source/provenance/commit;
- freshness/staleness semantics;
- machine-readable empty/error reason codes;
- producer identity;
- point-in-time versus latest semantics;
- breaking-change rule.

Add producer and consumer contract tests against the same schema. Backend publication validates; dashboard parser/fixture validates; CI fails if either side changes the contract alone. Reuse P1's contract/version pattern instead of creating another system.

## Question 2 — three block states

CHANGE — strong operational reasoning.

A test saying "every figure traces to a field or block is empty" is necessary but not enough. Production must distinguish current data from old real data after a failed refresh.

Runtime states should be:
1. real/fresh;
2. real/stale-or-failed, showing last real data plus as_of and reason;
3. empty, with machine-readable reason and expected/checked date.

"Example" is not a runtime state. It exists only in mockup/design files.

Add a production guard: runtime schemas/API have no example state; production build/test fails if mockup/example fixtures are imported into runtime publication; every rendered number traces to publication/source metadata.

## Question 3 — forecast contest before paper trading

CHANGE — reasoning only.

Start the forecast clock before paper trading: AGREE. Forecasts carry no money risk and need calendar time, so G1/G2/G3/G4 should start as early as their real inputs permit.

But do not make completion of the whole three-book forecast contest a prerequisite for Book 1 paper trading. Once B5 produces an approved strategy and Book-1 paper prerequisites pass, Book 1 should start paper evidence even if F1/G5 for AI books are still being built.

Exact order:
- start G1 -> G2 -> G3/G4 early;
- run Slice 2 Book-1 forecasting continuously;
- in parallel, proceed to Slice 3 Book-1 paper trading as soon as B5/D/C/E prerequisites pass;
- add Books 2/3 forecasts when F1/G5 exists;
- common-start three-book comparisons begin only when all compared books are ready.

This starts both slow clocks early instead of serializing them.

## Question 4 — done means end to end

AGREE with one map correction — strong engineering reasoning.

A user-facing slice is done only when real source -> producer -> contract -> publication -> real screen has been checked end to end by the judge.

BUILD_MAP currently calls Slice 0 "Data foundation" while its "First real thing on screen" is none. Either:
- call Slice 0 a foundation/prerequisite, not an end-to-end slice; or
- give it a real data-health/coverage screen.

Do not weaken the end-to-end definition to make Slice 0 fit it.

## Question 5 — gaps / missing stories

CHANGE — strong repository evidence.

The listed gaps are not complete, and one is probably duplicated.

Missing story:
1. Manual paper-account backend/read model. BUILD_MAP itself marks Home "your paper account (Manual account story)" as gap, but Next actions omits it. Add the story or explicitly remove/defer that block.

The proposed option-chain read-model story is justified for screens 32 and 35.

FII/DII download story is justified if A8 participant OI does not provide the cash-market flow series the screen means. Name the exact dataset; do not conflate participant derivatives OI with FII/DII cash flows.

India VIX history download: CHANGE / do not create a duplicate generic story. A3 already reads India VIX daily closes and A10 supplies the 2018 warm-up. If the screen needs a different VIX dataset, intraday history, or a separately published read model, name that exact missing artifact. Otherwise this is already data-covered and only needs a publishing/read-model story.

F&O news download: justified only after its exact source, point-in-time availability rule, archive/revision behavior and consuming screen/role are named. Do not create a vague "news" story.

Also add the Forecast-screen contract/read-model explicitly if P1/P2 do not already contain every G4 field the signed-off mockup needs; do not let a mockup become the contract.

## BUILD_MAP final verdict

CHANGE.

The thin end-to-end slice strategy is correct. Required changes before treating the map as final:
- strengthen contracts with version/provenance/freshness/null/error semantics and shared producer-consumer tests;
- make stale real data an explicit production state; Example stays mockup-only;
- start forecasts early but do not block Book-1 paper trading on completion of AI forecast books;
- classify Slice 0 as foundation or give it an end-to-end screen;
- add the missing Manual-account backend story;
- avoid duplicating existing India VIX history work; name the actual missing VIX artifact;
- define FII/DII and F&O-news datasets precisely before writing those stories.

# Final decisions

| Proposal | Verdict | Main reason |
|---|---|---|
| Experiment 1 v2.2 | CHANGE, then AGREE | Financial/statistical conventions are sound; freeze/access record must explicitly include the reader correction and all pre-freeze challenge metadata access. |
| G1 forecast protocol | CHANGE | Q5 fallback contaminates the primary target; 45-test Holm family is too broad for the actual three-book question and realistic six-month information. |
| Thin-slice BUILD_MAP | CHANGE | Core idea is right; contracts/states/order and missing-story list need the exact fixes above. |

No real-order behavior is proposed or approved by this review.
