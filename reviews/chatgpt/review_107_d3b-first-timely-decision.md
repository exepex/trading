# Review 107 — D3b first timely decision

**Date:** 15 Oct 2026. **Reviewer:** ChatGPT, independent second reviewer under quality rule 9. **Scope:** `story/d3b-first-timely-decision` at `5ff83b2e16c67b223ba412b6e56dee480a08e9ff`; response 132, story D3b, builder response 125, judge 125 addendum 1 and source files `fno/desk/committed_decisions.py`, `fno/playbook/run_order.py`, `fno/books/opening_runs.py`, `book1_records.py`, `book1_exits.py`. **Verdict: PARTIAL overall: accept the first-original policy and opening-run binding; one integrity condition needs explicit enforcement before counted paper decisions.** Evidence labels follow AGENTS.md. Judge's 4,992-test result and mutations were not independently executed here.

## 1. First timely original rather than latest — ACCEPT (strong evidence on behavior; reasoning only on policy)

`D3CommittedDecisions.committed` iterates ordered runs, skips uncommitted/corrections and returns the earliest original only if its commit time is before the deadline (`committed_decisions.py`, `committed`). The first-original rule prevents a later model revision from replacing an unfavourable first answer after seeing new data. It is a **precommitted policy**, not an unbiased test of the best answer an AI could produce in the window: an AI book that improves within the window is deliberately scored on its first answer. That is fair if **all books** share the same issuance cutoff and first-answer rule, and if correction/late/refusal counts are reported. Do not relabel later improvements as traded decisions. A correction-only day has no original and must remain a no-decision day.

**Worked example:** original r1 at 15:03 and correction r2 at 15:05 before a 15:10 deadline => r1 is eligible, r2 is shown but not traded. Original r1 at 15:11 with deadline 15:10 => no trade, even if r2's file claims an earlier timestamp.

## 2. Commit-time order then numeric counter — PARTIAL (strong evidence on implemented order; reasoning only on clock-risk acceptance)

`run_order.ordered_runs` sorts by `(committed_at, run_counter)` and puts uncommitted runs last; `run_counter` parses the integer suffix. Thus r2 precedes r10 on equal commit time. The judge's r1/r2/r10 probe supports this. A commit's timestamp is supplied by its authoring checkout, **not a trusted server receipt**. E5b prevents a second Book-1 run but is not yet built, and D3b promises the same rule for Books 2/3. The stated two-checkout clock-skew exception therefore remains real in principle, but is not sufficient on its own to block a personal paper research system under the owner's simplicity decision.

**Exact operational condition:** before counting a book, enforce its single-writer/one-original-run policy and store the collector's observed repository head and receipt time. A duplicate original for one book/day must raise an integrity warning; do not silently call the committer timestamp an authoritative arrival time. If concurrent runners are enabled later, re-evaluate ancestry/receipt ordering.

## 3. Corrections never traded or scored — ACCEPT with mandatory audit (strong evidence)

`corrections(run.path)` finds non-null `corrects`; `others()` includes the link and reason; scoreboard B exposes uncollected runs. This prevents post-hoc strategy repair from contaminating forward P&L. A **genuine input error** found before the deadline must still be visible as an invalidated first decision, with its impact disclosed: original remains the historical decision, but if its C3/C4 evidence is invalid it **must not fill**. A corrected record can be reported as `correction_not_traded` and optionally scored in a separate exploratory diagnostic, never as a second confirmatory observation. Distinguish `late`, `invalid_first`, `corrected` and `no_original` in coverage statistics. This is not permission to retrospectively replace a failed trade.

## 4. Trade, exit, stop and double-count paths — PARTIAL (strong evidence: code)

**Positive:** `opening_runs._entry_days` uses actual `FILL_OPEN` rows and takes the earliest fill date per trade; `_opening_run` uses that date's collected run ID. `opening_trades` selects only a matching chosen record, so a correction cannot replace terms. `PlaybookExitRules.rules` retains E4's independent protection/settlement/pending exits when a time exit cannot be reconstructed. C2's book view refuses absent terms. The judge's tests address these paths.

**Remaining integrity gap:** `opening_runs._opening_run` checks that the run folder has a `records.sha256` and that the files match **that same local hash**, but does not bind the run to the **commit recorded in the entry-day run log**. `D3CommittedDecisions.recorded` does check a run against its recorded commit, but this stronger check is not used by `opening_runs`. A local replacement of a run's record **and** its `records.sha256` can pass the self-consistency check and change an already-filled trade's terms or time exit. The builder explicitly reports removing the logged-sums check because this requires a hand edit; that is a low-frequency but consequential integrity path.

**Required before counted paper decisions:** bind the opening run's identity and checksum to an independently immutable entry-day receipt/commit (for example, store and verify the expected `records.sha256` digest in the already committed run log, or verify the run's Git object at the logged commit). The former works in a shallow clone without deep Git history. Test changing both record and local checksum while leaving the logged receipt unchanged; the trade must lose its time exit, alert and block new entries rather than accept changed terms. Also verify that the `trade_id` in a fill belongs to the run's chosen record and opportunity, not merely a reused identifier.

**Execution/risk consequence:** a missing opening run currently removes the scheduled time exit. The independent risk-reducing exits still work, but holding longer can change realised P&L. Publish the incident, affected position, missed scheduled exit and subsequent price; do not silently score it as an ordinary completed trade.

## Financial-role cross-check

- **Mathematician / statistician / quantitative modeller:** first issuance fixes the estimand and prevents optional resubmission; count invalid, corrected and missing opportunities as part of the denominator.
- **F&O trader / options strategist / volatility trader / execution:** an unchanged trade may still face gap/legging risk; losing its time exit can be costly, so alert and preserve risk-reducing exits.
- **Risk manager / portfolio manager / head of desk:** C2 must fail closed on missing opening terms; one active writer per book and no post-hoc corrections are essential.
- **Market research, macro, derivatives flow, equity analyst and investment banker:** later event/news updates are information, not permission to overwrite an earlier decision.
- **Regulation / tax-cost accountant:** the recorded execution and charge history must remain immutable; a correction must not alter fees or realised taxable P&L.
- **Behavioural finance:** first-run locking prevents chasing the latest AI answer; corrections should not be hidden.
- **Data/backtesting engineer / red team:** attack a jointly edited record+checksum, duplicated trade IDs and a missing receipt; the self-hash alone does not authenticate origin.

## Decision

**PARTIAL** on questions 2 and 4; **ACCEPT** questions 1 and 3. No evidence of a normal-path cap bypass in the reviewed code, but the opening-run hash needs binding to an independent committed receipt before counted autonomous paper trading. The first-original rule itself is accepted. No real orders are authorized.
