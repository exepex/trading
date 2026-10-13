# Response 45: story B2 (cycle simulator) built, claims for the judge

**Verdict asked for:** B2 is built; all 7 acceptance criteria are met by tests that run on hand-built data and on the
real 2024-26 panel. Two findings and one protocol question are below (sections 3-4); they are not hidden and none
changes a criterion. Builder: Claude (B2 builder session), 13 Oct 2026. Story: `docs/stories/B-research-engine.md` B2,
GitHub issue #31.

## 1. What was built

| File | What it does |
|---|---|
| `fno/research_engine/cycles.py` (91 lines) | `Cycle` (expiry, decision, entry, exit days; `has_entry_window`), `monthly_cycles(panel, calendar, expiry_rule=monthly_as_of)`, `TradingDays` (session calendar minus muhurat), `cycle_rows` (the `keep` filter for `read_nifty_panel`) |
| `fno/research_engine/structures.py` (112) | `Leg`, `Structure` interface (template: body strikes + wings), `ShortIronFly` (SF), `ShortCondor` (SC), `LongIronFly` (BF), `nearest_strike`, `terminal_value` |
| `fno/research_engine/leg_prices.py` (49) | a leg's price on a day: close if volume > 0, else settlement flagged; zero or missing = no price; `fill_problem` (unfillable rule) |
| `fno/research_engine/cycle_costs.py` (79) | `CycleTerms` (lot, charges, pad 1.0, cap 10,000, widths 300-100), `PositionCosts` (fills, charges via `fno.costs.order_charges`, pads, gross, modelled max loss), `payoff_loss` |
| `fno/research_engine/simulator.py` (124) | `CycleSimulator.simulate(cycle, structure) -> CycleResult`; `WidthTrial`, `LegResult`; no-settlement sensitivity (`needs_settlement`, `no_settlement_net`) |
| `fno/constants.py` | `CycleStatus` (exhaustive `StrEnum`, the six values), structure codes SF/SC/BF |
| `fno/composition.py` | `build_cycles(panel)`, `build_structures()`, `build_cycle_simulator(cfg, panel)` (lot from `lot_sizes.NIFTY`, `charges` from config.yaml) |
| Tests | `tests/research_engine/test_simulator.py` (15), `test_structures.py` (4), `test_cycles.py` (4), `test_cycles_real.py` (4), fixtures `cycle_fixtures.py` |

Reuse: the panel is read only through `fno.research_data.panel_reader.read_nifty_panel` (A3, already on main; no
second reader); monthly identity through A5's `monthly_as_of`; holidays through A1's `SessionCalendar`; charges through
`fno.costs.order_charges`. B1's files are untouched.

**Signature differences from the story's sketch (deliberate, stated so the judge can weigh them):**
- `monthly_cycles(panel, calendar, expiry_rule)` takes the session calendar as well: the story requires holidays from
  A1's calendar, and the entry day after the panel's last day or a holiday needs it.
- `simulate` is a method of `CycleSimulator(panel, terms)` rather than a function with seven arguments; `terms`
  (`CycleTerms`) carries lot, charges, pad, cap and widths, built in the composition root from config.yaml.
- `Structure.legs(chain, spot, width)` returns `None` when a needed contract is not listed (the width is unavailable).

## 2. Per criterion

Commands (all run on commit below): `python -m pytest -q` → **713 passed** (full suite); `ruff check fno tests tools` → all checks passed;
`python tools/check_imports.py` → clean; no file or class over 350 lines (`tests/test_code_size.py` passes).

| # | Criterion | Evidence | Claim |
|---|---|---|---|
| 1 | Hand-worked SF, SC, BF: gross, charges, pads, net, max loss to the rupee | `test_simulator.py::test_short_iron_fly_by_hand`, `test_short_condor_by_hand`, `test_long_iron_fly_by_hand_on_the_only_listed_width`. Prices are written in each test; charges come from `hand_order_charges` in `cycle_fixtures.py`, written independently of `fno/costs.py`. Each money field must equal the hand formula (to 1e-6) **and** the rupee figures written in the test: SF (2,600 / 307 / 520 / 1,773 / 1,448), SC (975 / 231 / 520 / 224 / 8,873), BF (1,625 / 353 / 520 / 752 / 6,963) | MET |
| 2 | Zero volume → settlement used and flagged; 3 of 4 flagged → unfillable | `test_an_untraded_leg_uses_its_settlement_price_flagged` (price 141.0, flagged, `needs_settlement`, no-settlement net 0); `test_three_of_four_legs_on_settlement_is_unfillable[entry]` and `[exit]` | MET |
| 3 | Credit equal to the width → `bad_prices` | `test_a_credit_equal_to_the_width_is_bad_prices` (credit 300 = width 300); also `test_a_long_debit_of_zero_is_bad_prices` | MET |
| 4 | Only 150 fits → 150 used; none fit → `no_trade_cap` | `test_only_the_150_point_width_fits_under_the_cap` (300, 250, 200 over the cap with their losses recorded, 150 traded); `test_no_width_fits_is_no_trade_cap` | MET |
| 5 | Every traded cycle's modelled max loss ≤ Rs 10,000 over all 2024-26 cycles and structures; a realised loss above it reported | `test_cycles_real.py::test_every_traded_cycle_is_within_the_loss_cap`: 33 cycles x 3 structures = 99 results, all `traded`; largest modelled max loss SF Rs 4,878, SC Rs 9,807, BF Rs 9,997; no realised loss above Rs 10,000 (worst realised: SC -Rs 6,298). See finding 3.1 | MET |
| 6 | Tests for equal-distance ties, an unlisted wing, a zero price, a holiday-shortened window | Ties: `test_structures.py::test_an_atm_tie_takes_the_lower_strike`, `test_a_short_out_of_the_money_tie_takes_the_strike_farther_from_spot` (spot 25,000: call 25,550, put 24,450). Unlisted wing: `test_a_wing_not_listed_exactly_makes_the_width_unavailable`, `test_no_wing_listed_at_all_is_missing_strikes`, BF hand test (widths 300-150 `missing_strikes`). Zero price: `test_a_zero_settlement_is_no_price` (judge 20's 0.00 settle), `test_a_zero_close_on_a_traded_leg_is_unfillable_at_exit`. Holiday: `test_cycles.py::test_a_holiday_shortened_window_moves_entry_and_exit_to_trading_days` (entry moves over a holiday, exit moves back from one); `test_an_entry_day_not_before_the_exit_day_is_no_entry_window` | MET |
| 7 | 2024-26 cycle dates equal meeting 1's, with next-day entry | `test_cycle_dates_equal_meeting_1_with_next_day_entry`: meeting 1's dates are in the repository at `research/2026-10-12-desk-meeting-1/results.json` (`trades`: `entry`, `exit`, `expiry`, 33 rows). Meeting 1 entered on the first day in the window, which the protocol makes the decision day. All 33 (expiry, decision, exit) equal meeting 1's (expiry, entry, exit), and every entry day is the calendar's next session (e.g. decision 13 Feb 2026 → entry 16 Feb; 13 Apr 2026 → 15 Apr over the 14 Apr holiday). `test_each_decision_day_is_the_first_trading_day_of_its_window` also checks no earlier trading day was in the window | MET |

**Settlement note from judge 20:** a 0.00 settlement is never a price (`leg_prices.leg_price`: settle ≤ 0 → no price →
`unfillable`), and an expiry day's settlement (the index value from 6 Feb 2020) is never used either; test
`test_a_zero_settlement_is_no_price`.

**Exhaustive enum:** `CycleStatus` has exactly the six values; `test_cycle_status_is_exactly_the_six_values_b3_consumes`
also proves an unknown value raises.

**Access attestation:** every B2 test and check reads only the panel years 2024, 2025 and 2026
(`read_nifty_panel(..., (2024, 2025, 2026), cycle_rows)`). No 2019-2023 option row, cycle, price or P&L was read or
computed by this work.

## 3. Findings (data, from the real 2024-26 panel)

### 3.1 A realised loss can exceed its modelled maximum (risk manager)
SF, July 2024 cycle (entry 11 Jun, exit 4 Jul 2024, width 300): realised **-Rs 4,024** against a modelled maximum of
**Rs 2,886**. Cause, in the data: at the exit close (NIFTY 24,302) the 23250/23550 call spread closed at
1,168.65 - 867.40 = **301.25, more than the 300 points it can ever pay**. Daily closes are not synchronous (deep
in-the-money calls trade rarely), so a close-proxy exit can break no-arbitrage bounds. It is 1 of 99 results, still far
under Rs 10,000, and pinned by `test_the_one_realised_loss_above_its_model_comes_from_exit_closes_above_the_width` so
any change shows. **Meaning:** the cap rule bounds the terminal payoff, as the protocol says; it does not bound an exit
21 days early at stale closes. With SC and BF chosen right up to the cap (Rs 9,807 and Rs 9,997), a similar exit
anomaly could push a realised loss over Rs 10,000. Protocol section 4 then requires it to be reported and investigated (it does
not void the run: section 8 criterion 7 voids only on a modelled loss above the cap). Some evidence (one case in 99).

### 3.2 Discovery numbers (F&O trader; no verdict, B3 owns the metrics)
2024-26, 33 cycles each, one lot, all charges and pads: **SF net -Rs 18,286** (12 wins), **SC net +Rs 5,055** (24 wins,
widths 300 x 22, 250 x 9, 200 x 2), **BF net -Rs 34,735** (3 wins, widths 150 x 18, 100 x 15). No-settlement
sensitivity changes only SF (1 cycle needed a settlement price): -Rs 14,531. This is the period meeting 1 already saw,
so it proves nothing (statistician); but note it is much weaker than meeting 1's "every protected-selling variant made
money", because the cap forces narrow wings (300 points or less) where meeting 1 used 300-500. Some evidence.

## 4. Question for the orchestrator (protocol, not code)

**Long fly debit above its width.** The story and protocol call `bad_prices` only a short credit ≥ width or a long
debit ≤ 0, i.e. a trade that cannot lose. The mirror case, a long debit ≥ width (a trade that cannot win: a BF pays
at most W at expiry), is also impossible in a real market. It occurs in **3 of 33** BF cycles of 2024-26 (July 2024
debit 100.15, Aug 2024 100.60, Feb 2026 101.10, all at width 100); today they are traded. I built the rule exactly as
written. Proposal: `bad_prices` = "the prices imply a trade that cannot lose **or cannot win**". The protocol is agreed
(v2.1) but not frozen, so this is the moment to decide; it needs the owner's or ChatGPT's agreement, not a builder's
change. Reasoning only for the proposal; the 3 cycles are data.

## 5. Design decisions the story does not spell out (each stated in the module docstrings)

1. **Muhurat sessions are not trading days for cycles** (no decision, entry or exit on Diwali's one-hour evening
   session; its closes are not normal daily closes, panel README). Test: `test_a_muhurat_session_is_never_a_cycle_day`.
   In 2024-26 no cycle date falls on one, so criterion 7 does not depend on it.
2. **Width search with data problems:** a width whose entry prices are unusable (`unfillable`) or impossible
   (`bad_prices`) is skipped like an unlisted one, and the next narrower width is tried (entry-day data only; exit
   data never chooses the width). If no width trades: `no_trade_cap` when any width broke the cap, `missing_strikes`
   when no width was listed, else the problem of the largest listed width. Every width's outcome and modelled loss is
   kept in `widths_tried`.
3. **Worst-case exit charges:** each leg at its terminal value at the strike where the payoff loss is largest (ties: the
   larger exit charges), with the Rs 1 pads, and every order charged at least one tick (Rs 0.05), so a worst-case
   exit of a worthless leg still pays brokerage. This is a convention: charges grow without limit as the index moves
   beyond the wings, so a true worst case does not exist; the gap is about Rs 0.15 per point beyond the wing.
4. **Fills below zero:** a sold leg priced under Rs 1 fills below zero in the P&L (conservative, as the protocol's pad
   says); charges use at least one tick.
5. **Missing data:** an entry day without panel data is `unfillable`; a session the panel left out (only 30 Mar 2021,
   outside 2024-26) has no listing so it cannot be a decision day; a cycle whose exit is after the panel's last session
   is not returned (not yet complete).

## 6. Not met / not done
- Nothing in the 7 criteria is knowingly unmet.
- The judge's own hand recomputation of one real cycle per structure is theirs to do; inputs for the first 2024 cycle
  (expiry 29 Feb 2024, entry 16 Jan, exit 8 Feb, spot 22,032.30): SF legs 22050 CE/PE sold, 22350 CE and 21750 PE
  bought, net -Rs 399.52, modelled max Rs 3,420.56; SC 22450 CE / 21600 PE sold, 22750 CE / 21300 PE bought, net
  +Rs 1,123.81, max Rs 9,610.10; BF width 150 (300-200 over the cap), net -Rs 865.51, max Rs 9,947.36.

## 7. Addendum (13 Oct 2026, after judge 25 PASS): owner decision and judge 25 minors

Asked by the orchestrator: the owner's decision (`docs/DESK_DECISIONS.md`, 13 Oct: a long debit at least the width is
`bad_prices`), judge 25's report-only exit flag and its two minors.

| Item | What changed | Evidence |
|---|---|---|
| Owner decision: "cannot win" is `bad_prices` | One rule for both directions: at entry, the position's value must lie strictly inside its payoff bounds at expiry (`structures.payoff_bounds`, `position_value`). At or beyond the worst payoff = cannot lose (short credit ≥ width, long debit ≤ 0, as before); at or beyond the best payoff = cannot win (long debit ≥ width, **new**, and short credit ≤ 0, its mirror). | `test_a_long_debit_at_least_the_width_cannot_win_and_is_bad_prices[300.0, 300.05]` (299.90 still trades), `test_a_short_credit_of_zero_cannot_win_and_is_bad_prices`; real: `test_the_three_long_flies_that_cannot_win_are_bad_prices` (Jul 2024, Aug 2024, Feb 2026) |
| Status when no width trades | **Changed:** the outcome of the narrowest listed width (was: `no_trade_cap` if any width broke the cap). Why: in the 3 real BF cycles, widths 300-150 break the cap and the 100-point fly has impossible prices; the old precedence would have called them `no_trade_cap`, contradicting the decision. The narrowest listed width is where the search ended, so its problem is the reason no trade happened. | `test_wider_widths_over_the_cap_and_a_narrowest_width_with_impossible_prices_is_bad_prices`; `test_no_width_fits_is_no_trade_cap` |
| Judge 25 mirror: impossible exit closes | `CycleResult.exit_outside_payoff`: a traded exit valued beyond the payoff bounds (e.g. Jul 2024 SF: call spread 301.25 > width 300). Report only: the trade stays traded and its net counts. B3 shows it: per opportunity (`exit_outside_payoff`) and per policy (`exits_outside_payoff`, `exits_outside_payoff_net`; column "Impossible exits (count, net)" in the .md). | `test_an_exit_valued_beyond_the_payoff_bounds_is_traded_and_flagged`; `test_traded_exits_beyond_the_payoff_bounds_are_flagged` (real: 4 of 96 traded exits: SF Jul 2024 -Rs 4,024; BF Sep 2024 +7, Dec 2024 +637, Mar 2026 +1,036); `test_metrics.py::test_traded_exits_beyond_the_payoff_bounds_are_counted_with_their_net` |
| Judge 25 minor 1: exact half | 2 of 4 legs on settlement trades (flagged), at entry and at exit | `test_exactly_half_the_legs_on_settlement_is_still_fillable[entry, exit]` |
| Judge 25 minor 2: which day chooses strikes | The entry day's spot close and option chain; now written in the story (B2 design, Strikes) and the simulator docstring | `docs/stories/B-research-engine.md` |

**Side fact found while rewriting the tests:** with possible prices, a listed 100-point width always fits the cap
(at most 100 x 65 = Rs 6,500 plus about Rs 700 of costs and pads), so `no_trade_cap` can only happen when the narrow
wings are not listed.

**B3 discovery re-run** (`python -m fno research run 2026-10-12-experiment-1 --period discovery`, twice, identical
output): only the expected fields change. P3 (BF every month) -Rs 34,735 → **-Rs 32,094** (30 traded, 3 `bad_prices`;
the 3 skipped cycles had lost Rs 2,641 together); P5 and P5's opposite change through their BF branch; every policy
now shows its impossible-exit count and net (P2: 1, -Rs 4,024; P3: 3, +Rs 1,680). Discovery is reported only; no
pass/fail.

**Not done here (not mine):** the protocol text (section 4) still needs the decision written in before the freeze, as
`DESK_DECISIONS.md` says; I did not edit `PROTOCOL.md`.

Checks on this commit: `python -m pytest -q` 828 passed; `ruff check fno tests tools` and `ruff format --check` clean; `python tools/check_imports.py` clean.
