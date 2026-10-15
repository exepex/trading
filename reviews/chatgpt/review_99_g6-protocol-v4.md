# Review 99 — G6 forecast protocol v4 (commit 3aa7818)

**Reviewer:** ChatGPT, independent second reviewer (statistician, quant, volatility trader, risk manager, data engineer and judge). **Date:** 15 October 2026 IST. **Branch:** `story/g6-protocol-v4`. Reviewed `reviews/claude/response_99_g6-protocol-v4.md`, `research/forecasts/PROTOCOL_v4.md`, G6 story and executable bootstrap implementation. The owner has confirmed choices A–C; judge 98 addendum 1 reportedly passed. Evidence labels follow `AGENTS.md`.

## Verdict: CHANGES REQUIRED

The protocol is unusually precise and many choices are defensible, but **two statistical validity defects must be fixed before freeze**. A passing test suite establishes that code matches the written formula, not that the statistical claim is valid.

### 1. Bootstrap p-value is not a valid one-sided null test as written — CHANGE (strong evidence: algebra and code)

`bootstrap.py:one_sided_test` computes `hits = count(means - observed <= observed)`. Let `D` be the observed mean and `D*` a resampled mean. This compares `D* - D <= D`, equivalently **`D* <= 2D`**. That is the intended centred-bootstrap test statistic, but a moving-block bootstrap of raw observations does not automatically produce a valid null distribution for every serially dependent process, especially with small n and overlapping targets. More importantly, the protocol gives no test of calibration/type-I error under realistic dependent nulls.

**Exact change:** before using a p-value as a confirmatory claim, add a pre-registered null simulation with at least 1,000 synthetic series each for independent and overlapping/AR(1) loss differences (true mean zero), at the minimum sample n=2L and at a realistic n (e.g. 125), and check empirical rejection frequency at the actual Holm/alpha-split thresholds. If it exceeds nominal beyond a declared Monte Carlo tolerance, use a studentized block bootstrap or a conservative HAC-based confirmatory test specified and re-reviewed **before any v4 score**. The current deterministic rebuild tests are necessary but not sufficient.

**Why blocking:** the project makes a family-wise claim of forecast skill; the size of the component test must be defensible, not just reproducible. This is a validation requirement, not an invitation to choose a method after seeing market outcomes.

### 2. Futility inference does not account for multiple sequential looks — CHANGE (strong statistical reasoning)

The 0.02/0.03 split explicitly controls false **positive** claims across two looks, but the stop rule can also issue a final **futility** NO at look 1 based on a one-sided 95% bound, and again at look 2 for still-open members. `PROTOCOL_v4.md` §5.5 says the intersection-union argument means “every member futile” at 5% per member; that addresses multiplicity across members **at one fixed look**, not optional sequential decisions over two looks.

**Exact change:** give futility its own predeclared two-look error allocation, for example one-sided 97.5% upper bounds at each of the two looks (Bonferroni 2 × 2.5% = 5%), or an anytime-valid upper confidence sequence. Use the same paired gate data, ratio estimator and fixed resampling method; change the nearest-rank quantile accordingly and add golden tests for both looks. If a member is final at look 1, record that; if still open, the second bound uses its preallocated error. Do not confuse the significance alpha split with futility error control.

**Why blocking:** the design's “NO” is consequential: it can switch off the research programme. An underpowered false-futility decision is exactly what the owner's three-way stop rule was meant to prevent.

### 3. Confirmatory family of 15 — AGREE (reasoning only)

The 15 members are V1, V2, V6a, V6b and V7 across rules/hybrid/AI. V3/V5/V4 remain descriptive, not confirmatory. This is a legitimate **predeclared scope choice**, not a claim that those targets are unimportant. The excluded questions must never be promoted by unadjusted significance claims. G6's explicit fixed member ordering, p=1 for absent/closed members and one version per slot are appropriate.

### 4. Two looks at 0.02/0.03 — AGREE for positive claims (strong evidence: Bonferroni bound)

Splitting the 5% family-wise positive-claim budget across two scheduled looks is conservative and defensible. A claim finalized at look 1 stays closed. Owner's confirmed A and B choices remove the governance ambiguity. The same split does not automatically control futility; see finding 2.

### 5. Premium-adjusted EOD IV30 proxy — AGREE with explicit limitation (some evidence)

Using the first-archived 2024-onward EOD option panel to estimate the premium ratio is preferable to leaving V2 unjudgeable until late 2028. It is labelled a close proxy and uses resolved training windows only. But **EOD close-proxy calibration may not transfer to 15:00 IV30**, so report the paired 15:00-versus-EOD ratio drift as forward diagnostic and never treat that proxy as proven equivalent. Owner's confirmed C permits the method, not a claim of equivalence.

### 6. V4 dimensional conversion and V5 settlement — AGREE (strong evidence on arithmetic and explicit source rules)

The golden V4 example matches the specified integrated-variance comparison, including the 7- versus 9-calendar-day case. V5 uses the frozen expiry's final NSE F&O settlement and rejects early/wrong-date substitutes. Those are appropriate reference contracts, subject to the judge's actual test evidence.

### 7. Session set and base rates — AGREE (some evidence)

Excluding special sessions is a disclosed difference from G1 v3. The measured 100/2409 and 331/2405 counts are reproduced by repository tests according to the builder; no new profitability inference follows from those base rates.

### 8. QLIKE and 3% effect gate — AGREE (strong mathematical evidence)

`ln(f)+RV/f` is defined for RV=0 and paired differences match textbook QLIKE for RV>0. The minimum-effect gate uses the same RV>0 paired dates for numerator and denominator; significance retains zeros. The owner confirmed the unit. Strictly positive baseline loss is enforced for the ratio.

### 9. Power report — AGREE with limitation (reasoning only)

The 60-outcome projection is planning information, not an inferential verdict. Reporting effective n/horizon is a rough heuristic, not a substitute for the actual block-dependent sampling distribution; do not promise a settle date from it.

### 10. Freeze and separation from G1 — AGREE (strong evidence from specification)

G1 v1–v3 remain frozen; G6 has no freeze or counted outcome yet. Waiting for G7/G8 code and recording hashes/ledger registration before first scored v4 forecast is correct. Owner A–C confirmations and judge PASS are prerequisites, not substitutes for the two statistical corrections above.

## Final decision

**CHANGES REQUIRED** before G6 v4 freeze. Fix the confirmatory bootstrap's empirical null calibration and the two-look futility error budget, with independent golden/negative tests. Then re-review only these changes. This review approves no trading edge, real order, or frozen v4 result.
