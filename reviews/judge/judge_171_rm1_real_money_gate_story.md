# Judge 171: RM1 real-money gate, story text and draft gate (judge A)

**Checked:** `story/rm1-real-money-gate` at `d29934f5` (one commit on main 35e999af). The files are:
- `docs/stories/RM-real-money.md`
- `research/evaluation/REAL_MONEY_GATE.md` (12 items)
- `reviews/claude/response_163_rm1-real-money-gate.md` (claims, trace table, Q1-Q10)
- the WORK_REGISTER row

I read them against:
- design v2 8.3 and 8.4 (`docs/design_v2/08_budget_and_stop_rules.md:77-109`);
- DESK_DECISIONS decision 8 and its amendment (rows 113 and 118), principle 4 (row 94) and decision 168;
- the S1 code: `fno/evaluation/order.py`, `completeness.py` and `freeze.py`.

**Numbering:** judge 163 and 167-170 are taken (168 and 169 by other judges while this was written), so this is judge 171. No code in this
round.

**Verdict: FAIL, 3 should-fix, no blocking.** The text never enables an order, and the one-freeze design is the right,
minimal choice. But two items would decide real money differently from what the owner accepted, and the evidence
record is not tied to the freeze.

## Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Every 8.3 condition and 8.4 element has an exact rule, traced | PARTLY | 10 of 12 sound; `real_test_sample` drops 8.4's registered number (SF3); slippage in `real_test_pass`/`real_test_stops` has no reference price (SF2) |
| 2-4 | `check`, `freeze` refusal, the gate's hash in `FREEZE_v<n>.md`, `verify` | MET as design | The reuse fits `freeze.py`'s target hashing and `verify`; see the note on completeness format |
| 5 | Owner numbers before the freeze | MET | Q1, Q2 and the status rule make the freeze refuse until decided |
| 6 | Never an order, no broker import | MET | The scope item and the hard line in the header; the import test is planned. Nothing reads the gate to act; eligibility is "a report line, never an order, a setting or a switch" |
| 7 | 350 lines | MET for text | Code later |
| — | Freeze "before the first counted paper decision" | NOT MET | SF1 |
| — | Owner questions complete and neutral | PARTLY | Q1-Q2 and Q4-Q10 neutral, each with real options and a labelled recommendation; Q3 lacks the 8.4 option (SF3) |

## Should-fix

**SF1. The evidence record is not tied to the freeze, and a shadow record is outside S1's order check.**
- **Evidence:**
  - The gate's "Terms" say the evidence record is "the version's completed forward paper positions in Book 1 … or its
    registered shadow account", with no condition on when they happened.
  - S1's order check proves only that the freeze commit is a strict ancestor of "every book's first counted decision"
    (a D3 run of a book; earlier runs are pilot evidence; `fno/evaluation/order.py:1-10`).
  - Book 1 paper-trades before the freeze as pilot evidence (DESK_DECISIONS row 83).
  - An `exploratory_shadow` may start collecting before rung 1 (`docs/design_v2/01_overview.md:125`). It is a
    recorded decision "never in a book", so no D3 book run and no order check covers it.
- **Path in normal running:** S1 v1 waits for the S2/S3/F8/F9 code and the owner's Q1-Q10. Meanwhile Book 1's pilot
  positions and a shadow's positions accumulate. They are then counted toward `paper_evidence` by a gate written while
  they were visible. That is principle 4's risk (a pass mark written after seeing results), and response 163 claim 3
  ("the order check already proves it") does not hold for shadows.
- **Expected fix (text):**
  - Define the evidence record as positions counted under the frozen protocol version that holds the gate (the
    decision's commit has that version's freeze as a strict ancestor, `order.py`'s "version of a decision").
  - For a shadow: either extend the order rule to registered shadow records in RM1's scope, or restrict the gate to
    Book 1 until a shadow has the same proof.
  - Pilot positions are shown, never counted.

**SF2. Real slippage has no reference price, so the pass and stop rules can be looser than 8.4.**
- **Evidence:**
  - 8.4: "real slippage per unit must be no worse than the paper pad plus Rs 0.50"; stop at "slippage twice the paper
    pad over 5 trades".
  - The gate: "the mean of real-minus-paper fill slippage per unit is at most the paper pad + Rs 0.50"; stop (b) "mean
    real slippage per unit … exceeds twice the paper pad".
  - A paper fill carries a price and a pad separately (`fno/desk/execution.py:52`,
    `Order(quote.side, quote.price, quote.units, FILL_PAD_RS)`). `fill_honesty` says "paper price before pad" explicitly;
    these two items do not.
- **Path:** if "paper" means the padded paper fill, a real buy may sit 2 × pad + Rs 0.50 above the quote and still
  pass, which is about double what 8.4 allows. If it means the quote, it matches 8.4. A real-money pass or stop decision
  depends on which one the builder picks.
- **Expected fix (text):** in both items, define real slippage per unit as the real fill minus the paper price before
  pad (sells: the reverse), signed so that worse is positive. That is the same reference as `fill_honesty`.

**SF3. `real_test_sample` replaces 8.4's registered number of trades with a fixed 20.**
- **Evidence:**
  - 8.4: "Duration: its registered number of trades or 6 months, whichever is later" (owner-accepted, decision 8).
  - The gate: "the later of 20 trades placed and 6 months".
  - Q3 offers 20, 30 or 12 and no "the version's registered number" option.
  - `paper_evidence` keeps the analogous rule ("the larger of S1's paper_gate and the sample the version's
    registration named").
- **Path:** a version registered for 40 trades finishes its real test at 20 trades or 6 months. That changes when a
  real-money verdict is given, against an owner-accepted row (coordination rule: a contradiction is a FAIL).
- **Expected fix (text):** "the later of max(20, the version's registered number of trades) placed and 6 months from
  the first real entry", and Q3 asks only the floor, stating 8.4's rule.

## The one-freeze design (asked: sound and minimal?)

**Sound and minimal, with SF1's caveat.**
- One more `frozen_files` entry reuses S1's hashing, refusal and `verify`, with no second freeze tool or record (DRY,
  KISS).
- The cost (a gate change is a new S1 version) is stated in "Known limits". It is the intended cost of principle 4.
- Q10 rightly goes to the owner, because `frozen_files` is owner-decided (14 Oct).
- The order check proves the gate precedes every book's counted decision, but not that it precedes the gate's own
  evidence (SF1).

## Notes (one line each, no fix asked)

- `completeness.py` accepts only the exact status "proposal, owner decides" or "decided by the owner on YYYY-MM-DD",
  and only the three bare evidence labels. Six gate items carry extra text ("owner number (Q1, Q2)",
  "reasoning only (a point comparison …)"), and the gate has no version line. So the test plan's "the real draft gate
  passes `check`" fails as written: move the question references to the Reason line, and exempt the version line by
  parameter.
- `fill_honesty`: A16 records only the nearest weekly and nearest monthly NIFTY chains (G10, `expiry_plan.py`). A
  version trading any other expiry gets no snapshot and can never reach 20 legs. Tell the owner.
- `real_cap_fit` "the last 20 sessions' 15:00 quotes": name the source. The 3 pm recorder captures at 14:55 today and
  moves to 14:30 at v4 go-live.
- Condition 6's fact checks out: Rs 5,000 / 65 = 76.9 points. An ATM monthly NIFTY premium is well above that (some
  evidence, as labelled).
- The prediction-interval formula, paper mean − t(0.95, m−1) × SD × √(1/n + 1/m), is the correct one-sided bound for
  the mean of n new trades. Route (b)'s 0.05/m is Holm's first step, as stated.
- The branch conflicts with main in `docs/WORK_REGISTER.md` and `reviews/claude/README.md`, rows only. Keep both
  sides.
- Coordination: no other row covers the real-money gate. S6's later `PROTOCOL.md` change is on other lines, as
  response 163 §4 says, so there is no duplicate.

## Gates

Gates at d29934f5 (text only; trial merge conflicts on rows only): pytest 5877 passed; `ruff check` clean; `ruff format --check` 1074 files formatted; `check_imports` clean.

**A re-check needs only:** the Terms line and order rule (SF1), the two slippage definitions (SF2), `real_test_sample`
and Q3 (SF3).

## Addendum 1: revision at c27f8c64: PASS

Scope as asked: SF1-SF3 and notes 1-3. The RM1 diff since the merge of main (c24096c1..c27f8c64) touches the story,
the gate, response 163 §5 and the register row.

- **SF1: MET.**
  - The Terms define the evidence record as Book 1 positions whose decision commit has the gate's freeze record as a
    strict git ancestor. That is S1's version rule (`order.py`).
  - Pilot positions (before the freeze) and shadow positions are "shown, never counted", with the reason given.
  - The story scope, criterion 6 and both Known-limits lists say the same.
  - `index_benchmark` now reads Book 1's record only.
  - "Book 1 only" is the simpler of my two options. The order check proves exactly that set.
- **SF2: MET.**
  - The new term "paper price before pad" is E8's snapshot ask for a buy and bid for a sell, without `FILL_PAD_RS`.
    Worse is positive.
  - `real_test_pass` 2 measures from it: real fill minus paper price before pad, mean ≤ pad + Rs 0.50, matching 8.4.
  - `real_test_stops` (b) uses the same definition over the legs of any 5 consecutive trades, against twice the pad.
  - `fill_honesty` already used the same reference.
- **SF3: MET.**
  - `real_test_sample` is the later of max(20, the registered number) trades and 6 months from the first real entry.
    It quotes 8.4.
  - Q3 now states 8.4's rule and asks only the floor: 20, 30, or none (the registered number alone). The options are
    neutral, and the recommendation is labelled.
- **Note 1: MET, checked by script.** `parse_protocol` on the gate at c27f8c64 finds 12 items and no duplicates.
  Every item has all four fields, the exact status "proposal, owner decides" and a bare evidence label, and no
  undecided words appear. The missing version line is exempted by `require_version` in the expected design.
- **Note 2: MET.** A16's expiry limit is stated in `fill_honesty` and in Known limits.
- **Note 3: MET.** `real_cap_fit` names the 3 pm recorder (A4, `research/data/quotes/`) at S1's timetable capture time.

**Coordination:** WORK_REGISTER row 38 (S1's text owner) lists RM1's `frozen_files` line as a pending edit "after S6".
RM1 no longer edits `PROTOCOL.md` itself. That is one builder per file, with no duplicate.

**Gates (trial merge with origin/main 96edbb15, tree 7cd16ee, clean merge):**
- pytest: 5878 passed;
- `ruff check`: clean;
- `ruff format --check`: 1074 files formatted;
- `check_imports`: clean.

**Note (one line, no fix asked):** response 163 §1 claim 4 still says "Book 1 or the version's shadow account". §5
supersedes it, but ChatGPT reads §1 first.

**Verdict: PASS.** Next come ChatGPT (rule 9), then the owner's Q1-Q10, then the code round.

## Addendum 2: delta re-check at 2945dbd8 (ChatGPT review 118 revision): FAIL (2 should-fix)

Asked by the builder directly, with the orchestrator copied, and reported to the orchestrator. The delta
f8cbbc6c..2945dbd8 touches the gate, the story's criterion 6 and status, and response 163 §3 (Q11-Q13) and §6.

**Sound:**
- **"Valid quote" and "execution slippage"** (the real fill minus the valid quote at the owner's order time) separate
  execution from the market's move. E8's fill at about 10:15 next session is confirmed in `G-forecasts.md` (G10 table).
  Unknown never counts as zero.
- **Paired net now binding** (`real_test_pass` 1): mean − t(0.95, n−1) × SD(d) / √n ≥ the Q11 margin. That is the
  paired test 8.4 names; the prediction bound stays as a floor and is labelled model-based.
- **`real_cap_fit`** uses the last 20 issued cards, re-priced with their own contracts, lot size, quotes and charges,
  plus the next proposed trade.
- **Numbers checked:**
  - 5,000/65 = 76.9 points and 4,000/65 = 61.5 points, before charges;
  - the credit vertical: 65 × (100 − 30) + 200 = Rs 4,750 and 65 × (200 − 30) + 200 = Rs 11,250;
  - **Q11:** t(0.95, 19) = 1.7291, and 1.7291 × 1,000 / √20 = **Rs 386.6**, so the builder's "about Rs 387" (Q11's
    "about 390") is correct; with a −Rs 500 margin, real must average within about Rs 113 of paper (Q11 says "about
    Rs 110", correct).
- **The Bonferroni wording** (one fixed family, one look) and the daily-settlement proxy label are correct.
- **Format:** `parse_protocol` on the gate at 2945dbd8 finds 12 items, no duplicates, every status exactly "proposal,
  owner decides", bare labels and no undecided words (my script).

**SF1. The unknown-leg rule in `real_test_pass` 3 has no exact rule at or under the 1-in-10 limit.**
- **Evidence:** the text says "a leg with unknown slippage counts against the test (not met if more than one in ten
  legs is unknown)". At 10% or fewer unknown legs it does not say what the mean uses. "Counts against" can mean the leg
  is left out, given the worst observed slippage, or given some other penalty. `real_test_stops` (b) says "left out of
  the mean and listed".
- **Path in normal running:** the owner misses the Groww screenshot on 3 of 40 legs, and A16 is older than 5 minutes.
  The pass on execution then depends on how the builder reads "counts against".
- **On the 10% number (asked):** it is reasonable. At 20 two-leg trades it allows 4 of 40 legs unknown. It sits
  inside Q12 for the owner, labelled reasoning only. The only fault is the missing rule beneath it.
- **Fix (text):** state the rule, for example "unknown legs are left out of the mean and listed; more than 1 in 10
  unknown is not met", the same as stop (b).

**SF2. Q13 is not neutral: it hides that its recommended option drops the owner-accepted test in 8.3 condition 4,
and it omits that test as an option.**
- **Evidence:**
  - 8.3 condition 4 (owner-accepted, decision 8) says "the mean gap between paper fill and the next real snapshot is
    within the pad".
  - The new `fill_honesty` (a) checks the fill against its own snapshot, which the builder rightly calls circular.
    (b) needs a second recorder at fill time.
  - Q13 offers (a) validity alone, (b) strict, which "blocks every version", and (c) a second recorder later.
  - Under (a), condition 4 has no independent comparison at all, and the question does not say that an accepted
    condition is relaxed.
  - The owner-accepted test is feasible: E8 fills from A16 at about 10:15, so the next A16 snapshot (about 10:30) is
    the "next real snapshot" of 8.3. ChatGPT's point, that a later move is no proof, makes it noisy, not impossible.
- **Path:** the owner picks the recommended (a) without being told it removes 8.3 condition 4's only independent
  check. That decides when real money can be put to the owner (coordination rule: a contradiction of an
  owner-accepted row must reach the owner as one).
- **Fix (text):** add option "(d) keep 8.3 as written: the mean gap to the next A16 snapshot (about 15 minutes later)
  within the pad, its noise stated". Say plainly in Q13 that (a) relaxes the owner-accepted condition 4.

**Notes (one line each, no fix asked):**
- `real_test_pass` Reason: "with n = m = 20 and SD Rs 5,000 the prediction floor sits about Rs 2,160 below paper's
  mean". By the gate's own formula it is 1.7291 × 5,000 × √(1/20 + 1/20) = **Rs 2,734**. Correct the number; "a weak
  filter" stands.
- Q11's SD near Rs 1,000 is an assumption. d includes the timing gap when the owner fills at a different time from
  E8's 10:15 model, so SD(d) may be much larger. Q11 says the real SD is unknown, rightly.
- The branch conflicts with main in `reviews/claude/README.md` (rows only). Keep both sides.

**Gates at 2945dbd8 (docs-only delta; the trial merge conflicts on index rows only):** pytest 5878 passed; `ruff check` clean; `ruff format --check` 1074 files formatted; `check_imports` clean.

**A re-check needs only:** `real_test_pass` 3's unknown-leg rule, Q13's options and wording, and the Rs 2,734 figure.
