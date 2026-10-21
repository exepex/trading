# Story O1-status-only: the public run log carries status, never data

Owner: the O1/O2 builder (session_014zYLf18PgCzR7YoHs1X5Dp). Lane 1, judge D. Ordered by the orchestrator on 21 Oct
2026, after judge 440 and O1's audit.

## The gap (strong evidence, from the audit of 21 Oct)

`journal/runs/<date>.json` is committed, so it is public. The daily run writes each step's whole result into it,
including free text. The four committed logs (17, 19, 20 and 21 Oct) are clean, but only because no trade has happened
yet. These are the code paths that put data values there:

| Step (owner) | Source | Value |
|---|---|---|
| exits (E3) | `fno/desk/exits.py:179`, `:166`; `settlement.py:72` | "net Rs ..." on every close; NSE's settlement price |
| owner_timing_fills (E8) | `exit_fills.py:49` through `exits.py:179` | the same "net Rs ..." |
| fills, exits (C3) | `fno/checks/market_checks.py:49`, `:58` | NIFTY spot and previous close, even with no trade open |
| fills (C2) | `fno/risk/rules.py`, `caps.py`, `drawdown.py` through `entries.py:96` | loss, margin, cash, equity, drawdown in Rs (refusal path) |
| reviews (E6) | `fno/scorecard/pauses.py:75`, `:109-110` | a trade's loss, its cap and the realised loss in Rs |
| pack (E2) | `fno/desk/snapshot_inputs.py:47` | NIFTY spot levels in one error |
| price_distribution (G13) | `density.py:26` `MEAN_OFF`, kept in `lines` | the forecast's mean and forward index levels |
| every command step (O1) | `fno/daily/processes.py:103` merges stderr | tracebacks, library logs, exception text |

Secrets are a separate question, already answered: the record scan refuses a token-shaped string in `journal/runs`
(tested 21 Oct with five token shapes; the commit is refused and the desk stops). A secret of an unknown shape inside a
traceback would not be caught, which is one more reason the text must not be there at all.

**Known exposure until this story lands (orchestrator, 21 Oct):** G13's `MEAN_OFF` line goes live on 22 Oct. It is a
rare problem path and an index level is public information, so G13's scoring file is not changed on go-live day. This
story ends it without touching G13: command steps no longer keep their printed lines in the public log.

## Who reads the run log, and what (the inventory of 21 Oct)

No reader matches on free text. Every decision uses `status`, `valid`, `reviewed`, `run_id`, `commit`, `snapshot_id`,
`committed_at`, `started_at`/`finished_at`, whether `error` or `waiting` is present, or whether a step is recorded.
Free text is only shown to people, in four places:
- the health check's detail (`fno/health/desk_checks.py` `_problems`);
- the card's "no valid execution snapshot (reason)" line (`fno/cards/rule_checks.py` `_verdict`);
- scoreboard B's `exit_review` field (`fno/scoreboard/committed_runs.py` `_unreviewed`);
- the next day's block reasons (`fno/desk/daily_run.py` `_unreviewed`, `_unfilled`, `_unscored`), which go into fills'
  result and alerts.

One reader breaks if `reason` is dropped: `_unfilled` reads `result["reason"]` with `[]`.

## The rule

The public run log holds, per step, only:
- the step's times and `status`;
- booleans, integer counts, and strings from a closed vocabulary: ids (run, snapshot, trade), commit and file hashes,
  ISO times and dates, step and book names, and each step's own status words (`how`, `outcome`);
- in place of every free-text field (`reason`, `error`, `line`, `lines` and the like), a **reason code** from a closed
  set for that step.

No float, no free text, and no child output reach it. The full text still goes to the #fno-desk alert (a private
channel), as today, and to a private full log (below).

## Design

1. **One boundary: `PublicResult`, applied where the desk records a step.** A new module, `fno/daily/public_log.py`
   (O1), turns a step's inputs and result into their public form. `DailyRun._step` (E3) records the public form in
   `RunLog`, so the run's own later readers and every rerun see the same thing as the file. The policy is injected
   from O1's composition root (`fno/daily/wiring.py` through `build_daily_run`). E3's own tests keep the identity
   default. A test asserts that the built day runner always carries the policy, so the live run can never write
   without it.
2. **Reason codes, without changing the producers.** Each step's codes are its producers' own message templates, named
   by their constants (for example `NOT_VALIDATED`, `BLOCKED`, `UNFILLED`, `STILL_RUNNING`, `NOTHING_WRITTEN`).
   - A text maps to the code of the template whose fixed prefix (the text before its first `{`) it starts with,
     longest prefix first.
   - **Any text that matches no template becomes `unlisted`.** So a new or changed message can never leak; it only
     loses its code until it is listed. A test lists every template in the registry and proves each maps to its own
     code.
   - Command steps use O1's own codes: `ok`, `nothing_written`, `exit_<n>`, `stopped_at_limit`, `not_live`,
     `no_live_date`, and `raised:<ExceptionType>`, where the type is kept only if it is a Python identifier.
   - Their `lines` are dropped. The quote parts keep `status`, `exit_code`, `how`, `started_at` and `commit`.
3. **`error` keeps its meaning.** It becomes `raised:<ExceptionType>`, which is still truthy, so `_unreviewed` and
   scoreboard B's missed-review rule work unchanged. `waiting` stays a list, and its items must pass the same
   vocabulary as any other string.
4. **The readers that show text** read the code instead: health, the card line, scoreboard B and the block reasons.
   For example: "exits not reviewed on 2026-10-21 (exit_review: raised:OSError)". The full text of that failure was
   already alerted on its own day. `_unfilled` reads `.get("reason_code")`. Old logs, written before this story,
   still hold text, so every reader uses `.get` and accepts both forms.
5. **Child stderr is no longer merged into stdout** (`ChildProcesses`). It goes to its own temporary file, and an
   unsent alert line is still relayed to the routine. Child output, stdout and stderr alike, is kept whole only in
   the private log.
6. **The private full log.** The full results (text, lines and child output) go to a git-ignored
   `journal/runs/.full/<date>.json` for the same container's reruns and for debugging. At the run's end the same
   content is written once to Drive through O9's data store (one file per run attempt, with its receipt). It never
   reaches the repository: the folder is in `.gitignore`, and a test proves it.

## Owners whose code this touches (agreed before the code, under the one-builder rule)

- E3: `fno/desk/daily_run.py` (`_step` records the public form; the three block-reason readers), and the
  `build_daily_run` parameter.
- O8: `fno/health/desk_checks.py`. T1: `fno/cards/rule_checks.py`. S2: `fno/scoreboard/committed_runs.py`. Each only
  reads codes, with `.get`.
- No producer's message changes: E3's, E6's, C2's, C3's, E8's and G13's texts stay as they are, so their alerts lose
  nothing.

## Acceptance

1. **A planted-value test through the real `DailyRun` and the real `PublicResult`.** A step result whose `reason`,
   `error`, `lines` and nested `results[].reason` hold "net Rs 12,345.60", a spot level "22,811.35", a float and an
   exception text with a path. The committed `journal/runs/<date>.json` contains none of those strings, no float, and
   only codes from the step's closed set or `unlisted`.
2. **The same for a real child.** A command that prints a price line and writes a traceback to stderr: neither its
   stdout nor its stderr text reaches the public log. Its unsent-alert line is still relayed to the routine.
3. **Every template in the registry maps to its own code.** An unknown text maps to `unlisted`.
4. **Readers work on both forms.** O2's whole e2e suite (normal day, outages, kill-rerun, hangs) passes unchanged in
   its status assertions. Readers of an old, text-bearing log (one of the four committed ones) still work.
5. **`_unfilled`, `_unreviewed` and `_unscored` still block on the same conditions.** Their block text names the code.
6. **The full log is git-ignored and never committed** (the same check as G4's list).
7. **The built day runner always carries the policy.**

## Known limits

- A code says which message it was, never its values. Debugging a day needs the private full log or the alert.
- A message reworded by its owner shows `unlisted` until its template is added to the registry. That is the safe side.
