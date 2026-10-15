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

## Addendum 1: revisions 2 and 3 at 2661b503 (replaces fd3a0344): FAIL

Revision 2 (fd3a0344, 20:59:40 UTC) was pushed minutes after this verdict reached main, so it answers the
orchestrator's list, not this file. Revision 3 adds only the NIFTY-move split to the report.

**Should-fix 2 (step place and failure rule): closed.**
- Rule 11 runs `owner_timing_fills` right after `quotes`, which only starts the parts and returns, so it cannot delay
  the 3 pm capture.
- A failed or refused step blocks new entries for every book through the existing per-book `_unreviewed` block
  (`fno/desk/daily_run.py:97`), and exits still run.
- One alert, then the run goes on.
- `DAILY_RUN_STEPS` in `fno/constants_operations.py` and the `DayStep` interface exist on `story/o1-daily-run`.

Criterion 10 still says only "the step runs first". It should also name the failure test (a planted failure gives no
new entry and `exits` still runs). This is a one-line note, to fix with the items below.

**Also closed: rule 3's invalid mark.** An invalid leg at the due mark means the entry is missed and the exit waits.
This is consistent with rule 7.

**The report's NIFTY-move split (revision 3): accepted.** It is what shows the owner the adverse selection of a price
cap, and criterion 11 tests it with one favourable and one adverse morning.

**Should-fix 1 (card time): open.**
- Lines 26, 80 and 243-245 still use a "15:08 card".
- Point 3 still covers only R = 30 and R = 60.
- Point 4 still says "a 14:00 decision puts R = 60 at 15:15 the same day".

Under O1 the card posts after `exits`, which is after the 15:15 snapshot, so R = 5 fills at the next session's 09:30.
Every view except `e4_1515` waits for A16. A 14:00 decision helps only with an earlier card. Revision 2's own rule 11
line, "the 09:45 and 10:15 marks have always passed", is right. The R = 5 example is not.

**Should-fix 3 (band figure): open.** Line 236 still says about 17%. The study's gap band gives about 32% at the
10:15 fill: 204 of 645 days for SF, 210 of 660 for LC.

**Should-fix 4 (new): the owner's entry-rule question is not held open.** The orchestrator lists three options: price
cap only (recommended), cap plus a 0.5% NIFTY band, or any price. The text instead writes the price cap as the rule
and offers only the band as an alternative:
- Rule 6 ("fills only if ... no worse than the approved entry ... otherwise missed, price moved");
- criterion 6 (one paisa worse gives "missed, price moved");
- the design (`EntryRange` with `ApprovedLimit` only);
- the scope's "Out" line ("a NIFTY band or any other entry condition beyond the approved limit, unless the owner picks
  one");
- the open question, which names two options and never "any price".

Under "any price" there is no "price moved" miss at all, so rule 6, criterion 6 and the card's "same limit" line would
all be wrong. That is an answer quietly assumed.

Fix:
- Write rule 6 as a slot: the entry rule is the `EntryRange` the owner chooses.
- List the three candidates, each with what it does:
  - `ApprovedLimit`: miss "price moved";
  - limit plus band: also miss "NIFTY moved", about 32% of overnight entries at 0.5%;
  - any price: no range miss, every valid quote fills.
- Mark which one is recommended and which one is wired until the owner answers.
- Give criterion 6 one line per option.
- Add "any price" to the open question with its plain cost. Every entry then fills, including the mornings that
  moved against the idea, so the verdict shows the full R = 60 cost but the trade can exceed C2's approved cash. Say
  how C2's cap still binds in that case, or state that it does not.

Would these change a trade? Yes. Each one decides whether an entry fills, at what time, or on what figure the owner
chooses.

Re-review needs should-fixes 1, 3 and 4 and the criterion 10 line.

## Addendum 2: revisions 4 and 5 at f2753ebf: FAIL, one should-fix of one line

**Closed, each checked against the text and the data:**

- **Should-fix 1 (card time).** A new "Card time" section quotes O1 (card after `quotes_done`, which is after the
  15:15 snapshot). The examples are now right:
  - R = 5, 30 and 60 fill at the next session's 09:30, 09:45 and 10:15.
  - Point 3 covers all three owner-timing views; only `e4_1515` fills before A16.
  - Point 4 says the 14:00 remedy needs an earlier card too, and names its cost.
  - Criterion 1 uses a 15:16 card: R = 5 gives 15:21, which needs the 15:30 mark, which is after 15:25, so the fill
    moves to 09:30. Correct.
  - The text now states that E8a's R = 5 cell does not describe the real R = 5 view, and that E8a has no 09:30 cell.
- **Should-fix 3 (band figure).** About 32%, with 204 of 645 (SF) and 210 of 660 (LC). The cited lines are right:
  `results.md` lines 200 and 216 at 76d73a06 hold SF 162 + 42 and LC 165 + 45.
- **Criterion 10.** It names the planted-failure test: no new entry in any book or view, and `exits` still runs.
- **Should-fix 4 (entry rule as a slot).**
  - Rule 6 lists three `EntryRange` candidates, each with its miss reason.
  - `AnyPrice` re-checks C2's hard caps on the fill's own prices. The Rs 10,000 per-trade cap is in `config.yaml`
    (`max_loss_per_trade_rs: 10000`, lines 53 and 80), and a breach gives "missed, over risk cap".
  - Criterion 6 has one line per candidate, with boundary fixtures (0.49% / 0.51%, one paisa).
  - The owner card states each option's plain cost.
  - The Out line no longer assumes an answer.

**The orchestrator's question: does a wired pending default hold the slot open?** Yes, on one condition.
- An unwired slot cannot run, so E8 would have no entry rule at all.
- `ApprovedLimit` is today's E4 behaviour, it is labelled pending in rule 6, the design and criterion 6, and the
  answer is one line in `wiring.py`.
- Until A16's routine runs, no owner-timing fill happens anyway (point 3), so the default decides no verdict fill
  before then.

**Should-fix 5: the owner's answer must come before S1's freeze.** The text says `wiring.py` joins S1's
`frozen_files` (S1 item 1) and that both build parts land before the freeze. If the freeze comes first,
`ApprovedLimit` is frozen as the evaluated rule, and the owner's later answer becomes a change to a frozen file,
needing a protocol amendment. So the pending default would quietly become the answer.

Fix: add one line to the S1 items, beside item 3 (the decision time): "The entry rule (rule 6) waits for the owner;
S1's freeze needs the answer, wired in `wiring.py`, or a recorded owner row keeping `ApprovedLimit`." Would it change a
trade? Yes: it decides which entries fill for the whole evaluation.

Re-review: only that line.

## Addendum 3: revision 6 at df7a1d65: PASS

Should-fix 5 is closed. The only change since f2753ebf is in `docs/stories/E8-owner-timing-fills.md` (+4, -1). It
adds S1 item 4: "The entry rule (rule 6) waits for the owner. S1's freeze needs the answer wired in `wiring.py`, or a
recorded owner row keeping `ApprovedLimit`", and gives the reason, that `wiring.py` is frozen. The old item 4 becomes
item 5.

The S1 text owner's register row on main records it as pending edit (9). The precondition is therefore on both sides:
E8's text and S1's own list.

E8's story text passes at df7a1d65. Under quality rule 9, it goes to ChatGPT next (it changes how fills are priced).
The owner's entry-rule answer stays open and is now a precondition of S1's freeze.
