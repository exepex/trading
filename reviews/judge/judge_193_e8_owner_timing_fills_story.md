# Judge 193: E8 owner-timing fills, story text revision 1 at 1a04a60d

Judge C. Branch `story/e8-owner-timing-fills`, head `1a04a60db0409f6dc78d024748ba46b8c71c2692` (builder
session_01H1CmuWzBtbtjzoQNJUz2Dz). Lane 1, issue #109. E8 gates S1's freeze. The change adds
`docs/stories/E8-owner-timing-fills.md` (295 lines) and a pointer section in `docs/stories/E-paper-desk.md`.

**Verdict: FAIL, three should-fixes.** Each changes a fill, or an owner decision about fills. The design itself is
sound: the clock as a strategy, A16 snapshots behind an interface, the entry range behind an interface, four views of
one decision, the availability file checked by commit time, and size L in two parts.

## Should-fix 1: the card time T in the examples is not the time O1 posts the card

The story works every example from a "15:08 card" and a "14:08 card", the same 8-minute card delay E8a assumed (FT1
PROTOCOL table, "card about 15:08"). On `story/o1-daily-run`, the agreed run posts the card only after `quotes_done`.
That step comes after `exits`, and the card is "always after `decisions` (final at 15:12) and `snapshot` (C3 final at
15:15), so a card never posts before what it shows is final" (O1 scope table, T2 builder, 15 Oct). G10 keeps the
15:10 deadline and the 15:15 snapshot. So in normal running T is 15:15 or later. Under rule 2, that gives:

- R = 5: T + 5 is 15:20 or later, so the first mark is 15:30. That is after 15:25, so the fill moves to the next
  session's 09:15 + 5, which is the **09:30 mark**, not 15:15 the same day.
- R = 30 and R = 60: 09:45 and 10:15 the next session, as the story says.

Three things follow:
- **(a)** The "R = 5 gives 15:15" example and criterion 1's 15:08 mapping describe a card time that does not occur.
- **(b)** Point 3, "until A16's routine runs, no verdict fill can happen", covers R = 30 and R = 60 only. The R = 5
  view is also next-morning and also "missed, no quote" until A16 runs. Only `e4_1515` fills before A16.
- **(c)** The remedy, "a 14:00 decision puts R = 60 at 15:15 the same day", needs the card delivered at about 14:08.
  Under O1 the card still waits for the 15:15 snapshot, so an earlier decision alone moves nothing: R = 60 stays at
  10:15 the next session. The remedy needs an earlier card too, an O1/T1 change that gives up "never before what it
  shows is final". E8a's 14:00 figures (LC 24.6 against 55.5 points) are what that change would buy.

Fix:
- State T as O1 really gives it.
- Rework the examples and criterion 1 from a card at 15:15 or later. Keep the 14:08 case only as "if the card moved".
- Widen point 3 to R = 5.
- Say plainly that the remedy is an earlier decision **and** an earlier card, and name the cost.

## Should-fix 2: the fill step's place and its failure rule

Rule 11 makes `owner_timing_fills` "a new first step of the daily run ... before `pack`", pending O1. The placement
the orchestrator reports as agreed is **right after `quotes`**, and it is also the only one that fits O1's text:
"the quote parts start before any of them, so a hung Groww call can never delay the 3 pm capture". A first step that
reads Drive and A16 copies before `quotes` would break that.

The story also gives no rule for when the step fails. O1's rule is "a step that fails never stops the next". So:
- **The path:** Drive or an A16 copy fails at the run's start, the step is recorded `failed`, and `decisions` still
  runs. C2 then sees no position for yesterday's due fills and can approve entries over a book's caps.
- **What is needed:** new entries fail closed for every book (and view) whose pending orders were not applied, while
  exits still run.
- **Fix:** write both, the step right after `quotes` and the fail-closed rule, into rule 11 and criterion 10, with a
  test: a planted step failure gives no new entry and still runs `exits`.

## Should-fix 3: the band's drop share in the owner's question is wrong (about 32%, not 17%)

The open question says a ±0.5% NIFTY band "would have dropped about 17% of overnight entries in 2024-26 (E8a's gap
figures)". E8a's gap band is exactly the band's test: `|index at fill / index at decision - 1|` (FT1 PROTOCOL line
133). At 15:00, R = 60, its counts are:
- SF: 162 + 42 = 204 of 645 days at 0.5% or more, that is **31.6%**;
- LC: 165 + 45 = 210 of 660, that is **31.8%**.

The 17% is the share of sessions whose **09:15 open** moved 0.5% or more from the close (rv_overnight). That is not
the 10:15 fill this band would test. The owner is asked to choose the entry range from this figure, so it must read
about 32%.

## The orchestrator's checks

| Check | Result |
|---|---|
| E8a's findings used correctly | Yes, apart from should-fix 3. I checked each against results.md at 76d73a06: single options 51.6-55.5 points (Rs 3,357-3,608) and 20.8-24.6 at 14:00; above 10% of risk on 23% (LC) and 28% (LP) of days; verticals 10.1-11.2 and 4.9-5.3 points, 4-8% of days; SF, BF and SC 2.9-4.4 and 2.5-2.6 points, 0% of days; bad flips LC 3.8% against 1.6%, four-leg structures 0.0-1.9%. The 14:00 figures assume a card at 14:08 (should-fix 1c). |
| G10's timeline | The skill score at the 15:15 snapshot and the money verdict at the 60-minute fill (`docs/DESK_DECISIONS.md:184`, G10 table) are carried correctly. The card time under G10 plus O1 is should-fix 1. |
| O1's placement | Not as agreed; no failure rule (should-fix 2). |
| "Missed, no quote" until A16 | Said plainly for R = 30 and R = 60. It must also cover R = 5 (should-fix 1b). |
| Size L in two parts | Accepted: four view accounts, the pending-order store and the A16 adapter outgrow M. Part 1 holds what the verdict needs, part 2 the rest; both come before S1's freeze. |
| Work register | Row E8 is this session's; no other row covers fills by owner timing. E8a is the study, T1 owns the card's trade fields (out of scope here), and LM1 and LM2 use E8's clock later. No duplicate. |

## The owner's open decision (the entry range's shape)

I judged on the builder's recommendation, the approved limit only. **The other option, the limit plus a ±0.5% NIFTY
band, does not change this verdict.** `EntryRange` takes the band as one class plus one line in `wiring.py`, and the
band reads NIFTY from the same due-mark snapshot. With the band, should-fix 3 matters more, not less: it would drop
about a third of overnight entries, not a sixth.

Note (reasoning only): the builder's case is sound. A limit-only fill keeps mostly the days the market moved against
the idea, and that is what a real limit order gets. The report splitting fills and misses by NIFTY's move is what lets
the owner see that bias.

## Notes (no change needed)

- **Rule 8, the availability file:** an away row counts only when its commit is earlier than T. This is the right
  guard against choosing "away" after seeing prices.
- **Rule 3, the stand-in:** an A4 capture within the 2-minute window can stand in for a missing mark, and E3's 15:15
  capture qualifies. For R = 5, 30 and 60 after should-fix 1, every due mark is next-morning, so the stand-in only
  ever serves the `e4_1515` view until A4 records mornings.
- The fill uses A16 bid and ask, while E8a used candle last trades. The story says so.
