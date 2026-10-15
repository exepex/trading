# Response 175: story C2c code, the stressed margin multiplies the whole margin (claims for the judge)

**Branch:** `story/c2c-whole-margin-stress`. **Text:** judge 174 addendum 1 PASS (`8a9a23e9`); ChatGPT review 117
accepted C2c unchanged (response 169). **Lane 1** (money and risk). C2d's code is not in this round.

## What changed (one term, in both copies)

- `fno/risk/margins.py` (C2): `MarginParts.stressed` and `at_entry` multiply the exposure by k:
  `max(0, k x scan - NOV) + min(0, NOV) + k x exposure`, and at entry `max(0, k x scan - NOV) + k x exposure`. The STR1
  cap (`_span`) is unchanged and still bounds the SPAN part only. `record()` labels the method with
  `STRESSED_MARGIN_STRESSES` (`fno/constants.py`): "scan and exposure (owner, 15 Oct 2026; story C2c)".
- `fno/checks/validity_margin.py` (C4's independent copy): `stressed_per_lot` adds `factor x exposure`, outside the cap.
- `fno/risk/capital.py`: module text only (k stresses the scan and the exposure; the exposure is outside the cap).
- `broker_margin` (k = 1) and `initial()` are unchanged, so no figure falls below the broker's.

## Criteria

1. **The five rows to the paisa, C2 and C4** (`tests/risk/test_whole_margin_stress.py`, real 14 Oct rows, lot 65):
   SF 100 86,854.01 (at entry 92,925.01); SF 300 90,885.09 (108,019.09); SC 300 98,012.27 (108,165.27); BF 300
   85,661.75 (85,661.75); CCS 300 52,260.42 (63,567.17). The broker figures 59,899.32 / 62,679.37 / 67,594.67 /
   59,077.07 / 38,968.08 are checked too. CCS 300 by hand in `test_ccs_300_by_hand`.
2. **Against k x what C2 counts, on all 47 real rows:** SF and SC equal it; BF at least it; CCS and PCS between what C2
   counts and k x it; every code at least the broker's figure.
3. **C2 = C4:** on every real row at k 1.0 and 2.0 (new) and 1.45 (STR1b's `test_validity_capital.py`, unchanged).
   Mutations, each planted alone and reverted (each caught by at least one test):
   | Mutation | C2 (`margins.py`) | C4 (`validity_margin.py`) |
   |---|---|---|
   | exposure not stressed | caught | caught |
   | premium stressed (`k x min(0, NOV)`) | caught | caught |
   | cap applied to the exposure's stress | caught | caught |
4. **STR1:** the cap still bounds the SPAN part (`test_capital.py` credit-spread and CCS 100 tests); LC and LP stay at
   0 (no exposure; new test); never below the broker's figure (criterion 2's test, every code).
5. **Record label:** `test_manager.py` pins the new exact string.
6. **Every changed pinned figure, with its recompute** (none loosened; each is still an exact or `approx` equality):

   | Test | Before | After | Recompute |
   |---|---|---|---|
   | `test_margin_formula`: SF 100 stressed at 1.45 | 1.45 x 822.25 + 59,077.07 | 1.45 x (822.25 + 59,077.07) = 86,854.01 | credit: exactly k x what C2 counts |
   | `test_margin_formula`: BF 100 stressed at 1.45 | 59,077.07 | 1.45 x 59,077.07 = 85,661.75 | max(0, 1.45 x 831.35 - 6,071) = 0, plus k x exposure |
   | `test_margins`: SF 200, scan 4,000, NOV -6,000, exposure 50,000, k 1.5, 2 lots, at entry | 124,000 | 174,000 | (max(0, 6,000 + 6,000) + 1.5 x 50,000) x 2 |
   | `test_margins`: same, netted | 112,000 | 162,000 | (12,000 - 6,000 + 75,000) x 2 |
   | `test_validity_limits`: C4 SF 200 (scan 9,000, NOV -10,270, exposure 65,000) | 78,050 | 107,300 | 1.45 x 9,000 + 1.45 x 65,000 |
   | `test_validity_limits`: plus SC 100 (scan 7,500, NOV -1,650) | 78,050 + 75,875 | 107,300 + 105,125 | 1.45 x (7,500 + 65,000) |
   | `test_capital`: CDS 200, PDS 300 at entry | exposure 29,538.53 | 1.45 x 29,538.53 = 42,830.87 | the premium is still not stressed; the old "before STR1b" difference (0.45 x debit) still holds after adding the exposure's 0.45 x 29,538.53 |
   | `test_capital`: LC 0, LP 300 at entry | 0 | 0 | no exposure |
   | `test_capital`: CCS/PCS 100 and 300 at entry | capped SPAN + exposure | capped SPAN + 1.45 x exposure | cap unchanged |
   | `test_capital`: CCS 100 by hand | 6,893.25 + 29,538.53 | 6,893.25 + 42,830.87 = 49,724.12 | |
   | `test_capital`: SF/SC/BF, 15 real rows | `+ exposure` | `+ K x exposure` | renamed "uncapped" (no longer "unchanged") |
   | `test_capital`: the stress reserve (new test) | LC, LP 0; CDS, PDS 0 (STR1b) | LC, LP 0; CDS 200, PDS 300, CCS 100 13,292.34 | 0.45 x 29,538.53, the exposure's stress outside the cap |
   | `test_manager`: record label | "scan risk only (judge 75)" | "scan and exposure (owner, 15 Oct 2026; story C2c)" | |
7. **Gates:** see "Gates" below.

## Builder self-review (quality rule 3)

One independent review agent, run on 16 Oct 2026 after judge 181. It was given only the diff (`b4276375..01d39e4d`),
the passed text and these claims, not my reasoning. It found:

1. **Correctness: none found.** It traced all four places that compute a margin from the rows (`stressed`,
   `at_entry`, `broker_margin` = `at_entry(1.0)`, C4's `stressed_per_lot`) and found no other consumer. It recomputed
   CCS 300 (52,260.42 and 63,567.17) and C4's 107,300 and 105,125 by hand. It also checked that "between initial and
   k x initial" holds for CCS and PCS by algebra, not only on the fixture.
2. **Should-fix, accepted after checking:** `capital_at_entry`'s `stress_reserve` (margin at entry minus the
   broker's) now includes `(k - 1) x exposure`. That contradicts STR1b's written reserve: "LC, LP, CDS and PDS have
   stress_reserve 0", and CCS/PCS "at most width - credit". My recompute: CDS 200 42,830.87 - 29,538.53 = 13,292.34,
   the same for PDS 300 and CCS 100; LC and LP 0. My test rename ("... on its premium") hid the change instead of
   stating it. **Fixed:** a new test pins each reserve
   (`test_the_stress_reserve_is_the_capped_span_extra_plus_the_exposure_s_stress`); CDS and PDS's at-entry figure is
   pinned as a number (42,830.87), not only as an identity; STR1b's text gets a "since C2c" note on the reserve and on
   its criterion 1 (no criterion rewritten); and this file states the effect:
   - **The recorded reserve:** `capital_rs.stress_reserve` and scoreboard B's `stress_reserve_days_rs` grow by
     `(k - 1) x exposure` for every code with exposure (all but LC and LP).
   - **What does not change:** `capital_tied` (broker margin plus premium), so scoreboard B's denominator is unchanged.
3. **Tests loosened: none found.** It recomputed every changed figure and planted the same six mutations, all caught.
4. **Stale text, minor, fixed:** a one-line "superseded by C2c" note in C2's story (judge 75 paragraph), A14's story
   (judge 75 bullet) and STR1b's reserve text; the `test_margin_formula.py` docstring re-wrapped.
5. **Code standards: none found.** `fno/constants.py` is at 344 of 350 lines, so the next constant needs a split.
6. **Design note (no fix):** stressing a debit spread's exposure reserves cash the position cannot lose. It models
   the broker blocking more margin in a crisis, which is the owner's "whole margin" decision. I agree.

## What the owner should know (reasoning, from the story)

Every stressed margin rises about 45% at k = 1.45, so about 31% fewer lots fit the same paper capital (1 - 1/1.45).
Groww's own margin is unchanged; this is C2's crash buffer, now working as it was measured.

## Gates

On the final tree after the self-review fixes: `python -m pytest -q` 6,158 passed (12 min 36 s); `ruff check fno
tests tools` and `ruff format --check` clean; `python tools/check_imports.py` clean; `python tools/check_records.py`
clean (6,016 files). The first round (01d39e4d) gave 6,153 passed; the 5 new tests are the reserve test's cases.
