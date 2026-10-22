# G13d. Next-session premium range for each contract, from a stated volatility rule, scored on the next 3 pm mid

**Repository:** trading · **Lane:** 1 (new story; forecast and evaluation records; Drive) · **Judge:** B ·
**Builder:** session_01UkTaDeTRF9ksDgQB9cTU5C · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Branch:**
`story/g13d-premium-ranges` · **Depends on:** G13 (`fno/price_distribution/`), G13b's sealing (`fno/price_ranges/`
seals) · **Status:** story text, revision 2 for judge
B after judge 453 (no code yet; built after G13c)

**Description.** As the options trader and the risk manager, I want, for every NIFTY and BANKNIFTY monthly contract
on today's 3 pm chain, a range (5/25/50/75/95%) for its mid at the next session's 3 pm. The range comes from one
written volatility rule, is sealed before the outcome, and is scored against the next 3 pm mid and two plain
baselines. Then the desk knows how far a premium can move in a day, and whether the simple rule gets that size
right, before any position is sized on it.

**Does this change a trade or stop decision?** No. Descriptive and scored; nothing reads it to size, enter, exit or
block a trade; it is in no frozen protocol. If it scores well, using it for paper stops is an owner question (Q1).

## The rule (stated once, no fitted parameter)

For one contract (strike K, side CE/PE, expiry T) on day d's 3 pm chain, with G13's values for that expiry:

1. **Forward move.** The next session d+ is the calendar's next regular or special session. `h` = calendar days from
   d to d+ over 365 (G13's `years` convention). `σ_atm` = G13's ATM IV of that expiry on d. The forward's quantiles
   are `F_q = F · exp(-σ_atm² h / 2 + z_q σ_atm √h)` for z at 5/25/50/75/95%.
2. **Sticky strike.** The contract keeps its own IV of day d (G13's `iv` for that contract), not the smile IV: the
   smile is a smoothness fit, the contract's IV is its quote.
3. **One day less.** Each `F_q` is priced with Black-76 at the contract's IV, `days - (d+ - d)` days to expiry, and
   G13's rate.
4. **Quantiles.** A call's value rises with F and a put's falls, so the call's quantiles are the values at `F_q` in
   order, and the put's are the same values in reverse order (the 5% premium comes from the 95% forward). The range
   is monotone by construction; nothing is re-sorted.
5. **Not ranged.** No contract IV, the expiry is d+ itself or earlier (then the next 3 pm is expiry day: out of
   scope), no G13 distribution for the expiry, or d+ is a special session with no 3 pm chain recorded (reason "d+ has
   no 3 pm chain"). Each such contract is counted by reason, never guessed.

What the rule leaves out, said in advance: IV changes (a fall in the index usually lifts IV, so put ranges should come
out too narrow on down days), the skew's movement, and the bid-ask spread. The scores will show how much this costs.

## Baselines

- `no_change`: a point at today's mid (all five quantiles equal).
- `decay_only`: the forward unchanged, IV unchanged, one day less: a point at that value.

Both are points: their quantile score is the absolute error. They show whether the range's width is worth anything
over plain carry.

## Outcome and scores

- **Outcome.** The contract's mid at d+'s 3 pm from A4's canonical chain (same source as d: Groww for Groww, NSE for
  NSE), only a valid two-sided quote (`LiveQuote.mid`). No valid quote at d+ means the row is unscored, counted.
- **Per row.** Pinball/QS in rupees (G13's `scoring.py`), inside 50%, inside 90%. Per row also QS divided by
  `max(d's mid, ₹2)` (relative; the ₹2 floor keeps near-zero premiums from dominating, judge 453 note), reported
  beside the rupee figure, because cheap options dominate one and dear ones the other. Relative QS is descriptive
  only; the verdict below uses rupee QS.
- **Buckets.** By |delta| at d: below 0.15, 0.15-0.35, 0.35-0.65, above 0.65; and by days to expiry: 2-7, 8-21,
  over 21.
- **Unit = session.** All contracts of one day share one index move, so coverage and the paired QS difference
  (rule minus baseline) are first averaged per session, then over sessions. Intervals come from G4's block bootstrap
  over sessions; rows are never treated as independent. The report prints the number of sessions beside every figure.
- **Verdict rule, written before any score (judge 453 SF1, option a).** Per underlying, on all ranged contracts
  (buckets descriptive only, never decided on):
  - *covers well*: the session-averaged 90% coverage's block-bootstrap 95% interval lies inside [0.85, 0.95], and
    the 50% coverage's inside [0.40, 0.60];
  - *beats carry*: the session-averaged paired rupee-QS difference (rule minus `decay_only`) has its 95% interval
    below 0 (against `no_change` it is reported, not decided on);
  - *fails*: a coverage interval lies wholly outside its band, or the QS interval lies wholly above 0;
  - otherwise *not yet decided*.
  - Looks are fixed in advance: at 60, 120 and 250 scored sessions per underlying, and at no other count. The report
    shows numbers from day one but prints "not yet decided (next look at n sessions)" between looks. Three looks
    with a containment rule slightly raise the chance of a lucky pass; the 250-session look is the one Q1 relies on
    unless the earlier pass repeats there [reasoning only].
  - Said in advance (corrected by judge 464 note 2): every contract of a session shares one index move, so a
    session's coverage is near 0 or 1. Its SD is about 0.3 at 90% and 0.5 at 50%, not 0.2. Even under exact
    calibration, the bands become reachable only from about 96 sessions (50%) and 138 sessions (90%). So the 60-session
    look will almost surely say "not yet decided", and the 120 and 250 looks are the real ones [reasoning only:
    judge's arithmetic, independent sessions assumed; autocorrelation would widen it further].

## Sealing, files, timing

- Issue at the 3 pm chain's record time (G13's step). Sealed the same way G13b seals (GitHub push time of the receipt;
  late if after 15:30 IST on d, the session's close, so no later price of d is known at the seal).
  A late record is scored but marked late.
- **Build note (O1's owner, 22 Oct): the command itself refuses at or after 15:30** ("nothing written: past the 15:30
  seal"; O1 records it refused and alerts once), so no issue is ever written that cannot be sealed. A late seal now
  happens only when an issue written before 15:30 is pushed after it; it is scored and marked late as above.
  - The timetable: on 19 and 21 Oct the card ended at about 15:19 IST, so G13's step and this one share about 11
    minutes. G13's runtime is first measured on its live day (22 Oct). The budget (minutes used against 11) is
    stated before G13d's go-live.
- Files: `data/premium_ranges/live/<underlying>/<day>.json.gz` and `.../scores/...` in Drive, write-once, O9
  receipts. Schema `g13d_premium_v1`, with the rule's method hash.
- Steps: `premium_ranges` right after `price_distribution`, and `premium_range_scores` after it on the next day.
  Adding them to O1 needs O1's owner (session_014zYLf18PgCzR7YoHs1X5Dp) and a `daily.live_from` date, null until a
  judged go-live.
- **No history back-fill in this story.** The 3 pm chain with bid/ask exists only from 14 Oct 2026. The end-of-day
  panel has traded closes only, a different target (close to close, no mid); a back-fill on it would be a second
  story with its own label.

## Reader names (for FL1 and the designer)

- `fno.premium_ranges.reader.PremiumRanges.for_day(underlying, day) -> list[PremiumRange]` (contract, side, strike,
  expiry, five quantiles in rupees, today's mid, sealed_at, late, rule).
- `fno.premium_ranges.reader.PremiumScores.latest(underlying) -> PremiumScoreReport | None`.

## Acceptance criteria

1. Hand cases: a call and a put at one strike give the hand Black-76 values at the five forwards; the put's
   quantiles are the reversed values; a zero-h case gives the decay-free value; the median forward includes the
   `-σ²h/2` drift term.
2. Each "not ranged" reason is produced by its case and counted; the expiry-on-d+ case is out.
3. Scores match hand values for an outcome below, inside and above, and the session-first averaging is tested (a day
   with 100 contracts weighs the same as a day with 10).
3b. The verdict rule gives each of its four answers on a synthetic case, only at 60, 120 and 250 sessions, and
   "not yet decided (next look at n sessions)" between; the ₹2 floor applies below a ₹2 mid.
4. Seal and late flag behave as G13b's (reuse, not copy).
5. Real-data run on two consecutive sessions' chains (16 and 19 Oct NSE) gives a report that the judge can rerun.
6. Gates: full suite, ruff, format, imports, records scan; every file under 350 lines.

## Open questions for the owner

- Q1. If the rule's ranges reach *covers well* at a fixed look (above), may the paper desk use them for stop
  distances? (Not in this story.)
- Q2. A second rule with IV moving against the index (a stated "spot-vol" slope from history) is the natural next
  candidate. Build it only if the first rule's put ranges are too narrow on down days, as expected? If built, its
  slope is fitted on history, and the sessions it is shown are recorded in `research/DATA_SPEND.md` (judge 453
  note).
