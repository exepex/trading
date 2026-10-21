# Response 270: F5 story text, Book 2's AI decider rewritten to design v2 (for judge E)

**Branch:** `story/f5-book2-decider`. The text is in `docs/stories/F5-book2.md`. `F-ai-layer.md`'s old F5 now points to
it.

**Why rewritten:** the old F5 predates design v2. It fed the red team (F3) and owner overrides into Book 2. REPLAN
turns F3 into the devil's advocate, whose objections can never block, and DESK_DECISIONS row 229 drops overrides
on paper.

**What the text decides, and who agreed it:**

| Point | Decision | Agreed with |
|---|---|---|
| Where the AI sees the rule default | A `BookSheet` E2 hook in the `pack` step, written into Book 2's private pack as `"evaluation"`. No journal file, because a committed file would be public (E2c's privacy rule; the O9 rule) | E2c's owner 0134MoC6 proposed it, and who edits the pack code is still open; F6's builder 01KTAQCD wants one hook for Books 2 and 3; O1's builder 014zYLf1 confirmed D2 needs data that exists only from the `pack` step |
| Hand-over | F1t's `AiBookDecider.decide(AcceptedDecision) -> DecidedRun`. F1t fills no record field | F1t 01PLbKH15 (story/f1t-ai-trading-runner f1204a5a) |
| Answer check | `check_decision`, standard library only, called by F1t's `seal` | F1t |
| Selection | F6's generic `SelectionAllocator` with `Pick(opportunity_id, reason, width, lots)` and a `rebuild`, so one implementation serves both books | F6's builder |
| C4 independence | C4 reads `rule_default` and `eligible` from the hash-covered sheet, never from the AI. D3's replay recomputes them | F1t; for judge E to accept or reject |
| Unproven limit | Re-checked at C4 from E5's counts | judge 260 addendum 2 (D4 option 2, for F5's switch-on) |
| Estimand | "AI veto and width selection within the same registered playbook" | D4's known limits; ChatGPT review 130 |

**Open questions in the text:**
1. Does Book 2 switch on without F4's AI judge? I recommend waiting for F4 (reasoning only).
2. One slot per rule-default trade, or a whole set?

**For the judge:**
- The 30 s budget is an estimate (reasoning only): D2 is not re-run at 15:11, only C2, C4 and the store write.
- The E2 hook changes E2c's files. Who makes that edit is not settled yet.

## Changes after review (16 Oct)

- **E2c's owner** (0134MoC6):
  - The common pack holds no per-contract quotes or D2 features. So the sheet reads only the canonical 3 pm snapshot
    named in the common pack's provenance (`a4_snapshot`), never "the latest", and only cutoff-time data. I checked:
    `fno/desk/common_pack.py:25` names `SNAPSHOT_INPUT = "a4_snapshot"`.
  - F5 makes the E2 edit, and E2c's owner reviews it.
  - Four rules added to the text and to criterion 1:
    - Book 1's pack SHA-256 is unchanged;
    - the sheet's output goes through `canonical_json`;
    - a failing sheet refuses only its own book's pack, with no partial pack;
    - a sheet reads only its own book's folders.
  - New tests: a planted later capture is not read; one book's failing sheet does not stop the others.
- **F1t** (judge 301, story/f1t-ai-trading-runner f1204a5a):
  - the shape check is named `check_decision`;
  - `seal` refuses private account figures in answer text;
  - **F5 now owns Book 2's `OrderBuilder` and `ExitRules`**: Book 1's `ReplayedOrders` and `PlaybookExitRules`,
    reused and parametrised by book, not copied. This is criterion 9.
- **F6:** its allocator criterion 12 matches this text (F6's story at 2153e9b0).

## Judge 307 (FAIL at 6d2b6331, 2 should-fix), answered

1. **No top-level `action`: accepted.** I checked F1t's base check (story/f1t-ai-trading-runner f1204a5a, lines
   184-185): `decision` needs `action` (text) and `reason` (one line). The decision is now `{"action": "follow_rule" |
   "change", "reason": <one line, 1-600 characters>, "slots": [...]}`. `action` is `follow_rule` exactly when every
   slot follows its default. The shape check is named `check_decision(decision, sheet=None)`. Criterion 2 now also
   requires that F1t's base check passes every decision `check_decision` accepts. Confirmed with F1t.
2. **Book 2's orders and exits: accepted.** Part 3 point 7 reuses Book 1's `ReplayedOrders` (replayed with the
   `SelectionAllocator` rebuilt from `inputs.json`) and `PlaybookExitRules`, parametrised, not copied. Criterion 9 has
   the judge's three cases:
   - a changed pick refuses every order;
   - a pick blocked by C4 is never ordered;
   - today's version file moves no exit.

**Minor points:**
- Shadow-only: the default the account takes passes the same allocator, C2 and C4 in the same run.
- The unproven re-check is a new `unproven` check in `EnvelopeMode`. Book 1's `PlaybookMode` is unchanged, and
  criterion 10 reruns Book 1's C4 cases.
- Citations now give decision titles, not row numbers. I also fixed the two I wrote into D3's and F4's text.
- D3 criterion 6 names Book 3's day-record exemption and the null `owner_override`.

**Other changes since 0b77381f:**
- The `BookSheet` port is now E2c's owner's (story/e2e-book-sheet, the orchestrator's choice). F5 builds only
  Book 2's sheet, under E2c's rules a and d.
- Picks run in D2's own rank order, not slot order (F6: one ordering rule).
- The sheet's time comes out of the 15:07 fire margin on a late-canonical day (O1's builder). It is timed at the
  playbook's most strategies, with a 5 s budget (reasoning only).
- The envelope components reach `served` through the run context (F6's `DecisionRun` change).
- S2's text: "overrides (F4)" removed from `S-scoreboards.md` S2's inputs (orchestrator: a one-line fix here, S2's
  owner told through the register). S2's stale `RecordedOwnerOverride` code is S2's (judge 300 addendum 1).
- **Judge 307 addendum 1 (FAIL at 0b77381f):** both points were already covered at 778e9c0f. The judge's three-valued `action` (`follow_rule | trade | no_trade`) replaces my `follow_rule | change`. Criterion 9 now also says the evaluator is rebuilt with the stored picks, a `choose_width` run orders the rebuilt width, and C4-blocked or `shadow-only` AI terms are never ordered.
