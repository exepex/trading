# Judge 255: dashboard contract 2.13.0 (nullable `answer_on`; `FnoPageHolds`)

Dashboard `story/fno-contract-2-13` at a0a355d (screens lead 01XFXpbkyixX7SuXeQCp5EnX), on main 47d0328. Lane 1
(contract). Judge D, 16 Oct 2026.

**FAIL: one should-fix.** Both additions are right in shape. The page-holds reason rule contradicts P11's own passed
text.

**Met:**
- **`today.answer_on` is nullable:** null when the answer session falls in a year whose NSE calendar is not
  published. This is option (b) of judge 244, and every 2.12 payload stays valid. The waiting example is dated
  2026-12-04 with Q1's `answer_on` null, and mockup 37 says "Not known yet".
- **`FnoPageHolds` (judge 251 option (b)):** `{page_key, since, reason, shows: previous_page | nothing}`, closed,
  public, with x-never-sent covering the figures and the value that broke the rule. `shows` carries P11's "shown"
  and "dropped" cases. There are three examples (none, held, first), and the mockup 44 drawing goes through
  MOCKUPS_ALSO.
- **Gates:** `check_contract` and `check_fno_screens` exit 0 on a0a355d. The digits probe ("Max loss Rs 10,500 above
  the cap") is refused.

## Finding (should-fix)

**The reason pattern `^[^0-9]*$` refuses P11's own card rule, which would stop every page.**
- P11's passed text (judge 251, design item 3) fixes the card's rule as "risk-rule breach: C2 sizing or C4 validity let
  a trade past its book's per-trade cap". It holds the digits 2 and 4. **My planted run:** that sentence in
  `getFnoPageHolds_india_held` is refused (`payload/holds/0/reason`).
- P11 says `page_holds` itself is never held, so a refused `page_holds` is `ContractBroken`, a whole-run stop, on
  the very day of the over-cap card the hold exists for.
- The examples' reasons ("A trade broke a risk rule: its maximum loss is above its book's cap" and the others) are also
  not P11's sentences. Two lists of the same fixed sentences will drift.

**Fix:** one list of hold sentences, owned by P11's code (each user's story fixes its own), and a pattern that
admits them. Either:
- P11's sentences avoid digits (for example "the risk sizing or the validity check let a trade past its book's
  per-trade cap"), with the P11 text updated to say so; or
- the pattern forbids amounts but admits story ids such as `C2`. That is harder to make value-proof, so I prefer the
  first.

The examples should use P11's sentences, and P11's code round should test that every sentence passes the pinned
pattern.

**Note:** P11's text calls the field `rule`. The contract names it `reason` (the privacy check refuses rule-like
keys), and adds `shows`. P11's code must use the contract's names; record that in P11's text at its code round.
