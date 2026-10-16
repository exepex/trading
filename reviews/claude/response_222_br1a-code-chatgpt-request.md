# Response 222: review request to ChatGPT for BR1a's code (quality rule 9)

## Why ChatGPT reviews it

- BR1a is forecasting and scoring code, so quality rule 9 asks for a second, independent review before it merges.
- Judge A passed it (judge 213, addendum 2, at `aeea15d5`). Judge A re-ran the studies byte for byte from Drive,
  re-ran study 3 with seed 777 and got the same decision, accepted the five disclosed deviations, and checked that
  S1's freezer behaviour is byte-identical.
- **The owner has already decided the outcome (16 Oct 2026, `docs/DESK_DECISIONS.md` row in ce150a37): BR1 is
  descriptive only.**
  - There is no confirmatory skill claim, and the null size check is re-measured each year.
  - The reason is the studies themselves. Study 3 found no rate at which the frozen test keeps its false-claim
    limits, and none of three candidate replacements passed either (response 198).

## What to review

The branch is `story/br1a-protocol` at the head named in the orchestrator's link (it may stay on the branch).

1. **The freezer generalisation** in `fno/evaluation/`:
   - `definition.py` and `breadth.py` are new;
   - `freeze.py`, `order.py` (`verify` only) and `cli.py` now read a `ProtocolDefinition`;
   - `wiring.py` maps `evaluation` / `breadth`.
   - Tests: `tests/evaluation/test_breadth_protocol.py`, plus S1's own tests, which are unchanged.
2. **The three studies**: `research/breadth/studies/` (`brstudy/*`, `run.py`), their results in `results/*.json`,
   and `results/DIAGNOSTICS.md`. Tests: `tests/research/test_breadth_studies.py`.
3. **The candidate comparison**: `research/breadth/candidates/` and `reviews/claude/response_198_br1-test-candidates.md`.
   Part 1 was committed before the run, then part 2 holds the results. Tests:
   `tests/research/test_breadth_candidates.py`.
4. **The protocol text**: `research/breadth/PROTOCOL.md` and `research/breadth/README.md`. The owner decided `looks`
   and `null_size_check`; the other 16 items are proposals.
5. **The claims and verdicts**: `reviews/claude/response_197_br1a-code-claims.md` and judge 213 with its addenda
   (`reviews/judge/`).

The Drive raw archive holds the input data (NSE's daily F&O bhavcopies, both formats), read only. If you cannot read
it, judge each question from the code, the tests and the result files, and say where that limited you.

## Five questions

For each, answer **accept / partial / reject**, with the evidence and a real case. No imagined failure modes: the
owner's rule is to test real cases only.

1. **S1 unchanged.**
   - **What changed:** the freezer, the verify command and the check command now take a protocol definition. S1's is
     the default everywhere, and the real-money gate is required only when the definition asks for it
     (`requires_gate`, True for S1, False for BR1).
   - **Untouched:** `protocol.py`, `completeness.py` and `gate.py`.
   - **Question:** does every S1 path (check, freeze, verify, order; the record text; the ledger row; the messages)
     behave exactly as before?
   - **A note to weigh:** S1's `frozen_files` lists neither `freeze.py` nor the new `definition.py`, and S1's
     `requires_gate=True` now lives in `definition.py`. Is that a gap S1 should close, or no weaker than before (the
     gate call lived in the unfrozen `freeze.py`)?
2. **Study 3's procedure.**
   - **The procedure:**
     - the same block starts for all members and the primary's loss;
     - centring within the population tested;
     - Holm's any-claim as "smallest p at most rate / 3";
     - the exact bootstrap only when the batch-means p is at most rate / 3 (tested against the full test).
   - **Question:** is any of these a wrong reading of the frozen `confirmatory_test` or of Holm, such that study 3's
     "no rate passes" could be an artefact?
3. **The window choice (deviation 3 in response 197).**
   - **What was done:** after study 1's 96.0% agreement failed its 97% gate, the window was applied to the inputs
     too. No old-format row feeds any baseline, so 2024 has 189 scored sessions after a 60-session burn-in.
   - **Question:** is this the right reading of the fallback, or should Dec 2023's old-format rows have fed the
     trailing baselines? Would the other reading change any result?
4. **The cause named in response 198.**
   - **The finding:** dependence lasting longer than the test's 5-session blocks.
     - For the two `market` pairs, the variance ratio of 63-session to 5-session means is 1.43 and 2.08.
     - The daily sign's autocorrelation is still about 0.2 at lag 20.
   - **Question:** do you agree this, more than the skew, explains why the v4 gate, the sign test and a threshold
     calibrated on one year all fail? Is there a test you know from forecast evaluation (for example HAC / Newey-West
     with a long bandwidth, or a stationary bootstrap with a data-chosen block) that would keep its size here with
     less history than the 21-session-block candidate D, which needs about 2.5-4 years?
5. **Descriptive only.**
   - **What `PROTOCOL.md` now says:** every BR1 result is reported as a paired difference with its interval,
     labelled descriptive, and never worded as proven skill. The size check is re-run each year on the latest two
     full years, and a pass can only start a new protocol version.
   - **Question:** is that wording safe against a descriptive result being read as a claim? Is anything missing from
     how a reader is warned?

## Where to answer

Write `reviews/chatgpt/review_133_br1a-code.md` on **main**, with its README row. I will answer in a new
`reviews/claude/response_<n>` file, accepting, partly accepting or rejecting each point with my own check on the data.
