# Response 317: G13d code, each contract's next-session 3 pm premium range (builder's claims, for Judge B)

**From:** G13/G13b builder, session_01UkTaDeTRF9ksDgQB9cTU5C · **Branch:** `story/g13d-premium-ranges` at caeebfcd ·
**Story text:** `docs/stories/G13d-premium-ranges.md` (judge 453.1 PASS; one build note added, below) · **Lane:** 1.

## What is built

New package `fno/premium_ranges/`, 12 files, the largest 104 lines. Its composition root
`fno/premium_ranges/wiring.py` is added to CLAUDE.md's list. The method hash covers G13d's own six number files plus
the G13 pricing and scoring, G4's block bootstrap and the Black-76 solver.

| File | What it does |
|---|---|
| `rule.py` | The stated rule. Forward quantiles `F exp(-s^2 h/2 + z s sqrt h)`, with `s` the expiry's ATM IV and `h` = calendar days to d+ / 365. Black-76 at the contract's own IV of d, one step less, G13's rate. A put's values are reversed. Baselines: `no_change` (d's mid) and `decay_only` (same forward and IV, one step less), both points. |
| `build.py` | One record per underlying and day from **G13's own 3 pm record of d**, which holds each contract's IV, mid, forward, ATM IV and rate (the same chain A4 captured, valued by G13). Not ranged, counted by reason: no contract IV, the expiry on or before d+, no G13 distribution, no ATM IV. |
| `issuer.py` | The live issue with G13's exit contract. It refuses itself at or after 15:30 (below), writes once, and reports no G13 record as a problem with exit 1, so a rerun can still issue. |
| `scores.py` | Each row against d+'s 3 pm mid from G13's record of d+, only from a two-sided quote and the same source as d. Rupee QS, relative QS (over `max(mid, Rs 2)`), inside 50% and inside 90%. Unscored rows are counted by reason: d+ has no 3 pm chain, d+ from another source, no two-sided quote at d+. |
| `sessions.py` | Session-first means, and G4's moving-block bootstrap over sessions (block 20; no interval below 40 sessions). The verdict follows the judged rule, in two parts. Coverage: *covers well*, *fails* or *not yet decided*. Carry, against decay_only only: *beats carry*, *fails* or *not yet decided*. It is read only at 60, 120 and 250 sessions, each on its first L sessions. Between looks the status says "next look at n scored sessions". |
| `report.py` | Per underlying: the summary, the looks, descriptive buckets by abs(delta) and by days (never decided on), unscored rows by reason, late issues (scored and marked), and pending issues (next session still ahead). |
| `reader.py` | `PremiumRanges.for_day` (the rule's five quantiles, d's mid, next session, stored seal) and `PremiumScores.latest`. |
| `cli.py`, `wiring.py`, `folders.py`, `constants.py` | `python -m fno premrange issue --live` and `premrange score`; Drive paths under `premium_ranges/v1/`; receipts pathspec. |

**Seals are G13b's, reused, not copied.** `SealCheck` takes `deadline_of`, and `Seals` takes `live_path_of` and
`seal_path_of`. The defaults are G13b's own, so G13b is unchanged. Neither file is in G13b's method hash: it stays
8d7d7301, and G13b's 92 tests pass. G13d passes `same_day_close` (15:30 IST on d) and its own paths.

**O1 steps, agreed with O1's owner (session_014zYLf1, 22 Oct):**
- `premium_ranges` runs right after `price_distribution`.
- `premium_range_scores` runs right after `price_range_scores`.
- Each is `Alerted(LiveFrom(CommandStep))` with G13d's receipts only, and `daily.live_from` is null for both.
- The pinned orders in `test_day_run` (both call lists, including the rerun's), `test_steps`' live dates, health's
  step string and G13's score-step test are updated. `price_distribution_scores` now follows `premium_ranges`.

## Deviation from the story text (build note, written into the story)

- **The 15:30 refusal moved into the command (O1's owner).** At or after 15:30 the issue prints "nothing written: past
  the 15:30 seal", exits 0, and O1 records it refused with one alert. So an issue that could never be sealed in time is
  never written.
- The late flag stays, for an issue written before 15:30 but pushed after it.
- **The timing budget:** on 19 and 21 Oct the card ended at about 15:19 IST, so G13's step and this one share about 11
  minutes. G13's live runtime is first measured today (22 Oct, its first live day). I'll state the budget, minutes used
  against 11, before asking for G13d's go-live.
- **The outcome comes from G13's record of d+**, not a second read of A4's chain. It is the same canonical chain
  (DRY). G13's record keeps only the quotes G13 used, so a few two-sided quotes G13 filters out are counted "no valid
  two-sided quote at d+".

## Real data (14-19 Oct, G13's 3 pm back-fill records; no live data yet)

| d -> d+ | Ranged | Scored | Rule QS Rs | decay_only | no_change | Rule inside 50% / 90% |
|---|---|---|---|---|---|---|
| NIFTY 14 -> 15 Oct | 179 | 156 (23 no quote) | 105.0 | 163.3 | 163.2 | 0.00 / 0.14 |
| NIFTY 15 -> 16 Oct | 184 | 176 | 33.3 | 63.7 | 63.6 | 0.17 / 1.00 |
| NIFTY 16 -> 19 Oct | 187 | 168 | 54.5 | 105.0 | 105.1 | 0.25 / 1.00 |

These are three sessions, far too few for any verdict; the first look is at 60. The rule's score is about half the
baselines' on each day. Its 50% coverage is low (0.00-0.25) and its 90% coverage swings (0.14 on 14 -> 15 Oct). That fits
the weakness the story named in advance: IV moves are not in the rule [reasoning only, three sessions]. One check I
made: a 35-day put five per cent out of the money losing about Rs 3.8 a day in decay_only is correct Black-76 decay,
not a bug.

## Tests and checks

- `tests/premium_ranges/`: 23 tests, covering criteria 1-5 and 3b:
  - hand Black-76 at the five forwards, the put reversed, the drift term, the zero step;
  - each not-ranged reason; hand scores below, between and above, and a point's absolute error;
  - the Rs 2 floor, buckets, unscored reasons;
  - a 100-contract day weighing the same as a 10-contract day;
  - the verdict's four answers, the looks only at 60/120/250 on their first sessions, pending versus unscored;
  - the issue's refusals including 15:30, write-once, no G13 record;
  - the 15:30 seal deadline with on-time, late and unknown evidence;
  - both readers, and the O1 step's wiring.
- **22 of 22 planted bugs are caught.** Three survived the first run (the 50% band's lower edge, an interval straddling
  zero, decay_only swapped for no_change); I added tests and re-ran.
- Full suite on the branch: 9,671 passed, 16 xfailed. Ruff, format, imports and the records scan are clean. Every file
  is under 350 lines.

## Owner questions (unchanged)

- Q1: may the paper desk use the ranges for stop distances, once *covers well* is reached at a look?
- Q2: a second, spot-vol rule, if put ranges come out too narrow on down days?
