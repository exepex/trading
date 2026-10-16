# Response 272: G11 round 2b design, the AI books on the v4 pack (proposal before code)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (G11 owner). For the orchestrator, the A16/G8/G10 builder
(01VK88LxJvV1Gi7Wbr3D4fzp), F1t (01PLbKH15BXYucP6cT9xtoxK), F8c (0134MoC6f7aAJVcHRBiyATo6) and judge B. Round 1 is
merged (7c1a9734, judge 275). This note fixes the parts of round 2b that cross other builders' work, before code.

## 1. The gap: how the book routine gets the v4 pack

- **Today (v2), strong evidence, the code:** `brief` builds the book's input from files committed in the checkout
  (`fno/ai/export.py`: the v2 pack `research/forecasts/live_v2/<YYYY>/<d>_pack.json` and `warmup_closes.csv`). The
  pointer (`fno/ai/pointer.py`, 4 KiB cap) carries only the pack's SHA.
- **v4 (G10 part 2, O9):** the pack lives only in Drive's `data` area (`fno/v4_pack/paths.py`, `v4/packs/<YYYY>/<d>.json`);
  GitHub holds its receipt. A routine session has no Drive credentials and must not have any (F1t's rule, F2's
  story: Drive also holds values a book must not see, such as G7b's implied baselines).
- **So the routine cannot read the pack.** Settled precedent, which I follow rather than invent another: F2 and F1t put
  the role's or book's own input **in its pointer**, one line of JSON capped at 64 KiB. An input over the cap is
  `not_fired`, never truncated. The collection checks the input's hash against the Drive file read through the
  verified cache (`docs/stories/F-ai-layer.md:150-158`, F1t story lines 140-166).

## 2. Proposed design (new modules; the files F8c and F1t change are touched last, after they merge)

1. **`fno/ai/v4_input.py`: the book's v4 input.** Built on the Actions side from the verified `Pack`
   (`fno/v4_pack/codec.read_pack` at the release record's SHA) and the official closes before the day. It holds spot,
   India VIX, the near future, IV30 (with its flag), the ATM strike's call and put mids for the nearest expiry (the
   implied move) and the chain within +-5% of spot, plus the closes of the last 260 sessions. For Book 2 only, it also
   holds the rules slot's own v4 values for the day's started questions, read from G7's committed records (written
   before 14:30). `input_sha256` is the canonical JSON's hash. The selection is reasoning only; it is the prompt's
   input, so the judge can challenge it.
2. **`fno/ai/v4_pointer.py`: a new pointer**, `kind: "forecast_v4"`, holding `book`, `day`, `version`, `pack_sha256`,
   `questions` (the rules slot's started set, criterion 1) and `input`. Capped at 64 KiB: one shared constant with
   F1t's (I propose `ROUTINE_POINTER_MAX_BYTES` in `fno/constants.py`, so the cap has one home); over the cap is
   `not_fired`. `fno/ai/pointer.py` (v2, 4 KiB) stays as it is until the freeze. Measuring a fixture pack's size is part
   of the round.
3. **`fno/ai/v4_fire.py`: the v4 firer**, reusing F1/G5's trigger, stop rule and alert sender:
   - It reads the release record. On a `system_late` day (no released SHA) it fires nothing and logs why; the books
     write no row, and the look's reconciliation leaves `system_late` days out (83a5ee7a).
   - It starts no later than `V4_LATEST_FIRE` (14:55). A later start is `not_fired`.
   - The fire log gains a structured key, `"stop_rule": true`, beside `fired: false` (agreed with R2/G7, 16 Oct). It
     replaces `v4_rows`' text prefix on `stopped` (root fix; `fno/ai/fire.py` joins the v4 freeze list).
4. **`fno/ai/v4_collect.py`: the v4 collection**, reusing `seal`, `outcome.judge` and `scoring_gate`:
   - It builds the `BookDay` from the submission, GitHub's receipt time against `V4_DEADLINE` (15:10:00 counts,
     15:10:01 is late; G10 part (b)'s `CommitmentTimes`, reused, not copied) and the fire log's flag.
   - It writes the rows through `v4_rows.write_book_day`.
   - It rebuilds the input from the Drive pack and checks the submission's `input_sha256` against it. A mismatch is
     `invalid`.
5. **`fno/ai/v4_rows.py`** (mine, merged): `BookDay` gets `pack_sha256` and the stop-rule boolean. `write_book_day`
   calls `fno/v4_pack.guard.check_pack_binding` before writing any row, with a test that another SHA and an empty SHA
   are refused (judge 274 addendum 1, judge 275's condition).
6. **Prompts v2** (`agents/forecast/book2_hybrid_v2.md`, `book3_ai_v2.md`, registered in `fno/ai/versions.py`): the
   V6a/V6b definitions, the 15:10 deadline (aim 15:05), and the reveal after 15:10. Timing needs no prompt step
   (F8c's capture in brief and reveal).
7. **Book side, last:** `brief` accepts the v4 pointer and prints its input; `seal` and `reveal` use the v4 paths and
   times. These are in `fno/ai/book.py`, which F8c changes and F1t then refactors, so this step waits for both merges.
   It is built on their versions, never alongside.

## 3. Dependencies and order

| Needs | Owner | State |
|---|---|---|
| `fno/v4_pack` codec, guard, paths; `V4_LATEST_FIRE` | A16/G8/G10 | on main (8321d73f, judge 277) |
| Release record reader (released SHA or `system_late`), `CommitmentTimes` (15:10 on GitHub's receipt), the fire workflow on `receipts/v4/days/**` | A16/G8/G10, G10 part (b) | to come |
| `brief`/`reveal` timing, `ai collect` usage line | F8c | with judge E |
| `book.py` publish helper | F1t | after F8c |

Steps 1, 2, 5 and 6 can be built now. Steps 3 and 4 need part (b)'s reader and `CommitmentTimes`; step 7 needs F8c
and F1t on main.

## 4. Questions

1. **A16/G8/G10:** will part (b) give a function that reads the release record through the verified cache and returns
   the released SHA, or `system_late`? Will `CommitmentTimes` take a repository path and return GitHub's receipt time?
   I will build against those names.
2. **F1t:** one shared 64 KiB constant in `fno/constants.py` (`ROUTINE_POINTER_MAX_BYTES`), or do you prefer to keep
   yours? Either is fine if there is one home.
3. **Orchestrator:** confirm that the v4 input in the pointer (the F2/F1t precedent) is the design, and the order
   above.
