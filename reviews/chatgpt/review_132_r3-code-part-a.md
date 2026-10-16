# Review 132 — R3 code part A: shadow accounts and Book 1 isolation

**Target:** `story/r3-shadow-accounts` at **b73fb49e**, Response 220, Response 211, R3 story, Book 1/decision-store/tracker code and reported judge 210 addendum 2. **Second reviewer:** ChatGPT, quality rule 9. **Verdict: PARTIAL — accept part A for merge, with explicit part-B integration gates and a Test B readiness clarification.** Evidence labels follow AGENTS.md. Judge 210's file was not available at the requested path; the 6,796 reported tests were not independently executed. No shadow fill implementation is claimed.

## 1. Can shadows contaminate Book 1? — ACCEPT for implemented part A (strong evidence)

`fno/books/book1.py:Book1.decide` opens registered research shadow accounts before reading D2 inputs; `book1_records._chosen` requires the correct `mode` for Book 1 versus a shadow account. `opening_trades` anchors terms to **that account's own filled trade IDs and opening run**, and `recorded_terms(root, book, decider)` uses Book 1's decision run only as provenance, not Book 1's account. `DecisionStore.record_file` keeps shadow records separate from book records even for equal opportunity IDs, and raises `RecordClash` instead of overwriting.

The builder's tests plant differing widths (Book 1 width 100, shadow width 50), wrong-mode matching IDs, separate accounts and a mutation removing the mode guard. The E6/S2 tests compare Book 1's account-derived section; S3 tests Book 1 actions with and without shadow records. This supports **no normal-path Book 1 trade/score contamination in part A**. The one-decision finder legitimately sees a different replay input file because D2 must record shadow state; it still chooses the same first run. No reason to require byte-identical entire decision runs.

**Part-B integration requirement:** repeat the with/without comparison after real shadow orders and fills exist, including C2, C4, E6, S2, S3 and Book 1's actual ledger. The current part-A tests cannot prove future E8 wiring.

## 2. New `shadow_<id>.json` naming — ACCEPT (strong evidence)

`record_file(opportunity_id, mode)` prefixes shadow filenames; book filenames stay unchanged. The writer uses the same mapping for replay, and `_record_files` lists `*.json` so existing generic readers can still see both kinds and filter by `mode`. `RecordClash` refuses collisions. Names are constrained to lowercase letters, digits and hyphens, so the `shadow_` prefix cannot be a valid book-version prefix. This is simpler than moving records to a subfolder and updating every reader. No shadow record is committed yet, so no observed migration issue.

**Known limit:** an external reader that assumes every `*.json` file in the run is a book record could misinterpret the new shadow filename; the existing Book 1 reader has the explicit mode guard. No speculative migration or dual-name compatibility layer is justified.

## 3. Two book-only readers until part B — ACCEPT with mandatory part-B tests (strong evidence)

`book1_orders._stored_action` and `recorded_c4` still locate decisions with book-only filenames. **No shadow orders are written in part A**, so there is no current path that calls them for a shadow. Leaving the change to part B is a sensible ownership boundary. However, **before enabling shadow orders**, both must accept explicit mode/account identity, and tests must plant a same-ID book and shadow record and prove each reader selects only its own record. A missing shadow record must fail closed, not fall back to Book 1. This can change a future shadow fill, so it is a part-B activation condition, not a part-A merge blocker.

## 4. Test B's Drive-local existence check — PARTIAL (strong evidence on code)

`stop_rule_tracker.py:StopRuleInput.exists` uses `(root / path).exists()`; E2c keeps shadow account files in Drive. A fresh checkout can therefore say **not computable yet** even when closed shadow trades exist remotely. Conversely, an empty local `journal/shadow` folder can make `exists()` return true despite **zero resolved trades**. These are normal deployment states, not adversarial cases. The tracker describes file presence, not actual statistical eligibility.

**Smallest fix at Test B integration:** after the ordinary E2c download, derive Test B readiness from **resolved shadow closed-trade records and the registered trial requirements**, not directory existence. Zero eligible/resolved shadows must remain `undecided/no_economic_test`, never NO. If the stop-rule review can run before download, report `data not loaded` explicitly instead of claiming a computed Test B. No new Drive API, remote scan or background service. This is not a blocker for part A's account opening because the actual Test B computation is not built yet.

## Role-by-role challenge

**Mathematician/statistician/quant modeller:** Book 1's sample must exclude shadow records; no trial can be inferred from an empty folder. **F&O/options/volatility trader:** own account terms and separate fills are essential for correct width/margin and spread economics. **Risk/portfolio/head of desk:** shadow losses cannot consume Book 1's cash or brakes; Test B must not falsely become NO or computable. **Execution/microstructure:** shadow fills later need per-account touch size and no book cross-reservation. **Market/macro/flows/equity research/investment banking:** simultaneous event days should affect both experiments through prices, not shared account state. **Regulation:** paper only. **Behavioural:** do not promote a lucky measurement shadow. **Tax/cost accounting:** per-shadow charges and closed nets must reconcile independently. **Data engineer/red team:** test same-ID mode selection, Drive-fresh checkout and empty shadow directory.

**Final verdict: PARTIAL, acceptable for part-A merge.** Before part B is enabled, implement the two mode-aware order readers and run a real shadow-fill isolation fixture. Before Test B can report a verdict, replace folder existence as a proxy for resolved economic evidence. No broader redesign.
