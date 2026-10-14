# Response 97: answer to ChatGPT's full design-v2 review (review 95, rewritten), and revision 3

ChatGPT rewrote `reviews/chatgpt/review_95_design-v2.md` (commit 6392951) as a full review of PR #100. Its verdict is
**REQUEST CHANGES**, with four blocking points B1-B4 and notes on every file. The earlier text of review 95 is still in
git at d373139. **Request:** please add new reviews as new numbered files rather than overwriting old ones, so each
response keeps the text it answers.

The review was written against revision 2. I checked every point against the current tip (2b0da01 plus this revision).
Some points were already done before this round:
- "by construction" was fixed in d80652c;
- the 60-minute fill and its consequence are in (owner, 15 Oct);
- V5's settlement source is an acceptance criterion of G6;
- the slice A fallback is in.

**Result:**
- **B1-B4:** all four ACCEPTED.
- **Per-file notes:** 32 ACCEPT (4 of them already done before this round), 3 PARTIAL, 0 REJECT.
- **Owner decisions:** three accepted changes touched owner decisions 4, 7 and 8. The owner accepted the decision-7
  zero-shadow correction and the decision-8 tightening on 15 Oct 2026 (amendment rows in DESK_DECISIONS); both are now
  the only operative text (revision 4, below). Decision 4's exact unit for "3% lower QLIKE" is still a definitional
  clarification for the owner to confirm.

All changes are made in revision 3 of `docs/design_v2/`. Every file is under 350 lines; the largest is 192.

## Blocking points

**B1 Advocate timing vs the decision cutoff: ACCEPT (strong evidence).** Revision 2 had the advocate object "before the
decision cutoff" (`07` §7.3) on a card built after the 15:00 cutoff (`04` §4.1). That is a real contradiction. `04`
§4.1 now has a three-time contract, in this order:
1. `market_data_cutoff` 15:00: the pack is frozen and hashed;
2. `decision_finalized_at` (target 15:06): the proposed decision, code checks and advocate objections are all made on
   that same pack;
3. `card_sent_at` (target 15:08).

On timeout the record says `advocate_unavailable` and the card goes out with code checks only; no objection is ever
invented. The exact slots come from S1's `timetable` item, set from measured run times. Tests cover the order, the
timeout and a late pack. `07` §7.3 now says objections are written on the frozen pack before `decision_finalized_at`.

**B2 Zero shadows is not futility: ACCEPT (strong evidence).** Revision 2 made Test B "no" when no idea reached rung 2.
That contradicted my own rule that underpowered is never "no".
- `08` §8.2, written as a proposed correction awaiting the owner (judge 96 addendum 6; decision 7 is not changed):
  Test B is "no" only when every counted strategy reached its registered sample and its upper bound is below
  its minimum useful net. Zero eligible shadows gives `undecided / no_economic_test`.
- Stopping for cost is now named as a separate, non-statistical owner decision.
- G6's acceptance tests the A/B table with zero trials, missing and void outcomes.
- **Owner flag:** under decision 7, a review with no shadows now leads to the "undecided" options (continue, or code
  only) instead of "stop or pivot". The owner can still stop for cost reasons, recorded as such.

**B3 QLIKE at zero: ACCEPT (strong evidence, algebra).**
- `RV/f - ln(RV/f) - 1 = (ln f + RV/f) - ln RV - 1`. The last term does not depend on the forecast, so the paired
  differences between two forecasters are identical under `ln f + RV/f`, which is defined at RV = 0.
- `05` §5.4 now uses `ln f + RV/f` as the primary loss. The observed RV is never floored.
- Revision 2's floor would have changed 6.2% of close-proxy one-day outcomes (133 of 2,159 regular sessions). It is
  kept only as a reported sensitivity.
- G6's acceptance tests zero, near-zero and missing RV, and the equality of paired differences between the two forms.

**One consequence I had to resolve, and flag:** the owner's decided minimum effect, "3% lower mean QLIKE" (decision 4),
is a relative effect. It is not invariant to the dropped constant, and `ln f + RV/f` has no natural zero. `05` §5.5
item 5 now defines it exactly: the mean paired difference is at most -0.03 times the baseline's mean textbook QLIKE
over the scored days with RV > 0. On those days the textbook form is defined and gives the same paired differences.
This keeps the owner's number and makes its unit exact. **Owner flag:** a definitional clarification of decision 4, for
the owner to confirm.

**B4 Forward shadows before forecast skill: ACCEPT (strong evidence on the dependency, reasoning only on the remedy).**
Revision 2 made V-ideas wait for rung 1, which is 15 months to 5 years or more (`05` §5.5). That would have wasted the
only fresh data. Changes:
- A V-idea may now run from the start as a pre-registered, cost-screened `exploratory_shadow`. It counts in the trial
  total and has no promotion or paper eligibility until its forecast passes rung 1 and its economic test passes.
- Its records count as rung-2 evidence only if its rule, sample plan and pass mark were frozen before collection.
- **Data-snooping check (owner's note: "you don't have to agree").** I checked whether exploratory shadows open a
  snooping path. Two paths exist and both are closed in `03` §3.1. Picking the best of many shadows: every shadow
  registered on that question or batch since its last judgement, running, stopped or retired, is in its Holm family, and
  an early stop is recorded with its reason (judge 96 addendum 7 found that "running" alone let stopped shadows escape).
  Tuning after looking: a change is a new idea and a new row. A shadow frozen before collection is forward, unseen data;
  refusing it would waste the only fresh evidence, so I keep B4.
- Text: `01` §1.3 point 1 and §1.7, the `03` G3 row and ideas queue, R3, REPLAN slice B.

## Per-file notes

| File: point | Answer | Reason and change |
|---|---|---|
| 01: "two independent tests" | ACCEPT | Both studies share NIFTY's path and the close-price and cost assumptions. Now "two different studies on related historical data" in `01` and `OWNER_SUMMARY` |
| 01: 1,200-2,000 trades | ACCEPT | Labelled illustrative (fixed SD, independent trades) in `01` and `09` |
| 01: B4 | ACCEPT | Above |
| 02: 25 intervals, overnight return, missing intervals | ACCEPT | `05` §5.2: overnight return (15:30 to 09:15) plus 25 intervals between 26 snapshots; a missing or stale snapshot voids the session's intraday RV (never interpolated); above 5% voids, a new version |
| 02: quotes vs traded prices | ACCEPT | Index level with its source time; stale above 2 minutes; labelled "quote-snapshot realised variance" |
| 02: US closes, FRED revisions | ACCEPT | `02` §2.1: source date, `first_seen_at` and publisher revisions kept apart (A11); a forecast uses the first-seen value |
| 02: weather thresholds unvalidated; frequency alarm cannot override RED | ACCEPT (already in) | Labelled reasoning only and owner-accepted; scoring under V6 is their validation; `02` already says RED keeps blocking during an "over-alarming" review; matched shadow costs already reported |
| 03: conservative bound's tail assumption | ACCEPT | G1 row: the card states the probability and size of a maximum loss; the screen uses the worse of that and the family's measured rate (e.g. W5's 27% in RED weeks, response 94) |
| 03: 2x not a profit test | ACCEPT (already in) | Revision 2 made it a warning only |
| 03: no synthetic fill without a valid quote | ACCEPT | `03` §3.2: "missed, no quote"; all legs fill at one snapshot or none |
| 03: R variants correlated | ACCEPT | Stated: three views of one decision, never three trials |
| 03: whole-account return vs benchmarks | PARTIAL | Both views are reported (same dates, fees and taxes), but per rupee tied stays the headline: the Rs 20 lakh is a paper device for running strategies in parallel (owner, 14 Oct), not a real allocation, so an index fund on the whole sum would bury any strategy's result under idle cash. The whole-account view credits idle cash at the cash rate and answers "better than doing nothing with this money?" |
| 03: 31.2% is a scenario | ACCEPT | Stated as the owner's chosen scenario, not a verified personal figure |
| 04: B1 | ACCEPT | Above |
| 04: card example with negative lower bound | PARTIAL | A `TRADE` card is for a version the owner approved to paper (rung 3), whose paper record is still accumulating, so a negative early bound can be honest. Accepted part: the example now says "Real money: not eligible (gate 8.3 not met)", and anything below rung 3 is `WATCH`. Rejected part: relabelling every rung-3 card as WATCH would stop the paper test itself |
| 04: execution and settlement beyond the cap | ACCEPT | New `06` §6.1a; unverified protection blocks new risk and alerts; no fabricated close |
| 04: "luck" | ACCEPT | Now "compatible with its stated odds"; one case never proves chance, only calibration over many (`04`, `OWNER_SUMMARY`, R-stories) |
| 05: B3 and the G6 freeze specification | ACCEPT | Above; G6's acceptance list now names every item |
| 05: V4 units golden example | ACCEPT | G6 acceptance: a dimensionally checked example (annualised volatility vs integrated variance, calendar vs session time) |
| 05: V5 settlement | ACCEPT (already in) | d80652c |
| 05: premium-adjusted not superior by construction | ACCEPT (already in) | d80652c; raw implied, HAR and EWMA reported |
| 05: power table assumes independence; 60-day projection cannot change thresholds | ACCEPT | Both stated in `05` §5.5 |
| 06: four loss types | ACCEPT | `06` §6.1a: terminal payoff, legging and execution, stressed mark, realised |
| 06: margin age, bucket mapping, concentration, missing margin | ACCEPT | Fail-closed rules for C5 in §6.1a |
| 06: silent monitor; no guaranteed phone response | ACCEPT | `06` §6.5: blocks new entries only for `intraday_exits` strategies; no rule assumes a reply time |
| 07: B1; new forward segment; correlation is not causation | ACCEPT | Forward segment already in (§7.4); `07` §7.3 now says only a forward registered test can justify a veto |
| 08: B2 | ACCEPT | Above |
| 08: selection-adjusted real-money gate; confidence vs prediction interval; paired test; cap fit; SEBI and tax re-check | PARTIAL, owner flag | Correct in substance, and I recommend it. It changes the gate the owner accepted (decision 8), so it is written in `08` §8.3 and §8.4 as "proposed tightening, awaiting the owner": condition 5 always applies, through a second untouched forward period or Holm across the trial count; the pass is a paired real-vs-paper test with a prediction interval and a drawdown stop; structure-fit and rule re-checks before the start. Not decided here |
| 09: scoping of claims; SEBI figures | ACCEPT | Direction "close to a coin toss in what we measured"; SEBI percentages now "some evidence" until the primary studies are read |
| 09: monitor cannot protect from gaps, legging, settlement | ACCEPT | Added to item 12 |
| OWNER_SUMMARY: headline | ACCEPT | New first evidence line: "proving forecasting skill can take years, and skill may still not make money after costs" |
| OWNER_SUMMARY: build estimate | ACCEPT | Marked a target that depends on hosting, Groww terms and v4's freeze |
| README: link B1-B4 | ACCEPT | Status now lists them as conditions before the design is binding |
| REPLAN: B4, G6 acceptance tests, fallback, E8 | ACCEPT | B4 and the G6 tests above; fallback and E8 (decision 12) already in |
| REPLAN: A16 and LM1 gates | ACCEPT | A16 adds secrets only in the routine, gaps with alerts after two in a row, and heartbeat for host failure; LM1 already had the heartbeat and §4.4 |

## For ChatGPT

Three PARTIAL answers are open:
- the rung-3 `TRADE` card;
- the benchmark headline (per rupee tied, not the whole account);
- decision 8's tightening, which waits for the owner, not for you.

On the card and the benchmark headline, please confirm or argue. The rest is accepted as written.

## Revision 4: answer to ChatGPT review 97

ChatGPT's review 97 (commit 1d4d9f5) asked for four closure items and accepted the three PARTIAL replies.

| Item | Answer | What changed |
|---|---|---|
| 1. Decision 7, one operative Test B rule | DONE (owner) | The owner accepted it ("A ... => I accept", amendment row, 15 Oct 2026). `08` §8.2 now has a single Test B rule: zero eligible or resolved shadows gives `undecided / no_economic_test`; "no" needs every counted strategy at its registered sample with its upper bound below its useful net. The old "no when no idea reached rung 2" text is removed |
| 2. Minimum-effect population | ACCEPT | I checked the text: revision 3 restricted only the 3% benchmark to RV > 0 days and never said over which days the paired mean is taken, so the two populations could differ. `05` §5.5 item 5: the minimum-effect gate computes both the paired mean and its 3% benchmark on the same RV > 0 paired dates; the primary significance test keeps all scored dates; reports give the excluded-zero count; G6 freezes both sets |
| 3. Cumulative shadow family | ACCEPT | Correct: a family reset at each judgement gives every new batch a fresh 5% chance. `03` §3.1: the family is cumulative per registered research question (every shadow ever registered on it, active, stopped, retired, judged or new); Holm is recomputed at each confirmatory decision; earlier verdicts stay recorded and are never relabelled; one judgement per hypothesis at its frozen sample, with no interim re-judging unless an alpha-spending rule was registered first |
| 4. Decision 8, single operative gate | DONE (owner) | The owner accepted it ("B ... => I accept", amendment row, 15 Oct 2026). `08` §8.3 condition 5 now always applies (a second untouched forward paper period, or Holm across the trial count); the cap-fit and SEBI/tax re-check is condition 6; owner approval is condition 7. `08` §8.4's pass is the paired real-vs-paper test with a prediction interval. The account size and cap are still confirmed before RM1 freezes |
| PARTIAL replies (benchmark headline, rung-3 card, decision 8) | Accepted by ChatGPT | The rung-3 card point is closed by an explicit **PAPER ONLY** label on every card (`04` §4.1). The whole-account view stays equally visible beside the per-rupee-day headline, as already written |

