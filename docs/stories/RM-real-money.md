# Epic RM: the real-money gate and the small real-money test

Roles: statistician, risk manager, F&O trader, tax and cost accountant, compliance. Goal: the rules that decide when
real money could ever be considered are written and frozen before any counted paper result exists, so no result can
shape them. Nothing in this epic places, modifies, cancels or enables a real order. Story template and definition of
done: `docs/IMPLEMENTATION_PLAN.md`.

---

## RM1. Real-money gate, frozen before the first counted paper decision

**Repository:** trading · **Issue:** #107 · **Lane:** 1 (the real-money gate; JUDGE.md rule 9: judge, then ChatGPT,
then the owner)

**Description:** As the owner, I want the real-money pass mark and the small test's rules fixed and hashed before the
first counted paper decision, so that I can never be talked into real money by a pass mark written after seeing the
results.

**Context and why:** Design v2 8.3 and 8.4; owner decision 8 (15 Oct 2026, accepted) and its amendment ("B ... =>
I accept": selection-adjusted evidence always; a paired real-vs-paper test with a prediction interval); principle 4
(14 Oct 2026: "a pass mark for real money is written before results and never lowered because time passed");
decision 168 (do-nothing gate); ChatGPT reviews 97 and 98 (the exact sample, statistic, interval and execution
constraints belong in RM1's frozen text before counted evidence); judge 158 (RM1 must say how several books'
`beats_index_after_tax` values combine).

**Scope.** In:
- `research/evaluation/REAL_MONEY_GATE.md`: the seven conditions of 8.3 and the test of 8.4 as items in S1's item
  format, each with an exact value or rule (draft on this branch);
- the gate listed in S1's `frozen_files`, so S1's freeze hashes it and S1's `order` check proves it precedes every
  counted decision (one freeze, one order check; no second freeze tool);
- the gate's evidence is only Book 1 positions counted under the protocol version that holds the gate (the
  decision's commit has that freeze as a strict ancestor); pilot and shadow positions are shown, never counted
  (judge 171 SF1);
- S1's freeze refuses while the gate is incomplete or any gate item is not decided by the owner; `python -m fno
  evaluation check` also checks the gate.

Out:
- computing the gate (eligibility report) and recording real fills: RM2, after a version reaches the gate;
- any order, broker call or setting that could place one;
- S6's `beats_index_after_tax` and E8's fills (read by the gate, built by S6 and E8);
- the crash-replay engine (condition 3(b) names the windows and data; the replay is built with the first version
  that reaches the gate).

**Expected design (after a text PASS):**
- `fno/evaluation/gate.py` (new, small): `GATE_FILE` and the gate's required items (the 12 keys of the draft).
- `fno/evaluation/completeness.py`: `completeness_problems` takes the required-item list (default S1's) and
  `versioned` (default true; false for the gate), so one checker serves both documents (DRY). The gate has no version line of its own: it is versioned and frozen
  with S1.
- `fno/evaluation/freeze.py`: `_require_gate` refuses unless the protocol's `frozen_files` lists the gate and the
  gate is complete and decided, naming each problem. `cli.py`'s `check` prints the gate's result as a second line.
- `research/evaluation/PROTOCOL.md`, `frozen_files`: adds `research/evaluation/REAL_MONEY_GATE.md` and
  `fno/evaluation/gate.py`. This changes an owner-decided item's list (as the scoring-code addition already
  foresees), so it goes to the owner as question Q10. S1's text owner (session 0185gR5DmoDh2zBAvgRU4CEB) makes that
  one-line edit; RM1 does not edit `PROTOCOL.md`.
- No new composition root: no outside service is touched.

**Acceptance criteria:**
1. The gate file has an exact value or rule for each 8.3 condition (1-7) and each 8.4 element (account, cap, lot,
   duration, paired pass, prediction interval, slippage, drawdown stop, slippage stop), each traceable to its source
   row (judge checks the table in response 163).
2. `python -m fno evaluation check` reports the gate complete; it rejects a missing gate item, an empty field, an
   evidence label outside the three, or "to be decided" and its kin, naming the item.
3. `python -m fno evaluation freeze` refuses while any gate item's status is not "decided by the owner on <date>",
   naming the items; the refusal writes no record and no ledger row.
4. A freeze with a complete, decided gate writes the gate's SHA-256 into `FREEZE_v<n>.md`; `evaluation verify`
   reports a later edit of the gate as changed.
5. The gate's two owner numbers of 8.4 (account size, per-trade cap) carry the owner's written decision and date
   before the freeze (decision 8): criterion 3 enforces it mechanically.
6. The gate's terms define the evidence record by S1's version rule (Book 1 only, decisions after the freeze) and
   measure execution slippage from a valid quote at the owner's order time (judge 171 SF1, SF2; ChatGPT review 118);
   `real_test_sample` keeps 8.4's registered number (SF3); the paired net test binds (review 118). Checked by
   reading, traced in response 163.
7. No code path reads the gate to place, modify or cancel an order, and no broker write is imported (the
   `check_imports` rule and a test that `fno/evaluation/` imports no provider or broker module).
8. Files stay under 350 lines; `fno/evaluation/freeze.py` stays one class with one job.

**Test plan (each criterion with a broken-code proof, rule 4):** completeness on a fixture gate (missing item, empty
field, bad label, "tbd"); freeze refused on an undecided gate (no record, no ledger row), freeze written on a decided
gate with the gate's hash; `verify` flags a one-byte gate edit; the import test; the real gate passes `check
--decided` (complete and decided by the owner).

**Judge verifies:** the text against 8.3, 8.4 and the decision rows (criterion 1's table); each owner question is
asked with options, never answered by the builder; the freeze refusal by planting an undecided status.

**Notes for RM2 (judge 171 addendum 4):** RM2's text names which A16 mark is "next" when a fill time equals a mark.

**Known limits:**
- The gate is frozen with S1, so changing it later is a new S1 protocol version (the intended cost: no quiet edit).
- S1 v1 cannot freeze before the owner answers RM1's questions; a slow answer delays counted paper evidence (Book 1
  keeps trading as pilot evidence meanwhile).
- Shadow records never count toward the gate until a later story extends S1's order check to them.
- `fill_honesty` needs A16 snapshots, which cover only the nearest weekly and monthly NIFTY expiries.
- The gate's conditions read data that does not exist yet (E8 fills, S6's benchmark, A16 snapshots); missing data
  counts as "not met", never as a pass.

**Depends:** S1 (draft built), S6 (text on main), E8 (story) · **Size:** S · **Status:** done (merged 4777653e; text
judge 171 addendum 4, code judge 190; every gate item decided by the owner on 15 Oct 2026)

---

## RM2. Real-money test record

**Repository:** trading · **Issue:** #108 · **Lane:** 1 (real money, fills and the gate's pass and stop rules;
JUDGE.md rule 9: judge, then ChatGPT, then the owner)

**Description:** As the owner, I want every real trade I place by hand recorded against the card it followed, paired
with the paper trade of the same card, and judged by the frozen gate's pass and stop rules, so that I know at once
when to stop and, at the end, whether real trading matched paper.

**Context and why:** Design v2 8.4; the frozen gate `research/evaluation/REAL_MONEY_GATE.md` (RM1, items
`real_test_account` to `real_test_stops`, decided by the owner on 15 Oct 2026); E8's owner-timing fills
(`docs/stories/E8-owner-timing-fills.md`); T1's card records in Drive only (8.5, owner option b); O1's day (the card
posts after `quotes_done`, so at 15:15 or later; `docs/stories/O1-daily-run.md` on `story/o1-daily-run`).

**When it runs (a real scenario, not now):** only after a version passes conditions 1-6 of the gate and the owner
writes the yes of condition 7. Until then RM2's code may exist but records nothing; no test is open.

**What happens on a real day (the only flow RM2 supports):**
1. The day's card (T1, Slack, at 15:15 or later) carries a TRADE for the version under test.
2. The owner places the order by hand in Groww, at a time of their choosing (the same session's last minutes or the
   next session). Before placing it, the owner takes a screenshot of Groww's bid, ask and quantities for each leg and
   saves it to the Drive folder `real_test/quotes/` (owner, Q12).
3. After the fill, the owner reports it: the card's date, and per leg the contract, side, units, fill price, order
   time and the screenshot's file name; then the contract note's total charges for the order.
4. RM2 writes one record to Drive (`real_test/trades/`), never to the repository, and replies with one line: the
   record's SHA-256, the execution slippage per leg, and the running test status.
5. The exit is reported the same way (screenshot, fill, charges). The trade's real net is then known.
6. After every recorded exit RM2 evaluates the stops; at the end of the test, the pass rule.

**Scope.** In:
- `RealTestRecord`: the test's header (version, its registration, the owner's yes row, first real entry date) and its
  trades, kept in Drive behind a `RealTradeStore` port (`DriveRealTrades`; `RawFileStore` rules: written once, the
  same bytes again change nothing, a correction is a new record naming the one it replaces).
- `fno realtest record-entry|record-exit|skip|status` (CLI). A Claude session runs it at the owner's word (owner
  question Q1). It checks the screenshot file exists in Drive and stores its id and SHA-256 with the typed values.
- **Pairing:** each real trade is paired with Book 1's paper trade of the same card (E8, R = 60), scaled to 1 lot
  (paper net ÷ paper lots). A card Book 1 did not fill ("missed, ...") gives an unpaired real trade: listed, kept out
  of the paired mean, counted in the discipline and stop rules.
- **Valid quote at the owner's order (the gate's term):** the screenshot's bid or ask with its quantity covering the
  leg's units, taken at most 5 minutes before the order time. The screenshot's time is the one the owner types from the
  phone's clock in the image (Drive's upload time comes after the order, so it cannot date the image); the file name's
  timestamp, when the phone writes one, is stored beside it, and a difference of more than a minute is flagged. Fallback (owner, Q12): A16's latest mark **at or
  before** the order time and at most 5 minutes before it. A mark exactly at the order time is valid (age 0).
- **Execution slippage** per leg (gate): real fill minus that valid quote (sells: the reverse), worse positive;
  unknown when there is no valid quote.
- **Timing gap** per leg, reported only: real fill minus the paired paper fill price before pad.
- **Discipline:** eligible cards = the version's TRADE cards delivered while the test runs. A card with no real entry
  recorded by the close of the next session is "skipped, not recorded"; `skip` records a reason earlier. Each skip is
  listed with its paper net (gate, Q8).
- **Stops (gate `real_test_stops`), evaluated after every recorded exit:** (a) cumulative real net from the first
  real entry at or below −Rs 20,000; (a2) cumulative real net Rs 20,000 or more below its highest value since the first
  real entry; (b) mean execution slippage per unit over the legs of the last 5 real trades above Rs 2 (twice the paper
  pad of Rs 1), unknown legs left out and listed. A stop posts one alert to #fno-desk (`FNO_SLACK_BOT_TOKEN`) naming
  the rule and the figure, and the test status becomes "stopped: <rule>" for good.
- **Pass (gate `real_test_pass`), evaluated once the sample is met** (the later of max(30, the registered number)
  real trades and 6 months from the first real entry): (1) the paired one-sided 95% lower bound of mean(real − paper)
  at or above −Rs 500 per trade; (2) the real mean at or above the prediction floor from the version's evidence
  record; (3) mean execution slippage at most Rs 1.50 per unit, with at most 10% of legs unknown (left out and listed
  when 10% or fewer); (4) at least 90% of eligible cards placed. Status: "passed" or "failed: <items>", posted once.
- `status` prints the test status, trades so far, the stop figures against their limits, and the days and trades left.

Out:
- placing, modifying or cancelling any order; any Groww call (RM2 reads Drive, A16's records and Book 1's paper trades
  only);
- the gate's numbers (they are the frozen gate's; RM2 reads them from one constants module, checked against the gate
  text by a test);
- parsing Groww contract notes or screenshots (the owner types the values; owner question Q1);
- scaling beyond 1 lot, automation (gate `scope`).

**Expected design:** `fno/realtest/` with `record.py` (the record and its trade rows), `rules.py` (the gate's
numbers as named constants), `pairing.py`, `stops.py`, `verdict.py`, `cli.py`; ports `RealTradeStore` and
`QuoteShots` (Drive), wired only in `fno/realtest/wiring.py`. Public repository: nothing but each record's SHA-256
and the test status line (no price, strike or rupee figure; 8.5). Every file under 350 lines.

**Note carried from RM1 (judge 171 addendum 4, note 2):** the gate's `fill_honesty` (b) "next A16 snapshot after the
fill" is the first mark **strictly after** the paper fill time. E8 fills always land on a mark (its due mark), so the
mark at the fill time is the fill's own snapshot; using it would compare the fill with itself (gap 0). This is
written into RM2's code and test, since RM2 is the first story that computes it from A16's records; the gate text is
unchanged.

**Acceptance criteria:**
1. A recorded entry and exit give the trade's real net from the typed fills and the contract note's charges, its
   paired paper net at 1 lot, the per-leg execution slippage and timing gap, all to the paisa on a constructed example.
2. Valid quote: a screenshot 4 minutes before the order is used; 6 minutes before is not, and the A16 fallback
   applies; an A16 mark exactly at the order time is used (age 0); one with too little size is not; no valid quote
   gives "unknown", never zero.
3. Stops: planted sequences trip (a) at exactly −Rs 20,000, (a2) after a Rs 20,000 fall from a +Rs 6,000 high (at
   −Rs 14,000), and (b) at a 5-trade mean of Rs 2.01; Rs 2.00 does not trip. Each posts one alert once; a rerun posts
   nothing new.
4. Pass: a constructed test meets all four items; flipping each item alone gives "failed: <that item>". The sample
   rule waits for both 30 trades (or the registered number) and 6 months.
5. Discipline: a card with no entry by the close of the next session is "skipped, not recorded"; 90% exactly passes,
   89.9% fails.
6. Strictly-after rule: a paper fill at 10:15 is compared with A16's 10:30 mark, never 10:15.
7. `rules.py` numbers equal the frozen gate's (a test reads the gate text); changing one fails the test.
8. Nothing reaches a broker: no Groww or order module is imported under `fno/realtest/` (import test); the public
   repository receives no price, strike or rupee figure (record-scan rule and a test on the status line).
9. Drive down: the CLI refuses to record ("not recorded: Drive <reason>"), changes nothing, and says so; a retry
   records once.

**Test plan:** fakes for Drive, Slack, A16's marks and Book 1's paper trades; constructed tests for each criterion,
with a broken-code proof per criterion (rule 4); one end-to-end run on a planted 30-trade test.

**Owner questions (through the orchestrator):**

| Q | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | How does the owner report a real fill? | (a) tell a Claude session, which runs the CLI; (b) a fixed-format Slack message RM2 reads; (c) upload the Groww contract note for parsing | (a): simplest and checked line by line; (c) later if typing proves error-prone (reasoning only) |
| Q2 | When does an unreported card count as skipped? | (a) at the close of the next session; (b) at the close of the same session | (a): the owner may place the order next morning, as E8's paper side does (reasoning only) |
| Q3 | Charges: the contract note's actual total, or C1's model? | (a) actual, C1 shown beside; (b) C1 | (a): the test is about real money (reasoning only) |

**Known limits:**
- The owner types the fills, the screenshot's values and its time; a typo is caught only by the owner's check of each
  reply and the file-name time check.
- A partial fill or a leg filled at another time is recorded as reported; the trade counts once, at its last leg.
- Real and paper fills are at different times (E8's paper fill is about 10:15 next session), so the paired net holds
  market moves as well; execution alone is judged from the screenshot (gate, Known limits).
- A Groww outage that stops the owner's exit is recorded as it happened; no rule waives it.

**Depends:** RM1 (done), E8 (paper fills), T1 (card records), A16 (marks) · **Size:** M · **Status:** story text for the
judge's story check; code starts only when a version reaches the gate and the orchestrator says go
