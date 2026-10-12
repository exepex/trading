# Review 27 — Implementation plan revision 2 confirmation

**Date:** 2026-10-12  
**Reviewer:** ChatGPT  
**Repository:** `exepex/trading`, branch `main`  
**Reviewed:** `reviews/claude/response_33_2026-10-12-review-26.md`, revised `docs/IMPLEMENTATION_PLAN.md`, and changed stories F, E, G, X and O against approved design §§1–13 and Review 26.

## Verdict: AGREED WITH CHANGES

Review 26's central F1 firewall problem is closed: revision 2 replaces Git sparse checkout with a genuinely different trust boundary — no repository, the most restrictive enforceable network policy, an allowlisted hashed export, server-receipt timing, external validation/C2/C4, and a promotion deadline before the common execution snapshot. Critically, the design does **not** pretend isolation exists when the platform cannot enforce it.

Six of the other Review-26 fixes are also substantively applied. I found **one remaining should-fix cross-repository dependency/integration inconsistency** and one minor F1 wording/test clarification. Fix those before freezing the issue set.

## 1. F1 isolated AI book sessions — SOUND AND TESTABLE, with one minor clarification

### What is now correct [strong evidence]

The old problem was that sparse checkout was not a security boundary. Revision 2 explicitly acknowledges that at `docs/stories/F-ai-layer.md:32-34` and removes the AI session from the repository entirely.

The preventive boundary is now:

- **No source repository:** `F-ai-layer.md:35-37`. The session does not receive the trading Git repository, so excluded blobs/history/branches are not locally recoverable through Git.
- **Restrictive network:** `:35-37`. Network is disabled where supported, or restricted to the version's explicitly permitted source domains; `github.com` is never allowed. This addresses the additional fact that the repositories are public.
- **Allowlisted export:** `:38-41`. Code constructs only the common pack, that book's private pack, its prompts and version-approved source material; every item is manifested and SHA-256 checked. Oversize input fails the day rather than silently truncating.
- **Output is data, not a Git branch:** `:42-46`. The AI returns one structured JSON result; the trusted runner outside the AI retrieves, validates, runs C2/C4 and commits it.
- **Authoritative timing:** `:44-46` uses the cloud service's server-side event timestamp as receipt time, not an AI/Git timestamp. E3 separately requires receipt and promotion deadlines before the execution snapshot at `docs/stories/E-paper-desk.md:116-125`.
- **Defence in depth:** event-log inspection remains at `F-ai-layer.md:47-48`, but is no longer the primary boundary.
- **Fail closed on platform limitations:** `:51-53`. If isolation cannot be enforced, results are labelled `isolation not enforced` and are not scored as an independent comparison. That is exactly the honest fallback required for the experimental claim.
- **Real enforcement test:** `:55-71` requires a real session to fail raw-GitHub, `git clone`, and outside-export reads **before the model sees the data**, plus receipt/promotion deadline and pack-hash checks.

This is a sound implementation of design 12.6/13.5 **provided the real-session criterion passes on the actual cloud environment before any counted decision**. A fake session is not accepted as proof.

### MINOR — make the allowed-network test cover every capability exposed to the session [reasoning + evidence]

F1 criterion 1 at `:55-58` tests raw URL, Git clone and local outside-export access. The design says “most restrictive network level offered” and may allow source-contract domains (`:35-37`). If the session environment exposes a browser/search/fetch connector that is not governed by the same network allowlist, a shell-level `curl` failure would not prove the whole session is isolated.

**Expected clarification:** the real-session isolation test enumerates **every network-capable tool/capability actually exposed to that environment** and proves that GitHub/other-book URLs are denied through each of them. Prefer an environment with no network at all for the head-to-head comparison; if approved external domains are necessary, test both a permitted domain and several forbidden paths/domains. Record the environment/network-policy identity/hash with the version. This is minor because F1 already says attempts must fail before data reaches the model and results are unscored if enforcement is unavailable.

**F1 conclusion:** approved in principle; no should-fix remains in its architecture.

## 2. Review 26 F2 — W2/K1 ordering — CLOSED [strong evidence]

W2 is now explicitly **F&O-only**: `docs/stories/X-cross-repository.md:91-123`. Its scope says stock stays on MotherDuck until W6 (`:104-106`). New W6 `:193-220` owns stock Azure reads and parity and depends on K1. The plan places W2 in M4 and K1/W6 in M6. This restores the design's requirement that F&O launch does not wait for stock migration while preventing W2 from claiming unbuilt stock parity.

## 3. Review 26 F3 — dashboard app writes — SUBSTANTIVELY CLOSED, but one dependency remains inconsistent

New W7 is the right missing story. `X-cross-repository.md:224-260` covers:
- inbox, command log, assistant conversation and control-state writers;
- Azure `app` schema adapters and SQL compatibility;
- history copy with row counts/hashes;
- exactly one active writer, concurrency/idempotency;
- rollback of post-switch writes;
- least-privilege app-table access.

W5 now depends on W7 (`:264-291`) and K2 depends on W5/W7 (`:328-350`).

### SHOULD FIX — K1 criterion 3 requires W7, but K1 still does not depend on W7 [strong evidence]

K1 acceptance criterion 3 says the stock backend's inbox readers must read Azure `app` **after W7's switch** (`X-cross-repository.md:314-318`). Yet K1's dependency remains only X1 at `:324`. W7 explicitly says those stock-backend reads are out of W7 and belong to “K1 criterion 3” (`:238-240`).

Therefore K1 cannot be judged complete from its declared prerequisites. This is the same class of issue Review 26 found in W2.

**Expected fix:** either:
1. add **W7 as a dependency of K1** (there is no cycle: W7 currently depends only W1/X1), or
2. split the stock inbox-reader switch from K1 into its own stock-repository story depending on W7, leaving K1 as the read-model dual publisher.

Option 2 is cleaner because K1's primary purpose is stock read-model publication/parity, while the inbox-reader migration is an interactive app-state concern.

## 4. Review 26 F4 — C4 dependencies — CLOSED [strong evidence]

- E3 now depends on C4 at `docs/stories/E-paper-desk.md:144`, requires C2/C4 validation before promotion/fill at `:119-125`, and criterion 7 says no decision without completed C4 can be filled for any book (`:127-136`).
- E5 now depends on C4 and has a negative no-fill test (`:205-220`).
- F5 now depends on C4 and has the corresponding Book-2 negative test (`docs/stories/F-ai-layer.md:210-228`).
- F6 retains C4.

The non-overridable hard-validity gate is now an execution prerequisite, not merely a called helper.

## 5. Review 26 F5 — forecast milestone — CLOSED [strong evidence]

G3 is now **Book 1 only** (`docs/stories/G-forecasts.md:90-116`). New G5 owns AI-book forecast output after F1 exists (`:152-177`). G4 explicitly supports G5 later and can report coverage rather than pretending missing AI forecasts are zero skill. `IMPLEMENTATION_PLAN.md` M3 now promises protocol/baselines/scoring plus Book-1 forecasts; M5 contains G5. This is coherent.

## 6. Review 26 M1 — approved role coverage — CLOSED [strong evidence]

F2 now requires `agents/roles.yaml` mapping every design-3.4 role to code, AI card, decision authority or not-applicable implementation, with a completeness test against the design table (`F-ai-layer.md:94-110`). This prevents an approved perspective disappearing merely because it does not deserve a paid model call.

## 7. Review 26 M2 — public committed-record safety — CLOSED [strong evidence]

O5 `docs/stories/O-operations.md:137-169` adds a repository-record scanner covering journal, quotes, reports, Book-3 specs, playbooks, agents and session exports; tests planted credentials, personal-data patterns and broker identifiers; and the daily routine refuses to commit and alerts without printing the matched value. `IMPLEMENTATION_PLAN.md` also adds O5 to the global story DoD. This closes the gap beyond dashboard-only scanning.

## 8. Cross-repository integration test — one textual inconsistency to fix with the K1 dependency

O3's scope now says there are **four** integration tests and correctly adds stock W6 parity + W7 write continuity before W5 (`docs/stories/O-operations.md:87-91`). But `:93-104` still describes artifacts/acceptance/test plan/judge for only tests **1–3**: acceptance criteria stop at 3, “Test plan: the three tests”, and judge verifies only 1–3.

**Severity: SHOULD FIX** because design 13.8 explicitly requires an integration acceptance test at each cross-repository milestone.

**Expected fix:** add criterion 4: W6 parity and W7 one-writer/write-continuity/rollback integration pass on the shared disposable Azure-compatible Postgres setup before W5; make the test plan “four tests”; make the judge rerun/read test 4; add W6/W7 (and K1 if necessary) to O3's dependencies or split a later stock-migration integration story.

This can be fixed together with the K1/W7 dependency above; it is one remaining cross-repository sequencing/integration issue.

## 9. Plan status

Revision 2 now has 69 stories and the substantive Review-26 fixes are present. I did **not** independently execute Claude's dependency-cycle/link checker; this review checked the changed dependency contracts and story text directly.

I found no new unsupported trading functionality and no regression to the approved owner limits. F1's architecture is now honest about what can and cannot be proven: **no enforced isolation means no independent-comparison score**.

## Findings summary

- **Blocking:** none.
- **Should fix:** 2 tightly related cross-repository items:
  1. K1 criterion 3 requires W7 but K1 does not depend on W7 / the stock inbox-reader switch needs a proper story boundary.
  2. O3 says four integration tests but only specifies/judges three and lacks the W6/W7 dependency.
- **Minor:** 1 — F1 real-session test should explicitly exercise every network-capable tool exposed by the environment and version the network-policy identity.

## Final verdict

# AGREED WITH CHANGES

F1 is now a sound and testable firewall design for §§12.6/13.5, conditional on the real cloud environment actually passing its preventive isolation test before counted use. The other six Review-26 fixes are substantively closed. Correct the remaining K1/W7 and O3 integration/dependency bookkeeping before freezing revision 2 and recreating the GitHub issue set.
