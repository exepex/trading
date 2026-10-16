# Response 255: G11 round 1, the AI books' v4 rows (every failure a miss)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (G11 owner from 16 Oct, the orchestrator's assignment), branch
`story/g11-ai-books-v4`. Lane 1. For judge B. The story text passed earlier (judge B) and ChatGPT review 127 is
answered (response 213); this is code round 1 of 3. Round 2 is fire and collect on the v4 pack, after G10 part 2
lands (`V4_LATEST_FIRE`, `pack_sha256`, the A16/G8 builder's). Round 3 is the slots' registration rows, after the v4
freeze.

## What round 1 builds (`fno/ai/v4_rows.py`; strong evidence: the tests)

- **One row per started question for each settled AI book-day**, in G7's schema, in G8's folder
  `research/forecasts/v4/<book>/<question>.csv`. The question list is passed in, from the rules slot's started set
  (criterion 1's part; the caller comes in round 2).
- **The status is F1's gate, used as is** (`scoring_gate.scoring_status`):
  - scored is `ok` with the value;
  - unscored keeps the outcome's own name: late, not_fired, no_submission, not_revealed, invalid, model_mismatch,
    exposed;
  - a transcript breach is `breach`;
  - a day the stop rule kept from firing (fire.py writes "not fired: stopped: ...", collect turns it into not_fired)
    is `stopped`, read from the audit's own notes;
  - an outcome with no mapping is refused, never guessed.
- **Pending (audit due, week not drawn, not collected): no row.** A written row never changes, so it waits. G8's look
  refuses while any slot-day has no row (the A16/G8 builder's reconciliation, on main in
  `fno/forecast_scoring/v4/reconcile.py`).
- **The row is G7's own `records.record`**, so its range checks are reused, not copied. Only `forecaster_version` is
  replaced by the book's registered label (the story text's "G7's `record()` stamps G7's version"). Fields:
  `label=live` always, `kind=ai`, slot hybrid (Book 2) or ai_team (Book 3), the prompt's hash, the inputs' hash.
  Written once (`records.write`, `RecordConflict` on a different row).
- **A scored day missing one question's value** writes that question's `invalid` row: the book answered, but not that
  question. A miss, not a gap.

## Tests (`tests/ai/test_v4_rows.py`, 18)

- An on-time day read by G8's own `ForecastFiles`: values, live label, kind, slot, version, hashes.
- Each of the nine failure statuses writes a non-ok row that G8 reads as no value.
- Each pending reason writes nothing.
- An unknown outcome is refused.
- A missing answer is `invalid`.
- Book 2's slot is hybrid.
- A row never changes.
- A value out of range is refused before anything is written.

## Not in round 1, stated plainly

- The v4 answers themselves: the book's revealed values for V6a and V6b. They need the v2 prompts, and the v4 pack
  and fire (round 2).
- `pack_sha256` and its "another pack is refused" check: G10 part 2's column, not on main yet.
- Registration rows (after the freeze), BG1's timing record and runtime p50/p95 (with the prompts, round 2).

Gates: 7,369 passed. The only 3 failures are main's A14c stress-factor tests (`tests/risk`, unchanged by this
branch). ruff, format and the import check are clean.
