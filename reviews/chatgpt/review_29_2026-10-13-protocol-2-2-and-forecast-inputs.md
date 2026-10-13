# Review 29 — Experiment 1 v2.2 holdout disclosure and forecast live inputs

**Date:** 13 Oct 2026  
**Reviewer:** ChatGPT, second reviewer  
**Repository / branch:** `exepex/trading` / `main`

**Overall verdict:**  
1. **Experiment 1 v2.2: AGREE with the disclosed G1-golden access recorded permanently; no new holdout is needed.** The golden file weakens the claim that challenge *inputs* were never computed, but it does not expose challenge outcomes/P&L, and it was created only after Experiment-1 rules were fixed. Changing the holdout now would introduce more researcher discretion.  
2. **Forecast protocol v2 interim live pack: CHANGE before adoption.** The architecture is right, but the cutoff must be enforced per input/quote, not by when the snapshot attempt “finished,” and the source of the 15:00 India VIX value must be explicit. The daily d-1 close download is a hard prerequisite for a live forecast.

Evidence labels follow `AGENTS.md`.

# 1. `response_61_protocol-2-2-written.md` — Experiment 1 v2.2 and the G1 golden-file disclosure

## Protocol v2.2 as written

**AGREE — strong evidence.**

The changes accepted in Review 28 are now the right rules:
- monthly expiry = same-expiry NIFTY future listed that day;
- 60 challenge cycles / 33 discovery cycles;
- Black-76 F1 on the same-expiry future;
- F1 thinner ATM leg volume >=10;
- nearest-rank C1 threshold;
- exact random generator/draw conventions;
- decision-day period / exit-day P&L year;
- fixed drawdown, losing-run and win-rate definitions;
- long debit >= width => `bad_prices`;
- P6 empty removed set cannot pass the event-filter claim;
- freeze recipe and pre-freeze access record;
- 30 Mar 2021 reader correction recorded before freeze.

The newly found code gap — the 10-contract rule was written but not implemented — had to be fixed before freeze. Response 61 says it was fixed; that is the correct action. The eventual freeze/judge must verify code and protocol match.

## Does G1's golden file weaken the Experiment-1 holdout?

**AGREE that it weakens pristine input blindness; REJECT the stronger conclusion that the holdout is invalid — strong evidence + reasoning only on remedy.**

### What was exposed

`research/forecasts/golden_iv30_rv20.csv` contains, for every panel session from 2019:
- IV30;
- trailing RV20;
- flags/expiries.

Those are **entry-known predictor values** over the Experiment-1 challenge period. They overlap materially with F1's ingredients:
- Experiment F1 uses ATM implied volatility minus trailing RV20;
- G1 golden exposes a 30-day ATM IV estimate plus trailing RV20.

So the statement “no 2019-2023 feature value has been computed” is no longer literally true. That must not remain in the Experiment-1 access attestation.

### What was *not* exposed

**Strong evidence from the file/protocol purpose:** the golden contains no future option exit price, strategy P&L, policy result, bootstrap result, pass/fail verdict, or target outcome. IV30 and trailing RV20 are known at the forecast date; they are not future outcomes.

It also does **not** equal Experiment F1 exactly:
- G1 IV30 interpolates/falls back across monthly maturities;
- Experiment F1 uses the ATM IV of the experiment's target monthly expiry on the decision day;
- the common RV20 component overlaps exactly in concept.

### Timing matters

**Strong evidence from repository history stated in Response 61:** the golden file was computed after all Experiment-1 policy rules, structures, controls, thresholds, F1 minimum-volume choice and pass/fail rules were fixed, and before challenge outcomes/P&L were viewed.

That is the key protection. Seeing a predictor after the hypothesis/rules are fixed cannot retroactively tune those fixed rules unless the team now changes them based on what it saw.

### Remedy

**AGREE: disclose and freeze; do not replace the holdout — reasoning only, supported by the chronology.**

Exact actions before Experiment-1 freeze:

1. In §10 access attestation, replace any blanket claim such as “no challenge feature value was computed/viewed” with the narrower truth:
   > Before the Experiment-1 freeze, G1 generated `research/forecasts/golden_iv30_rv20.csv` over 2019-2026. It computed IV30 and trailing RV20 for challenge-period sessions. These are entry-known predictors and overlap with F1's components, but no Experiment-1 F1 decision-day series, policy action, option outcome, trade P&L, control statistic or pass/fail result was computed or viewed from this work. The golden was generated only after the Experiment-1 rules and thresholds had been fixed.

2. Record the golden-file commit/hash and the date/order relative to the final rule-setting commits.

3. **Hard rule from now until freeze/run:** no Experiment-1 rule, F1 threshold, structure, policy, control or pass criterion may be changed in response to any 2019-23 golden value. A data/code correctness bug may be fixed, but it must be disclosed and independently judged before freeze.

4. Do not print/analyse challenge-period G1 golden distributions specifically for Experiment 1 before the run. Existing committed golden data can remain; deleting it would not “unsee” it.

5. In the final report, describe 2019-23 as a **historical holdout with limited pre-freeze predictor exposure**, not a perfectly untouched/blinded holdout.

### Why I do not recommend a new holdout

**Reasoning only.** There is no obvious second historical period with the same value:
- 2024-26 is already discovery.
- moving to another old period after this disclosure would itself be a post-hoc holdout choice;
- future paper trading is already the stronger untouched test and remains mandatory even if Experiment 1 passes.

Discarding 2019-23 would throw away the pre-registered challenge because entry-known inputs were computed after the rules were fixed, while providing no cleaner comparable historical replacement.

**Statistician / red-team verdict:** the holdout is weaker than “never touched,” but still valid for the pre-registered challenge if the chronology and exposure are disclosed exactly and no rules now move.

**Portfolio-manager verdict:** any pass remains only a gate to forward paper trading, never proof of live edge. This limitation makes that existing rule even more important.

## Experiment-1 item verdict

**AGREE, with the disclosure wording above required before freeze.** No new challenge period and no protocol redesign.

# 2. `response_62_g2-g3.md` — proposed G1 protocol v2 interim live input pack

## Need for an interim pack before E2

**AGREE — reasoning only.**

Waiting for E2 would waste months of forecast history. A small deterministic pack containing only inputs needed by the already-frozen forecast methods is the right root-cause fix. It should later be replaced by E2 without changing forecast semantics.

## Pack contents: A4 snapshot + closes through d-1 + session calendar

**CHANGE — strong evidence.**

The content is almost right, but “canonical A4 snapshot of d, used only if its capture finished by 15:00” is not a sufficient cutoff rule.

A snapshot attempt can span time. What matters is when **each market observation** was captured/known, not when the attempt was declared complete.

Exact rule:

> Every same-day field used by a 15:00 forecast must have its own `observed_at/retrieved_at <= 15:00:00 IST`. A canonical attempt completed after 15:00 may still contribute fields individually observed by 15:00, but no field observed after 15:00 may enter the pack. If a required same-day field lacks a trustworthy observation time at or before 15:00, that input is missing and the affected forecast is “no forecast.”

The pack manifest/hash must include each source field's timestamp/provenance, not just the aggregate file hash.

**Execution/data-engineer reason:** this prevents a 15:03 option/future quote from being smuggled into a nominal “15:00” forecast merely because it belongs to the day's canonical snapshot.

## Replacing d's close with the 15:00 NIFTY spot

**AGREE — some evidence / reasoning only.**

For live forecasting, the 15:00 spot is the correct point-in-time substitute for the unavailable 15:30 close. Using previous official closes plus today's 15:00 spot for trailing returns mirrors B7's live-F1 convention and avoids look-ahead.

But the protocol must name these live quantities differently from historical close-proxy quantities in records, e.g. `live_1500_proxy`, so later analysis never mixes them silently.

## Replacing d's VIX close with “15:00 VIX”

**CHANGE — strong repository evidence.**

The proposal must name the actual source and timestamp rule for India VIX at 15:00. A4 is a NIFTY monthly option/future quote recorder; do not assume it supplies a valid India VIX observation unless its schema/code explicitly does.

Exact rule:

> VIX(d) for a live 15:00 forecast comes only from a named India VIX source whose observation timestamp is <=15:00 IST and is included in the pack provenance. If no such value exists, any method requiring current-day VIX records “no forecast”; it must not use d-1 VIX as if it were current.

This is especially important for Q4 and the VIX statistical baseline.

## Baseline (a): IV30 from A4 mids and futures carry

**CHANGE — some evidence.**

Using live bid/ask mids is preferable to last prices, but the pack must be capable of constructing the same estimator honestly.

Exact conditions:
- both ATM call and put need valid two-sided quotes for each expiry used;
- use midpoint `(bid+ask)/2`;
- quote observation time <=15:00;
- same-expiry future input time <=15:00;
- preserve the existing monthly-expiry rule;
- preserve interpolation/fallback/flag semantics;
- if the required bracketing expiries/legs are absent from A4's captured universe, do not silently change the estimator: flag/fallback exactly as the protocol says or return no IV30.

**Volatility-trader reason:** changing from historical traded closes to live mids is expected for a live cutoff, but maturity/ATM/flag behavior must stay the same so only the price observation changes.

## Closes through d-1

**AGREE, and this is a hard prerequisite — strong evidence.**

Response 62 correctly identifies that the repository currently stops at 12 Oct. A live base rate/HAR/VIX model cannot honestly run on a stale history window.

Add the daily NSE index-close download as a prerequisite of live capture:
- archive the official d-1 file through the existing raw-store/revision/fingerprint path;
- before forecasting on d, verify history is complete through the latest prior session;
- if not, affected methods return “no forecast” and the run reports `history_stale`; never forecast from a silently stale window.

This is not optional operational polish; it is part of point-in-time correctness.

## Pack hashing

**AGREE with expansion — strong engineering evidence.**

Hash the canonical serialized pack and commit the hash with every forecast record. The pack must include:
- session/date/cutoff;
- source IDs/commits/hashes;
- per-field observation/retrieval times;
- previous-close coverage-through date;
- A4 snapshot/attempt ID;
- values actually supplied to the forecast method.

This lets a judge reproduce the exact input rather than merely prove that some source file existed.

## Golden values unchanged

**AGREE — strong evidence.**

Protocol v2 should not rewrite the historical golden values merely to support live inputs. Historical close-proxy behavior and live 15:00 behavior are two explicitly labelled input modes of the same forecast definitions.

Add fixture/golden tests for the **live pack transformation** separately. Do not mix live 15:00 proxy values into `golden_iv30_rv20.csv`, whose purpose is to lock historical panel behavior.

## Deadline 15:30

**CHANGE — reasoning only / integrity concern.**

A 15:30 commit deadline is operationally convenient, but commit time is not the evidence that the forecast was made before seeing the close. The decisive controls are:
1. every input in the pack is cutoff-safe <=15:00;
2. forecast output is generated from that immutable pack;
3. the output/pack are written before any process can ingest d's official close.

I recommend a **15:15 IST forecast-generation/receipt deadline** (after the A4 capture window, before close) and allow the Git push/commit to finish later. Record a signed/run timestamp from the Actions run plus the pack hash. If the project keeps 15:30 as the Git commit deadline, it must not be used as the anti-look-ahead proof.

**Reason:** at 15:30 the target day's official close is becoming available; relying on mutable Git committer time is weaker than enforcing the data boundary in the computation itself.

## IV30 flag in `method_or_version`

**CHANGE — reasoning only.**

Do not overload `method_or_version` with data-quality state if protocol v2 can evolve the schema cleanly. Add a dedicated optional field such as `input_quality` / `iv30_status = interpolated | flagged | none` to v2 records.

Method/version identifies the forecaster. Input quality identifies the day's data. Combining them makes grouping/version analysis unnecessarily brittle.

Because this is explicitly a **new protocol version**, a schema version bump is the right time to separate these concepts.

## Freeze semantics for v2

**AGREE — strong evidence.**

Version 1 remains immutable. Version 2 should be a new protocol/freeze, registered before its first live forecast. Do not amend v1 in place. Freeze:
- v2 protocol;
- live-pack schema/transformation code;
- forecast code it owns;
- live-pack fixture/golden behavior.

Shared raw readers remain behavior-tested rather than byte-locked, consistent with judge 47.

## Forecast-input item verdict

**CHANGE before protocol v2 is written/frozen.**

Required changes:
1. per-field <=15:00 observation cutoff, not “snapshot completed by 15:00”;
2. named timestamped India VIX source or no forecast;
3. exact validity rules for live-mid IV30/futures inputs;
4. daily d-1 closes completeness is a hard gate;
5. pack contains/hash-covers field-level provenance and coverage;
6. live 15:00 proxy mode is labelled separately from historical close-proxy mode;
7. use a dedicated IV30/input-quality field in v2 rather than overloading method/version;
8. do not use a 15:30 Git commit timestamp as the anti-look-ahead control; generate/receipt-lock the forecast before the close (recommended 15:15) and treat later Git push as transport.

# Final decisions

| Item | Verdict | Evidence |
|---|---|---|
| Experiment 1 v2.2 rules as written | **AGREE** | **Strong evidence:** code/protocol conventions and judged cycle identity align. |
| G1 golden predictor exposure over 2019-23 | **AGREE to disclose and retain holdout** | **Strong evidence** on what the file contains and chronology; **reasoning only** on remedy. It exposes entry-known predictors, not outcomes/P&L, after rules were fixed. |
| New historical holdout/remedy | **REJECT** | **Reasoning only:** no cleaner comparable period; choosing a new one now adds post-hoc discretion. Forward paper remains the untouched test. |
| Interim live forecast pack | **CHANGE** | **Strong evidence:** cutoff/source/history gaps above must be explicit for point-in-time validity. |

No real-order behavior is approved or introduced by this review.
