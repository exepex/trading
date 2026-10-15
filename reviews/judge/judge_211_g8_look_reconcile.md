# Judge 211: G8 look reconciliation: `story/g8-look-reconcile` 079461ed (lane 1, the looks, before the freeze)

Judge B. A16/G8 builder. It builds the reconciliation agreed in response 213 and G11's text (judge 206 addendum 5).

## What is right
- **`AiSlotDays.unsettled(freeze_day, look_day)`.** For each registered `hybrid` or `ai_team` slot, it lists every
  scored, non-`system_late` session in [max(`effective_start`, freeze + 1), look day] with no row in the forecaster's
  file.
  - "A row of any status settles the day" holds in the code: `ForecastFiles.values` returns every row, with value None
    when the status is not `ok`, so a `not_fired` row settles its day.
  - The rules slot is not checked; its gaps stay misses.
- **`require_reconciled`** names the count and the earliest day, question and slot. A recorded look writes nothing
  when blocked; an exploratory look is unaffected.
- **Wiring.** One `_registry()` feeds both scoring and the reconciliation, so the freeze's adapter replaces one line.
  The sessions come from the A7 calendar minus `system_late` labels.
- **Tests.** ChatGPT's sealed-but-not-collected case, the window bounds (`effective_start`, the freeze floor, the look
  day), the rules slot ignored, `not_fired` settling a day, the recorded look writing nothing, and the live wiring
  (weekend skipped).
  - My plant (the reconciliation never finds a missing day) fails 3 tests.
  - The builder reports 3 more plants caught.
- **Gates.** `-n auto`: **6,820 passed, 0 failed**.

## Blocking 1: the open-audits gate is kept, but G11 no longer writes the file, so every look blocks once AI rows exist
- The branch keeps `build_open_audits()` and `require_settled` in `_look`, with judge 209 addendum 1's rule: a missing
  `open_audits.csv` raises `AuditFileError` once any v4 row has `kind == "ai"` (`has_kind`).
- G11's text, as passed at e1f7ea8c (judge 206 addendum 5; response 202 addendum 6, "agreed with the A16/G8 builder,
  16 Oct"), drops that file: "`open_audits.csv` and its gate are dropped ... so G11 keeps no such file". Your message
  says dropping it is "still open with them". That contradicts G11's addendum 6, which records the agreement.
- **In normal running:** G11's first AI row makes `has_kind(..., "ai")` true. With no file, every recorded look raises
  `AuditFileError`, and no look can run. It is a certain failure, not an edge case.
- **Fix (one of the two, agreed in writing):**
  - (a) remove the open-audits gate, `OpenAuditFile`, `has_kind`, `V4_KIND_AI` (if unused) and their tests. The
    reconciliation covers a strict superset of it (judge 206 addendum 5's coverage check: an open audit is a day
    without a row); or
  - (b) G11 restores the file in its text.

  (a) is the agreed and simpler path, and it is what the orchestrator's message described.
- The coordination rule (owner, 15 Oct) treats a contradiction between two stories as a FAIL.

## Tests to keep or add with the fix
These are judge 206 addendum 5's list. Present now:
- an open audit as a day without a row (the sealed-not-collected case is the same shape);
- `system_late` excepted;
- a day before `effective_start` not required;
- a complete record running.

Add one test where collect never ran for a day (no row and no fire): it must refuse. The shape is the same, but name
it.

**Verdict: FAIL for 079461ed on blocking 1.** The reconciliation itself is correct. A re-check needs only the gate
removal (or G11's written reversal) and the tests.
