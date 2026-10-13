# Response 51: C2 risk manager, builder's claims for the judge

Story: `docs/stories/C-code-roles.md` section C2 (issue #38). Package `fno/risk/`, wired in `fno/composition.py`
(`build_risk_manager`), settings in `config.yaml` `risk` (now in `ALLOWED_APP_KEYS`). Tests: `tests/risk/` (94 tests).

**Verdict first:** every acceptance criterion has code and a test; the desk cannot open any paper trade yet, on
purpose, because no margin and no stressed-margin factor have been entered (owner input, below). Strong evidence for
the code (tests, hand computations); reasoning only for the stress and exposure limit values (design 8.1 says so).

## How to check

```
python -m pytest -q tests/risk          # 94 passed
python -m pytest -q                     # whole suite
ruff check fno tests tools && python tools/check_imports.py
```

## Design (what the judge will find where)

| File | What it does |
|---|---|
| `fno/risk/verdict.py` | `RiskRule` interface: `check(proposal, book, market) -> RiskVerdict(rule, ok, reason, numbers)` |
| `fno/risk/rules.py` | `MaxLossPerTrade`, `MaxOpenTrades`, `StressLoss`, `ExposureLimit`, `MarginRoom` (one class each) |
| `fno/risk/drawdown.py` | `DrawdownBrake` and the high-water mark with owner restarts |
| `fno/risk/stress.py` | stress engine: full repricing with `fno.analytics.bs_price` |
| `fno/risk/margins.py` | `MarginTable` (margins.csv, 7-day fail-closed) and the two frozen stressed-margin methods |
| `fno/risk/trade_costs.py` | `TradeCosts` interface; `SimulatorTradeCosts` reuses B2's `PositionCosts` (max loss, pads, charges) |
| `fno/risk/inputs.py` | proposal, market snapshot, one book's view; input errors |
| `fno/risk/book_view.py` | builds a book's view from its own E1 paper account (`PaperAccount`, `trade_positions`, `AccountState`) |
| `fno/risk/overrides.py` | reads `journal/<book>/owner_overrides.csv` through the E1 book-path firewall |
| `fno/risk/manager.py` | runs every rule; any unusable input refuses the trade; the decision record |
| `fno/risk/settings.py` | reads and checks the `risk` block; a missing limit is an error, never a default |

Reuse (as asked): E1 for cash, closed and marked equity and available cash (`fno/books/equity.py`, unchanged); C1
through E1's fills (charges by component); B2's `PositionCosts.max_loss` for the per-trade maximum loss (test
`test_max_loss_is_the_cycle_simulators_model_with_every_charge_and_pad` shows the same rupees). One small E1 change:
`fno/books/paths.py` gains `book_folder` (the `journal/<book>` folder, same book-name check), used by
`account_folder` and by the overrides file.

## Acceptance criteria

| # | Criterion | Code | Test (`tests/risk/`) |
|---|---|---|---|
| 1 | Rs 9,999 passes, Rs 10,001 blocked with reason and numbers | `rules.py` `MaxLossPerTrade` | `test_rules.py::test_max_loss_per_trade_threshold` (9,999 / 10,000 pass; 10,000.01 / 10,001 blocked; numbers checked); end to end with B2's model: `test_manager.py` (1 lot Rs 3,354.54 passes, 4 lots Rs 12,851.77 blocked) |
| 2 | 3 open trades: a fourth is blocked | `MaxOpenTrades` | `test_rules.py::test_max_open_trades_allows_a_third_and_blocks_a_fourth` |
| 3 | Brake at 30,000 below the high blocks entries, open trades not closed, owner restart re-arms 30,000 below that day | `drawdown.py` | `test_drawdown.py` (all 7 tests), on real accounts `test_books.py::test_the_owners_restart_row_reopens_only_its_own_book` |
| 4 | Open short fly + proposed short condor: per-scenario losses equal a hand computation; blocked above 30,000 | `stress.py`, `StressLoss` | `test_stress.py`: hand values in the module docstring and `HAND_VALUES` (e.g. NIFTY -8%: fly Rs 6,110 from marks, condor Rs 10,985 from entry, Rs 17,095 counted); 3 lots: Rs 39,065, blocked; Black-Scholes repricing checked against the textbook value 10.4506 |
| 5 | A proposal pushing the 2%-move loss above the setting is blocked | `ExposureLimit` | `test_rules.py::test_a_proposal_pushing_the_2pct_move_loss_above_the_setting_is_blocked` (alone Rs 6,500, with the open spread Rs 19,500 > 15,000) |
| 6 | Every rule: just inside and just outside | all rules | max loss, open trades, brake (490,000.01 / 490,000.00), stress (17,095.00 / 17,094.99), exposure move and IV rise, margin room (44,850.00 / 44,850.01) |
| 7 | Two books: a brake in one blocks only that one; stress never includes another book | `book_view.py`, `stress_positions` | `test_books.py` on real E1 accounts in a temporary journal (book 1 brake hit, book 2 open fly) |

Judge's crafted proposals: `tests/risk/test_manager.py` shows inside (all 7 verdicts pass), outside (4 lots, per-trade
limit) and borderline (the limit equal to the maximum loss passes, one paisa less refuses), through
`build_risk_manager` exactly as the app wires it.

## Decisions I made, with reasons (please check them)

1. **Which margin figure (judge 1's question).** The initial margin (SPAN plus exposure) for the structure, width and
   lots, from `research/data/margins/margins.csv`, never the broker's live total for an open short structure: that
   total includes the marked loss, which available cash already deducts through min(cash, marked equity). Reasoning
   only, from the definition.
2. **Margin room arithmetic.** Stressed margin of every open trade plus the proposal must be at most the available cash
   **after** the proposal's entry: min(cash + entry cash flow, marked equity + entry cash flow + the proposal's marked
   value) - premium reserved. The book view sets margin blocked to 0 so no margin is counted twice. Test with numbers
   in `test_rules.py::test_margin_room_counts_every_open_trade_and_the_proposal_against_cash_after_entry`.
3. **What the stress limit counts.** Open trades from their current marks (the story's wording); the proposal from its
   entry (its cash flow at padded fills after charges), so a new trade's pads and charges count. Both losses (from
   marks and from entry) are reported for every trade and scenario.
4. **Exposure** is measured by full repricing (NIFTY +/-2% and IV +5 points, no time passing), not by Greeks, with every
   position valued from its mark: it is a sensitivity, so entry costs are left out.
5. **Replays** use the close-to-close NIFTY 50 move and the India VIX ratio from the previous session to that day
   (`warmup_closes.csv`, muhurat sessions excluded): 23 Mar 2020 -12.98%, VIX x1.0729; 4 Jun 2024 -5.93%, VIX x1.2775.
   "Feb 2026's worst day" is ambiguous, so **both** candidates are scenarios: the largest fall (1 Feb, Budget day,
   -1.96%, VIX x1.1079) and the largest move (3 Feb, +2.55%, VIX x0.9301). Each replay applies the VIX ratio to every
   leg's IV and passes one day. `test_settings.py` checks the four against the closes and checks the two February picks.
6. **A restart row on a day the brake was not in force is an input error** (the brake then refuses trades until the row
   is corrected): otherwise a stray row would silently lower the high-water mark and loosen the brake. A row dated
   after the decision day is not yet in force.
7. **Fail closed.** Any `ValueError` from a rule (missing quote, margin, terms; stale proposal quote; malformed row)
   turns that rule's verdict into a refusal with the input's message; any other exception (a bug) is raised, never
   swallowed (`test_a_bug_in_a_rule_is_not_swallowed`). All rules always run so a refusal lists every reason.

## Known limits (said plainly)

- **No trade can open today:** `margins.csv` is empty and `risk.stressed_margin` has no factor, source or date, so
  `margin_room` refuses every proposal (`test_the_repository_settings_refuse_every_trade_until_margins_and_the_factor_are_entered`).
  This is deliberate: I have no sourced number for either. **Owner input needed:** margins per lot for the structures
  and widths that will be traded (Groww's margin calculator or NSE SPAN), and either a stressed-margin factor with its
  source and date or a scenario margin file. My suggestion, reasoning only: for defined-risk flies and condors the
  margin is close to width x lot plus exposure margin, so a factor of 1.5 is likely conservative; please check it on
  the calculator under a +/-8% move before entering it.
- **Open trades' terms** (structure, width, lots) are an input: E1 records fills only. The decision record that opens
  a trade (C4/E4) must keep them; until then an open trade without terms refuses new trades in its book.
- **Stale marks** are recorded in every decision but do not block here: design 9 makes stale data a no-new-trade
  condition, which is story C3's check. If C3 is not built before paper trading, this is a gap.
- Stress repricing uses Black-Scholes on spot with each leg's given IV. If the snapshot's IV is not implied from the
  same mid on the same model, a zero-move scenario shows a small non-zero loss; C3/E4 should supply consistent IVs.
- Stress losses leave out exit charges (the per-trade maximum loss includes them).
- Pending orders are not counted as open trades; E4 adds them through `premium_reserved` and the open count.
- Exposure limits (Rs 15,000 each) are design 8.1's proposed values, reasoning only, to be set from research.

## Project rules

Files 30-170 lines (`fno/composition.py` 274); no `# fmt: skip` in the new code; constants in `fno/constants.py`
(`OWNER_OVERRIDES_FILE`, `OVERRIDE_RESTART_BRAKE`, stressed-margin method names); every limit from `config.yaml`;
wiring only in `fno/composition.py`; no secrets; research data untouched by tests (conftest guard).
