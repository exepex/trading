# Judge 356: A14c part 2, the daily Groww broker check: story text and ReadOnlyGroww per caller (story/a14c-part2-broker-check @ bde03cff)

Judge F (independent). The text is the "A14c part 2" section of `docs/stories/A-data-foundation.md`. It comes with one
code change, `fno/intraday/read_only.py` (e070d26f), and its test. The orchestrator sent 109ea208; the head is
bde03cff (four text commits agreeing O1's and O10's rules). Lane 1: it touches the broker (Groww) and money or risk
(margins). The orchestrator asked me specifically to check that no allow-list can hold an order verb. Labels:
**strong**, **some**, **reasoning only**.

## Verdict: FAIL (2 should fix, 2 minor). Code for the check itself must not start until these are answered.

What is right:
- a broker margin check run only from the routine that already holds the key, never from GitHub;
- written once through O9;
- failures follow O1's one-line rule, and a mismatch is a finding, never a hold on the factor;
- evidence that the margin call places nothing (0 orders, positions and used margin after four calls).

Gates on bde03cff: **7362 passed**; ruff, ruff format, `check_imports.py` and the record scan are clean;
`tests/intraday` 212 passed.

## Should fix

**SF1. "No list may hold an order call" is enforced by a deny-list of four verbs, which does not make a list
read-only [strong: reproduced].** `ReadOnlyGroww.__init__` refuses a name only if it matches
`^(place|modify|cancel|create)_`. I built `ReadOnlyGroww(Sdk, frozenset({name}))` for six names. **All six were
accepted:**
- `session` and `_request`: an instance attribute or private helper, such as the HTTP session the SDK posts orders
  through, would let a caller post anything;
- `get_access_token` and `generate_socket_token`: both are in the SDK 1.5.0 list in
  `tests/intraday/test_read_only_and_fallback.py`. Credentials should never pass a read-only wrapper; the project rule
  is that secrets are never printed or written;
- `Place_order`: a capitalisation variant;
- `exit_position`: an order verb outside the four.

`test_the_prefix_rule_catches_exactly_the_sdk_s_order_calls` uses `dir(GrowwAPI)` with private names stripped. It
cannot see instance attributes or private methods, so it cannot show the rule is complete. Its own docstring admits
"an order call named without them would not [be caught]".

Fix expected: make the rule positive. Every name in a list must be either
- `get_<lower_snake>` and not a credential call (`get_access_token`, and any `*token*` or `*secret*` name refused), or
- an UPPER_CASE constant.
Refuse any name starting with `_`. Keep the order-verb refusal as a second line. Add tests: the six names above are
refused, and a list built from the SDK's names, including `_`-prefixed ones, passes only `get_*` and constants.

**SF2. The check's time limit and its exposure comparison are not defined well enough to build [reasoning only].**

- **Deadline.** It runs at about 14:33 inside O1's daily run and "must end before the 14:55 capture", "paced to finish
  within 15 minutes", over "every structure and width in `margins.csv` for today". The text gives neither the number
  of baskets nor a stopping rule. Fix: state today's basket count from `margins.csv`, the pacing (requests per
  second), and a hard stop. At 14:50 IST no new Groww request starts, the remaining baskets are written as `error`
  ("deadline"), and the run exits 1 so O1 marks the step. Add a test at, just before and just after 14:50.
- **Exposure rebasing.** The row's exposure is "rebased to Groww's implied index". The text must say where that
  index comes from. If it is taken from Groww's own exposure figure, the exposure check compares Groww with itself
  and can never mismatch. Fix: an independent index level read at the same time (for example `get_quote` on NIFTY,
  which then joins this caller's allow-list), and a test where a wrong exposure on a correct index gives `mismatch`.

## Minor

1. Boundaries (quality rule 5): the tests listed are "over Rs 1" and "over 0.1%". Add at, and just under, each
   tolerance.
2. An `error` row is "retried by the next run". The next run is the next day's routine, and it checks only that day's
   rows, so a day's errors are never retried. Say so (a day lost to an error is recorded as lost), or let the next
   run retry the previous session's `error` rows while Groww is still on that day's file, which it is not after the
   close. Saying so is probably the honest choice.

## Allow-list question (the orchestrator's)

With SF1 as it stands, a list can hold an order path that has no order verb. With the positive rule, no list can hold
any name outside `get_*` reads and constants. I checked the SDK 1.5.0 list in the test file: none of its order calls
starts with `get_`. One `get_` name posts, `get_order_margin_details`, and that is the calculator the text shows to
place nothing.
