# Response 256: D3 refuses an owner override in every book (builder's claims)

**Why:** The owner decided on 16 Oct 2026 (DESK_DECISIONS row 229, item 4, "Accept all five"): the owner never
overrides a paper decision; only S1's safety stop remains. The D4 and D5 tables require D3 to refuse any non-empty
`owner_override` for every book, **before any Book 2 or Book 3 paper decision**. This is that code item. It is lane 1,
because it changes the decision-record schema.

**Branch:** `story/d3-no-owner-override`, from `main`.

**What changes:**
- `fno/playbook/decision_record.py`: a new `ALWAYS_NULL = ("owner_override",)`. `validate_record` refuses any value
  but null, in every book: "owner_override must be null: the owner never overrides a paper decision".
- `docs/stories/D-playbook-decisions.md`: D3's field list says `owner_override` is always null and why.
- `tests/decisions/test_records.py`: 9 cases (3 books by 3 values: a link, an empty string, a mapping). Each record
  is valid with null and refused with the value.

**Claims and evidence:**
- Every book refuses it. Strong evidence: the 9 parametrised cases.
- Nothing that writes records sets it today. Strong evidence: D3's run builds the field as null
  (`decision_run.py:29`). The only other reader is `fno/scoreboard/sources.py`, whose override check now always reads
  "no override".
- Mutation check: disabling the refusal fails all 9 cases. Restored.

**Deviation:** the text says "non-empty". I refuse an empty string too, because null is the schema's value for
"absent" and an empty string is no link. Reasoning only.

**Not in this change (for the orchestrator):**
- **F4's story text** (`docs/stories/F-ai-layer.md`, F4) still has the owner overriding judge check-2 and check-3
  failures through `journal/<book>/owner_overrides.csv` (criteria 2-3). That contradicts row 229. F4 has no owner in
  the register. I asked the orchestrator whether to amend F4's text here or give F4 an owner.
- **C2's drawdown-brake restart** (`fno/risk/overrides.py`, the same `owner_overrides.csv` name) is the owner's
  written restart of a stopped book. It is a risk control, not a decision override, so it is untouched.
- **`fno/scoreboard/sources.py`'s override reader** belongs to S2's owner. It is now always false, but I have not
  removed it, since it is not my file.

## Added: Book 3's day record names no strategy (agreed with F6's builder, 16 Oct)

The F6/F7 builder (01KTAQCD) pointed this out, and I checked it. D3 makes `strategy_id` and `strategy_spec_sha256`
required for Book 3, but Book 3's day record (`opportunity_id` "no_trade") has no strategy, so every Book 3 day would
be refused. Strong evidence: the new test's first line failed before this change.
- Fix: `DAY_RECORD_NULLABLE` lets Book 3's day record alone leave both null. Every Book 3 opportunity record must
  still name its strategy.
- Test: the day record passes with both null; an opportunity record with both null is refused.
- Mutation check: removing the day-record rule fails the test. Restored.
