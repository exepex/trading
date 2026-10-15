# Judge 125: story D3b text, a book's timely decision is its first original run (quality rule 1; judge C)

Date: 15 Oct 2026 (UTC). Branch `story/d3b-first-timely-decision` at **5251ddc447b9a3454a3679ad00924a11362ab10e**
(text only: `docs/stories/D-playbook-decisions.md` D3b, response 125), from `main` 49b09b1. Checked against:
- the orchestrator's decisions 58, 59 (b) and 60;
- judge 123 (E5b);
- the code at 5251ddc: `committed_decisions.py`, `decision_store.py`, `book1_records.py`, `evaluation/order.py`,
  `recorded_c4.py`, `decision_timing.py` and `scoreboard/*`.

## Verdict: PASS (text); 4 minor

**The design is right:**
- **The first original run is collected.** Corrections are recorded and shown apart, never collected or scored.
- **One shared order function.** It has a test that no caller sorts by itself.
- **The `-r10`/`-r2` name-sort bug is real.** I checked it: `DecisionStore.runs` sorts by folder name.
- **The builder's key finding is real.** `book1_records.decided_trades` globs every run's records on disk
  (`book1_records.py:34`), committed or not, and the last one with a trade ID wins. The fix (the opening run named in
  the entry day's run log) is the right source.

### The orchestrator's points

**(a) The reader table is complete for order-dependent readers. Two readers are missing (minor 1); neither depends on
order.**

My grep for `DecisionStore`, `DECISIONS_FOLDER`, `SUMS_FILE` and `.runs(` over `fno/` and `tools/` finds 16 files.
Beyond the table:
- `fno/desk/recorded_c4.py` reads the **collected** run's record and its `edited` check (`recorded_c4.py:24-32`), so it
  follows the collector.
- `fno/playbook/decision_timing.py` judges one given run and has **no caller** today.
- `book1_orders.py` builds orders from the run E3 hands it.
- `book1.py` (E5b) checks only whether a run exists.
- `no_decision.py` writes the marker file.
- `forecast_scoring/score_sources.py` matched on its own `RECORDS_SUFFIX` (`_forecasts.csv`), which is not a decision
  run.

Nothing in `market_read_models`, `cards`, packs or `tools/` reads decision runs.

**(b) Commit time as the key: two runs in one commit, and clock skew.**
- **One commit holding two runs:** both have the same commit time, and the counter as a number orders them. That is
  covered.
- **Clock skew (minor 2, reasoning only).** Commit time is the committing checkout's own clock.
  - Two checkouts racing on one book (both commit, one push is rejected, it pulls with a merge and pushes) give two
    commits on parallel branches. With a fast clock, the later decision can carry the earlier time and be collected as
    "first".
  - If the second commit was made after pulling the first, the first is its **ancestor**. Ancestry is the true landing
    order and immune to skew.
  - Suggested rule: order by ancestry where it decides (`git merge-base --is-ancestor`), and by commit time only for
    commits on parallel branches.
  - The risk is small: cloud clocks are synced to within seconds, and E5b prevents a second Book 1 run. But this story
    is the guarantee "whatever writes the run".

**(c) Can an uncommitted run ever be collected? No.**
- The collector's `_decision` returns None when no commit added the run's `records.sha256`
  (`committed_decisions.py:50-55`), so an uncommitted run has no commit time and is never compared with the deadline.
- "Sorts after committed runs" only places it in the run log's list.
- S1's `first_counted_decision` already asks git for each run's `records.sha256` (`order.py:61-62`). The shared order
  must keep "uncommitted is never first counted": say so in criterion 4b.
- A run committed locally but not pushed is a separate case, governed by E3's unchanged visibility rule. In the daily
  run's checkout, E2b's stray-commit refusal stops the run at its next commit (fail closed).

**(d) Trades opened by a run that later gets a correction: right, with one gap (minor 3).**
- The trade follows its opening run, and a later record naming the trade is alerted once and shown apart. That is the
  correct rule: a correction is information, never a change to a live position.
- **The gap:** the story makes the entry day's run log the source of the opening run. It does not say what happens when
  that log is missing, or names a run whose folder or `records.sha256` no longer matches.
- Say: alert once and never fall back to "the latest record". Also say how the trade's exits keep running in that case,
  since design 9 requires risk-reducing exits always to run, for example from terms held with the open position, or
  refused with an alert naming the trade.

## Minor

1. **Add the two missing readers to the table:** `recorded_c4.py` (reads the collected run; follows the collector) and
   `decision_timing.py` (one given run; no caller).
2. **Order by ancestry where it decides, commit time otherwise** ((b) above), or state why commit time alone is enough.
3. **State the opening-run fallback** ((d) above): run log missing or mismatched means an alert, never the latest
   record, and the exits' behaviour is named.
4. **Today `decided_trades` also counts trades from runs that were never collected or never filled**, for C2's view of
   the book (`book1_records.py:31-40`, "every trade the book's committed records chose"). With the opening-run rule,
   say that only trades opened by fills, from their opening run, are in the book, and add that to criterion 5's test.

## Project rules

- Lane 1, since it decides which decision trades. Rule 9 applies: ChatGPT after my code PASS.
- `fno/evaluation/order.py` is in no freeze: `research/evaluation/` holds no `FREEZE_v*.md` on `main` (checked).
- With criterion 7, any existing test that asserts the "latest timely run" must be named with its reason, which keeps
  changed tests visible.

**Verdict: PASS for 5251ddc447b9a3454a3679ad00924a11362ab10e** (story text). Code may start. Minors 1-4 go into the
text or the claims, and I check them in the code.

## Note (15 Oct 2026): the owner's "keep the design simple" rule

Under `docs/DESK_DECISIONS.md`, 15 Oct row "Keep the design simple", a judge's finding needs a path that happens in
the normal running of this system. Under that rule:
- **Minor 2 (ancestry for clock skew) is withdrawn.** It needs racing checkouts with skewed clocks.
- **Minor 3 (a missing or mismatched opening run log) becomes one line under the story's Known limits, with no code.**
  After E2b, the run log is committed with every step.
- **Minors 1 and 4 stand.** Minor 1 is text only. Minor 4 is a real path: a chosen trade that does not fill is a normal
  outcome.
