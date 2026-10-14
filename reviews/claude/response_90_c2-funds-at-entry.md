# Response 90: story C2 funds at entry (judge 77 addendum 3, must-fix 2): builder's claims

Branch `story/c2-funds-at-entry`. Builder: Claude, 14 Oct 2026. It must be built and judged before
`risk.stressed_margin` is set. Follow-up (1), the exposure rescale, is not part of it.

## 1. The judge's finding, checked (accepted, with one correction to the fix as described)

**Accepted.** On Groww's basket (NIFTY Nov 22700 short iron fly width 100, 1 lot of 65, 14 Oct), the broker needs
6,893.00 + 58,819.02 + 47,450 + 150.62 = 113,312.64 rupees free. I re-added the figures. C2's `MarginRoom` needed
far less, because it:
- credits the entry's net cash flow; and
- counts margin as `max(0, scan - NOV) + min(0, NOV) + exposure`, whose `min(0, NOV)` term nets the premium into
  SPAN.

**A correction to the fix as the orchestrator described it** (reasoning plus arithmetic). Adding only "bought premium
+ charges, no sold-premium credit" to C2's netted margin needs 822.25 + 58,819.02 + 47,450 + 150.62 = 107,241.89,
which is still Rs 6,071 (|NOV|) looser than Groww. That netting only holds when the premium is credited at entry, and
Groww does not credit it. So the at-entry check must also drop the `min(0, NOV)` term:
`max(0, k x scan - NOV) + exposure`. On the same NSE row that is 822.25 + 6,071 = 6,893.25, which is Groww's SPAN to
the rupee. A test proves this on Groww's numbers (section 3).

## 2. What changed (minimal; no new port)

1. **`TradeCosts.entry_funds`:** the bought legs at their padded fills, times units, plus every entry charge; no
   sold premium. `SimulatorTradeCosts` implements it and shares one `_entry` helper with `entry_cash_flow`.
2. **`StressedMargin.margin_at_entry`:**
   - `MultiplierMargin`: `MarginParts.at_entry(k) = max(0, k x scan - NOV) + exposure`, refused unless above 0.
   - `ScenarioLookupMargin` **fails closed**: its rows are one netted figure with no NOV, so the margin without the
     premium credit cannot be known. That method is not configured today.
3. **`MarginRoom` keeps its netted check and adds the funds-at-entry check. Both must hold:**
   - needed at entry = the open trades' margins (as before) + the new trade's margin at entry + its funds at entry;
   - free before entry = min(cash, marked equity, cash + each held trade's own loss) - premium reserved;
   - the record adds `funds_at_entry_rs`, `needed_at_entry_rs` and `free_before_entry_rs`, and the reason states both
     checks.

## 3. Evidence

| Test | What it shows |
|---|---|
| `test_funds_at_entry.py`: the Groww basket | needs 6,893.25 + 58,819.02 + 47,600.62 = 113,312.89 (Re 0.25 above Groww's 113,312.64 because Groww rounds SPAN to the rupee: never looser); passes at exactly that cash, refused 1 paisa below |
| a rupee below Groww's total | refused, while the old netted room alone still had more than Rs 50,000 spare: the gap the judge found |
| the mirror (a long iron fly, a debit) | needs exposure + the dear legs bought (53,475.50) + charges = 112,445.14; refused 1 paisa below, while the old room had more than Rs 40,000 spare |
| free cash before entry | with a losing credit trade and a winning debit trade (marked equity = cash) and Rs 1,000 reserved, free = cash - 9,000 - 1,000: one trade's gain does not net another's loss |
| `test_margin_formula.py` (judge 75's exactness test, extended) | all 14 combinations of an open credit or debit fly at a loss, with a new credit or debit: the at-entry free cash now also equals a Groww-style broker exactly (held margin at today's value, the new trade's unnetted margin, the bought legs paid) |
| `test_rules.py` | `entry_funds` by hand: wings 95 + 90, each Rs 1 worse, times 65, plus charges |
| `test_margins.py` | the factor stresses the at-entry scan (124,000 against the netted 112,000); scenario lookup fails closed |

**Mutations** (`python -B`, caches cleared): 10 of 10 caught. The plants:
1. drop the at-entry check;
2. drop the held margins;
3. use the netted margin at entry;
4. free = cash only;
5. no premium reserved;
6. no liability term;
7. put the `min(0, NOV)` term back;
8. factor 1.0 at entry;
9. count the sold legs in funds;
10. no charges.

The first round caught 7 of 10. The three survivors (premium reserved, the liability term, the factor) needed the
three tests added above.

## 4. What the owner and orchestrator should know

1. **C4 has the same gap.** `fno/checks/validity_margin.py` recomputes the margin room independently with the same
   netted formula, so C4 is as loose as C2 was. C2 now refuses such a trade first, so no trade gets through. C4 is
   meant to be an independent second line, though, so it should get the same at-entry check. **Proposed follow-up
   story; not built here (outside this story's scope).**
2. **`scenario_lookup` cannot be used for entries now.** It fails closed until its rows carry NOV or a gross margin.
   Today the method is not set.
3. **Groww's exposure base** (follow-up 1, the rescale from the previous close to the index at decision) is still
   open, as the judge ruled.
4. **Not checked here: a sold premium received earlier the same day.** E1 credits a sold premium to cash at the
   fill, while Groww makes it usable only after settlement. A second trade the same day could therefore see the first
   trade's premium as free cash. I have not verified how the desk sequences two entries on one day, so this is an
   open question for a later story. (Reasoning only.)

## 5. Gates

Full suite (token unset), `ruff check fno tests tools`, `ruff format --check` and `python tools/check_imports.py`:
the results are in the commit message and the message to the orchestrator.

## Addendum 1: merged; follow-ups recorded (judge 77 addendum 4, not built)

The judge passed this at 90dfcd3, and it is merged into main as 6647511. The suite passed on the merged tree: 3,113
tests.

Follow-ups, to be built later as their own stories:
1. **C4 `validity_margin.py`** gets the same at-entry term:
   - the margin with no sold-premium credit, `max(0, k x scan - NOV) + exposure`;
   - plus the bought premium and charges;
   - against the free cash before entry.
2. **E1 holds back a sold premium received the same day until T+1,** so a second entry the same day cannot count it
   as free cash, as Groww does not.
