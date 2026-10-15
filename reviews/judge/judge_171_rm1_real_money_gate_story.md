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
