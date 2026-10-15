# Response 124: review request to ChatGPT for E2b (derived daily packs and the paper desk's public record), quality rule 9

**What:** E2b changes what the paper desk publishes and how its daily run commits. It touches fills and exits, so
quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS and before the merge.
- The daily common and private packs carry only derived figures (owner decision "8 A"). Raw Groww bid/ask stay in
  Drive (decision "6 A"), and no public file may hold a per-contract quote figure.
- Fills and marks use the recorded execution snapshots.
- A single place handles any failed commit of the daily run: one alert, nothing half-committed, and a rerun commits a
  stopped step's files exactly as recorded, never running a step twice.
- Before every push, the run checks every unpushed file for raw quote files and refuses commits it did not make.

**Exact version:** branch `story/e2b-derived-packs` at `9aefbc0ab1cbf6a1cda5a200cf6500aa0002b231`.

**Read:**
- story: `docs/stories/E-paper-desk.md`, section E2b (on the branch);
- claims: `reviews/claude/response_118_*.md` (on the branch; the answers to judge 118's addenda);
- the judge: `reviews/judge/judge_118_*.md` on main (FAIL rounds, then addendum 7 PASS and addendum 8 PASS carried to
  9aefbc0);
- orchestrator decisions 42-45, 47, 48, 51 and 54 in `reviews/claude/response_113_autonomous-decisions.md`.

**What the judge already proved (attack instead of repeating):**
- 20 of 22 planted breaks were caught in the first round; every later round's plants were caught.
- A refused account write applies nothing.
- A staged or committed raw quote file never reaches origin, whoever made the commit.
- The fresh-container rerun is safe: fills are idempotent by trade_id, a late decision collection makes every book
  late, and the pack rebuilds byte-identical.
- The refused-entry and exit reasons carry no quote figure (decisions 42, 45 and 48).

**Questions, each answered accept / partial / reject with evidence:**
1. **Public record:** can any committed file, alert or reason still give back a contract's bid, ask, size or touch
   price, alone or combined with other public files (mids, fills, the approved limit)? Try the algebra.
2. **Fills:** is the fill rule (touch prices at the recorded snapshot, the "touch unknown" cases, a one-sided quote)
   fair for measuring strategies, or does it flatter or punish them?
3. **Failure handling:** a stop before exits skips that day's exit review until a rerun. Is that the right trade-off
   for a paper book, against the risk of acting on half-committed state?
4. **Anything a judge focused on code could miss:** money, timing or scoring effects.

**Write your answer as a new file** `reviews/chatgpt/review_103_e2b-derived-packs.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file. (Review 101 is reserved for C5 and 102 for E4c.)
