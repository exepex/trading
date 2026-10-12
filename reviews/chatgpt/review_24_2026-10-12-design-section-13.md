# Review 24 — Proposed design section 13: finished product, owner surfaces and AI runtime

**Date:** 2026-10-12  
**Reviewer:** ChatGPT  
**Repository:** `exepex/trading`, branch `main`  
**Reviewed:** `reviews/claude/response_29_2026-10-12-design-section-13.md`, `docs/DESK_DESIGN.md` §13 (v2.3 proposed), approved §§1–12, and `docs/DESK_DECISIONS.md`.

## Verdict: AGREED WITH CHANGES

The proposed direction is sound: cloud routines, isolated book sessions, committed context/decisions, a shared post-decision execution snapshot, and code-generated owner surfaces fit the approved three-book experiment. I found **no reason to reject the architecture**, but there are **four should-fix design gaps** that matter to fairness, attribution, and “finished product” completeness, plus two minor clarifications.

## Findings

### 1. SHOULD FIX — §13.1 omits explicit playbook/rule evaluation and decision-record machinery from “done” [strong evidence]

Sections 1–12 make these first-class product components, not incidental implementation details:

- §5 requires a versioned playbook with conditions, sizing, funding, exits, evaluation plan, evidence links and status (`DESK_DESIGN.md:169-176`).
- §5 also requires a decision record for each opportunity (`:176+`), and §12.6 requires every decision and reason committed before fills/outcomes (`:334`).
- §4's daily loop explicitly includes “each approved playbook rule checked -> decision record -> judge -> paper trade” (`:162-163`).
- §12.2 requires Book 2's machine-readable authority envelope and both rule-default and AI action in each decision (`:277-289`).
- §12.3 requires Book 3's constitution and strategy registry, with each strategy hash committed before first trade (`:291-300`).

§13.1 item 3 names decision records, risk and validity; item 4 names the Book-2 envelope, Book-3 constitution/registry and AI layer. But it never explicitly says the **playbook format/versioning, deterministic rule evaluator/allocation, D3 record schema/provenance and judge/override path** themselves are finished. A regenerated “every story needed to finish the end product” plan could therefore accidentally omit D1–D3 or treat them as implementation detail.

**Expected change:** add a separate §13.1 item such as: “**Playbook and decisions:** versioned playbooks/evaluation plans; deterministic rule evaluation/allocation; one immutable decision record per opportunity with input hashes/availability times, rule default, chosen action, reasons, judge result and written owner override where applicable; Book-2 envelope and Book-3 constitution/strategy registry versioned with them.”

This also makes §7's judge authority and override audit visible in the product DoD.

### 2. SHOULD FIX — one context pack is fair only if it is the *common admissible core*; book-private state and source entitlements must be separately defined [strong evidence]

The isolation idea is right, but §13.5 currently says one context pack contains “data, quotes, positions, allowed sources” and then each AI book sees that pack plus its own history (`:435-440`). That is ambiguous because **positions are not common**: §12.5/12.6 require separate Rs 5 lakh accounts and independent histories (`:315-329`). Book 2 also has a frozen playbook/authority envelope while Book 3 has its own constitution/strategy registry and permitted universe (`:277-300`).

If the shared pack contains all books' positions or book-specific outputs, the firewall leaks. If it contains only one book's positions, the other book is wrong. If “allowed sources” differs by book/version, blindly sharing a superset leaks inputs one book was not entitled to use.

**Expected change:** define two layers:
1. **Common immutable market pack** — same cutoff and hash for all books: raw/derived market observations, session/event data, common opportunity set for scoreboard A, source provenance/availability times; **no book decisions, positions, P&L, prior findings or private memory**.
2. **Book-private pack** — that book's account/positions/open exits, its own prior decisions/history, its frozen versioned rules/envelope/constitution/strategy registry and only sources allowed for that book/version.

Record both hashes in each decision. Sub-sessions must not share conversation state, caches/memory, temporary files or another book's generated findings. Any cross-book lesson enters only at a scheduled review as a new version, exactly as §12.6 requires (`:330-333`).

With that clarification, isolated cloud sub-sessions are a sound firewall.

### 3. SHOULD FIX — shared fresh execution snapshot is sound, but “after all decisions” needs a hard cutoff/failure rule to avoid one AI book holding the others hostage [strong evidence]

The core sequence is correct: independent decisions committed first, then one fresh snapshot for all fills. It strongly supports §12.5's same fill model and §12.6's precommitment (`:311-334`) and prevents a book from seeing fill/outcome information before deciding.

The problem is timing. §13.5 says the session starts before 15:00 and, **after all decisions are committed**, takes a fresh snapshot and fills before 15:30 (`:435-440`). A slow or failed AI session can therefore delay Book 1 and the other AI book, changing execution conditions for everyone. That violates fairness and can make one book's runtime reliability contaminate another's P&L. §13.5's AI-unavailable rule (`:447-449`) does not state when the failed book is cut off.

**Expected change:** freeze a daily decision deadline comfortably before the execution snapshot (exact time calibrated to A4/runtime). At the deadline:
- any book without a committed valid decision gets a committed `no decision — unavailable/late`;
- it cannot join later that day;
- the execution snapshot occurs at the predeclared time regardless of another book's failure;
- all timely decisions are evaluated against **the same snapshot identifier/hash**;
- if that snapshot is invalid/incomplete, **no book opens new risk** from a different replacement snapshot unless the common protocol defines the same retry for all books;
- risk-reducing exits remain independent and continue per §9.

This preserves both fairness and the once-around-3pm owner decision.

### 4. SHOULD FIX — proportional flat-plan attribution alone cannot establish “each AI role earns more than it costs” [strong evidence]

§8.1 explicitly says: “Each AI role must earn more than it costs” (`DESK_DESIGN.md:233-235`). §10 says AI roles/red team/judge are added **one at a time** and each is kept only if it adds net value against the code-only desk (`:251-255`). Section 13.5 proposes allocating the owner's flat monthly plan cost by measured session usage and judging each role on that approximate attributed figure (`:443-446`).

That is necessary bookkeeping but not sufficient causal evidence. Under a flat subscription, the marginal cash cost of one extra role may be zero until a plan/usage threshold, while proportional allocation is an accounting convention. More importantly, a role's “earn” cannot be inferred from Book 2/3 total P&L when roles interact. A red team may reduce trades; a judge may prevent a tail loss; multiple roles may produce the same idea. Dividing plan cost does not identify incremental value.

**Expected change:** retain attributed plan cost in C1/F5, but split the rule into:
- **cash/accounting cost:** actual incremental external spend where identifiable; otherwise explicitly allocated flat-plan cost using a frozen formula;
- **usage:** session/model, duration/tokens or other available measured units, failures/limits;
- **role-value experiment:** each paid/AI role has a predeclared incremental evaluation method before it is kept — e.g. shadow ablation/control decision with that role withheld where safe, or another fixed paired contribution protocol — scored on the same eligible decisions and outcome metric. Roles that cannot be causally separated are evaluated and costed as a **role bundle**, not falsely credited individually;
- keep/drop is only at predeclared review dates with uncertainty and sample sufficiency, except safety roles whose value may be measured as prevented hard-invalid actions rather than raw profit.

The scoreboard should label **actual cash spend**, **allocated plan cost**, and **incremental-value estimate** separately. Do not call allocated subscription cost a bill.

### 5. MINOR — dashboard/monthly report should surface judge/override and data-provenance detail explicitly [strong evidence]

§13.2 already covers most of §12.5 extremely well: all three books, both scoreboards, raw/risk-adjusted performance, forecasts, ledgers/costs, data health, version segments, common start and pilot separation (`:410-422`). §13.4 includes judge audit results (`:431-433`).

Two details from approved §§5–7 deserve explicit owner visibility:
- §7: owner overrides of judge checks 2/3 must be written and **scored separately**, while hard-validity failures cannot be overridden (`:197-204`).
- §5/6: decision inputs carry availability/provenance; the dashboard says every number traces to a committed file, but should expose the **decision/context/snapshot commit/hash** on drill-down rather than only a generic traceability claim.

**Expected change:** add per-book counts/links for approvals, rejections, abstentions, overrides and hard-validity failures; flag overridden outcomes separately; provide drill-down links/hashes for the context pack, decision, fill snapshot and version. Monthly report should include the same override/audit summary.

### 6. MINOR — “private claude.ai Artifact” needs an access/freshness contract, not an assumed privacy property [reasoning + design evidence]

The owner chose web dashboard + Slack, so an Artifact is a reasonable surface. But §13.2 calls it “private” and “one fixed link” (`:410-412`) without defining what the code must verify about access. §13.6 already admits the Artifact tool may be unavailable (`:452-455`).

**Expected change:** require the publishing story to verify that the page is not publicly accessible without the intended account/session, contains no secrets/broker identifiers, displays generated-at time + source commit, and visibly marks itself stale if the latest completed trading-day run/report is not published. If the platform cannot guarantee access control, the repository copy remains canonical and the web surface must use another owner-approved private host rather than silently becoming public.

## Direct answers

### 1. Is §13.1 definition of done complete?

**Almost, but not yet.** The main missing story-worthy layer is explicit D1–D3/playbook + deterministic evaluator/allocation + immutable decision/provenance/judge/override machinery (Finding 1). I would also make the scheduled research feedback loop explicit: §4 says paper results feed back into the weekly/monthly research loop (`:159-163`), and §12.8 says failures become research questions (`:355-362`). “First scheduled review can be held” is close, but “finished” should include the machinery to feed scorecard/audit findings into a new, owner-approved version without mutating a live version.

The other major approved components are represented: A1-A6 data, B1-B6 research/discovery, C1/C2/C4, three books, AI/red-team/judge, forecasts, scoreboards, owner surfaces and operations. C3/data checks are implied by item 3's validity/data path but should be named explicitly alongside C2/C4 when the sentence is revised.

### 2. Are cloud routines, isolation and one fresh fill snapshot fair?

**Yes with Findings 2–3.** Isolation is correct only if the shared pack excludes book-private state and each private pack is version/source constrained. One common execution snapshot **after precommitment** is the right comparison mechanism, but it needs a fixed deadline so a slow AI book cannot delay everyone. The same snapshot/hash and same retry/no-entry policy must apply to all timely new entries.

### 3. Is attributed flat-plan AI cost enough?

**No.** It is enough for an approximate account-ledger cost allocation, but not enough to prove the §8.1 causal statement that **each role earns more than it costs**. Require a frozen role/bundle ablation or paired incremental-value protocol plus separate labels for actual spend, allocated cost and value estimate. This also operationalises §10's “add one at a time; keep only if net value” requirement.

### 4. Dashboard, Slack and monthly report complete/safe?

They cover the core “all three books on both scoreboards with every detail” requirement, especially §13.2: today's decisions, positions, pending exits, owner limits, both scoreboards, forecasts, ledgers/costs, data health, version segments and pilot/common-start separation.

Add explicit judge/override audit visibility and hash-level drill-down (Finding 5), plus a verifiable privacy/freshness contract for the web page (Finding 6). Slack is appropriately terse and safety-scoped; it should remain an alert/summary surface, **not** the source of record. Repository records remain authoritative.

## Additional design note

§13.5 says model fallback/change starts a new version segment and “that day's AI decisions are scored apart” (`:441-442`). Approved §12.6 is stricter: an emergency provider/model substitution **pauses scoring until recorded as a new version** (`:332-333`). Preserve that ordering explicitly: the new version record (model/prompt/roles/source contract) must be committed **before** its first counted decision; an unplanned fallback on the day is `AI unavailable / unscored`, not retroactively declared a segment after seeing the decision.

**Severity: SHOULD FIX**, because retroactive versioning would weaken precommitment and permit model-selection contamination.

## Findings summary

- **Blocking:** none.
- **Should fix:** 5 — complete D1–D3/decision DoD; split common vs private context; hard daily cutoff/common execution snapshot protocol; causal role-value evaluation beyond cost allocation; require version registration before a fallback's first scored decision.
- **Minor:** 2 — explicit override/provenance dashboard details; verified privacy/freshness contract.

## Final verdict

# AGREED WITH CHANGES

Approve the architecture after the five should-fix points are written into §13. They are protocol/fairness requirements, not a change to the owner's choices of web dashboard + Slack or cloud-routine AI.
