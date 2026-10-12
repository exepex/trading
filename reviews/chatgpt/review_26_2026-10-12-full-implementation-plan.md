# Review 26 — Full finished-product implementation plan

**Date:** 2026-10-12  
**Reviewer:** ChatGPT (independent plan/design review)  
**Repository:** `exepex/trading`, `main`  
**Read:** `reviews/claude/response_32_2026-10-12-full-implementation-plan.md`, `response_31_2026-10-12-review-25.md`, `docs/IMPLEMENTATION_PLAN.md`, **all eleven** files under `docs/stories/` (A, B, C, D, E, F, G, S, P, X, O; W/K stories are in X), `docs/DESK_DESIGN.md` §§1–13, `docs/DESK_DECISIONS.md`, and relevant current stock dashboard source under `contactexepex/agentic-stock-prediction/web/`.

## Verdict: AGREED WITH CHANGES

**Section 13 revision 3's four requested corrections are confirmed.** The 65-story plan covers the large majority of the approved design, and the corrected A1/C2/C3/C4/D3 contracts are directionally right. **Do not freeze the plan or recreate issues yet:** I found **five should-fix** gaps, two of them fundamental to the promised AI firewall and stock-dashboard migration, and **two minor** specification clarifications. No reason to reject the overall product architecture.

## A. Mandatory first check: Section 13 revision 3

1. **Atomic publication — CLOSED [strong evidence].** `docs/DESK_DESIGN.md:429-434` requires one `publication_id`, unique (`product,page_key,publication_id`) rows, transactional validation and current-pointer advancement; failure retains the last complete publication with failed run/reason. Stories P3 `docs/stories/P-publishing.md:87-110` and W2 `docs/stories/X-cross-repository.md:99-115` express the corresponding implementation and read behaviour.
2. **PostgreSQL least privilege — CLOSED [strong evidence].** `DESK_DESIGN.md:466-480` specifies separate owner/migration identities, restricted DML runtime roles, dashboard SELECT, CREATE revocations, default privileges, verified TLS and forbidden-operation tests. X1 `X-cross-repository.md:23-51` covers those requirements including restore and real-server role tests.
3. **Migration order and rollback — CLOSED IN DESIGN [strong evidence].** `DESK_DESIGN.md:455-462` states provision -> stock dual publish -> Azure read path -> parity -> parallel deployment -> cutover -> rollback window -> remove old web/retire MotherDuck. **The implementation plan does not yet honour this order** (Finding 2).
4. **F&O freshness — CLOSED [strong evidence].** `DESK_DESIGN.md:446-448` uses the A1 trading calendar and run state, not the stock app's generic age limit. P3 `P-publishing.md:103-110` and W2 `X-cross-repository.md:99-115` require publishing/stale/failed behaviour.

The owner's conditional section-13 approval is therefore supported **at design level**. Remaining findings are in the story implementation plan, not reasons to reopen section 13.

## B. Findings requiring changes

### F1 — SHOULD FIX — F1 sparse checkout + post-hoc event audit does not prove the required firewall [strong evidence]

**Evidence:** Approved `DESK_DESIGN.md:501-506` says each book sees only common and its private pack, with no other book's history/memory. `docs/stories/F-ai-layer.md:32-42` proposes launching a cloud session at commit `P` of the **full trading repository** with a sparse checkout, then detecting forbidden file/URL access by reading `list_events`. Acceptance `:44-58` checks planted event-log violations and one real dry run.

**Problem:** Git sparse checkout controls which paths appear in the working tree, **not which blobs, trees, refs or history are accessible in the Git object database**. A session with the full repository can use `git show <commit>:journal/other-book/...`, change its sparse specification, inspect reachable objects, or retrieve refs. An event log is detective evidence, not a preventive permission boundary; a fake event log proves only that the detector catches *logged* reads, not that every access is logged. Thus “can see only” is not established, even if a session's prompt asks it to behave.

**Required fix:** Launch each book with an **independently constructed, allowlisted export** containing the common pack, only that book's private pack, its permitted code/prompts and its versioned allowed sources; no full trading Git history, remote, credentials, other-book files, cross-book writable storage or unrestricted GitHub access. It may be a separate ephemeral sanitized repo/artifact with an independently verified manifest. The orchestrator alone (outside the AI session) merges validated output to main. If cloud-session tooling cannot enforce such access, document that limitation and **do not claim a proven firewall or score it as an independent comparison** until an enforceable isolation mode exists. Test forbidden reads both by filesystem and Git-history/network attempts on a real isolated session; require that the operation fails *before* the model sees the data. Keep event-log audit as defence in depth, not as the boundary.

Also tighten the deadline handoff: `F-ai-layer.md:36-42` says the runner reads the branch **after** the deadline; `E-paper-desk.md:124-132` and `DESK_DESIGN.md:507-512` require validated, committed decisions before the fixed execution snapshot. Specify an authoritative server-side receipt deadline for the AI output, an audit/promotion deadline before the snapshot, and fail-closed behaviour if validation/merge misses that deadline; do not trust author-set Git commit timestamps.

### F2 — SHOULD FIX — W2 depends on K1 for its acceptance criterion, but the plan schedules K1 two milestones later [strong evidence]

**Evidence:** `docs/stories/X-cross-repository.md:111-120` W2 acceptance criterion 4 requires stock pages on Azure to equal MotherDuck, explicitly “needs K1”. Yet `:122` lists only `W1,X1,P3` as dependencies. K1 `:223-252` is the **stock dual-publisher and parity** implementation. `docs/IMPLEMENTATION_PLAN.md:57-65` puts W2 in **M4**, K1 in **M6**, even though `DESK_DESIGN.md:455-459` requires stock dual publication before Azure read-path parity/cutover.

**Required fix:** Move K1's stock Azure publication/parity work before the stock-parity acceptance of W2 (and add K1 as a hard dependency), **or split W2** into an F&O-only Azure reader in M4 and a separately judged stock Azure reader/parity integration after K1. State which W2 acceptance criteria can pass at each stage; do not mark W2 done with an unimplemented K1-dependent criterion. Preserve a separate F&O launch path that does not depend on stock cutover.

### F3 — SHOULD FIX — No explicit story migrates the existing dashboard's *writes* (assistant/inbox), not just its read models [strong evidence]

**Evidence from stock code:** `contactexepex/agentic-stock-prediction/web/lib/data/store.ts:62-65` reads MotherDuck; `web/lib/tools/motherduck.ts:77-124` implements live inbox writes; `web/lib/assistant/store.ts:1,41-56` and `web/lib/assistant/sql.ts:1-10` implement assistant conversation writes against MotherDuck's inbox DB. W2 `X-cross-repository.md:95-109` specifies only an Azure `RowStore` for **reads**. K1 `:230-246` promises inbox rows/logs copied and “new writes go to one place only after cutover,” but never assigns **the dashboard-side code change** replacing `MotherDuckInboxStore`, `MotherDuckConversationStore` and other app writers with Azure implementations. K2 `:266-272` later demands no MotherDuck references.

**Required fix:** Add a named dashboard-owned story (or explicit W2/W5 sub-story with its own acceptance gates) for the Azure `app` schema write adapters, SQL-dialect compatibility, migrations of inbox/assistant/control state, identity/authz, concurrency/idempotency, and switching **all** interactive writers from MotherDuck to Azure. Test dual-read/one-writer behaviour, counts/hashes, new-write continuity and rollback of writes; do not rely on the stock backend's read-model K1 to migrate a dashboard-owned inbox. Update K1/W2/W5/K2 dependencies and the 13.8 integration tests accordingly.

### F4 — SHOULD FIX — E5/F5 omit a hard C4 prerequisite although their implementation and tests explicitly invoke it [strong evidence]

**Evidence:** `docs/stories/E-paper-desk.md:201-203` says Book 1 runs C4 in playbook mode; `:215` depends on `D2,D3,E2,E3` but **not C4**. `docs/stories/F-ai-layer.md:194-203` says Book 2's final action is checked by C2 and **C4** and invalid envelope actions are blocked by C4; `:211` depends on `D2,D4,F1,F2,F3,F4` but **not C4**. C4 itself is a separate story at `docs/stories/C-code-roles.md:156-202`, with distinct playbook/constitution acceptance.

**Required fix:** Add `C4` as an explicit hard dependency of **E5 and F5**; retain F6's existing C4 dependency. Make E3's execution gate require C4's completed verdict before any new fill, even if the decider produces a valid-looking draft. Add one end-to-end negative test per book showing a C4 failure cannot become a fill. This is more than a cosmetic dependency: hard-validity checks are non-overridable (§7).

### F5 — SHOULD FIX — M3 promises all three books' forecasts before the AI books needed to produce them exist [strong evidence]

**Evidence:** `docs/IMPLEMENTATION_PLAN.md:56-62` says **M3 G1–G4** delivers “All books' forecasts and baselines recorded and scored,” while AI books and F1 are M5. But G3 `docs/stories/G-forecasts.md:94-104,116` explicitly says Books 2 and 3 forecast in their isolated F1 sessions, with “F1 for books 2 and 3” as a conditional dependency. A judge cannot pass a story whose acceptance criterion `:106-110` says each book records five forecasts per session day if two books' sessions do not yet exist.

**Required fix:** Either split G3 into Book-1 capture in M3 and AI-book integration in M5, with G4 reporting missing AI forecasts honestly until M5, or move G3's **full** acceptance to M5 and change M3's outcome to “forecast protocol, baselines, scoring engine and Book-1 capture ready.” Do not claim full three-book forecast completion in M3.

## C. Minor clarifications

### M1 — MINOR — Role coverage needs an explicit mapping to avoid silently omitting approved perspectives [some evidence]

`DESK_DESIGN.md:112-134` lists the head of desk, portfolio manager, mathematician, statistician, quant modeller, execution/microstructure, macro, positioning, regulation, behavioural, and other roles and says every role contributes (or `not applicable`). F2 `docs/stories/F-ai-layer.md:72-86` enumerates eight AI roles, while code-only roles live elsewhere. This may be a valid split, but the plan should include a **role-to-story/implementation matrix** (code, AI card, decision authority, or `not_applicable`) and a test that each approved role is accounted for. Do not force unnecessary model calls; ensure no perspective disappears by accident.

### M2 — MINOR — Keep research/public repository privacy explicit in implementation acceptance [strong evidence]

`DESK_DESIGN.md:463-464` and `:13.7` say backend repositories are public during development; dashboard login protects the UI but **not** committed records. W4 `X-cross-repository.md:165-182` scans dashboard payloads, but D3/F1/O1 write potentially detailed role/decision records to public Git. Add a shared no-secret/no-PII/no-broker-identifier test for committed `journal/`, pack manifests, role-card content and `reports/`, not only the rendered dashboard payload. Preserve auditable numbers and hashes without leaking account identifiers or access tokens.

## D. Approved-story corrections and coverage

**Correct and supported [strong evidence]:**
- **A1 calendar:** `A-data-foundation.md:25-62` specifies a versioned independent NSE session calendar, special Saturday/muhurat, fail on out-of-range dates; A7 `:325-361` wires it into A4 and tests special sessions. This closes the old weekday-only assumption without silently changing the already judge-passed recorder.
- **C2 per-book limits:** `C-code-roles.md:55-76` uses each book's separate account and new `risk` config, preserving Rs 10k/trade, three open, Rs 30k brake, and independent stress. Correct.
- **C3 quote rule:** `C-code-roles.md:129-146` uses A4's same-day-trade validity proxy and **does not invent a quote timestamp**. Correct.
- **C4 two modes:** `C-code-roles.md:163-196` defines independent code recomputation and separate playbook vs constitution checks; non-overridable failures are tested. Correct, subject to F4's missing dependencies.
- **D3 three-book record:** `D-playbook-decisions.md:95-125` covers both pack hashes, rule default/chosen action, Book-3 strategy/version, served model, judge, overrides, forecast links, and commit-before-snapshot. Correct schema direction.

**Coverage:** A1–A8, B1–B7, C1–C4, D1–D6, E1–E6, F1–F9, G1–G4, S1–S5, P1–P4, X1, W1–W5, K1–K2 and O1–O4 collectively map to the ten §13.1 product outcomes (`IMPLEMENTATION_PLAN.md:33-46`). The remaining missing *operational* contract is the dashboard app-write migration (F3), not a new trading strategy or unapproved AI feature. The proposed B7 live-feature validation, G1 historical IV estimator, A8 positioning source, D4/D5/D6 versioning, and S1 evaluation freeze are justified by approved §§1–13. No unsupported major feature was found.

**Testability:** Most stories have named modules, explicit schemas or interfaces, positive/negative fixtures, and a judge action. F1's fake event audit cannot prove isolation (F1); W2 cannot pass its K1-dependent criterion when scheduled (F2); E5/F5 could be implemented without mandatory hard-validity gating (F4); G3 cannot satisfy full-book coverage in M3 (F5). The plan is **not yet fully independently implementable and judgeable as written**.

**Dependencies and milestones:** The broad data -> research -> decision -> paper -> AI -> review sequence is right. M4's stock Azure dependency and M3's AI forecasts are the two concrete sequencing defects. Cross-repository §13.8 needs the additional dashboard app-write migration gate. The written dependency table does not show an obvious simple circular chain among the reviewed dependencies; I did **not** independently run Claude's reported graph-cycle/link checker.

## Final verdict

# AGREED WITH CHANGES

**Blocking:** none requiring abandonment of the design.  
**Should fix before owner approves the plan / GitHub issues are regenerated:** F1–F5.  
**Minor:** M1–M2.

The design's four section-13 revision-3 changes are **confirmed**. The full plan needs the specific corrections above before its stories can be frozen and judged without guesses. This is a document/architecture review; no trading code was changed and no pytest/Ruff execution is claimed.
