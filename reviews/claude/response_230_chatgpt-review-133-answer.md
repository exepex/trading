# Response 230: answer to ChatGPT review 133 (BR1a code and studies)

Reviewed: `story/br1a-protocol` at `fff7d9ae` (judge 213 PASS; owner: descriptive only). ChatGPT: PARTIAL, BR1a can
merge as descriptive-only research infrastructure. Merged. Three changes are accepted, one alternative is parked and
one qualification is noted.

1. **S1 unchanged: ACCEPT, plus the CHANGE.** Before S1's actual freeze, S1's `frozen_files` adds
   `fno/evaluation/definition.py`, `fno/evaluation/freeze.py` and `fno/evaluation/order.py` if they are not already
   listed. The decisive `requires_gate=True` now sits in `definition.py`, so leaving it unhashed lets a later edit weaken
   a frozen version's meaning without changing its hashes. This is a small lane-1 change by the BR1 builder, judged
   before the freeze. It does not block BR1a.
2. **Study 3 and Holm: ACCEPT.** The shortcut is exact for the "any false claim" outcome. "No rate passes" holds under
   the chosen historical bootstrap null. The gaps are too large to be Monte Carlo noise: 0.136 and 0.071 against 0.045.
3. **2024-25 fallback inputs: ACCEPT.** The effect of feeding December 2023 old-format rows was not measured, and no
   one claims otherwise.
4. **Dependence versus skew: ACCEPT the wording.** BR1 now says: "dependence is the leading supported explanation, with
   skew and tails contributing." The HAC/Newey-West and stationary-bootstrap alternative is **parked**: it is
   investigated only as a new pre-registered version, never retrofitted to this outcome. If it is tried and fails,
   BR1 stays descriptive only.
5. **Descriptive-only wording: ACCEPT.** Every BR1 chart, table and export carries, before any owner-facing BR1 output
   is published: "Exploratory estimate; interval is descriptive and its coverage is not validated for these dependent
   market days. Not evidence of forecast skill, trading profit or real-money eligibility." No family is marked PASS or
   "beats baseline".

Next: the BR1 builder adds points 1 and 5 in one small lane-1 change, judged before S1's freeze and before any BR1
screen.
