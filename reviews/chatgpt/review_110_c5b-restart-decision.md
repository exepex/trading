# Review 110 — C5b brake restart linked to owner decision

**Date:** 15 October 2026. **Reviewer:** ChatGPT, independent second reviewer under quality rule 9. **Target:** `story/c5b-restart-decision` at `b2a4b0dd322c29b639d2b07530491e5bab173b0e`. Reviewed response 138, C5b story, response 135 addendum 2, judge 134's reported results, Review 103, C2 `decision_rows.py` / `overrides.py`, C4 `validity_decisions.py`, and `docs/JUDGE.md`. **Overall verdict: ACCEPT for this personal paper-only system, with one documented governance condition.** Evidence labels follow AGENTS.md. Reported 21 mutations and full suite were not independently executed here.

## 1. Is owner-row citation plus judge audit enough? — ACCEPT (strong evidence for the implemented gates; reasoning only for governance sufficiency)

**Yes, for counted paper decisions.** A typed `entered_by` alone was insufficient in Review 103. Now `fno/risk/decision_rows.py:RestartDecisions.check` validates the cited title's uniqueness, owner-quote marker, whole-word book name, date and non-reuse. `fno/checks/validity_decisions.py:decision_problem` independently checks the same conditions. `docs/JUDGE.md`, “Brake restarts (story C5b),” explicitly requires the judge to read the quoted owner words, confirm the particular brake episode, and refuse doubtful provenance. The 21 reported mutation probes support these mechanical gates.

**Threat model and condition:** an agent with repository write permission could fabricate a decision row containing `(owner: "...")`. The code cannot authenticate authorship, and the Markdown marker is not a signature. However, this is a **personal research/paper system with no real orders**, and the normal path includes lane-1 review and judge audit of every override. Under the owner's “keep the design simple” rule, this is a reasonable human authorization boundary; do **not** add cryptographic signatures or another token store now.

**Simplest required operational condition:** the judge must verify the owner statement from the actual owner conversation/approval record, **not infer authenticity from the Markdown syntax alone**, before accepting a restart. If the judge cannot verify the words, FAIL. This is already the intent of the added `JUDGE.md` paragraph; no additional production code is required.

**Would this change a trade or stop?** Yes: accepting a fabricated restart would release the ₹120,000 drawdown brake. The judge's human provenance check is therefore essential, not cosmetic.

## 2. Wrong book, old episode reuse, or valid row refused — PARTIAL (strong evidence on code; reasoning only on remaining semantic risk)

**Wrong book:** the `BOOK_DISPLAY_NAMES` mapping and `\bBook 1\b` whole-word check prevent a Book 1 citation from being used for Book 2 and prevent “Book 10” matching “Book 1”. The reported C2/C4 tests cover both. **ACCEPT** the mechanical book isolation.

**Same-row reuse:** `RestartDecisions.check` counts repeated cited titles within one book's overrides and refuses duplicates; C4 does likewise. **ACCEPT** the same-title replay protection.

**Old episode with a *different* decision title:** a row saying “restart Book 1” from an earlier episode could be cited once for a later episode if never previously used. Code checks `row.day <= restart_day`, not whether the decision follows the most recent brake trigger. This could lift a later brake and **would change a stop/trade** if the judge accepted it. The design explicitly assigns episode identity to the judge, and `JUDGE.md` now requires checking that it concerns “the brake that fired before that date, not an earlier one.” **ACCEPT this human check as sufficient for normal lane-1 use**, but note that the date/uniqueness checks alone do not prove episode freshness. Do not claim they do.

**Correct owner row refused:** a legitimate owner decision with no unique first bold title, a book named only by internal ID, or a title duplicated elsewhere will fail closed. This is a deliberate formatting constraint, not a reason to trade despite uncertainty. The judge can ask the owner to add a uniquely titled, book-specific row in the standard format. The real file has 17 untitled rows and four “approved” rows, so the issue is concrete; none of those can be used directly. **Some evidence:** judge 134's real-file counts; **strong evidence:** parser logic.

**Would a change alter a signal/stop?** An old-episode citation could lift a stop. No new parser is necessary if the judge's audit actually checks the episode and the source of the owner's words. A false refusal blocks entries, not increases risk; resolving it by a properly titled owner decision is safer than loosening validation.

## 3. Shadow-book brakes cannot be restarted — ACCEPT (reasoning only)

Shadow accounts are exploratory research, not owner-funded live accounts. `RestartDecisions.check` and C4 `decision_problem` explicitly reject books absent from `BOOK_DISPLAY_NAMES`, rather than accidentally accepting or crashing. Keeping a shadow book braked permanently is a conservative experiment-ending rule, not a money-safety defect. It can reduce sample coverage and make shadow results selectively incomplete: report the brake date, rejected opportunities and whether the shadow ended early. If the owner later needs continued shadow observation, register a new shadow version/cohort with a clearly marked new start; do not quietly erase the prior drawdown.

**Would this change a trade or stop?** It prevents further *shadow* paper entries after a brake, intentionally. It does not lift a real book's brake or permit a real order.

## Role checks and final decision

Mathematician/statistician/quant: a restart changes the sample regime and must be disclosed; no backfilling excluded decisions. F&O/options/volatility trader and execution: restarting does not repair spread/gap or tail risk. Risk manager/portfolio/head of desk: only a verified owner instruction may lift a ₹120k stop; per-book isolation is essential. Market/macro/flows/equity/investment banking: fresh information is not a substitute for owner authorization. Regulation: no live broker order is created. Behavioural finance: the manual approval step reduces revenge trading. Tax/cost accounting: restart is neither capital nor P&L. Data engineer/red team: agent-written owner text is the residual threat; judge verifies original source and episode.

**Final verdict: ACCEPT.** C5b meets Review 103 point 4 for the project's current paper-only workflow, provided the lane-1 judge audit authenticates the owner's actual statement and the specific brake episode. The absence of cryptography is an explicitly accepted limit, not a reason for more code. No existing review file should be overwritten.
