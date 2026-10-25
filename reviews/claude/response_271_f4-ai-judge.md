# Response 271: F4, the judge of the AI books' daily decisions and its monthly audit (text round)

Builder: session_01AN94h4cY98oYa3CF2MZfak · Branch: `story/f4-ai-judge` · Judge: E · Story: `docs/stories/F4-ai-judge.md`

## Claims (text round)

1. The amended F4 text needed changes, so it is rewritten to design v2 in `docs/stories/F4-ai-judge.md`; the F4
   section of `F-ai-layer.md` now points there (as F5 did).
2. **The daily judge is code, not an AI session.** Evidence (strong, F1t's story at 13653f05): reveal 15:10:10,
   observation 2 at 15:11:00, promotion committed before 15:12:00, F5's `decide()` budget 30 s; F1's measured
   fire-to-answer was 66-99 s on 16 Oct (its best day) and about 5 min on 15 Oct. An AI judge cannot fit, and a miss
   is a Book 2 fail by the F4 text, so it would turn Book 2 into a no-trade book. What code cannot check (whether
   the reasoning is sound) is named as F4b, out, owner question 1.
3. Every requirement of the amended F4 text is in the gap list as a criterion or out with its reason.
4. The port is dependency-free (`JudgeCase` of plain mappings), so F1t adapts its `AcceptedDecision` in one place and
   `fno/judge` never imports `fno/ai_trading`.

## Coordination (sent 16 Oct; answers recorded here when they arrive)

- **F1t (session_01PLbKH15BXYucP6cT9xtoxK):** the judge runs in `ai_collect` after F1t's own checks and before
  `decide()`; new status `judge_failed` (Book 2, no trade); `AcceptedDecision.judge` = verdict path; verdict file
  committed with the outcome record. Answer: pending.
- **F5 (session_01SFDjjZx7JYziM3jqJytG2z):** top-level `evidence` key in Book 2's decision, `check_decision` calls
  `fno.judge.evidence.evidence_problems`, three prompt lines, D3 `judge` field. Answer: pending.
- **F6/F7 (session_01KTAQCDjPkDBKwfCMhWphXb):** the same for Book 3; verdicts never block. Answer (16 Oct): agreed;
  shadow entries, trades and proposals each carry `reason`, `spec` is not a reason; D3 `judge` set from
  `AcceptedDecision.judge` through the run context. Condition accepted: F6 adds `evidence` in one follow-up after
  `fno/judge/evidence.py` is on main (F6's judge re-checks it as an addendum); Book 3 cannot go live before. Push-back
  (a reason may cite a private pointer without writing its number): already so, the check runs one way; now stated
  in design 2.

## Owner questions (via the orchestrator)

1. F4b (meaning re-checked monthly by another model): recommended yes, after a month of Book 2 decisions.
2. Strict interpretation (every number cited, also on `follow_rule` days): recommended keep strict and measure.

## Monthly audit routine (for the orchestrator; builders never create scheduled tasks)

Proposed stored prompt, 2nd of each month, 09:00 IST: "Run `sh tools/routine_setup.sh`, then
`python -m fno judge audit <last month as YYYY-MM>`; commit and push `journal/judge/audits/` (`git pull --no-rebase`
first); if it printed 'alert NOT sent', post its lines to #fno-desk with the Slack connector."

## Judge 308 (FAIL, 2 should-fix, 2 minor) on 80c3ca5f: each finding

Numbering: this claims file keeps 271 (reserved by the orchestrator in `reviews/claude/README.md`); judge E's verdict is
308 (its range). Different folders, no clash.

1. **Should-fix 1, owner's word before code: accepted.** Checked: DESK_DECISIONS line 254 says "F4 follows its amended
   text", which names an AI session. Question 1 now states both options and that code waits for the answer; sent to
   the orchestrator to take to the owner.
2. **Should-fix 2, interfaces: accepted.** `change` replaced by "any action other than `follow_rule`" (checked: F5's
   slot actions are `follow_rule | trade | no_trade`). Asked F1t (status `judge_failed`, the `JudgeStep` call before
   `decide()`, `AcceptedDecision.judge`, the judge's time in 15:11-15:12, and correcting "travels inside the decision"),
   F5 and F6 (the `evidence` key and the `evidence_problems` call) to put the agreement into their own texts for
   judge E's addenda.
3. **Minor 1, citable private values: accepted,** stated in design 2.
4. **Minor 2, where the audit runs: accepted,** design 5 item 6: the owner's scheduled routine session with the Drive
   settings; without them it stops with an alert.

## Partner texts for judge 308 should-fix 2

- **F6:** done at `c625151e` (`story/f6-book3-engine`, `docs/stories/F6-F7-book3.md`, "F6 addendum 1"): the evidence
  shape and the `check_decision` call, the prompt lines (account files not citable, `/evaluation` scalars are), D3
  `judge` from `AcceptedDecision.judge`, verdicts never block, the sequencing note, criterion 17. Read by me: matches
  F4 design 1-3.
- **F5 (16 Oct):** agreed to the `evidence` key, the call and the prompt lines. Checked each point:
  - correction 1 (`change` is stale): already fixed at 90066e7d; slot changes are covered because `check_decision`
    refuses a `follow_rule` top level over a changed slot; now stated.
  - correction 2 (dates, IDs and strategy names in reasons): checked the tokenizer: "sc-iv-v1" gives no token (the digit
    follows a letter), but an ID such as "opp-3" gives "3", and "27 Nov" gives "27". Chosen: the values the decision
    names outside its reasons (IDs, width, lots; text over 200 characters excluded) count as allowed, since F5/F6 and
    C4 check them against the sheet; dates in prose are cited and written as the pack writes them. Reason: an
    exemption by pattern would let any invented date through.
  - push-back (no D3 run on a judge fail loses scoreboard A's paired day): **accepted.** Checked: the amended F4 text
    says "the rule default is recorded as a shadow", which my design 4 had missed. Now `decide()` always runs with
    `judge_blocks`; Book 2 writes "no trade, judge failed" with the rule default as a shadow; F1t's run check refuses a
    blocked run holding a chosen trade (defence in depth).
  - known limit stated in Context.
- **F5's text:** `story/f5-book2-decider` 61f0f1aa holds the evidence key, the call, the prompt lines and D3 `judge`;
  `0bb574de` adds the `judge_blocks` run (criterion 11) and the dates prompt line. Read by me: matches F4 design 2 and 4.
- **F1t:** requested (port updated to the above); pending.
- **Owner question 1 answered** (orchestrator, 16 Oct; DESK_DECISIONS line 257): "Code daily + AI monthly
  (Recommended)". Q2, orchestrator's ruling: strict on `follow_rule` days, measure the first month. Both in the text
  under "Owner decisions".
