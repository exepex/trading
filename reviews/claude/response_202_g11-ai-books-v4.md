# Response 202: G11, the AI books on the v4 questions (story text and claims)

Story text: `docs/stories/G-forecasts.md`, section G11. Code waits for the v4 freeze (about 22-23 Oct).

## Claims

1. **Same questions, same day, same scoring.** Books 2 and 3 answer exactly the `rules` slot's started questions (at
   the freeze V6a and V6b), from the same released v4 pack, by the same 15:10 deadline, written in G7's schema to
   G8's folder, so G8 scores them with no AI-specific path. Strong evidence for the reuse: G8 discovers forecasters
   by folder (`fno/forecast_scoring/v4/inputs.py:106-107`); protocol v4 already names the `hybrid` and `ai_team`
   slots (`PROTOCOL_v4.md:225-228`).
2. **No silent gaps.** Every outcome other than on time with no breach writes a non-`ok` row, which G8 counts a miss
   under the 10% caps (`fno/forecast_v4/misses.py`). Strong evidence that a missing or non-`ok` row is a miss in G8
   today; the mapping itself is new.
3. **No second version of anything.** F1/G5's firer, seal, reveal, outcome and scoring gate are reused; the timing
   comes from `fno/forecast_v4/terms.py`; only a prompt version per book and one record writer are new.
4. **Cost.** BG1 caps minutes (50% of measured session minutes until December 2026; alert 80%, stop 100%). No book
   run is measured yet; one day (15 Oct) shows about 5 minutes from fire to commitment (some evidence). Estimate
   10-20 minutes a session day for both books under option A (reasoning only). The new prompts write BG1's timing
   record, so the real figure is measured from day one.
5. **Honest starting point.** No AI book has an on-time day (14 Oct `no_submission`, 15 Oct `late` by about 12 s).
   v4's window is wider (release about 14:32, deadline 15:10), but if the books stay late the 10% cap makes their
   slots "undecided, operations", which the story treats as a result, not a fault.

## Open points (state on 16 Oct)

- **A16/G8 builder:** agreed, see addendum 1.
- **Owner:** chose A (addendum 3).
- **Orchestrator:** answered (addendum 3); the workflow step is agreed (addendum 4).

## Addendum 1: agreed with the A16/G8/G10 builder (16 Oct), each point checked in the code

- **Pending audit: accepted, write the row only after the gate settles.** My option 2 (`pending_audit`) cannot work:
  `fno/forecast_v4_rules/records.py:74-90` raises `RecordConflict` on any changed row, so a pending row could never
  become `ok` or `breach` (strong evidence, read the code). Added: "N days awaiting audit" in G11's output, and every
  audit settled before a confirmatory look (a look is recorded once).
- **Registration: accepted.** FREEZE_v4 registers only `rules` for V6a/V6b (response 157); G11 appends its own rows,
  `effective_start` no later than the slot's first eligible session (judge 184).
- **Own writer: accepted.** `records.record()` stamps G7's `VERSION = "1"` (`records.py:20,61`).
- **Pack hash: accepted.** `inputs_sha256` stays the book's own inputs; the pack's hash goes in the column G10 part 2
  adds for every family.
- **Slots and kind: accepted.** `V4_SLOT_HYBRID = "hybrid"`, `V4_SLOT_AI = "ai_team"` (`fno/constants.py:191`);
  `kind=ai`. V7 is a member never judged (`terms.py:65` `DESCRIPTIVE_ONLY`); not started at the freeze.

## Addendum 2: judge 206 should-fix (who builds the look's refusal)

Accepted (strong evidence: the look code is G8's, byte-checked at the freeze). The A16/G8 builder builds the refusal in
`fno/forecast_scoring/v4/` before the freeze, with their register row and a freeze-checklist line (their written
answer, 16 Oct). G11 supplies a committed file, `research/forecasts/v4_audits/open_audits.csv`
(`day,forecaster,question`), so G8 never imports G11's code. Criterion 6 and the Out list now say so; criterion 4
names G10's receipt-time check as reused.

## Addendum 3: the orchestrator's answers (16 Oct)

- **Owner chose A:** at the v4 freeze the AI books' v4 run replaces the v2 AI run (`DESK_DECISIONS.md`, 16 Oct row).
  Cost: the same number of runs a day as today.
- **`fno/ai`:** this builder owns its v4 changes for G11 (register row updated).
- **`forecast-capture.yml`:** the AI fire step moves after the v4 pack's release; that workflow change belongs to the
  A16/G8/G10 builder (G10's capture owner) and is a prerequisite of G11 going live. The exact step is being agreed
  with them.

## Addendum 4: the fire step, agreed with the A16/G8/G10 builder (16 Oct)

Accepted, reasoning only (no run yet): no new or moved cron. The fire runs on the push that lands the released pack;
G10 part 2 adds `V4_LATEST_FIRE = 14:55` to `fno/forecast_v4/terms.py`, and a later start is a recorded `not_fired`
miss. Collect and audits-due keep `forecast-capture.yml`'s slot (about 15:30), re-pointed to v4; the v2 AI steps go at
the freeze; the CLI stays `ai fire` and `ai collect`. The workflow file is theirs. One risk added (strong evidence,
`forecast-capture.yml`'s own note): a push made with an Actions run's own token starts no workflow, so the pack's
commit must come from the routine's credentials, or the fire never starts.

## Addendum 5: ChatGPT review 127 (AGREE, one change), orchestrator's answer response 213

Checked each point; all accepted:
- **Reconcile before a look: accepted** (strong evidence: a collect that dies after a sealed commitment leaves no
  audit row and no v4 row, so `open_audits.csv` alone cannot see it). Proposed interface, sent to the A16/G8 builder:
  G11 writes one v4 row per AI slot, question and settled day whatever the outcome; the look refuses while any
  AI slot-day up to its date has neither a v4 row nor an `open_audits.csv` row. No new file; G8 reads only files it
  already reads. Awaiting their confirmation.
- **Claim scope: accepted** (reasoning only: Book 2 sees the rules' value, so their errors correlate).
- **Runtime p50 and p95 by question set from day one: accepted;** no second runtime cap.
