# Judge 198: RM2 real-money test record, story text (judge A)

**Checked:** `story/rm2-real-money-record` at `9f964dc6`. That is the RM2 section of `docs/stories/RM-real-money.md`,
its claims file (response 186, to be renamed 189, text only) and the register row. I read them against:
- the frozen gate on main (`research/evaluation/REAL_MONEY_GATE.md`, RM1 merged 4777653e);
- E8's card-time section (`docs/stories/E8-owner-timing-fills.md:52-62`), which cites O1:88;
- C1's charges (`fno/costs.py`).

**Verdict: FAIL, 1 should-fix, no blocking.** It never places an order and makes no Groww call. The times and every
gate number check out. One pairing rule biases the binding pass test against real trades.

## Checked and sound

- **Gate numbers, item by item against the frozen gate:**
  - 1 lot; max(30, registered) trades and 6 months (gate line 158);
  - paired bound −Rs 500 (169);
  - the prediction floor;
  - Rs 1.50 per unit (175);
  - 10% unknown legs, left out and listed when 10% or fewer;
  - 90% of eligible cards (178);
  - stops (a) at or below −Rs 20,000, (a2) a Rs 20,000 fall from the peak, and (b) above Rs 2 per unit over 5
    trades (191-193);
  - valid quotes within 5 minutes, with the A16 fallback in the same 5 minutes (35).

  Criterion 7 pins `rules.py` to the gate text. Criterion 3's boundaries are right: −20,000 trips; a +6,000 high
  falling to −14,000 trips; 2.01 trips and 2.00 does not.
- **Times:** the card posts at 15:15 or later (O1:88, via E8:54). E8's R = 60 paper fill is the next session's 10:15
  mark (E8:60). The owner may place the order in the same session's last minutes or the next session, and pairing by
  card handles either.
- **"Next snapshot" is strictly after the fill:** right, because E8 fills on its due mark, so the mark at the fill
  time is the fill's own quote (gap 0). Criterion 6 pins 10:15 against 10:30. That is my RM1 note 2, answered.
- **Order-time quote:**
  - the screenshot comes first, and its time is typed from the image, because Drive's upload time cannot date it;
  - the file-name time is kept as a check, flagged when it differs by more than a minute;
  - the A16 fallback is the latest mark at or before the order, within 5 minutes, with age 0 allowed;
  - with no valid quote, the slippage is unknown, never zero.
- **The timing gap is reported only,** as the gate requires.
- **Drive only:** the public repository gets SHA-256s and a status line with no price, strike or rupee figure
  (criterion 8 and 8.5). The stop and pass alerts go to #fno-desk only.
- **No order path:** RM2 reads Drive, A16 and Book 1 only. The import test bans Groww and order modules.
- **Owner questions Q1-Q3 as open slots:** each is neutral, with options and a labelled recommendation, and none
  changes a gate number. Q2 fills the gap the gate leaves (when a card counts as skipped). Q3: the gate says "every
  charge included", so (a) actual charges is the reading that fits "real net".
- **Coordination:** the new register row RM2 has the same builder as RM1. It only reads E8, T1 and A16, so there is
  no duplicate.

## Should-fix

**SF1. "Paper net ÷ paper lots" misstates paper's 1-lot cost, which biases the paired test against real.**
- **Evidence:** C1 charges brokerage as a flat Rs 20 per order, plus 18% GST (`fno/costs.py:27,34`), whatever the lot
  count. Book 1's paper trades are sized to its Rs 10,000 cap, while the real test is 1 lot under Rs 5,000, so paper
  usually holds 2 or more lots. Dividing paper net by lots therefore divides the fixed brokerage too.
- **Path:** take a two-leg spread, opened and closed, so 4 orders.
  - Real at 1 lot pays 4 × Rs 23.6 = Rs 94.4 in brokerage and GST.
  - Paper at 2 lots, divided by 2, carries Rs 47.2.
  - So every paired d = real − paper is about Rs 47 worse, with no execution difference at all (about Rs 63 at 3
    lots, Rs 71 at 4).
- **Why it matters:** the binding pass test is lower bound ≥ −Rs 500, with about Rs 387 of noise at n = 20 and SD Rs
  1,000. A built-in −Rs 47 to −Rs 71 is 10-14% of the margin, against real every time. The prediction floor (pass
  item 2) has the same issue, since its evidence record is "scaled to 1 lot".
- **Expected fix (text):** scale paper's gross P&L per unit to 1 lot, then apply C1's charges for 1 lot on each leg's
  orders. The paper pad is per unit, so it scales exactly. Use this for the paired trade and the evidence record
  alike.

## Notes (one line each, no fix asked)

- **Valid quote, both sides:** the gate's valid quote needs "both sides present" as well as depth. Criterion 2 should
  also refuse a screenshot showing only one side.
- **A16 fallback times:** use the mark's observed quote time, not its nominal time (G10's honest-times rule). A
  "10:15" mark is fetched over about 50 seconds, so an order at 10:15:20 must not use a quote fetched at 10:15:40.
- **Stop (b)'s window:** "the last 5 real trades" after every exit equals the gate's "any 5 consecutive" only if
  trades are ordered by exit time. Say so.
- **Gates** (trial merge with origin/main 0659c386, tree 7a35213, clean, `-n auto`):
  - pytest: 6520 passed;
  - `ruff check`: clean;
  - `ruff format --check`: 1155 files formatted;
  - `check_imports`: clean.

**A re-check needs only the pairing and scaling rule (SF1).**
