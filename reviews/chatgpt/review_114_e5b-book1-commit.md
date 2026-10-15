# Review 114 — E5b Book 1 commit failure and one decision per day

**Reviewed version:** `story/e5b-book1-commit-failure` at `1a7d5f18` (not latest branch). **Reviewer:** ChatGPT, independent second reviewer under quality rule 9. Read `AGENTS.md`, request 156, E5b story, response 123 code round, response 134, Review 107, and the relevant Book 1, Git, pending-commit and test code. **Overall: ACCEPT for the present personal paper-only system.** The remaining concurrent-writer case is a Known limit, not a reason for more code before a Book 1 routine exists. Evidence labels follow AGENTS.md. Judge 163's PASS and builder's reported tests were examined, not independently executed (the connected repository does not expose a local executable checkout).

## 1. Can normal running create two counted decisions or count changed inputs? — ACCEPT (strong evidence: code and tests)

`fno/books/book1.py:Book1.decide` first calls `committer.recover()`, then `decided.find(day)`; any found run returns through `_already` and **does not call `run.decide`**. `fno/books/decided_runs.py:GitDecidedRuns.find` fetches origin and checks origin, local HEAD and disk. If origin is unavailable, it raises `CommitFailed` rather than deciding without the check. `Book1._already` compares fresh `inputs.json` with the recorded bytes and alerts on changed top-level fields; it never replaces the first decision. `tests/book1/test_commit_failure.py` covers changed cash, marker recovery, disk-only and sequential checkouts.

D3b's first timely **non-correction** run determines the collected decision; a duplicate original, if present, triggers the collector alert rather than making the latest decision count. Thus two *stored* runs are possible under concurrent writers, but not two **counted** originals in the normal D3b path. This is a distinction, not a claim that duplicates are impossible.

**Worked sequence:** 15:02 r1 written; push fails; 15:06 book cash changes. A rerun recovers and pushes r1's original bytes, alerts that `inputs.json: book` changed, and does not produce r2. If r1 reaches origin only after the collector's deadline, it is late; recovery cannot backdate it into a counted trade.

**Normal-path limitation:** `_already` recomputes D2 *read-only* to compare inputs. This may be expensive or fail when today's inputs are unavailable, but it does not write another decision. No new guard is justified unless a real failure shows an alert or exit was lost.

## 2. Two checkouts at exactly the same time — ACCEPT as Known limit (reasoning only; strong evidence for existing fallback)

The pre-commit origin re-check was intentionally dropped by owner/orchestrator decision 67. Two simultaneous checkouts could each fetch before either pushes and create two originals; the story's original acceptance criterion overpromises prevention of that precise case. The builder explicitly disclosed the deviation. D3b deterministically selects the first timely original, and `daily_steps` alerts on multiple originals. **No Book 1 routine exists yet**, and the sequential two-checkout test already proves the ordinary retry path finds the first origin run.

**One Known limits line:** “Concurrent Book 1 writers may publish two original runs; D3b counts only the first timely one and alerts on duplicates. Revisit single-writer scheduling if a routine is introduced.” No lock service or VerifiedPass-style infrastructure is needed now. If a second writer is actually scheduled, prevent overlapping runs operationally before enabling it.

## 3. Pending-marker recovery and `--commit-run` — ACCEPT (strong evidence: code and real-Git tests)

`fno/desk/pending_commit.py` writes an atomic marker containing the original message and SHA-256 for each file before attempting the commit. `recover` verifies every file, then commits/pushes those bytes; a changed/missing file raises `PendingChanged`, never regenerates D2. `book1.py:commit_run` accepts only a run found **on disk only**, checks `DecisionStore.edited`, and calls the committer without invoking D2. `book1_cli.py` converts `CommitFailed` into one alert, one printed line and exit 1. The separate `.pending_book1.json` avoids overwriting the daily-run marker.

**Tests with actual Git repositories** in `tests/book1/test_commit_failure.py` cover staged raw quotes, unreachable origin, three rejected pushes, changed inputs, changed recorded files, hand recovery, second checkout, and marker isolation. Those are realistic failures for this workflow. A self-consistent hand edit to a disk-only run and its checksum remains a documented integrity limit, but needs intentional manipulation and is not a normal-path blocker under the owner's simplicity rule.

## 4. Anything that changes a trade or stop and must change before merge? — ACCEPT: no new blocker (strong evidence on control flow; reasoning only on operational implications)

The previous failure mode was consequential: a failed push could leave an uncounted first decision and a later run could decide using fresher inputs, changing a trade. E5b removes that normal path. A failed Book 1 push may still block the daily run in the **same checkout** because of an unpushed commit, so the operational alert must be acted on promptly; this is already disclosed in the CLI error and was tested. E5b does not itself repair or guarantee timely exits; do not present an alert as an executed exit.

**Non-blocking documentation correction:** E5b's story still says the second check before commit prevents simultaneous writers, but response 123 says it was removed. Align that sentence with decision 67 at the next story-text edit; do not add code solely to satisfy obsolete wording. A late push must remain late, never become a backdated successful decision.

## Role-by-role check

- **Mathematician / statistician / quant researcher / quantitative modeller:** first-original selection prevents optional resubmission and biased forward scores; count late, missed and duplicate days in coverage.
- **F&O trader / options strategist / volatility trader:** a later IV/spot update must not replace a recorded signal; fills and option economics remain governed by E4/E8.
- **Risk manager / portfolio manager / head of desk:** one counted decision per book/day is essential; failed commit or missed exit needs operational visibility, not a fictitious NO TRADE.
- **Market research / macro economist / derivatives flows / equity research / investment banker:** later news, OI, RBI/Fed or earnings changes are information, not grounds to rewrite a committed decision.
- **Market microstructure / execution:** the true decision arrival deadline and the next-session fill rule are distinct; a delayed push can cause a no-fill.
- **Regulation:** paper only, no broker order.
- **Behavioural finance:** refusing to re-decide prevents chasing a newer, more flattering signal.
- **Tax and cost accountant:** a retry cannot duplicate a trade, fee or P&L solely by regenerating a decision; actual fills remain the accounting source.
- **Data/backtesting engineer / red team:** origin/HEAD/disk checks and pending SHA-256 recovery address real Git failure paths; concurrent writers and intentional file+checksum edits remain documented limits.

## Final verdict

**ACCEPT E5b at `1a7d5f18` for merge under quality rule 9.** No demonstrated normal-path trade/stop error requires another code change. Preserve D3b first-original selection and duplicate alert; clarify the outdated concurrent-writer promise in documentation when next edited. No real orders are authorized.
