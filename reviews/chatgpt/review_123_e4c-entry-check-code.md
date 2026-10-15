# Review 123 — E4c protective-leg entry check (code)

**Reviewed:** `story/e4c-protective-leg-refusal`, judged code `f4a1f642`; request 186, story E4c, builder Response 184, Judge 197's reported PASS, and `entry_check.py`, `entries.py`, `daily_steps.py`. **Second reviewer:** ChatGPT, quality rule 9. **Overall verdict: ACCEPT for the current paper-only model, with scoring disclosures; no new blocking code change.** Evidence labels follow AGENTS.md. I inspected code and reported tests, but did not independently execute the 6,357 tests.

## Q1 — Is all-legs-and-sell-back-at-one-snapshot right? ACCEPT (strong evidence for code behavior; reasoning only for external realism)

`entry_check.entry_problems` calls E4's `price_leg` for each leg's opening side and every bought protective leg's closing side. `EntryDesk.enter` performs the entire check **before** the first `record_fill`. A 65-unit position whose wing's displayed bid has 64 units is refused, whereas 65 units passes (builder's boundary fixtures; judge's plants). The policy avoids charging spreads for an entry known, at the chosen snapshot, to lack an exit-capable hedge.

This is **not a simulation of every real limit-order execution policy**. A trader might wait or leg in, possibly filling at better or worse prices and carrying unhedged risk. E4c deliberately estimates a more restrictive, immediately hedgeable policy. It may look **worse** by excluding subsequently profitable trades, and **better** by avoiding losses and double-spread unwinds; the sign of the selection bias cannot be asserted without forward data. Report refusal counts and opportunity-level results; do not treat refused opportunities as trades with zero *conditional executed-trade* return.

## Q2 — Omitted checks: PARTIAL, no new guard now (strong evidence for code; reasoning only for liquidity implications)

**Short-leg buy-back ask depth:** Accept omission. It is not required for the opening sale, and exits use later quotes. It remains an **exit-liquidity risk**, not a guarantee that the short can be closed promptly. Report pending exits and time-to-close.

**Maximum spread:** Accept omission. E4's `worse_than_approved` already compares net touch proceeds/costs to C2's approved entry. A separate arbitrary spread percentage is unsupported by A16 forward spread evidence. Report actual spread and after-cost returns privately.

**Two entries consuming the same displayed size:** This is a genuine **model limitation** if the *same book* can open two trades sharing a contract and snapshot: two 65-unit entries against displayed size 100 each pass independently, although 130 units cannot both fill at that touch without replenishment. `entry_problems` has no cross-order depth reservation and `DeskSteps.fill` loops over orders. **No change to E4c now** under the owner's simplicity rule: this was true before E4c, and the record does not demonstrate two same-book simultaneous entries against one quote in the current book. Record as **Known limit**; if the normal strategy begins opening multiple same-contract trades at one snapshot, aggregate required units across that book before filling, or refuse the second entry. Do not pool depth across independent hypothetical books as if they were one real account.

## Q3 — E6 and C5 scoring: ACCEPT with explicit denominator (strong evidence)

The normal E4c path produces no `FILL_UNWIND` when a check refuses: `EntryDesk.enter` records `not_opened`, not a fill; `EntryResult.legging_cost_rs` stays null. Therefore E6's **legging cost** becomes zero except for a post-check guard failure. This is a change in the execution policy, **not proof that trading costs or liquidity risks vanished**. The entry bid/ask cost, C1 charges, and missed-opportunity rate must remain visible.

C5 correctly counts **zero newly opened risk** for a refused entry because the ledger has no fill; D2's already committed choice still counts as a decision/opportunity. This is the correct separation between decision risk and actual paper exposure. A strategy's opportunity-level result must retain the refusal in its denominator and show filled-only net separately; otherwise selectively executable strategies can appear better. No new risk-bucket charge for a trade that never opened.

## Q4 — Paths and replay: ACCEPT (strong evidence for inspected control flow; some evidence for judge's tests)

`EntryDesk.enter` checks an existing recorded terminal entry event **before** any fresh check/fill, so a rerun returns `_result(done[0])` with `refused_by_check=False`. Only a new `entry_problems` refusal sets `refused_by_check=True`; `DeskSteps._fill_one` sends the information alert only in that case. This prevents a normal replay from resending the alert. The `_unwind` guard remains available if a fill fails after the precheck; the builder's unchanged guard assertions and judge's planted breaks support it.

One **Known limit**: the precheck and fill both read the same immutable snapshot, so this cannot model a live order book changing between the two legs. That is intentional paper-model scope, not a code bypass. A failed Slack send prints its failure and is not retried on a replay; it is an information-only alert, so this does not change a trade or stop. No blocking change.

## Financial roles and final decision

**Mathematician/statistician/quant modeller:** conditional-fill selection can move measured expectancy either way; preserve the original opportunity denominator. **F&O trader/options strategist/volatility trader:** touch size and hedge exitability matter, but same-snapshot liquidity is not guaranteed real execution. **Risk/portfolio/head of desk:** refused entry means zero held risk; pending exits still count and can block new risk. **Execution/microstructure:** short buy-back depth and repeated same-contract depth are limitations; don't invent queue fills. **Market research/macro/flows/equity/investment banking:** news/gaps can affect refusal patterns; split by market regime. **Regulation:** paper-only, no broker orders. **Behavioural:** don't cherry-pick only filled winners. **Tax/cost accounting:** refused entries have no executed charges; guard unwinds retain real modeled charges. **Data engineer/red team:** verified precheck ordering, replay flag, first failure, and guard path.

**Final: ACCEPT E4c code for merge.** No demonstrated normal-running buy/sell or stop error requires a new guard. The repeated-contract size case is a known limit to revisit when the same book actually generates multiple entries at one snapshot. E4c does not itself prove a profitable or fully executable strategy.
