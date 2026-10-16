# Response 231: BR1a's follow-up after ChatGPT review 133 (claims, lane 1; must be judged before S1's freeze)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ, branch `story/br1-followup` from main at 03705884. Asked by the
orchestrator in response 230.

## The three changes

1. **S1 hashes its freezer.**
   - `research/evaluation/PROTOCOL.md` `frozen_files` adds `fno/evaluation/definition.py`, `freeze.py` and `order.py`.
     `definition.py` holds S1's definition, the real-money gate's `requires_gate=True` included; until now it was
     unhashed.
   - Test `tests/evaluation/test_freezer_is_frozen.py`: the real list contains the three files. A fixture freezes a
     decided protocol listing `definition.py`, then turns `requires_gate` to False, and `verify` then reports the
     file changed.
   - **For the judge:** `frozen_files` is decided by the owner (14 Oct). Its rule already adds code to the list before
     the freeze ("is added to this list before the freeze"), so I kept its status. If the judge reads a new
     non-scoring file as a change to a decided item, it is the S1 owner's and the owner's call. S1 is not frozen, so
     nothing frozen changes.
2. **BR1's disclaimer.** These four places carry the text verbatim:
   - `research/breadth/README.md`, `PROTOCOL.md` (item `reporting`, as the rule for every future chart, table and
     export), `studies/results/DIAGNOSTICS.md` and response 198's results.
   - The text: "Exploratory estimate; interval is descriptive and its coverage is not validated for these dependent
     market days. Not evidence of forecast skill, trading profit or real-money eligibility."
   - No BR1 text marks a family PASS or "beats baseline". Test: `tests/research/test_breadth_wording.py`.
3. **The explanation.** README, PROTOCOL (`null_size_check`) and DIAGNOSTICS say "dependence is the leading supported
   explanation, with skew and tails contributing". The README records the HAC or stationary-bootstrap test as parked:
   only a future pre-registered version, never retrofitted.

## What was not changed, and why

- **The committed study and candidate result files** (`study*.json`, `candidates/results.json`) were written once by
  pre-registered runs. Adding a field to them after the fact would edit results. The disclaimer sits beside them, in
  the README and DIAGNOSTICS.
- **No BR1 chart or export exists yet.** The rule in `PROTOCOL.md` `reporting` binds the first one (BR1b-e), and the
  wording test covers every `.md` under `research/breadth/`.

Gates: ruff, format and `tools/check_imports.py` clean; `pytest -n auto` 6,912 passed.
