# Response 204: stories D4 (Book 2's authority envelope) and D5 (Book 3's constitution and strategy registry), story text

Builder: Claude, 16 Oct 2026 (IST), branch `story/d4-d5-envelopes`. Lane 1 (new stories). Owner, 16 Oct: "D4/D5 text
only, no AI cost" (`docs/DESK_DECISIONS.md`). The trading code waits for slice E's trigger. Texts are in
`docs/stories/D-playbook-decisions.md`, sections D4 and D5, which replace the 12 Oct texts. **No code.**

## Claims (to check against the text and the code)

1. **The playbook format cannot express three of design 12.2's allowed actions today.** Strong evidence (code read):
   - Strikes are set by code from the ATM strike (`fno/playbook/structure_spec.py:32`); there is no strike set.
   - The only machine exit is the time exit (`fno/playbook/exit_terms.py:1-19`: the profit, loss and event exits must
     read "none" for `paper`).
   - S3's standard unit values only that exit (`fno/scoreboard/standard_unit.py`).

   So envelope v1 allows only `follow_rule`, `choose_strategy`, `no_trade`, `choose_width` (the version's own
   `widths`) and `reduce_lots`. Strike choice, exit choice and the early event exit are "out, with the reason". Each
   comes back as a later envelope version once D1 and E4/S3 support it.
2. **Delay entry is not a separate action.** Under E3's fixed timetable (`config.yaml` `desk.timetable`: deadline
   15:12, snapshot 15:15), a delay past the deadline means no trade that day (design 12.2's own note). So it is
   `no_trade`. Strong evidence (the timetable).
3. **No new hash register.** D6 already names "envelope" and "constitution" as version components
   (`fno/books/version_registry.py:1-4, 21`). It marks a decision whose served components differ as unscored
   (`fno/books/versions.py:97-109`). So both files' hashes go into `components` and D3's `served`, and C4 refuses a
   mismatch. This replaces the 12 Oct text's "hash in `playbook/registry.csv`", which would duplicate D6. Strong
   evidence (code read).
4. **C4 plugs in at one line each.** `validity_modes()` in `fno/checks/wiring.py:72-80` maps Book 2 to
   `WaitsFor("envelope", "D4")` and Book 3 to `WaitsFor("constitution", "D5")`. D4 and D5 replace those entries with
   `EnvelopeMode` and `ConstitutionMode`, both `ValidityMode`s. Strong evidence.
   - **Lane-1 change outside the new files:** `ValidityProposal` gains `action` and `rule_default` (D4) and
     `strategy_id` (D5). That file is C4's, and the change must be agreed through the orchestrator.
5. **Book 3's specs reuse D1's playbook format and fingerprint** (`parameters_sha256`, `fno/playbook/schema.py:108`),
   so there is no second spec format. The registry's ancestry check reuses D6's `_registered_before`
   (`fno/books/versions.py:70-76`, strictly before), and B4's `Git` underneath. Strong evidence (code read).
6. **D3 has no constitution field.** `served` takes any named string (`fno/playbook/decision_record.py:147-149`), so
   the constitution's hash goes there and D3's schema does not change. Strong evidence.
7. **"Never override on paper"** (design v2 `03_layers_factory_desk.md:121-123`; `REPLAN.md:41`) is honoured: neither
   enum has an owner action. D3 still carries an `owner_override` field (`decision_record.py:21-25`); see question 4.

## Questions for the owner (via the orchestrator), each with a recommendation

1. **"Holding up to 3 weeks"** as `max_holding_days: 21` calendar days from entry to the planned exit. The other
   option is 15 NSE sessions. **Recommend 21 calendar days**: it reads as the owner wrote it, and holidays do not
   change it. Reasoning only.
2. **Book 3's structures:** all nine defined-risk codes C4 accepts (LC, LP, CDS, CCS, PDS, PCS, SF, SC, BF), with the
   STR1 activation gates applying as for every book. Or a smaller set? **Recommend all nine.** C4's bounded-loss check
   and C2's limits already contain the risk, and a narrower list would make a strategy choice for Book 3. Reasoning
   only.
3. **Monthly NIFTY expiries only.** Strong evidence: the 3 pm recorder records NIFTY monthly quotes only (CLAUDE.md,
   A4), and E4 and S3 price from those snapshots. **Recommend monthly only**, with weeklies as a later constitution
   version if A4 records them.
4. **D3's `owner_override` field.** The owner dropped overrides on paper (REPLAN line 41), yet D3 still has the field.
   **Recommend** that D3 refuses a non-empty `owner_override` for every book, and that S1's safety stop is recorded
   only as S1 says. This is a small D3 change outside D4/D5; who builds it is the orchestrator's call. Some evidence:
   the field exists, and the decision says it should not be used.
5. **Envelope v1's narrow scope** (claim 1). Accept it, or first extend D1's format with a strike set and an exit set
   so that the envelope matches design 12.2 in full? **Recommend accepting v1**: those actions need E4 and S3 support
   too, and slice E should not wait on that. Reasoning only.

## Known limits

They are stated in each story: envelope v1 is narrow; `reduce_lots` has no effect at `lots: 1`; Book 3 uses monthly
expiries and the time exit only.

## A conflict I found (not mine to fix; reported)

DESK_DESIGN 12.4 (line 304) and S1's `catastrophic_loss_book` still say "3 open trades" and a Rs 30,000 brake.
`config.yaml` `risk.profiles.books` has a Rs 1,20,000 brake and no open-trade limit, on the Rs 20 lakh account. REPLAN
section 4 already lists `catastrophic_loss_book` as changing ("the account brake and bucket caps on Rs 20 lakh").
D4 and D5 reference C2's limits rather than numbers, so they work with whichever figure S1 settles. Strong evidence
(the three files).

## The owner's answers (16 Oct 2026, `docs/DESK_DECISIONS.md` row "D4/D5: the five design questions accepted as recommended")

All five were accepted as recommended. They are written into the texts as decided:
1. 21 calendar days to the planned exit;
2. all nine of C4's defined-risk codes for Book 3;
3. monthly NIFTY expiries only;
4. D3 refuses any non-empty `owner_override` for every book. This is a D3 code item at slice E, and its builder is
   settled then (orchestrator). It is named in both gap lists;
5. envelope v1 stays narrow.

The Rs 30,000 brake conflict goes to S1's text owner (orchestrator).

## Judge 207 (FAIL at 0cb5234d, 2 should-fix and 2 minor): all accepted, each checked

| Point | Check | Change |
|---|---|---|
| SF1: one `components["envelope"]` key cannot hold the envelopes that `choose_strategy` implies; "envelope" collides with Hybrid's forecast envelope | Confirmed. Choosing among two eligible versions means two envelope files. `fno/ai/envelope.py` and `ai/versions.py` `envelope_width` already use the word. | Option (b): one `trade_envelope:<name>-v<n>` D6 component per playbook version, the same key in `served`. **The traded version's envelope governs every action of that trade**, `choose_strategy` included. New criterion 8 (A and B eligible, different statuses). I chose (b) over a book-level file because design 12.2 versions the envelope with the playbook. |
| SF2: a `shadow-only` action has no reader on scoreboard A | Confirmed: S3's `action_of` reads only `record["decision"]` (`fno/scoreboard/matched_actions.py`), which is the account's rule default. | Stated plainly: unscored until S3 reads the shadow `chosen_action`. That reading change is in Depends and in the gap list, routed to S3's builder at slice E. Criterion 3 now says it is listed, never scored. |
| m1: `proposed_on` from the clock | Correct: a proposer-written date is a small hole beside the commit check. | `register()` sets it on the registration day (IST). Criterion 1 tests that a spec's own date is ignored. |
| m2: C4 owner agreement in Depends | Correct. | Both stories' Depends name the `ValidityProposal` fields and C4's owner's agreement. |
