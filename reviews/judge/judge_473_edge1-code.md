# Judge 473: EDGE1 code, freeze and protocol revisions 4-6

**Scope:** story/edge1-build at 3152ed44 (FREEZE.md; code frozen at b4a9a855), builder session_01UkTaDeTRF9ksDgQB9cTU5C.
It covers protocol revisions 4-6, the 19 study files, the two shared engine changes and the tests. Round 1 of 2.

**Verdict: PASS.** Nothing blocking, nothing to fix. Three conditions apply to the runs (none needs a code change).

## Gates (my run, on 3152ed44)
- pytest `-n auto`: 9904 passed, 16 xfailed.
- `ruff check` and `ruff format --check`: clean (research/edge1 included).
- `check_imports`: clean.
- Freeze hashes: all 21 FREEZE.md hashes (PROTOCOL, LOT_CHECK, 19 .py) and the 2 shared engine hashes match the
  files. b4a9a855..3152ed44 adds FREEZE.md only.

## Checked
- **Shared engine changes.** Neither changes an existing caller: `ShortCondor(offset)` defaults to CONDOR_OFFSET, and
  `resampled_means(block=)` defaults to BLOCK_LENGTH. Apart from these two files, the code this study imports is
  identical on origin/main today (config.yaml, costs, research_engine, factory, scoreboard, itm_chance, research_data,
  price_ranges, fo_bhavcopy, nse_margins).
- **Seal (rev 3 and 468.4).** Rows are cut at load, then relabelled; the NIFTY panel is sealed, then relabelled. The
  order is correct as read; no test covers it, which the builder states as gap 1. Run 1's settlement is called only
  for expiries on or before the seal.
- **Expiry relabel (rev 6).** It is keyed by the future's (year, month). Every move named (28 Jun 2023, BANKNIFTY
  Mar 2024 and Jan 2025, Tuesday Sep 2025) stays inside its month, because "last X of the month" never crosses one.
  Options move only on days when a future carries their date, so weeklies are untouched.
- **Lots (rev 5).** UDiFF starts on 1 Jan 2024, so NIFTY's 2024 changes (50 to 25 to 75) and BANKNIFTY's (15 to 30
  to 35) come from NewBrdLotQty, not the schedule. The legacy schedule matches NIFTY 75 then 50 from Jul 2021, and
  BANKNIFTY 20, then 25 from Jul 2020, then 15 from Jul 2023. A trade keeps its entry day's lot.
- **Trades.**
  - Entry happens only if every leg traded, at the widest width that fits the cap.
  - SL2 fires at 3 x credit and TP50 at 0.5 x credit, strictly between entry and the T21 day, on fully traded days.
  - EXP trades have no exit pad, and settlement STT falls on long ITM legs only (`fno.costs`: closing side sell).
- **Statistics.**
  - G1 = the t-bound on sd_gross minus cost minus `Tail.extra_loss`, the same as `MeasuredGross.edge` in `factory
    screen`.
  - p is re-centred, with +1/(B+1); Holm runs across both indices; k is fixed by sorted names; the floors are 30 and
    20.
  - The nomination's 4 conditions match section 11. Ordering by raw p equals ordering by Holm-adjusted p.
  - Expected run-2 cycles = 44, which matches the probe.
- **Rev 4 (card order).** It follows the factory's own gate order (G1, then G2, then G3); measurements are cards with
  `measurement: yes`.
- **Owner's block-2 line** (section 10, lines 192-193) and the 468.3 against-cap rows: present.

## Plants: 14 of my own, 4 caught
- **Caught:** narrowest width first; panel options not relabelled; lots not relabelled.
- **Equivalent on real data** (they cannot change any result):
  - trigger allowed on the T21 day (same close, label only);
  - run-1 decisions to 14 Feb 2023 (the expiry filter drops them all);
  - lot change `>` instead of `>=` (no expiry falls on the 1st).
- **Survived on decided figures; the current code is correct, as read above:**
  - tail at 3x instead of 2x (G1);
  - G1 bound on sd_net instead of sd_gross (G1);
  - settlement STT sides swapped (EXP net);
  - nomination's run-1 mean on all trades instead of complete ones;
  - RUN1_YEARS 3 (G3's frequency).
- **Survived on report figures only:** p without +1; drawdown unsorted; against_cap dropping trigger exits.

These survivors are not a should-fix. The code is frozen, so any edit breaks the guard's hash, and no normal run
reaches them. Tests are outside the guard, though, so the builder can add the five decided-figure tests without a
re-freeze. Recommended, not required.

## Conditions on the runs (no code change)
1. **Both runs on the frozen engine.** `fno/`, `config.yaml` (its `charges` table, read at run time) and the shared
   files must be byte-identical between the run-1 and run-2 commits. Never merge `main` into the branch between the
   runs; the guard does not check these files. At reproduction I check `git diff <run1> <run2> -- fno config.yaml`;
   a non-empty diff means run 2 is invalid.
2. **Copy G1 inputs exactly.** Each card's G1 inputs are copied from selection.json's `g1.inputs`: `mean_gross`,
   `sd_gross` (not `sd_net`), `n`, `mean_cost`, `tail_share`, `tail_mean_loss`. I check every card against
   selection.json at reproduction.
3. **Probe stays out of the frozen folder.** Gap 2 (the probe outside the repo) needs no commit: run 1's
   `cycles`/`not_taken` figures restate its counts. A probe committed under research/edge1 would need a hash
   (re-freeze).

**Next:** run 1. I reproduce selection.json byte for byte and check the cards; then run 2.
