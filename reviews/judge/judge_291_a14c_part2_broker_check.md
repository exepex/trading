# Judge 291: A14c part 2, daily Groww broker check (story/a14c-part2-broker-check at efd40677)

**Verdict: FAIL, 3 should-fix in the story text.** The code part, `ReadOnlyGroww` with an allow-list per caller, is
sound and would pass on its own (below).

## The code part: `fno/intraday/read_only.py` and `tests/intraday/test_read_only_per_caller.py`
| Check | Result | Evidence |
|---|---|---|
| The recorder keeps its list by default | MET | `allowed: frozenset[str] = ALLOWED`; test |
| A caller's list lets only its own names through | MET | `__getattr__` checks `self.__allowed`; test with MARGIN_ONLY |
| No list may hold an order call | MET | the constructor refuses any name matching `^(place\|modify\|cancel\|create)_` |
| The prefix rule is exactly the SDK's order calls | MET | I checked the installed `growwapi` (85 public names): the matches are exactly `cancel_order, cancel_smart_order, create_smart_order, modify_order, modify_smart_order, place_order`. No other trading-like prefix (exit, square, convert, buy, sell) exists |
| `get_order_margin_details` is a calculator | MET (some to strong evidence) | the SDK source posts the basket to `/margins/detail/orders`. The builder's read-only account check after 4 calls found 0 orders and 0 positions |
| Planted mutations | 3 of 3 caught | constructor check off (7 failed); `create_` dropped (2 failed); global list instead of the caller's (1 failed). tests/intraday plus intraday_backfill: 304 passed on a trial merge |

## Should-fix (story text)
1. **The market-hours window shuts out the only time the check runs.** The text runs the check as O1's
   `margin_check` step in the daily run, and allows it only "09:30 to 14:30 IST". O1's routine starts at **14:33 IST**
   (CLAUDE.md, "Daily desk routine"), and `margin_check` is the second step after `quotes` (`DAILY_RUN_STEPS`). So it
   would print "outside market hours" every day and never record anything: each day lost, the very thing the widening
   was meant to stop.

   The window has to fit the run. That also needs an end bound: the quote parts start first and begin their Groww
   capture at 14:55, and the check now asks Groww once for *every* structure and width of the day. So the text must
   give:
   - a time after which it starts no new request (for example 14:50);
   - the expected number of baskets a day;
   - and the pacing, so it can never overlap the 14:55 capture.

   ("Before the 3 pm quote parts" is also out of date: since O1 the parts start first and wait.)
2. **The exposure check has no independent index.** The text compares Groww's `exposure_required` with "the row's
   exposure rebased to Groww's implied index". Groww's answer carries no index: response 77 lists `exposure_required`,
   `span_required`, `option_buy_premium` and `total_requirement`. The allow-list proposed for this caller has no quote
   call. So the only way to "imply" the index is from Groww's own exposure figure, and then the comparison is circular:
   it can never show a mismatch.

   The text must name an index source that does not come from the figure being checked. Two options:
   - a read-only NIFTY `get_quote` added to this caller's list, taken at the check time;
   - or A16's 15-minute NIFTY level nearest the check.

   It must also give the test: a planted Groww exposure 0.2% off, with the planted index, gives `mismatch`.
3. **O1's step still names the old command and file.** On main, `fno/daily/wiring.py` has:
   - `MARGIN_CHECK = ("margins", "stress-broker-check")`;
   - `MARGIN_CHECKS = "research/data/margins/stress_broker_check.csv"` as the step's commit pathspec.

   The text renames the command to `margins broker-check` and moves the record to O9's Drive store with a receipt under
   `receipts/`. It must name the matching O1 change and its owner (O1's builder, lane 1): the command and the pathspec,
   which becomes the receipt path, unless the child commits its own receipt. Otherwise, on its `live_from` date the step
   runs a command that does not exist and commits nothing. Today the step is behind `LiveFrom`, so nothing breaks yet.

## Notes (not should-fix)
- **Committing a receipt from inside the step is safe under O2's lock rule**, because `CommandStep` runs on its own
  with the run's thread asleep (the same as Book 1's own commit, judge 204 addendum 3). Say which of the two the build
  uses.
- **`research/ops/capture_errors.csv` versus "nothing is appended in GitHub".** If O10's file lives in git, the step
  appends to GitHub. Make the sentence say "no margin figure is appended in GitHub", and add the file to the step's
  pathspec.
- **The SPAN tolerance of Rs 1 a lot and exposure 0.1% are "some evidence"** (one basket, one day), as stated. Keep the
  first weeks' mismatches as a finding for the owner, never as an automatic change.

## Addendum 1: heads 0f20dd73, c8498066 and bde03cff (bde03cff is the head to judge)
The three heads were pushed before my verdict above reached the builder, so they answer O1's owner, not this verdict.
I judged bde03cff against the three should-fix items.

**Verdict: still FAIL: should-fix 2 is open, and should-fix 1 is partly met.**

| Should-fix | Result | Evidence |
|---|---|---|
| 1. The window fits the run | PARTLY | Now 09:30-14:50 IST, "the step after the quote parts start (about 14:33 IST)", "paced to finish within 15 minutes". Still missing: a rule that **no request starts after 14:50**, whatever time the step began. A rerun or a late routine starting the step at 14:45 would otherwise be paced to 15:00 and overlap the 14:55 capture. Also missing: the expected number of baskets a day, behind the 15-minute claim |
| 2. An independent index for the exposure check | NOT MET | Unchanged: "rebased to Groww's implied index". Groww's answer has no index field, so the check is circular unless the text names a separate NIFTY level (a `get_quote` in this caller's list, or A16's nearest 15-minute level) and a planted-mismatch test |
| 3. O1's command and file | MET | It keeps O1's name `margins stress-broker-check`; `receipt_pathspecs()` replaces `stress_broker_check.csv`, agreed with O1's owner; the step commits only its own receipts |

**The new exit rules are right.** A mismatch is a finding: its own line saying what to do, exit 0, the step `ok`, never
a capture miss and never retried. Exit 1, with no alert of its own, is only for a Groww or write failure. Neither
`capture_errors.csv` nor the step's own alert duplicates O1's journal and `Alerted`. This also closes my note on
`capture_errors.csv`.
