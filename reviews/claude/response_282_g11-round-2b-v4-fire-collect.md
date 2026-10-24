# Response 282: G11 round 2b part 1, the AI books' v4 fire and collect (switched off until the v4 go-live date)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (G11 owner). Lane 1. For judge B. Branch `story/g11-ai-books-v4`; the head
is given in the message to the judge. The design was confirmed by the orchestrator (response 272 and its addenda 1-3).
G10 part (b1) (judge 282 addendum 1 PASS) is merged into this branch and lands with it, which is judge B's condition
for (b1).

Round 1 (the v4 rows, judge 275) is on main. This part adds everything from the released pack to the rows except the
routine's own steps. **Nothing runs live:** every v4 step refuses before `daily.live_from.forecasts_v4`, which is
`null`.

## What it builds (strong evidence: the tests named)

1. **Each book's v4 input** (`fno/ai/v4_input.py`, `v4_book_inputs.py`; tests `test_v4_input.py`).
   - Built from the verified pack: spot, the future, VIX, IV30 and its flag, each expiry's ATM straddle, the chain
     within 5% of spot for the nearest expiry, plus the last 260 closes and the derived facts.
   - Hybrid (Book 2) also gets, per question, the rules slot's registered forecaster (for V6 the weather, decision 70)
     and the primary baseline. Both are their live rows of the day. It also gets an envelope of the baseline
     plus or minus 0.10.
   - A full two-expiry chain measures 20,713 bytes, a third of the cap.
   - The questions are the book's own slot's registrations from `effective_start`. A registered question the prompt
     does not define is refused loudly.
2. **The v4 pointer** (`v4_pointer.py`; `test_v4_pointer.py`). The whole input travels in the pointer, because a
   routine has no Drive credentials (the F2/F1t precedent). It is capped at `ROUTINE_POINTER_MAX_BYTES` (64 KiB, one
   home in `constants_operations.py`); over the cap the book is not fired, never truncated. Every field is checked on
   arrival, and the pointer module is standard library only (a test).
3. **Prompts v2** (`agents/forecast/book2_hybrid_v2.md`, `book3_ai_v2.md`; `test_v4_versions.py`).
   - They cover V6a and V6b, with GitHub's receipt by 15:10 (aim 15:05) and the reveal at 15:10:10.
   - They are registered with their SHA-256 as **protocol v4** versions beside v1. `current_version(book)` still
     returns v1 for v2, so today's run is unchanged (a test).
   - A version names its `questions` and its `forecaster` (`book3_ai_v2`).
4. **The v4 rows** (`v4_rows.py`, round 1 plus these changes; `test_v4_rows.py`).
   - A book-day carries its registered `BookVersion`. Book, folder, label and prompt hash all come from it, so the
     pack guard's book and the folder never disagree.
   - Rows go to `v4/<book>_v2/`, the name G8's reader and the look's reconciliation look for. A test checks this
     with G8's own `AiSlotDays`.
   - `check_pack_binding` (G10) is called before any row, with a test that another SHA and an empty one are refused.
   - `stopped` comes from the fire log's flag, never from a reason's wording (R2/G7).
5. **The v4 fire**, `python -m fno ai fire --protocol v4 --day <d>` (`v4_fire.py`; `test_v4_fire.py`).
   - It refuses a day that is not today in IST, and any day before go-live. A refused day never touches Drive (a
     test without Drive settings).
   - With no released pack it fires nothing and logs why.
   - Each book fires once. A start after 14:55, the stop rule (logged as a flag), a refused trigger, an undefined
     question or a pointer over the cap is a logged not_fired with one alert.
   - **The v2 AI fire stops from the same date** (owner's choice A), so the books are never fired twice a day.
6. **The v4 collect**, `python -m fno ai collect --protocol v4` (`v4_collect.py`, `v4_settle.py`; `test_v4_collect.py`).
   - It reuses F1/G5's `read_submission`, `judge`, `mark_exposures` and `scoring_status` under one `RunTerms` (`run_terms.py`). The terms carry v4's paths, deadline and reveal window, and v2's terms are the default,
     so there is no copy of the chain.
   - **15:10 is G10's own rule:** a test checks that RunTerms and `commitment.on_time` agree at 15:09:59, 15:10:00
     and 15:10:01. A row whose commitment arrived at 15:10:01 is `late`.
   - The input is rebuilt from the Drive pack and must match the hash the fire logged; otherwise the day is `invalid`.
   - The release record is read by collect itself, and its SHA is stored in the audit for the pack guard. That gives
     two sources, not one.
   - A session the fire never ran, or ran while no pack could be read, is `not_fired` for every registered question:
     a miss, never a gap. No released pack means nothing is collected and no row is written. G10's publisher
     writes `system_late` for such days, and the look excuses them.
   - Settled days become their rows, written once. Pending days are counted: "N day(s) awaiting audit".

Other, default-preserving changes:
- `answer.check_answer`, `outcome.Outcome/judge`, `submissions.read_submission` and `scoring_gate.scoring_status` take
  the day's questions and `terms`.
- `timing.py`'s functions are now V2_TERMS's, with the same names and values.
- `paths.py` takes a folder.
- `Envelope.around` and `from_json` are added.
- `export.realised_vol_points` is made public.
- `record_writer.audit_text` is now a module function, reused by v4.
- G8's `_registry()` is now public as `build_slot_registry()`, the one registry for scoring, the look and the fire
  (its owner agreed).
- `FORECAST_PROTOCOL_V2/V4` are added to `fno/constants.py` (346 lines).

## Limits, stated plainly

1. **The routine's own v4 steps are not built** (part 2): `brief`, `seal` and `reveal` for the v4 pointer. They wait
   for F1t's refactor of `book.py`. Until then a fired book's routine could not answer. Nothing fires before go-live
   anyway. The tests publish the two files with F1's own seal code instead.
2. **The audit draw and the stop rule still count v2 days only** (round 2c, mine by the orchestrator's ruling, before
   the 22 Oct freeze). Until 2c, every on-time v4 day stays `awaiting audit` (`weekly audit draw not made yet`) and
   gets no row. That is the safe direction: never scored clean by default. The stop rule could not stop a v4 book
   yet.
3. **The `pack_sha256` column in the rows** waits for R2/G7's column (judge 280) to reach main. The guard already
   runs; the rows will carry the SHA from that merge.
4. **O11's replay check** for G11 (`tests/e2e_acceptance/test_expected_missing.py`) stays an expected failure. The
   books cannot answer the recorded day until part 2. It becomes a real check with part 2.
5. Each input selection is reasoning only. The prompt's input is the judge's to challenge.

## Gates

They were run on this branch with latest main merged; the numbers are in the message to the judge. I ask that it
may land before the freeze as switched-off code, together with (b1).
