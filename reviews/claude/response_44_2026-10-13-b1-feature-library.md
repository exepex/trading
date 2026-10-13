# Response 44: story B1 (feature library), builder's claims

Builder session for story B1 (GitHub issue #30). Code commits: `6430d45` (merged into `main` as `fa80701`) and `30c0cfb` (the sweep requires all 20 F1 values to be real).
Checks on the merged head: `python -m pytest -q` 669 passed; `ruff check fno tests tools` clean; `ruff format` applied;
`python tools/check_imports.py` clean (148 files); `tests/test_code_size.py` passes (largest new file 137 lines).

## What was built

| File | What |
|---|---|
| `fno/research_engine/features.py` | `Feature` interface (`name`, `known_at`, `value(data, decision_day, context)`), `ResearchData` (panel + events), `DecisionContext` (expiry, entry day, exit day), `available_at` (when a session's closing data exists) |
| `fno/research_engine/implied_vol.py` | `ImpliedVolModel` strategy: `Black76` (F1) and `SpotBlackScholes` (comparison); bisection between 1% and 200%, `None` outside or at a bound |
| `fno/research_engine/volatility_features.py` | F1 `AtmIvMinusRealised`, F2 `VixAboveMedian`, `atm_strike`, `traded_close` |
| `fno/research_engine/close_series.py` | daily close series without muhurat sessions; realised volatility; last valid values |
| `fno/research_engine/event_features.py` | F3 `ScheduledEventInWindow`, only through `fno.research_data.events.in_window` |
| `fno/research_data/panel_reader.py` | reads A3's panel back (`read_nifty_panel(folder, years, keep)`); a left-out session stays listed with no closes. No reader existed (`panel_store.py` only writes); this one sits next to the writer and reuses its file names (`MANIFEST_FILE`, `TABLE_FILE`) and column lists (`panel_rows.TABLE_COLUMNS`), so the format is defined once |
| `fno/composition.py` | `build_features(cfg)` (F1 wired to `Black76` and `risk_free_rate`), `load_research_data(years, keep)` |
| `fno/constants.py`, `fno/storage/wiring.py` | feature names, `SESSION_CLOSE_TIME` 15:30, `OPTION_CALL/PUT`; `EVENTS_FILE` path |
| `tests/research_engine/lookahead_harness.py` | the reusable look-ahead harness (`assert_no_lookahead`, perturbers) |

## Design choices to check (each is a decision, stated, not hidden)

1. **Black-76 vs "fno.analytics.implied_vol" (the conflict the orchestrator named).** Resolved by design: F1 takes an
   `ImpliedVolModel` (strategy interface) chosen in the composition root. `Black76` uses the same-expiry NIFTY future's
   close as the forward and the rate only to discount. `SpotBlackScholes` delegates pricing to
   `fno.analytics.bs_price` (the module the story text named) and is kept as the comparison that shows why it is not
   used. Evidence, 12 Oct 2026, ATM strike 22350 (strong evidence, real panel rows):

   | Expiry | Black-76 call / put IV | gap | Spot BS 6.5% call / put IV | gap |
   |---|---|---|---|---|
   | 27 Oct 2026 | 14.51 / 14.47 | +0.04 | 13.41 / 15.41 | -2.00 |
   | 23 Nov 2026 | 14.39 / 14.51 | -0.11 | 13.67 / 15.06 | -1.39 |

   All 11 strikes within 300 points of ATM (Oct expiry) whose call and put each traded 1,000+ contracts agree within
   0.26 points under Black-76. Tests: `test_implied_vol.py::test_call_and_put_iv_agree_within_half_a_point_at_the_atm_strike_on_12_oct_2026`,
   `::test_black76_agrees_within_half_a_point_at_every_liquid_strike_near_the_money`.
   The existing `fno.analytics.implied_vol` was not changed (its bounds are 0.01%-500% and it never returns `None` at a
   bound, so it does not meet the story's solver rule either).
2. **The forward must have traded.** `Black76.underlying` uses the same-expiry future's close only if its volume > 0
   (the story's "settlement is not used for features" applied to the forward); otherwise F1 is `None`.
3. **ATM IV = mean of the call IV and the put IV at the ATM strike**, in volatility points. The story says F1 needs both
   legs but not how they combine; the mean is my choice (reasoning only). F1 = that minus realised, both in points.
4. **ATM strike** = nearest listed strike (any row of that expiry that day, traded or not) to the Nifty 50 close; tie
   to the lower. The leg must then have traded, else `None` (the story's rule; spot is the story's reference for ATM,
   not the forward).
5. **The first argument is `ResearchData` (panel + events), not the panel alone.** F3 must read events; putting them in
   the same object means the harness changes every input a feature can read. `DecisionContext` holds only the
   cycle's dates.
6. **Muhurat sessions** are left out of every close series and are never decision days (`None`): their closes are not
   normal daily closes (panel README). Special weekend sessions count as normal sessions.
7. **A session the panel left out (only 2021-03-30)**: F1's 21-close window must be 21 consecutive sessions with
   valid closes, so F1 is `None` while the window spans 2021-03-30 (a two-day return would bias realised volatility);
   F2 takes the previous 250 *valid* closes, skipping it (a median only loses one sample). Tests:
   `test_f1_is_none_with_fewer_than_21_valid_closes`, `test_f2_is_none_with_fewer_than_250_valid_previous_closes`.
8. **Availability times.** Panel rows of a regular or special session are available at 15:30 IST that day; muhurat at
   the end of the day. F1-F3 declare `known_at` = decision day 15:30. Events: A6's dates are days, so a scheduled
   event's date counts as known from the start of `announced_on`; an unscheduled one only from its own date.
9. **Rate** comes from `config.yaml` `risk_free_rate` (0.065, as the story says), wired in the composition root, so
   B5's freeze must hash `config.yaml` as a whole, not only the charges block (it only discounts under Black-76).

## Criteria

| # | Criterion | Evidence | Status |
|---|---|---|---|
| 1 | Any panel value after the decision day changed: result unchanged, all three features, 20 random days | `test_lookahead.py::test_every_feature_is_unchanged_by_data_after_its_cutoff_on_20_random_days`: 20 days drawn with seed 20261013 from the 202 decision days 15 Jan 2025-10 Sep 2026 on the real panel (2024-26, options 28-47 days to expiry) and the repository events; every session after the cutoff has its closes scaled or removed, every option and future row of those sessions repriced, one leg in ten removed, legs made untraded, extra strikes added, events not yet known moved and 4 invented events added. all 20 F1 values (from -11.01 to 4.31 points) and all 20 F2 values (14 `True`, 6 `False`) are real values, so it never compares `None` with `None`. F3 is `False` on all 20 random days, so `test_f3_is_unchanged_on_days_with_a_known_meeting_in_the_window` adds 3 real days where F3 is `True` (14 Jul, 22 Sep, 24 Nov 2025) | met |
| 2 | Three sample days equal hand values (F1 to 0.01 points) | `test_features_real_days.py`: 12 Mar 2025, 22 Sep 2025, 16 Sep 2026 recomputed in the test straight from the panel's CSV rows with an independent Black-76 and bisection (not fno's reader or models), and pinned: F1 3.74 / 2.31 / 4.43, F2 False / False / True, F3 False / True (RBI 1 Oct 2025) / False. Also the hand-built panel: `test_f1_equals_the_hand_calculation` (ATM IV (18+16)/2 = 17, realised 0.01 x sqrt(252) = 15.87, F1 1.1255) and the F2 median tests | met |
| 3 | Missing or untraded ATM leg, solver failure, < 21 closes: F1 `None`; < 250 VIX closes: F2 `None` | `test_volatility_features.py`: `test_f1_is_none_for_a_missing_or_untraded_atm_leg` (CE and PE), `test_f1_is_none_when_the_solver_fails_or_hits_a_bound` (price above the discounted forward, a 250% price, a 0.5% price), `test_f1_is_none_with_fewer_than_21_valid_closes`, `test_f1_is_none_without_a_traded_same_expiry_future`, `test_f2_is_none_with_fewer_than_250_valid_previous_closes`, muhurat and non-session days | met |
| 4 | The harness also mutates same-day data after the cutoff (15:00 for live versions) | No live feature exists yet (B7 builds them), so the proof uses test features: with a 15:00 cutoff the harness changes the decision day's own closes (stamped 15:30): `test_a_live_cutoff_changes_the_decision_days_own_closing_data` shows F2 declared as a 15:00 feature is caught on 5 days, and a correct 15:00 feature reading only earlier sessions passes. The harness also catches a daily feature reading the next close and an F3 that ignores announcement dates (`test_the_harness_catches_a_feature_that_reads_data_after_the_decision_day`), and refuses to pass when nothing follows the cutoff (`test_the_harness_refuses_to_pass_when_nothing_follows_the_cutoff`). B7 plugs its 15:00 snapshots in as an extra perturber | met for the harness; the live features themselves are B7 |
| 5 | An event announced after the decision day is ignored | `test_event_features.py::test_f3_ignores_an_event_announced_after_the_decision_day` | met |
| 6 | F3 only through `known_on`/`in_window`; ignores 22 May 2020; sees the Feb 2022 meeting at 9 Feb when deciding on 10 Jan 2022 | `test_f3_ignores_the_unscheduled_22_may_2020_rbi_decision`, `test_f3_sees_a_moved_meeting_at_the_date_known_on_the_decision_day` (window to 9 Feb: true; to 8 Feb: false; after the 6 Feb move a window to 9 Feb: false, to 10 Feb: true), `test_f3_reads_events_only_through_story_a6s_in_window` (AST check: no event field read in `event_features.py`, calls `in_window`) | met |

## One real day for a calculator (16 Sep 2026, expiry 27 Oct 2026, 41 days, T = 41/365)

- Nifty 50 close 23217.60 -> ATM strike 23200. Call close 478.80 (volume 4006), put close 301.95 (volume 5930).
- Same-expiry future close 23370.60 (volume 6308). Rate 0.065.
- Black-76 IVs: call 12.563, put 12.317, mean 12.440 points.
- Last 21 Nifty 50 closes (18 Aug to 16 Sep 2026): 24154.90, 24078.30, 24231.85, 24252.00, 24219.05, 24334.55,
  24207.75, 24090.85, 24175.65, 24080.40, 24055.80, 23914.45, 23873.45, 23897.70, 23779.15, 23635.10, 23431.50,
  23477.80, 23398.10, 23118.60, 23217.60 -> realised 8.006 points.
- F1 = 12.440 - 8.006 = 4.43.

## Not met, limits and findings (read these)

1. **F2 cannot be computed for most of 2019, F1 not before about 31 Jan 2019.** The panel starts on 1 Jan 2019; F2
   needs 250 previous valid VIX closes, reached only about early January 2020. Experiment 1's challenge period is
   2019-2023, so every 2019 cycle has F2 = `None` ("condition not met"), which silently changes what P-policies using
   F2 do in 2019. Root fix: add 2018 Nifty 50 and India VIX closes (NSE's index-close files; not option outcomes) to the
   research data before B5's freeze. That is an A3/A1 data extension, outside B1: the orchestrator is raising it as
   its own data story (2018 index closes for Nifty 50 and India VIX).
   Some evidence (arithmetic on the session count).
2. **F3 is rarely true under the protocol's dates.** On the 202 real decision days of 2025-26 with a 30-45 day monthly
   expiry, entry next session and exit 21 days before expiry, a known event falls in the window on 41 days (20%):
   the window (about 10-24 days) mostly misses the bi-monthly RBI meetings. Budget 2025 (1 Feb) was not known on the
   January 2025 decision days because its official announcement date is 30 Jan 2025 (A6's late bound). Strong evidence
   for the count; it matters for any policy conditioned on F3 (few cycles).
3. **The look-ahead harness changes the data that was loaded.** The real-panel test loads options 28-47 days to
   expiry (192,487 rows; loading all four million rows takes about 20 s and 1 GB); features read only the cycle's
   expiry, so rows outside the slice cannot reach them. The hand-built tests cover the rules on full chains.
4. **No 2019-2023 market data was opened by this work** (for B5's access attestation): the tests and my checks read the
   2024-2026 panel files and the manifest; the only pre-2024 inputs are A6's events (2020 and 2022 meetings, criterion 6).
5. `read_nifty_panel` over the whole panel takes about 20 s (stdlib csv; pandas is not a dependency). Fine for a
   research run; B3 should load once and pass `keep` for the monthly expiries.
6. Times are IST without a time zone, as elsewhere in the repository.
