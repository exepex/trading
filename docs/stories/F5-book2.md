# F5. Book 2: AI decisions inside the envelope (design v2)

**Repository:** trading · **Owner session:** 01SFDjjZx7JYziM3jqJytG2z · **Judge:** E · **Status:** story text

**Description:** As the owner, I want Book 2's AI to take, each day, the rule default or one alternative its envelope
allows, with a reason, so that scoreboard A can show whether **AI veto and width selection within the same registered
playbook** beat the rules alone.

**Context and why:**
- Design 12.1, 12.2 and 12.9; design v2 `07_ai_team.md` 7.1 and 7.3; REPLAN: F5 kept for slice E, F3 becomes the
  devil's advocate (T2, T3), and F4 drops owner overrides.
- The owner's decisions:
  - D4/D5's five answers: DESK_DECISIONS row 229 (16 Oct), including no owner override on paper;
  - "build Books 2 and 3 end to end": the orchestrator's assignment of 16 Oct.
- This text replaces the earlier F5 text in `F-ai-layer.md`. That text predates design v2: it had the red team and
  owner overrides as inputs.

**What Book 2 measures (D4 "Known limits", ChatGPT review 130 point 1):** with the playbook's approved versions and
their lots, the AI's real interventions are vetoes, width choices, lot reductions and switching to another eligible
version. Every report names the estimand **"AI veto and width selection within the same registered playbook"**
(`BOOK2_ESTIMAND` in `fno/constants.py`, read by S3), never "AI judgement adds value". The rule default is the paired
control. A zero difference is "inconclusive".

## Scope

**In:**
- Book 2's day sheet in its private pack (part 1);
- the answer shape and its check (part 2);
- the decider that turns an accepted answer into one D3 run with C2 and C4 inside (part 3);
- the estimand label.

**Out:**
- the runner, prompts, sealing and the deadline (F1t);
- the analyst cards (F2);
- the devil's advocate (T2, T3);
- the AI judge (F4);
- the envelope files and their versions (D4, D6);
- Book 3 (F6).

## Part 1: Book 2's day sheet (E2 hook, shared with F6)

- **Port** (E2): `BookSheet` (ABC) with `sheet(book, day, common: CommonPack) -> Mapping`, JSON-ready.
  - `WrittenPacks.build` runs each book's sheet right after the common pack is built, inside the existing `pack` step.
  - `PrivatePackBuilder.build` puts the sheet in the private pack's body as `"evaluation"`. A book without a sheet
    (Book 1) is unchanged, byte for byte.
  - Wired in `fno/desk/pack_wiring.py`, one line per book. Book 3's sheet is F6's.
  - Who edits `packs.py` and `private_pack.py` is agreed with E2c's owner (0134MoC6) before code.
- **Book 2's sheet** (`fno/book2/sheet.py`): D2's `RuleEvaluator` at the cutoff over Book 2's approved versions, with
  Book 2's own book and counts. It writes:
  - `opportunities`: every book-mode outcome, with its ID, version, decision, reason, and built terms (width, lots,
    structure);
  - `rule_default`: the opportunity IDs D2 chose, each with its terms;
  - `eligible`: the versions that reached C2 (`DayEvaluation.eligible`).

  No journal file is written. The private pack stays out of git (only its `.sha256` is committed), so the sheet is
  never public (E2c's privacy rule and the owner's O9 rule).
- **Why in the pack:** Book 2's AI must see the rule default before it decides at about 15:00, and D2 needs the cutoff
  data, which exists only from the `pack` step (O1 builder, 16 Oct). There is no new daily step.

## Part 2: the answer (`fno/book2/answer.py`, standard library only)

- **Shape:** `{"slots": [...], "reason": str}`. There is one slot per rule-default trade, in the sheet's order:
  `{"default": <opportunity_id>, "action": "follow_rule" | "no_trade" | "trade", "opportunity_id": <id or null>,
  "width": <number or null>, "lots": <int or null>, "reason": <non-empty str>}`.
- When the rule default is "no trade", `slots` is empty. The AI can never trade when the rules offered none (D4).
- `check_answer(obj, sheet=None) -> list[str]` lists the problems, and an empty list means it is acceptable:
  - wrong types;
  - a missing reason;
  - slots that do not match the rule default one to one;
  - two slots choosing the same opportunity;
  - with `sheet` given, an `opportunity_id` not in the sheet.

  F1t's `seal` calls it without the sheet. The decider calls it with the sheet. The envelope is **not** checked
  here: C4 does that.

## Part 3: the decider (`fno/book2/decider.py`, F1t's `AiBookDecider`)

`decide(accepted: AcceptedDecision) -> DecidedRun` (F1t's hand-over port, story/f1t-ai-trading-runner 1da500c4):

1. **Inputs only from code.**
   - The sheet comes from `accepted.private_pack`, whose hash F1t checks against the pointer.
   - `rule_default` and `eligible` come from that sheet, never from the AI.
   - The AI's answer is only its choice and reason.
   - A missing or malformed sheet raises `DecisionRefused`, so the day is `refused`.
2. **Picks.** Each slot becomes a `Pick(opportunity_id, reason, width, lots)` for F6's generic `SelectionAllocator`
   (`fno/playbook/selection.py`, story/f6-book3-engine):
   - `follow_rule`: the default's opportunity at its own terms;
   - `no_trade`: no pick;
   - `trade`: the named opportunity, at the named width and lots.

   The allocator runs with `threshold=True` and a `rebuild` from D2's `CandidateBuilder` for a changed width or lot
   count. C2 and the unproven limit then run on the picks in slot order. Every other candidate is NOT_CHOSEN "not
   chosen by book2_hybrid".
3. **C4 per chosen trade** (`EnvelopeMode`, D4):
   - the proposal carries `rule_default` (the slot's default terms) and `eligible` from the sheet;
   - `permits` derives the actions;
   - `shadow-only`: the account takes the rule default and the choice is written as a shadow record (D3 `mode:
     shadow`);
   - `forbidden`: no trade, and the attempt is recorded.
4. **The unproven limit, re-checked independently at C4** (judge 260 addendum 2: D4 option 2, kept for F5's
   switch-on). C4 gains each version's completed and open paper-trade counts from E5's records as an input. A pick
   that would hold more than the limit fails `unproven` at C4, whatever the allocator said.
5. **One D3 run** (`DecisionStore`, atomic), like Book 1's `DecisionRun`. Every record has:
   - `rule_default`, `chosen_action`, `reason` and `authority_check` as non-empty text (D4 criterion 7);
   - `model_served` (= `model_reported`) and `session_id` from `accepted`;
   - both pack hashes;
   - `owner_override` null (D3);
   - in `served`, the playbook, config and `trade_envelope:<name>-v<n>` of every envelope used.

   The picks go in `inputs.json` under `selection`, so D3's replay rebuilds the allocator and reproduces every record.
6. **Evidence, not inputs.** The analyst cards (F2) and the devil's advocate's objections (T3) are linked in the
   record. They are never an input of the allocator, C2 or C4.
7. **Timing.** `decide()` runs in O1's `ai_collect` step, between 15:11:00 and E3's 15:12 deadline. It does not
   re-run D2; it reads the sheet. Its run time is measured in the tests on a realistic day and reported, with a
   budget of 30 s, half of F1t's 60.

## Acceptance criteria

1. Book 2's private pack holds the sheet: rule default, eligible set and outcomes. Book 1's pack bytes are unchanged.
   No sheet file appears under `journal/`.
2. `check_answer` refuses each malformed shape in the test plan, and accepts the four actions.
3. Each envelope action works end to end on fake sessions:
   - `follow_rule` trades the default;
   - `no_trade` trades nothing;
   - `choose_width` and `reduce_lots` trade the rebuilt candidate;
   - `choose_strategy` trades another eligible version;
   - a `shadow-only` action makes the account take the default and writes the shadow;
   - a `forbidden` action writes "no trade, blocked by C4" with the attempt.
4. A choice of an approved version that did not reach C2 (the rule did not fire, its own threshold, or the unproven
   limit) is refused by C4. So is a pick that breaks the unproven limit, whatever the allocator did.
5. Every record passes `validate_record`, and D3's replay reproduces the run from `inputs.json`.
6. With no approved version, Book 2 writes the day's "no trade" record ("no approved strategy"), like Book 1.
7. A Book 2 decision failing C4 never becomes a fill (end-to-end negative test through E4).
8. `decide()` takes at most 30 s on the test day (measured and reported).

## Test plan

- Fake `AcceptedDecision`s built from the test playbook and a recorded common pack.
- The sheet compared with D2's own evaluation.
- One test per envelope action and per refusal.
- Mutation checks on the eligible check, the unproven re-check and the shadow path.

## Judge verifies

- Replays three Book 2 records against their sheet, envelope and packs.
- Checks that nothing the AI wrote reaches `rule_default` or `eligible`.

## Open questions (to the orchestrator, then the owner if needed)

1. **F4's AI judge is not built.** Its old text says Book 2's judge failure means no trade. Does Book 2 switch on
   without F4, recording `judge: "not built"` with C4 as the last gate, or does it wait for F4? Recommendation: wait
   for F4, because a judge that can block is part of Book 2's design (12.2). Reasoning only.
2. **Several rule-default trades on one day.** The design here gives one slot per default trade, and a switch
   replaces only its own slot. Is that the intended unit, or should Book 2 choose a whole set? A set would change D4's
   one-choice-against-one-default check.

**Depends:** D2, D3, D4 (merged), E2 (the hook), E5 (counts), F1t, F6's `SelectionAllocator` · **Size:** M
