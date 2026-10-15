# Judge 102: P1, the F&O data catalog: dashboard `story/p1-data-catalog` 3cf4baa7a8bf84df454a6dc4274e5021957d4958 and trading `story/p1-data-catalog` c083b4b36487465bf357868f7b71e96aacf11e65 (lane 1 in both, response 102)

Judge B.

**What I did:**
- **Read:**
  - the story text first (quality rule 1);
  - the claims file;
  - all six `fno-*.yaml` schemas and the paths file in full;
  - the 17 examples, the dashboard check tools, the trading test and pin, and the REPLAN row.
- **Checked against:**
  - design v2 4.1, 4.4, 2.3, 3.1-3.2, 5, 6.2 and 8.3;
  - the owner's rows: contract A, P1 into slice A, the five screens, "4 A", cards in Drive, privacy, and the 14 Oct isolation conditions;
  - the built S2 code.
- **Pin:** hashed every pinned file against the dashboard at 3cf4baa.
- **Planted mutations:** 9 in the dashboard schemas and 3 in trading.
- **Mockups:** rebuilt 39 and 40 and looked at two screenshots.
- **Gates:** ran both repositories' gates, plus a trial merge of trading with `main`.

## Gates

| Where | Result |
|---|---|
| Trading at c083b4b (Slack token unset) | 3,187 passed; `ruff check`, `ruff format --check` (706 files) and `check_imports` clean |
| Trading, trial merge with `origin/main` | clean merge; 3,187 passed; same checks clean |
| Dashboard at 3cf4baa | `check_code_size` passes. `npm ci`, typecheck clean, `npm test` 465/465, `npm run build` compiles. `check_mapping`, `check_contract` (with openapi-spec-validator installed: "OpenAPI 3.1 valid ... every planted break caught"), `render_catalog --check`, `examples --check`, `check_fno_screens` (231 leaves, 25 built, 21/21 planted) and `render_fno_catalog --check` all exit 0 |
| Dashboard `main` | Has not moved since the branch base 5a6a2a1. No existing check tool was changed; the diff adds four new files under `tools/api/` and two CI steps |

## Checks the orchestrator asked for

| # | Question | Result |
|---|---|---|
| 1 | Live strikes, entry ranges or internals? | Keys are clean: the internal-word scan passes and my free-text scan finds no thresholds or model names. Live fields carry `x-visibility: owner`, but changing the card's `trade` or `objections` to public is caught only because the generated table goes stale; regenerating the table passes (should-fix 3). The mock TRADE card uses a real upcoming contract (NIFTY 29 Dec 2026, 22,600/22,450 PE, Rs 52-58); see minor 1 |
| 2 | Pin byte-equal; what moves it | All 33 pinned files have SHA-256 equal to the dashboard at 3cf4baa and to `pin.json`. 3cf4baa is a branch commit, so the merge order must be fixed (condition C1) |
| 3 | The 25 fillable fields | Every `x-record` exists here. The type test catches my retype of `TradeLine.gross` to `str` and my rename of `CheckReport.ok`; a byte change in a pinned schema fails 4 tests. One mapping needs a value translation: `family` (rule, hybrid, ai) comes from `paper_account:book` (book1_rules ...); minor 2 |
| 4 | v4 fields provisional | PARTLY: see should-fix 1 |
| 5 | W10/W11 checks unchanged and passing | MET. No existing check file changed, and all of them pass. The new tag keeps the F&O screens out of the `blocks` rules by design, with its own checks |
| 6 | Mockups 39 and 40 | MET. Rebuilt twice, with no byte change (`git status` clean); `data.json` comes from the catalog. 24 screenshots: card 5 states and weather 3, each at 1280 full, 390 full and 390 viewport. Rendering nits: minor 3 |
| 7 | Card rules traceable? | MET, all traced. "Only rung 3": 4.1 ("A TRADE card is only ever for a version approved to paper (rung 3); anything earlier is WATCH"). RED: 4.1 reason codes, 6.2 and the owner's 14 Oct principles. Failed data check and hard-rule breach: 4.1. Intraday AMBER to RED only: 2.3. Missing weather blocks: owner "4 A". Nothing invented |

## Must-fix

**1. The Forecast lab has no isolation label and no per-forecast counted status (an owner condition and judge 58's precondition).**
- The owner's 14 Oct acceptance of `sealed_same_day` set condition (2): the label "sealed same day (not full F1)" stays
  on every record and report.
- Judge 58 required G4 reports to honour `model_mismatch`, exposed and breach days, and to show coverage and the
  isolation label.
- The Forecast lab shows the AI books' forecasts but has no field for any of these. `grep -i "sealed\|isolation"`
  finds nothing in the schemas or examples.
- The branch's own fixture builds "today's forecasts" from the 14 Oct live records. Those were generated at 19:27 IST,
  after protocol v2's 15:15 lock, so none counts (the claims file says so itself), yet the lab shows them unflagged.
- Fix:
  - an isolation label per AI forecaster;
  - a per-forecast status, at least: counted, late (not counted), breach (unscored), model mismatch;
  - per-forecaster coverage (made, missing, late).

**2. The card has no daily stress line (design 6.2: "Every card shows, for all open positions, the loss under fixed scenarios").**
- The scenarios are NIFTY −5% and −10% overnight with VIX +50% and +100%, and +5%.
- No card field holds them, and the gap list does not mention it. `worst_cases` is per trade and historical, which is
  a different thing.
- Fix: add the stress block (scenario, total loss across open positions, sum of maximum losses as the ceiling), or
  list it as out of scope with a reason and an owner story.

**3. Gap list (quality rule 2).** The gap list is drawn from the orchestrator's brief, not from the design sections the
story cites. Besides 1 and 2 above, these are in neither "covered" nor "out of scope":
- the weather's v0 checklist baseline (2.3: "any new weather model must beat it and the base rate"). Only the base
  rate is scored;
- coverage and missing-forecast counts (5; "a missing forecast is left out and counted": the schema has no place for
  the count).
Fix: add the gap list against 4.1, 4.4, 2.3, 3.1-3.2, 5, 6.2, 8.3 and the owner rows, with each item covered or out of
scope.

## Should-fix

1. **v4-dependent fields that are not marked provisional.**
   - `FnoForecastComparison.p_value` ("bootstrap p-value ... v4 one-sided"), `interval` ("95%, unadjusted"), `verdict`
     (no futility value) and `scores.n_needed` ("v4: twice the block length") describe v4 as it stood before G6
     revision 1.
   - G6 now uses the larger of a batch-means t-test and a studentized bootstrap, a 97.5% two-look futility bound and
     "futile" as an outcome (`PROTOCOL_v4.md` at dbba574, lines 182-239).
   - Only `min_effect_met`, `variance`, `settle` and the weather scores carry `x-provisional`.
   - Mark the v4 meaning of these shared fields provisional too, or split v3 and v4 comparison shapes.
2. **Fields that force a made-up value before their story exists.**
   - `closed[].fills` requires three E8 fills on every closed trade. Book 1's E4-only trades cannot be published
     without inventing them.
   - `open[].monitor` and `alerts_today` are required before LM1 exists: "alert_only" and 0 would claim a monitor that
     does not run.
   - Allow null, or a `not_measured` state, until E8 and LM1 exist (the story's own rule: "never faked").
3. **Visibility downgrade is not guarded.** My plants that made `FnoCardTrade` or `advocate.objections` public pass
   `check_fno_screens`. They fail only `render_fno_catalog --check`, which a regenerated table also passes. Pin the
   owner-only paths (card trade, legs, entry, exit plan, objections, open legs) in the check, with a planted break.
4. **Strategy lab `results[].costs` includes "its allocated AI and data costs" per strategy version.** The built S2
   (`fno/scoreboard/book_board.py:5`, judge 87) charges operating and AI costs at book level only, "so no rupee is
   counted twice". Per-version costs must be charges and pads only. Book-level AI and data costs belong on a book line.
5. **Unguarded rules.** My plants that survived every check:
   - card `max_loss` maximum raised from 10,000 to 50,000 (the owner's per-trade cap);
   - the "settle needs 60 outcomes" rule deleted.
   Add planted breaks for both.

## Conditions for the merge (not findings)

- **C1. Merge order.** Merge the dashboard first. Re-pin trading at the dashboard's merge commit (byte-equal files, new
  commit in `pin.json`), then merge trading. My merge check will verify that the pinned commit is on the dashboard's
  `main`.
- **C2. P2 conflict.** The builder's note (P2 commits pages under `reports/dashboard/`) is right and important: P2 must
  keep owner-visibility fields out of any public commit.

## Minor

1. **The mock TRADE and WATCH cards use real upcoming contracts.** They show `NIFTY26DEC22600PE` near today's spot with
   an entry range, labelled Mock and PAPER ONLY. Design 4.1's illustration does the same, but decision 9's reasoning
   ("publicly readable calls") favours an expired expiry or a clearly fictional level in public mocks.
2. **`family` needs a translation from `paper_account:book`.** It takes rule, hybrid or ai from book1_rules,
   book2_hybrid, book3_ai; name the mapping in the field table.
3. **Mockup 40, missing state.** It prints "None" in "The last sessions" (a Python null leaking to text), and shows
   "Within the limit" with no session counted. It does not say that new trades are blocked, though `blocks_new_entries`
   is true (owner "4 A").
4. **TRADE needs rung exactly 3.** A rung-4 version still trades on paper. Fine while `real_money_eligible` is
   `const false`; revisit with RM1.
5. **The claims file still says the trading push was refused.** c083b4b is on the remote; update the line.

## Per-criterion table

| Criterion | Builder's claim | My evidence | Result |
|---|---|---|---|
| 1 Five screens, schema, endpoint, three cases | 17 examples | Read every schema; the examples cover positive, negative and empty for each | MET |
| 2 Examples validate in both repositories, Mock, 2.7.0, page key, hash | tests and checks | `check_fno_screens` and the trading tests pass; my pinned-schema byte change fails 4 tests | MET |
| 3 Every leaf documented; built fields name real records with types | type test | Retyping and renaming are caught; but fields without a story force made-up values, and the v4 meanings are stale | PARTLY (should-fixes 1, 2) |
| 4 Paper, PAPER ONLY, no internal names, never-sent lists | checks | Keys and text clean; visibility downgrade unguarded; per-version AI cost wrong | PARTLY (should-fixes 3, 4) |
| 5 Mockups from the catalog only | build and check | Deterministic rebuild; data from the catalog; 24 screenshots | MET (minor 3) |
| 6 Planted breaks | 21/21 | Their 21 caught; 4 of my 9 schema plants survived every check, 2 of them real gaps (max_loss cap, settle rule); 2 more caught only by the stale table | PARTLY (should-fixes 3, 5) |
| 7 Gates | as listed | Reproduced in both repositories and on the trial merge | MET |
| Design coverage (quality rule 2) | gap list from the brief | Missing: isolation label and counted status, stress line, v0 weather baseline, coverage counts | **NOT MET** (must-fixes 1-3) |

## Claims vs reality

- **"All 33 files byte-identical".** True, by my hash check.
- **"21 of 21 planted breaks caught".** True. My own plants found the gaps above.
- **"v4-only fields carry x-provisional".** True for v4-only fields, but not for shared fields whose v4 meaning G6 has
  since changed.
- **"Design rules ... TRADE rung 3, never in RED".** Traced to the design; not invented.
- **"3187 passed".** Reproduced at c083b4b and on the trial merge.
- **Two independent reviews and their 20 findings.** Each "fixed" item I spot-checked is in the code:
  - visibility never downgraded through `$ref`;
  - the card rules;
  - the type test;
  - `page_key` asserted.

**Verdict: FAIL** for dashboard 3cf4baa7a8bf84df454a6dc4274e5021957d4958 and trading
c083b4b36487465bf357868f7b71e96aacf11e65:
- must-fix 1: the Forecast lab's isolation label and counted status (an owner condition);
- must-fix 2: the card's stress line (design 6.2);
- must-fix 3: the gap list against the design sections;
- should-fixes 1-5.

The contract's structure, the privacy design, the pin and the drift tests are sound, and the card rules trace to the
design.
