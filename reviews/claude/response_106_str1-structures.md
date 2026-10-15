# Response 106: STR1 one- and two-leg structures (claims for the judge)

Branch `story/str1-structures` (lane 1: it changes what can be built, priced, margined and checked before a trade).
Story text: `docs/stories/B-research-engine.md`, section STR1. No strategy, playbook version or trading decision is
added: the six new codes can be built and checked, but nothing uses them yet. This is round 2: the orchestrator's
conditions and `docs/JUDGE.md` quality rules 2-6 are applied below (round 1 was `62ef09a`).

## 1. Frozen files (first judge item)

**This changes files listed in experiment 1's FREEZE.md. Reproducibility rests on RUN_COMMIT `0c1c957`.**
- Changed, and listed in `research/2026-10-12-experiment-1/FREEZE.md`:
  - `fno/research_engine/structures.py` and `fno/research_engine/cycle_costs.py` (byte-identical to the freeze until
    this branch);
  - `fno/constants.py` and `fno/composition.py` (they already differed on `main`).
- `simulator.py`, `leg_prices.py` and every other frozen file are untouched.
- The orchestrator approved the change on 15 Oct (go ahead, with conditions). Each condition:
  - **(1) SF/SC/BF byte-for-byte equal.** Proven three ways, all strong evidence:
    - **(a) Overlay run, judge C's stronger option.** I made a worktree of `0c1c957` and copied STR1's
      `structures.py`, `one_side.py` and `cycle_costs.py` over it. `sha256sum -c` of FREEZE.md then fails on exactly
      those 2 listed files and passes the other 43. Then I ran both periods from that worktree:
      - discovery `814a79a56db4361d9925364642c791d0b82c6a7cb15f98fd18170cfe3353c98b`;
      - challenge `4826897ed4d7e4edf738ec49b926111eb924e3c47cf471fb0aaa73d4e6aff9b6`.

      Both equal the published hashes.
      - **Sensitivity proof:** the same run with `CONDOR_OFFSET = 0.03` planted gives challenge
        `74387d8f2abc...`, a different hash.
      - **Gotcha for whoever re-runs it:** the first run writes `research/ledger.csv`, and the next run is refused
        until that file is reset. Commands:
        ```
        git worktree add <W> 0c1c957eb49cfa3c2ea3efb6b93befa66d6b6928
        cp fno/research_engine/{structures,one_side,cycle_costs}.py <W>/fno/research_engine/
        cd <W>; for p in discovery challenge; do git checkout -q research/ledger.csv
          python -m fno research run 2026-10-12-experiment-1 --period $p; done
        sha256sum research/2026-10-12-experiment-1/results_{discovery,challenge}.json
        ```
    - **(b) In the suite:** `tests/research_engine/test_structures_match_frozen.py`.
      - It loads the frozen `structures.py` and `cycle_costs.py` from git at `0c1c957`.
      - On every cycle of 2019-26 (both periods, 90+ cycles) and every width, it checks that frozen and current code
        give identical legs, payoff bounds and max loss (more than 1,000 priced max-loss comparisons).
      - It takes about 22 s.
    - **(c)** `tests/research_engine/test_four_leg_regression.py`: the 99 discovery results equal
      `results_discovery.json` field by field.
  - **(2) The weekly study and G1 v1-v3.**
    - `research/2026-10-14-weekly-weather/study.py` imports only `fno.costs`, and STR1 does not touch `fno/costs.py`.
    - None of the 43 `fno/` files that G1 v1-v3 freeze or record is changed by STR1 (checked by script).
    - **Reported, as asked:** importing those 43 modules at HEAD does load `fno.composition`, `fno.constants` and,
      through them, `structures`, `cycle_costs` and `one_side` (`forecast_scoring/wiring.py` and others import the
      composition root). So frozen forecast code runs beside the changed files. Their results cannot change, because
      no forecast path builds a structure or prices a position. That last point is reasoning only: there is no test
      for it beyond the full suite passing.
  - **(3) Named.** This section; the story text's "Frozen files" paragraph names `structures.py` and `cycle_costs.py`.

## 2. Gap list (quality rule 2)

Requirements from the STR1 paragraph (`REPLAN_new_stories.md`), design 03 (structures and interfaces) and the
orchestrator's scope, each mapped to a criterion or marked out with a reason:

| Requirement | Where | Criterion |
|---|---|---|
| B2's `Structure` builds any number of legs | REPLAN STR1; design 03 interfaces | 1 |
| Bought options (single call, single put) | REPLAN; design 03 item 3 | 1, 3 |
| Vertical spreads, debit and credit, call and put | REPLAN; design 03 item 3; orchestrator scope | 1, 3 |
| Never a naked short leg: impossible to construct | REPLAN; design 03 item 3; orchestrator | 2 |
| C4 refuses any position whose max loss is not fixed at entry (planted attempts) | design 03 item 3; orchestrator | 4, 10 |
| C4's shape check accepts the new shapes | REPLAN | 4, 10 |
| C4's independent max loss, never trusted from the builder | REPLAN; orchestrator | 5 |
| D1's structure codes | REPLAN | 6 |
| D2's candidates | REPLAN | 7 |
| A14's margin rows (bought options, verticals) | REPLAN | 8 |
| Existing four-leg condors keep identical results (regression on golden values) | orchestrator | 9 |
| No frozen file changed, or stop and report | orchestrator | section 1 (reported, approved with conditions) |
| Protected four-leg structures stay allowed | design 03 item 3 | 9 |
| Response 92's put spread about 3% below spot | response 92 | **Out:** PCS sells the ATM put. A 3%-out variant is a new code or a spec field: owner choice |
| Anchor check for SF/SC/BF | (same gap as before STR1) | **Out:** a separate C4 change; their leg relations are still checked |
| Straddles/strangles (V2 "straddles within the cap"), ratios, calendars | design 03 V2 | **Out:** not in STR1's paragraph; a later story |
| Any strategy or research run using the new codes | REPLAN ("no new strategy") | **Out:** a registered trial first (data spent) |
| Broker check of the new A14 rows | judge 77 | **Out:** the owner's check. The rows are held, not written, until it is listed in config |
| E4 fills/exits, E5 exits and scorecards with 1-2 legs | design 03 (desk) | **Out:** not changed or tested. I believe they are leg-generic, but that is reasoning only |

## 3. Acceptance criteria, broken-code proof and cases (quality rules 4 and 5)

The mutation command for every row:
`python /tmp/.../scratchpad/mutate.py <id>`. The script is reproduced in section 7. Each mutation is planted, its test
is run, and the file is restored. Result: **all 17 fail their test.**

| # | Claim | Code | Test | Mutation that makes it fail | Cases (positive / negative / boundary / empty) | Evidence |
|---|---|---|---|---|---|---|
| 1 | Each code builds from ATM; None when unlisted; bad width raises; SF = CCS+PCS, BF = CDS+PDS | `one_side.py:20-46`, `structures.py:90-108` | `tests/research_engine/test_one_side.py` (first 5), `tests/research_engine/test_structures.py` | 1: flip OTM direction; 1b: ATM tie goes higher | pos: 8 code-width pairs. neg: widths -50, 0 for spreads. boundary: ATM tie at spot 24,025 takes 24,000; width 0 for LC/LP. empty: empty chain and one-strike chain give None | strong |
| 2 | No structure returns a naked short leg; B2's cost model refuses one (so C2 does too) | `structures.py:63-72,107`, `cycle_costs.py:65` | `test_one_side.py::test_no_structure...`, `::test_the_cost_model_refuses...` | 2a: drop the `legs` check; 2b: drop the `max_loss` check | neg: 5 planted shapes (short call; short put; short call over a bought put; ratio call spread; condor missing a wing). boundary: equal sold and bought per type passes (all 9 codes) | strong |
| 3 | `payoff_bounds` covers 0 to unbounded; four-leg bounds unchanged | `structures.py:75-82` | `test_one_side.py::test_a_bought_call...`, `::test_a_vertical...`, `::test_four_leg_bounds...` | 3: no upper infinity; 9b: level -500 | pos: LC (0, inf), LP (0, K), verticals (0, w) and (-w, 0). boundary: 15 four-leg cases equal the old formula | strong |
| 4 | C4 shape check per code; `bounded_loss` refuses every planted naked short whatever the code | `validity_shapes.py:23-104`, `validity.py:103-112`, `validity_money.py:74-78`, `checks/wiring.py:55-70` | `tests/checks/test_validity_shapes.py` | 4a: drop the vertical width check; 4b: `bounded_loss` always ok | pos: 6 codes accepted. neg: 9 wrong shapes, 5 naked shorts through the full checker. empty: unknown code fails | strong |
| 5 | C4's max loss equals B2's to the paisa for each new code; a correct trade passes all of C4 | `validity_money.py` (unchanged) | `test_validity_shapes.py::test_a_correct_trade...` | 5: C4 pad 1.01 | pos: 6 codes, difference < 0.01. boundary: Rs 1 tolerance (existing C4 test) | strong (fixture quotes) |
| 6 | D1 accepts the six codes; width 0 only for LC/LP; refuses non-finite, negative and bool widths and unknown codes | `vocabulary.py:34`, `structure_spec.py:39-63` | `tests/playbook/test_one_side_codes.py` | 6: refuse 0 for LC/LP | pos: 6 codes. neg: 0 for 7 sold-leg codes, -50, XS, nan, inf, True. boundary: 0 and -0.0 (read as 0.0) | strong |
| 7 | D2 builds each new code at the widest width within the cap and names each refused width | `playbook/wiring.py:86`, `composition.py:220-232` | `test_one_side_codes.py::test_d2_builds...`, `::test_d2_skips...`, `::test_d1_c4_d2_and_a14_know_the_same_nine_codes` | 7: drop CCS from the tradable list | pos: 6 codes. boundary: credit spreads fall back 300 to 200 at the cap. neg: ATM LC over a Rs 5,000 cap, named | strong |
| 8 | A14 rows equal hand values (LC/LP also at width 0); rows of uncovered codes printed, not written, exit 0; config list strict; C2/C4 accept margin 0 and width 0 for LC/LP only | `nse_margins/rows.py:49-70`, `job.py:107-121`, `independent_check.py:29-55`, `nse_margins/wiring.py:37-41`, `risk/inputs.py:66-80`, `risk/margins.py:66-119,189`, `checks/validity_margin.py:79` | `tests/nse_margins/test_one_side_rows.py`, `tests/risk/test_bought_only.py`, `test_validity_shapes.py` (margin), `tests/checks/test_validity_anchor.py::test_a_bought_option_with_a_zero_margin_row...` | 8a: write uncovered rows; 8b: C2 refuses 0; 8c: C4 refuses 0; 8d: C2 refuses width 0 | pos: 6 hand rows; LC margin 0 end to end through C4. neg: CDS/PDS/SF at 0 refused; a string, empty list or unknown code in config refused. boundary: margin exactly 0. empty: missing config list means SF/SC/BF | strong for the arithmetic. **Reasoning only** that NSE/Groww block no margin on a long option |
| 9 | Four-leg results unchanged | n/a | section 1 (a)(b)(c); `tests/research/test_experiment_1_frozen.py` | 9a: condor offset 0.03 (also changes the overlay hash) | pos: 2 published hashes; 99 discovery results; every 2019-26 cycle | strong |
| 10 | C4 refuses a new-code trade off the snapshot's ATM anchor, or with no spot; four-leg trades need no spot, as before | `validity_evidence.py:51-58`, `validity_shapes.py:89-93`, `validity_modes.py:37` | `tests/checks/test_validity_anchor.py` | 4c: anchor always ok | pos: 6 codes at ATM pass. neg: 4 off-anchor trades. boundary: spot 25,024.99 / 25,025 / 25,025.01. empty: no spot, no usable quote, other expiry give no ATM, and the trade fails | strong |

**Mutation results (planted 15 Oct 2026, each restored):** 1, 1b, 2a, 2b, 3, 4a, 4b, 4c, 5, 6, 7, 8a, 8b, 8c, 8d, 9a and
9b all fail their test.

One mutation needed a fix. My first 9a (flip the ATM tie rule) **passed** the real-data regression tests, because no
real entry day has its spot exactly halfway between strikes. Two changes:
- the tie rule is now listed under criterion 1 as 1b, pinned by the tie unit tests (which do fail);
- 9a is now a mutation that changes real results (condor offset 0.03).

## 4. Self-review by independent agents (quality rule 3)

I ran two agents on `22e33fd..62ef09a`: one for correctness, one for silent failures. Neither found a blocking bug.

**Correctness agent.** It confirmed by running the code:
- the legs and strike direction of every code;
- every shape's bounds, and that SF/SC/BF bounds are unchanged;
- that B2 and C4 agree on the worst level and its exit charges;
- that zero margin cannot reach a code with a sold leg.

Its findings and what I did:
- *Should-fix:* `structures: LC` (a string) was read as `{L, C}`, so every row was held silently. **Fixed:** anything
  but a non-empty list of known codes now raises (`independent_check.py:47-55`, 4 tests).
- *Nit:* LC's width was not tied to the leg's strike. **Fixed** with the anchor check (criterion 10).
- *Nit:* D1 accepted `[nan]` (this predates STR1), and `-0.0` printed as "-0". **Fixed:** non-finite widths are refused,
  and -0.0 is read as 0.0.
- *Nit:* exact float equality on widths. **Not changed:** NIFTY strikes are multiples of 50 and exact in binary, the
  same as before STR1.
- *Nit:* held rows for a past day are never back-filled. **Not changed:** see below.
- *Note:* D2's widest-first order means `[300, 0]` for LC always picks 300, the cheapest. **Not changed:** this is D2's
  existing rule. Playbook authors must order widths knowingly; I flag it to the owner.

**Silent-failure agent.** Its findings and what I did:
- *Should-fix:* C4 never checked the strike for LC/LP, or the ATM anchor of a spread. **Fixed:** criterion 10. C4 now
  re-derives the ATM strike from the committed snapshot's spot (the same meta `spot` that D2's market is built from)
  and its A4-usable strikes. The trade fails if C4 cannot tell.
  - **Remaining limit:** D2's chain also drops quotes without an implied volatility. If the true nearest strike had no
    IV, C4 would refuse a trade D2 built. That fails closed, so it is safe, but it is untested on live data.
  - SF/SC/BF keep their old relation-only check (out of scope, see the gap list).
- *Should-fix:* held rows are lost for good with no alert. **Partly rejected:**
  - Nothing is lost that matters. The SPAN file stays archived in Drive, and a row is only usable for 7 days, so after
    the owner's broker check the job writes fresh days from the next run.
  - A daily alert until the owner acts would be noise on #fno-desk. The held codes are named in the job's printed line
    every run.
  - **Owner choice** if you want one #fno-desk line instead.
- *Should-fix:* no test kept the code lists in step, and D2 would crash with a KeyError on a drift. **Fixed:**
  `test_d1_c4_d2_and_a14_know_the_same_nine_codes`.
- *Nit:* the config type problem: **fixed**, as above.
- *Nit:* C4's zero-margin branch was untested end to end. **Fixed:**
  `test_a_bought_option_with_a_zero_margin_row_passes_c4_end_to_end`.
- *Nit:* `NakedShortLeg` is not caught in D2. **Not changed:** the wired structures cannot raise it, and a crash is the
  right reaction to a code bug.

## 5. Real output (quality rule 6)

Made by `python research/2026-10-15-str1-samples/samples.py`, a dry run of the committed code. Full output:
`research/2026-10-15-str1-samples/output.txt`.
- **Historical example:** entry-day closes of the last discovery cycle. No exit or P&L is computed: that would be an
  unregistered trial on spent data. I removed one such line from my first draft for that reason.
- **C4 and D2** rows come from the test fixture chains.

```
HISTORICAL EXAMPLE: entry 2026-09-16, expiry 2026-10-27, exit 2026-10-06, close 23217.6
  LC width 300: buy 23500 CE @ 312.35; payoff bounds (0, inf); modelled max loss Rs 20,489.13
  LP width 300: buy 22900 PE @ 207.75; payoff bounds (0, 22900); modelled max loss Rs 13,687.07
  CDS width 200: buy 23200 CE @ 478.8, sell 23400 CE @ 363.7; payoff bounds (0, 200); modelled max loss Rs 7,895.26
  CCS width 200: sell 23200 CE @ 478.8, buy 23400 CE @ 363.7; payoff bounds (-200, 0); modelled max loss Rs 5,949.11
  PDS width 200: buy 23200 PE @ 301.95, sell 23000 PE @ 235.55; payoff bounds (0, 200); modelled max loss Rs 4,708.58
  PCS width 200: sell 23200 PE @ 301.95, buy 23000 PE @ 235.55; payoff bounds (-200, 0); modelled max loss Rs 9,088.78
  B2 refusal: more CE legs sold than bought: [(25000.0, 'CE', -1)]
C4 on the test chain (spot 25,000, 14 Oct 2026 fixture):
  a short call called LC: FAIL bounded_loss: naked short ['CE']
  a short call called LC: FAIL shape: LC: the leg must be a bought CE, not sold CE
  a short call over a bought put called CCS: FAIL bounded_loss: naked short ['CE']
  a short call over a bought put called CCS: FAIL shape: CCS: needs two CE legs, not ['CE', 'PE']
D2 candidate on the evaluation test chain (spot 25,000):
  PCS: width 200: sell NIFTY26112725000PE, buy NIFTY26112724800PE; max loss Rs 8,145.15; score 0.0184
  LC: width 300: buy NIFTY26112725300CE; max loss Rs 6,270.55; score 0.0239
```

## 6. Findings for the owner (each role)

- **Risk manager / strategist: bought options barely fit the Rs 10,000 cap.** On 16 Sep 2026 (real closes):
  - a call 300 points out of the money had a modelled max loss of Rs 20,489;
  - the put 300 points out had Rs 13,687.

  Both are over the cap, and an ATM option is roughly Rs 30,000 a lot. So with this cap, Book 1 can use LC/LP only far
  out of the money. Spreads fit: Rs 4,700-9,100 at 200 wide on that day. Evidence: some (one real day) plus reasoning.
- **Risk manager: C2's "margin above 0" (judge 75) blocked every bought option.** SPAN's scan for a long option is at
  most its own value, so the margin is 0 at factor 1. Zero is now allowed for LC/LP only; every shape with a sold leg
  is still refused at 0.
- **Regulation / risk: the 14 Oct broker check (judge 77) compared four-leg rows only.** New-code rows are held (printed,
  not written) until your broker check of them passes and is listed in `config.yaml`
  `risk.margins.nse_span_check.structures`. Until then every new-code trade is refused: fail closed.
- **Strategist: response 92's put spread sold about 3% below spot; PCS sells the ATM put.** A 3%-out version needs a new
  code or a spec field: your choice.
- **Process: quality rule 9 may apply.** STR1 touches margin limits. If the orchestrator counts it as a money story, it
  needs a ChatGPT review after the judge.

## 7. Mutation script (as run; scratchpad, not committed)

It holds a list of (id, file, exact old text, new text, test node). For each entry it asserts the old text occurs
exactly once, writes the mutant, runs `pytest -q -x <test>`, prints `FAILS (good)` or `PASSES (BAD)`, and restores the
file in a `finally`. The entries are the 17 mutations named in section 3. I will commit it under
`research/2026-10-15-str1-samples/` if the judge wants to re-run it verbatim.

## Known limits

- C4's anchor check is new for the six codes only; SF/SC/BF are still checked on leg relations alone.
- E4/E5/scorecards with one- or two-leg trades: not tested (reasoning only that they are leg-generic).
- The B2 simulator can run the new codes, but no research run with them exists, and none should run on 2019-26
  without a registered trial.

## What the judge should test hardest

1. The overlay run in section 1 (a), and whether condition (2)'s import finding is acceptable.
2. Plant naked shorts at every layer: a custom `Structure`, a hand-built C2 `Proposal`, and a `ValidityProposal` under
   every code.
3. The anchor check against a real committed snapshot: does D2's spot equal C4's `meta.spot` there?
4. Recompute one vertical's max loss (B2 and C4) and one A14 row by hand.
5. Whether the zero-margin allowance can reach any code with a sold leg.

Gates on this push: `pytest -q` 3344 passed (FNO_SLACK_BOT_TOKEN unset); `ruff check` and `ruff format --check` clean; `tools/check_imports.py` clean; all 17 mutations fail.
