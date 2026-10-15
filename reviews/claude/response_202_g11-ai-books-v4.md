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

## Open, to agree before code

- **A16/G8 builder (asked 16 Oct):** a row whose transcript audit is pending (write after the gate settles, or a
  `pending_audit` status G8 ignores); whether the freeze's ledger row carries the AI slots. Answer: not yet received.
- **Owner, through the orchestrator:** option A (the v4 run replaces the v2 AI run at the freeze) or B (both run, about
  double the minutes). Lean A, reasoning only: v2's AI record has no on-time day and the two cannot share one run.
- **Orchestrator:** who owns `fno/ai` (no register row); who changes `forecast-capture.yml` (the fire step moves after
  the v4 pack; a workflow change this builder does not make).
