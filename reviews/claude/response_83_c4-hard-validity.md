# Response 83: story C4, hard-validity checks (builder's claims for the judge)

Story: `docs/stories/C-code-roles.md` C4. Builder: Claude, 14 Oct 2026. Branch `story/c4-hard-validity` (nothing on
`main` until the judge passes it). Research and paper only: nothing here places, modifies or cancels orders.

## 0. The verdict in two lines

Every trade D2 chooses for a book is now re-checked by separate code before D3 writes its record. A failure turns the
trade into "no trade, blocked by C4 hard validity", is logged in `journal/<book>/validity_failures.csv`, and nothing
(the owner included) can turn it into a pass. Book 1's playbook mode is built in full. Book 2's envelope (D4) and
Book 3's constitution (D5) do not exist yet, so their modes **fail closed**: no Book 2 or Book 3 trade can pass.
Criteria 6 and 7 wait for D5 and D4; I did not fake them.

## 1. Design

| Part | File | Job |
|---|---|---|
| Money | `fno/checks/validity_money.py` | the independent maximum loss: the payoff at expiry on a 1-point grid of index levels across the strikes; each order's charges straight from the `charges` table |
| Evidence | `validity_evidence.py` | re-reads the A4 snapshot from the store; both files' SHA-256 must equal C3's `CaptureRecord`; parses the raw CSV itself; monthly expiries = the latest listed expiry of each month |
| Proposal | `validity_proposal.py` | the trade as plain values (legs with the prices used, terms, claimed loss, C2 result, open trades, version) and `CheckResult` |
| Checker | `validity.py` | evidence, date, expiry, each leg, max loss, loss limit, open trades, C2 verdicts, then the book's mode; `override()` raises `HardValidityError` on any failure |
| Modes | `validity_modes.py` | `ValidityMode` seam; `PlaybookMode` (version fingerprint, permitted on the day, structure code, width, lots, leg shape); `WaitsFor` (fails closed) |
| Adapter | `validity_adapter.py` | `BookTradeValidator`: D2's chosen outcome to a proposal, checked, failures logged (not in a replay) |
| Capture | `validity_capture.py` | the capture is the one the day's committed common pack names (pack checked against its `.sha256`), via C3's `PackSnapshotSchedule` |
| Failure log | `validity_failures.py` | append-only CSV, one row per failed check, header once |
| D3 link | `fno/playbook/decision_validity.py`, `decision_record.py`, `decision_run.py` | `validate_chosen` runs in `DecisionRun.decide` and in `replay` (DRY); `validity.c4` holds the result |
| Wiring | `fno/checks/wiring.py` (C3's composition root, extended) | modes per book; charges and limits read from `config.yaml` directly; `build_decision_run` gets the validator |

**Independence.**
- No `fno/checks/validity*.py` imports `fno.costs`, `research_engine.cycle_costs`/`structures`/`simulator`/`leg_prices`,
  `risk.trade_costs`/`rules`/`manager`/`margins`/`stress`, `playbook.candidates` or `playbook.allocation`.
- `tests/checks/test_validity_independence.py` checks this two ways: it reads each file's imports, and it imports
  them all in a fresh interpreter and checks none of those modules was loaded through any chain.
- Planting `from ..risk import trade_costs` in `validity_money.py` fails both tests. Planting an import of
  `fno.playbook.wiring` in `validity_evidence.py` (a transitive route) fails the second.

**The definition of maximum loss** is the frozen protocol's (experiment 1, section 4): the worst terminal loss
between the outer strikes, plus entry charges, every pad (Rs 1 per unit per leg, entry and exit), and the exit
charges at the worst level. Where levels tie, the larger charges count. Every order is charged at a price of at
least one tick.

The method differs from the proposer's (`cycle_costs`):
- C4 walks a grid of levels instead of using the proposer's formula.
- It charges from the table, not through `fno.costs`.

Over 3,000 random trades the largest difference between the two was 1.8e-12 rupees.

**What blocks.** In D3's record, the trade's `chosen_action` and `decision.action` become "no trade". The `reason`
becomes "blocked by C4 hard validity: <check>: <why>; ...". The day's `no_trade` record leaves the trade out of its
chosen list. D2's own outcome (`decision.outcome`) is kept, so the record shows both what D2 chose and why C4 stopped
it.

Only chosen book trades are checked. Shadow and unchosen outcomes are not trades.

Open trades are counted as the book's open trades plus the trades chosen earlier that day, in opportunity-ID order.

## 2. Claims per acceptance criterion

| # | Criterion | Tests |
|---|---|---|
| 1 | Seeded wrong proposals blocked | `test_each_seeded_wrong_proposal_fails_with_its_check`: 17 seeded cases, each failing **exactly** the named checks (set equality, so an extra or missing failure fails the test). The cases are stale date, snapshot after the cutoff, weekly expiry, one leg on another expiry, strike not listed, price 5 paise off the mid, claimed loss Rs 1 off, loss over Rs 10,000 (a 200-wide long fly, claim correct), a fourth open trade, tampered snapshot, missing record, wrong lots, version not permitted, wrong structure, changed rule fingerprint, a failed C2 verdict, and a quote received after the cutoff. Also `test_a_claimed_loss_off_by_under_a_rupee_passes_by_a_rupee_fails` |
| 2 | A correct proposal passes with every check's numbers | `test_a_correct_trade_of_each_structure_passes` (SF, SC, BF, the 3 correct ones; claimed loss = the PROPOSER's B2 model, difference < Rs 0.01); `test_a_valid_trade_carries_its_c4_result_and_stays_chosen` (the record holds every check with its numbers) |
| 3 | No path turns a failure into a pass | `test_nobody_overrides_a_failure` (owner, desk, judge: `HardValidityError`; the report is frozen); the checker has no override input; the D3 link has none |
| 4 | Tampered and absent evidence fail | seeded "tampered hash" and "missing snapshot"; `test_a_pack_that_differs_from_its_hash_names_nothing` |
| 5 | ≥ 10 hand-computed vectors to Rs 0.01 | `tests/checks/reference_vectors.md` (12 vectors, all three structures, every step shown), `reference_vectors.json`, `test_reference_vectors.py` |
| 6 | Constitution mode | **waits for D5.** Until then Book 3 fails closed: `test_books_2_and_3_fail_closed_until_their_stories` |
| 7 | Book 2 envelope | **waits for D4.** Same test: Book 2 fails closed |

D3 link (orchestrator's "validity.c4 gets filled"): `tests/decisions/test_validity_link.py`.
- A pass fills `c4`.
- A failure blocks the trade, is logged, and is reproduced by `replay(..., validator=...)`.
- A replay with a different validator result reports "validity differs".

`tests/decisions/test_validity_adapter.py` checks what the adapter reads for itself:
- the permitted versions come from the playbook, not the outcome (a version paused before the day fails);
- the rule is checked against the version's own file;
- the prices come from the decision market;
- trades chosen earlier the same day count as open;
- the day checked is the run's own, not the market's.

The reference vectors use a different method again from the code. The payoff is straight between strikes, so the
worst level is found among the strikes, not on a grid. The numbers were worked by a calculator script that imports
nothing from `fno`, and the arithmetic is printed in full.
- V1 checked by hand: credit 400 - 242.60 = 157.40; loss 200 - 157.40 = 42.60 per unit; x 65 = 2,769.00; plus pads
  520.00 = Rs 3,289.00.
- V5-V7 equal the proposer's numbers in the fixtures (3,540.57; 5,584.03; 6,511.78).

## 3. Mutation checks: 38 of 38 caught (bytecode off, caches cleared)

The mutations, each applied and then reverted:
- tolerances: loss tolerance 1.5; `<` to `<=`;
- limits and verdicts: loss limit off; the open-trade +1 dropped; C2 verdicts ignored;
- time and expiry: start before the cutoff ignored; same day ignored; monthly expiry ignored; each leg's expiry
  ignored; quote time ignored;
- price tolerance Rs 1;
- override allowed;
- evidence: hash check off; monthly expiry = the earliest of the month;
- money: pad 0; no tick floor; STT on buys; GST on brokerage only; exit charges left out; ties go to the smaller
  charges; exit without the pad;
- playbook mode: permitted, fingerprint, lots, structure and shape each ignored;
- books 2 and 3 given playbook mode;
- failure log: header on every append;
- capture: pack hash ignored;
- adapter: approval taken from all strategies; the version taken from the outcome;
- D3 link: open count ignores earlier choices; block ignored; a blocked trade still in the day list; `c4` not
  stored; replay without the validator; failures not logged.

The first run missed one: a single leg on another expiry. I added that seeded case, and it is now caught.

Not mutated, said plainly: a grid step of 50 instead of 1. NIFTY strikes are multiples of 50, so the result is the
same.

## 4. Limits and decisions to confirm, said plainly

1. **Not every C2 limit is recomputed independently.** C4 recomputes two limits itself: the per-trade maximum loss
   (Rs 10,000) and the open-trade count (3).
   - The drawdown brake, the stress loss (Black-76 repricing) and funding or margin are not recomputed. C4 only
     requires that every C2 verdict recorded for the trade passed (`risk_verdicts`).
   - The story says "all C2 limits". An independent stress model is a second pricing implementation, a larger piece
     of work. I recommend a follow-up story (reasoning only) rather than widening C4.
   - The drawdown brake is simple to recompute from the book's closed equity and could be added quickly if the
     judge wants it in C4.
2. **Contract for E3 (the live decision market):** each leg's price must equal the capture's (bid + ask) / 2.
   - C4 compares to 1e-6 rupees.
   - A market built from another source, or a stale mark, is blocked on every leg. That is intended, but E3 must
     build its market from the same capture.
3. **"Rs 1 or more" is the threshold.** A claimed loss wrong by under Rs 1 passes (tested at Rs 0.99). In practice the
   two implementations agree to about 1e-12.
4. **The capture comes from the committed common pack** (C3's `PackSnapshotSchedule`). With no pack, or a pack whose
   bytes differ from its `.sha256`, the evidence check fails and nothing trades. When E3 brings its own execution
   schedule, it is one line in `fno/checks/wiring.py`.
5. **Monthly expiry** is the latest listed expiry of its month in the snapshot, not the futures list in the
   snapshot's meta. The futures come from NSE and can fail on a capture, which would block every trade.
6. **Charges for C4 are read straight from `config.yaml`**, the same table the proposer reads. A wrong table
   entry would be wrong in both, so C4 cannot catch a wrong table. The reference vectors pin the table's use, not
   its values.
7. **Book 2 and 3 modes are placeholders that fail.** When D4 and D5 land, they replace `WaitsFor` in
   `validity_modes()`, one line each.

## 5. Gates

On the tree merged with `main`:
- full suite;
- `ruff check fno tests tools` and `ruff format --check`;
- `python tools/check_imports.py`;
- every file under 350 lines (the largest new file is `validity.py` at 115).

The numbers are in the message to the orchestrator.

## Addendum 1 (14 Oct 2026): judge 83's three must-fixes and the should-fix

I checked each finding against the code before accepting it. **All three are correct, and all are fixed.** Sections 3
and 4 above are superseded where this addendum differs: the mutation count, limits 1 and 5.

### Must-fix 1: a wrong lot size passed (accepted)

**Check.** C4 took `lot_size` from the proposal and recomputed the loss with the same units. I reproduced the judge's
number: the proposer's model, priced for 75 units, gives **Rs 4,056.23**, and C4 passed it.

**Fix.** `fno/checks/validity_listing.py` reads **NSE's own daily F&O file** of the previous session (the newest one
in the 7 days before the decision day, never the day's own). Every NIFTY option row carries `NewBrdLotQty`.
- The new `lot_size` check requires NSE's lot sizes for the expiry to be exactly the proposal's.
- No file in the week before means `listing` fails, so nothing trades.
- Neither the proposer's `config.yaml` `lot_sizes` nor A4 is consulted.

**Tests.**
- `test_the_judges_lot_of_75_with_a_consistent_claim_is_blocked` (claim 4,056.23; only `lot_size` fails).
- `test_a_lot_size_nse_revised_is_blocked`.
- `test_no_nse_file_in_the_week_before_fails_closed`.
- `test_nse_listing_reads_the_newest_file_before_the_day_never_the_days_own`.

### Should-fix: the monthly expiry from NSE's listing (done)

The monthly expiry is now the last listed NIFTY expiry of its month in that same NSE file, not in the snapshot.
- `test_the_monthly_expiry_is_nses_not_the_snapshots`: NSE lists 28 Oct as October's last, so the snapshot's
  27 Oct chain fails `expiry`.
- The fixture also holds a BANKNIFTY option on a later October expiry and a stock option. Both must be ignored, and
  the mutation that drops the NIFTY filter is caught.

### Must-fix 2: the sidecar was untested (accepted)

**Check.** The judge is right: no test tampered with the meta file.

**Test.** `test_a_rewritten_sidecar_fails_with_the_quote_file_intact`:
- a capture started at 15:05 has its sidecar's `started_at` rewritten to 14:55 after the record was committed;
- the quote file is unchanged;
- it fails `evidence` ("meta file SHA-256 … differs") and nothing is priced.

Mutation "meta hash check off" is caught.

### Must-fix 3: the trusted limits (accepted, for all of them)

**Check.** C4 took drawdown, stress, exposure and margin from C2's boolean, so a C2 bug would pass C4 too.

**Fix.** Each limit is recomputed from raw inputs with C4's own code. C2's verdicts are still required to pass
(`risk_verdicts`), but only as an extra block, never as evidence.

| Limit | C4's inputs | C4's arithmetic (file) |
|---|---|---|
| Open trades | the ledger's open trades plus the trades chosen earlier that day that passed C4 | count + 1 ≤ 3 (`validity_limits.py`) |
| Drawdown brake | the committed E1 cash ledger, read directly (rows filled by the 15:00 cutoff), and `owner_overrides.csv` | closed equity at each day's close; high-water mark; a restart re-arms only if the brake was in force, else it fails closed (`validity_account.py`, `validity_drawdown.py`) |
| Stress | the snapshot's mids | its own Black-76: forward by put-call parity, each leg's volatility implied from its own mid; open trades from marks plus the proposal from its entry (pads and charges), in every `config.yaml` scenario (`validity_pricing.py`, `validity_chain.py`, `validity_stress.py`) |
| Exposure (C2's `exposure_limit`; not named by the judge, recomputed too) | same | ±2% move and +5 volatility points, every position from marks |
| Margin room | **A14's three-part file** (scan, NOV, exposure, source, date) and the account | per lot max(0, k·scan − NOV) + min(0, NOV) + exposure, with k the owner's dated, sourced multiplier. Available cash after entry is the least of cash, marked equity and cash plus liabilities, less reserved premium (`validity_margin.py`) |

The trades chosen earlier that day count as entered in every limit, as D2's `book_after_entry` counts them, but only
those that passed C4. C4 then passes `book` and the earlier trades instead of a count.

**Seeded breaches, one per limit** (`tests/checks/test_validity_limits.py`):
- drawdown exactly at Rs 30,000;
- a restart dated when the brake had not fired;
- stress over the limit;
- exposure over the limit;
- margin room too small (needed 78,050 = 1.45 × 9,000 + 65,000);
- four ways the margin fails closed: no row, a stale row, an unsourced row, no multiplier;
- a fourth trade counting one chosen earlier that day;
- an open trade with no recorded terms;
- an unreadable account.

**Cross-checks.**
- `test_c4_reads_the_ledger_as_e1_and_c2_do`: a real E1-written ledger gives C4 the same closed-equity series as
  C2's `closed_equity_series`, and the same cash as E1. A fill at 15:15 is correctly left out at the 15:00 cutoff.
- Black-76 equals Hull's textbook value (1.1166).
- The implied volatility and the parity forward round-trip.
- A shock's move, volatility scaling and days passing are pinned in a test.

**Independence.** The guard's list now also covers C2's `drawdown`, `overrides`, `book_view`, `settings`, B1's
`implied_vol`, E1's `account`, `equity` and `fills`, and D2's `book_effects`. A fresh interpreter loads none of them.
To keep it so, the ledger's file name moved from `fno/books/account.py` to `fno/constants.py`.

### E3 fit (the judge's ruling, written into story C4)

C4 runs once, inside D3's decision run, on the common pack's A4 snapshot. Its pass is stored in `validity.c4`. **E3's
`ValidityGate` reads that committed pass and never re-runs C4 on the 15:15 execution capture**, which would fail every
leg's price check.

### Gates and mutations (bytecode off, caches cleared)

- Full suite on the branch: **2,707 passed** before the four new tests. The final numbers on the tree merged with
  main are in the orchestrator message.
- `ruff`: clean. `check_imports`: clean. Largest new file: `tests/checks/test_validity.py` (160 lines).
- **Mutations: 57 of 57 caught.** The first run left four survivors:
  - the NIFTY filter;
  - days passing in a shock;
  - the volatility shock;
  - which strike sets the forward.

  One more mutation ("risk verdicts") had a bad pattern and never ran. I added the four missing tests, then re-ran
  all five; each is now caught.

### Limits, said plainly

1. **C4's stress numbers differ slightly from C2's.**
   - C4 uses a parity forward and its own implied volatilities. C2 uses the traded future's close and B1's
     volatilities.
   - On the fixture's SF the worst stress loss is Rs 3,152, under its Rs 3,541 maximum loss, as a defined-risk trade
     must be.
   - Near a limit the two can disagree. C4 blocks whenever its own number is over (reasoning only: the safe
     direction).
2. **Margin needs A14 and the owner's factor; until both exist, every trade is blocked.**
   - `main`'s `margins.csv` still has the old one-column header, and the stressed multiplier is unset. So C4's
     `margin_room` fails every trade, exactly as C2's does today.
   - When A14 merges, its header equals C4's, and the tests need no change because they use A14-format rows. I will
     then add a wiring test that reads the real file.
   - Only the `multiplier` method is checked. `scenario_lookup` fails closed, by name.
3. **Two account inputs are still taken as recorded, not recomputed.** Each open trade's terms (structure, width,
   lots, recorded when it was decided) and the premium reserved for pending orders (E4) come from the D2 book. A
   ledger trade with no recorded terms fails the margin.
4. **A replay reads committed files again:** the ledger (rows by the cutoff), the margins file and NSE's file. It
   reproduces the result while those stay append-only, as they are.
5. **On an expiry day,** a leg is valued at its intrinsic value, as C2 values it.
