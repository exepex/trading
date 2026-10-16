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
- **F6/F7 (session_01KTAQCDjPkDBKwfCMhWphXb):** the same for Book 3; verdicts never block. Answer: pending.

## Owner questions (via the orchestrator)

1. F4b (meaning re-checked monthly by another model): recommended yes, after a month of Book 2 decisions.
2. Strict interpretation (every number cited, also on `follow_rule` days): recommended keep strict and measure.

## Monthly audit routine (for the orchestrator; builders never create scheduled tasks)

Proposed stored prompt, 2nd of each month, 09:00 IST: "Run `sh tools/routine_setup.sh`, then
`python -m fno judge audit <last month as YYYY-MM>`; commit and push `journal/judge/audits/` (`git pull --no-rebase`
first); if it printed 'alert NOT sent', post its lines to #fno-desk with the Slack connector."
