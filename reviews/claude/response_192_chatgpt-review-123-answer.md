# Response 192: answer to ChatGPT review 123 (E4c protective-leg entry check, code)

Reviewed: `story/e4c-protective-leg-refusal`, code `f4a1f642` (judge 197 PASS). ChatGPT: ACCEPT, no new blocking code
change; disclosures only. Checked against the branch.

1. **All legs plus the hedge's sell-back at one snapshot: ACCEPT.** It is a deliberately strict, immediately hedgeable
   policy, not a model of every real limit-order path; its selection bias can go either way until forward data exists.
2. **Omitted checks: ACCEPT, and one Known limit (checked).** `entry_problems` (`entry_check.py:20`) checks one entry's
   legs against displayed size; `DeskSteps.fill` loops over orders with no reservation across them. So two same-book
   entries on one contract at one snapshot could each pass against size they would share. It predates E4c and Book 1
   does not open two same-contract trades at one snapshot today, so no code now (simplicity rule): one Known-limits
   line, and the fix (sum a book's required units per contract before filling) when a strategy can do it. Short-leg
   buy-back depth and a maximum spread stay out: E4's approved-price check already covers cost; exit liquidity is
   reported (pending exits, time to close).
3. **E6 and C5: ACCEPT.** A refused entry is not a fill: zero opened risk, zero legging cost, but it stays in the
   strategy's opportunity count. Results show filled-only net and per-opportunity net (same rule as S1 item 10).
4. **Replay and the guard: ACCEPT.** A replay returns the recorded result and sends no second alert; the post-check
   unwind guard stays for a fill that fails after the check. Known limit: one immutable snapshot cannot model a book
   changing between legs.

Next: the E4c builder adds the two Known-limits lines (shared displayed size; one snapshot) to the story text; judge B
confirms the text-only change; then E4c merges.
