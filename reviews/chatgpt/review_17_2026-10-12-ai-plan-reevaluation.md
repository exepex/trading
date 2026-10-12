# Review 17 — judge validation of AI plan re-evaluation

**Date:** 2026-10-12  
**Reviewer / role:** ChatGPT, independent judge  
**Reviewed on `main`:** `reviews/claude/response_19_2026-10-12-ai-plan-reevaluation.md`, `docs/AI_PLAN_REEVALUATION.md`, old `docs/AI_DESK_PLAN.md`, `docs/WAVES.md`, approved implementation stories, and running code including `fno/brief.py`, `fno/live/runner.py`, deployment watchdog, news/shock/kill-switch paths.  
**Verdict: CHANGES REQUIRED.** The reevaluation is mostly correct, but **D1-D5 are not a complete conflict list**, two item verdicts are too permissive, and **G4 duplicates E4 instead of being a genuinely new story**. G1-G3 are justified with scope tightening. **Confidence: strong evidence for code/document contradictions (repository sources); reasoning only for product recommendations.**

## 1. Verdicts in the comparison

### Correct verdicts

I agree with these classifications:

- Pre-market strategist as a decision stage: **superseded** by the once-daily 3 pm approved desk.
- Live per-candidate AI authority: **conflict**.
- Automatic AI news exit: **conflict**.
- Post-market grading: **covered in part** by E3/F4; lessons are not explicitly covered.
- Plain-English AI narrative: **not covered by E2**; optional gap is real.
- Weekly AI researcher: research mechanics are covered, scheduled AI meeting/orchestration is not.
- W1.1 fills: superseded by A4/E1 for the new desk.
- W2.1, W2.2, W3.2 and W1.4 as old intraday-option-buyer rules: **superseded** for the new desk.
- W1.3 family/concentration concept: adequately subsumed by C2's portfolio-level risk controls for the new NIFTY desk.
- W2.3 positioning data: **keep as research input/candidate**, not as an untested live signal.
- W3.1 shock detector: not part of the new 3 pm desk unless separately proven.
- Facts/code, no-lookahead and AI role scoring: covered by the approved design/stories.
- Old strategy-development process: superseded by the ledger/freeze/challenge/judge/owner/paper process.
- Old self-merging decision-rule authority: conflict with D1/playbook governance.

### Verdict that is wrong / too permissive #1: “Groww prices + fast news watcher = keep (old desk)”

For the **new desk**, “superseded” is correct. For the **old desk**, saying “keep” before D3 is decided is too permissive because the running old desk is not passive data infrastructure. `fno/live/runner.py` is a long-lived scanner/entry/exit service; the deployment watchdog explicitly starts `python -m fno live run` every five minutes if absent. Waves 0/3 wire fast news into `news_shock`, `adverse_news` exit and shock-driven trade rechecks.

**Exact classification:** **conflict / quarantine pending D3**, not “keep (old desk).” The reusable news/data collectors may be kept as components, but the old live orchestration must not remain enabled by implication.

### Verdict that is wrong / too permissive #2: “stock tool verified news = keep; F1 input”

The read-only source may be useful, but F1 currently requires every observation's source/time and decision cutoff. The reevaluation does not establish that the stock-tool GitHub material exposes point-in-time publication/availability metadata in the exact form F1 needs.

**Exact classification:** **candidate input, subject to F1 point-in-time validation**, not unconditional “keep as F1 input.” No new story is needed; F1 already owns the validation.

## 2. Running behavior check

The stated 9:25 brief is materially incompatible with the new desk if presented as a current trade recommendation.

`fno/brief.py` does not merely summarize markets. It:
- scans configured underlyings and expiries;
- builds/selects option strategies;
- publishes a **“Top setup”**;
- gives exact legs, prices, max loss/profit, stop, target and size;
- writes candidate JSON;
- tells the user how to paper-open the setup.

Therefore D3 is a real conflict, but the recommendation “keep the brief … as information only, clearly labelled old strategy” is insufficient **unless the actionable candidate/size/open language is removed or the entire old brief is isolated under an explicit legacy mode/channel**. A label alone does not turn an actionable trade recommendation into neutral information.

The old live desk is also genuinely active behavior, not dormant code: the deployment watchdog's `ensure-running` launches `fno live run`; `LiveRunner` scans repeatedly, manages entries/exits, runs news and price-watch paths; the old kill switch is explicitly “close all trades,” which conflicts with the new entry-only drawdown brake. E4 correctly recognizes this.

## 3. Are D1-D5 complete? NO.

D1-D5 capture the largest product decisions, but **two additional conflicts are missing**.

### D6 — old safety/account semantics versus the approved risk model

Old Wave 0 includes:
- 2% risk per trade;
- trade-frequency caps;
- weekly loss limit;
- overnight exposure cap;
- automatic performance kill switch;
- kill switch that closes all trades;
- paper/live profiles with old money rules.

The approved design instead fixes a Rs5 lakh paper account, Rs10,000 max modeled loss/trade, max 3 open trades, Rs30,000 **entry-blocking** drawdown brake, C2 whole-account stresses/exposures, and explicitly says open trades keep their own exits. E4 mentions only the old kill switch in its background; it does not decide whether the other old safeguards continue to govern the new desk.

**Decision D6:** old Wave-0 money/risk rules apply **only to the legacy desk**. The new daily desk uses C2 + playbook limits exclusively; no old frequency/weekly-loss/overnight/per-trade-%/performance-kill rule may silently gate or close a new-desk trade. Shared generic safety code is allowed only if its behavior is explicitly selected by the active desk.

**Recommendation:** approve this separation. Strong evidence: otherwise two different risk policies can act on the same paper strategy.

### D7 — old shadow-book/promotion semantics versus the approved paper process

Wave 0's shadow book “trades one lot of every idea, ignores portfolio limits,” and the old AI plan promotes a strategy if it beats live strategies. The approved process instead uses frozen research evidence, owner-approved playbook, E1 paper fills under real constraints, E3 >=3 months AND >=20 completed positions, and F4's tightly matched counterfactual shadow evaluation.

Leaving the old shadow book active for the new desk would create a second, incompatible evaluation/promotion record.

**Decision D7:** old shadow book remains legacy-only. It is not evidence for new-desk promotion. New-desk paper evidence comes from E1/E3; AI counterfactuals come only from F4 under matched constraints.

**Recommendation:** approve this separation.

With D6-D7 added, I find no other owner-level behavioral conflict that requires a separate decision. Several old components can remain in source code as legacy/research utilities; the conflict is activation and authority.

## 4. D1-D5 recommendations

- **D1 — recommendation needs correction.** The table says AI may have a “recorded veto,” but approved F1 explicitly says agents cannot change the playbook, and D2 says rules evaluate candidates. F4 can score a counterfactual decision with/without a role; that does not require giving the AI operational veto authority. **Recommendation: no AI veto in the active decision path initially. Record a shadow veto/recommendation and score it under F4. Only a later approved playbook/design change can give it authority after evidence.**
- **D2 — AGREED:** no automatic discretionary AI early exit. A tested playbook event-exit rule may close; AI can flag evidence/alert.
- **D3 — AGREED conflict, but strengthen action:** old desk must be disabled/separate before new desk activation; old 9:25 actionable candidate brief must either be disabled or explicitly moved to legacy output with no current “open this setup” semantics. Reusable news collection may continue only as data collection, not as old entry/exit authority.
- **D4 — PARTLY AGREED:** deciding runtime/budget before F1 is reasonable, but “cloud routines” is a recommendation, not a requirement derived from the approved design. The old plan explicitly chose the owner's PC; either runtime can satisfy F1 if availability, secrets, provenance and F5 cost tracking work. Owner should choose based on operational evidence/cost.
- **D5 — AGREED:** withdraw self-merging decision-parameter changes for the new desk.

## 5. Gaps G1-G4

### G1 lessons memory — JUSTIFIED, but narrow it

This is not in F1-F5. It can be valuable, but “memory” can create look-ahead and self-reinforcing errors.

**Required story constraints:** only validated/evidence-linked lessons; `available_from` timestamp; immutable source decision/result/judge IDs; retrieval only when `available_from <= decision_cutoff`; corrections append/supersede rather than overwrite; role can ignore a lesson; historical AI replay must not receive lessons created later. Score whether retrieval changes decisions/value.

### G2 AI plain-English summary — JUSTIFIED, optional

E2 is deterministic source-of-truth reporting, not an AI narrative. Add only in F/on-hold. Narrative must be generated exclusively from the immutable daily record/finding cards, every numeric claim checked, and failure must fall back to E2 without blocking the desk. It must not introduce a new trade/exit recommendation outside the recorded decision.

### G3 weekly research meeting automation — JUSTIFIED, but it must not bypass B4/B6

The automation is a real gap. Every proposed empirical trial must be registered **before its result/data evaluation**, and candidate scans obey B6's predeclared grid/multiplicity controls. The weekly meeting may propose protocols/questions; it cannot repeatedly mine results and relabel them as fresh hypotheses. Outputs are research proposals, never direct playbook changes.

### G4 old desk and brief separation — NOT a separate gap/story

This is already the purpose of **E4**, whose user story is “one active desk per paper account,” with `desk.active`, separate journals and an account-scoped single-writer lock. D3's brief/channel labeling is a small extension/acceptance criterion to E4, not a new story.

**Exact action:** extend E4 to include:
1. legacy brief/news/trade outputs use an explicitly legacy label/channel/path;
2. inactive legacy orchestration/watchdog cannot start or mutate the active paper account;
3. the current 9:25 brief cannot publish actionable old-strategy candidates as if they belong to the active daily desk.

Do **not** create G4 as a second E story; that would recreate the duplication this reevaluation is meant to prevent.

## 6. Is anything else missing?

Beyond D6/D7, one implementation gap belongs inside existing stories rather than a new story:

- **F1 data-input contract:** global cues, verified news and positioning sources named by the reevaluation must each satisfy F1's source-time/cutoff/missing-data rules. Do not create separate feature stories merely because the old plan collected them.

I do **not** restore G5. The new research feature F1 computes IV premium from historical daily option data; old end-of-day IV snapshot history is not required for Experiment 1. If later research wants an IV-rank feature, register/test it through B6 rather than reviving W1.2 by default.

## Final judge answers

1. **Any verdict wrong? YES.** “Keep old desk Groww/news behavior” must be conflict/quarantine pending D3; stock-tool news is only a candidate F1 input pending point-in-time validation. The 9:25 brief is confirmed actionable, not neutral information.
2. **Are D1-D5 complete? NO.** Add **D6 old risk/safety semantics** and **D7 old shadow-book/promotion semantics**. Also change D1 recommendation to shadow veto first, not operational veto.
3. **Are G1-G4 justified?** **G1-G3 yes with the constraints above. G4 no as a separate story; fold it into E4.** Nothing else warrants a new story from this comparison.

**Judge verdict: FAIL the reevaluation as currently written; revise it before creating E/F/gap issues.** The approved 28-story design itself is not rejected by this review.
