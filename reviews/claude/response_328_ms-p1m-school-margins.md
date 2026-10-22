# Response 328: MS-P1m, the school's margins per trade (builder's claims for two judges)

Builder session 01Vm1WnH8i9waM8EJG8zwWqg (A14's owner), 22 Oct 2026. Branch `story/ms-p1m-margin-rows`. Text: the
"MS-P1m" section of `docs/stories/MS-market-school.md` (orchestrator's answers of 22 Oct folded in). Lane 1, money
limits: two judges (JUDGE.md).

## The decision the measure forced (strong evidence)

The orchestrator's rule was: measure first, and if any road's ATM row is ever below the real legs, price each trade
on its own legs. The measure (`tools/ms_p1m_margin_gap.py`, 13,736 comparisons on 37 archived sessions) found the ATM
row below the real position in 66-98% of credit spread and condor cases, as low as 0.76 of it. The table is in the
story. So no rows are added: C2's margin room prices every school trade, open or proposed, on its own legs from the
day's archived file. Re-running the committed script reproduced all 13,736 rows identically.

## What is built

| Part | Where | Tests |
|---|---|---|
| `RoadTradeTerms` (C2's terms plus index, expiry, legs, lot) | `fno/nse_margins/road_margin.py` | `test_a_school_trade_s_terms_refuse_what_the_margin_cannot_price` [4] |
| `ArchivedSpanMargin`, C2's `StressedMargin` on the trade's own legs and lot, at C2's factor, STR1 cap | same | `test_the_margin_is_a14_s_figure_for_the_trade_s_own_legs_at_c2_s_factor` [SF, PCS off-ATM], `test_the_trade_s_own_lot_is_used`, `test_c2_s_one_side_cap_applies_to_a_spread`, `test_another_index_is_read_from_its_own_part_of_the_file` |
| C2's own `MarginRoom`, unchanged, on it: open trade plus proposal; exact room passes, one rupee short refuses; an open trade without legs refuses | `tests/nse_margins/test_road_margin_room.py` | 2 tests |
| Fails closed by name: not archived, not the first copy, written at 09:00, damaged, no part for the index, expiry day, a leg not listed, terms without legs, Drive down (class name only) | `road_margin.py` | `test_every_way_the_figure_cannot_be_had_refuses_by_name` [7], `test_terms_without_legs_are_refused_by_name`, `test_a_drive_failure_refuses_by_its_class_name_only` |
| Downloaded once per session, parsed once per index | same | `test_the_file_is_read_once_per_session_and_parsed_once_per_index`, `test_the_day_s_file_is_downloaded_once_whatever_asks_for_it` |
| Records: method, factor row, the label "k measured on NIFTY monthly only [reasoning only]", file and SHA-256, legs, lot, per-lot figures | same | `test_the_records_name_the_file_the_factor_and_its_label` |
| Composition root, Drive on first use, C2's factor file from config | `fno/nse_margins/road_wiring.py` | `test_the_wiring_needs_no_drive_until_a_margin_is_asked_and_reads_c2_s_factor_file` |
| A14's 09:00 rule in one place (`SpanFile.written_in_time`), used by A14's job, A14c's run and this margin | `span_file.py`, `job.py`, `stress_run.py` | the existing A14 and A14c tests, unchanged |

`margins.csv`, `fno/risk/` and `fno/checks/` are not touched (`git diff` names no file under them).

## On the real 21 Oct file, through the real wiring (strong evidence)

| Check | Adapter | Reference | |
|---|---|---|---|
| NIFTY ATM SF 100, 23 Nov, lot 65 (scan, NOV, exposure) | 635.05, -6100.25, 59511.27 | `margins.csv` row of 21 Oct: 635.05, -6100.25, 59511.27 | same |
| BANKNIFTY PCS 53500/53300, 23 Nov, per unit | 132.02, -30.05, 1109.76 | by hand from the file's arrays | same |
| FINNIFTY PCS 23900/23800, 23 Nov | 64.06, -16.50, 499.74 | by hand | same |
| MIDCPNIFTY PCS 12950/12900, 23 Nov | 31.53, -8.78, 271.30 | by hand | same |
| NIFTY weekly PCS 22400/22300, 3 Nov | 78.92, -15.55, 457.78 | by hand | same |

"By hand" means scan is the largest of the 16 scenario sums, NOV the signed prices, and exposure 2% (3% beyond 10% out
of the money) of the index per short leg. Each is computed in the script straight from the parsed arrays, not by
the calculator.

## Self-review round (22 Oct, before the judges): two blocking and five minor findings, each checked

| Finding | Check | Fix | Test |
|---|---|---|---|
| **Blocking:** C2 prices the margin from the terms but counts units from the `Proposal`/`OpenTrade`; nothing tied them (a lot of 1 inside a 65-unit proposal passed, Rs 840 needed instead of Rs 54,600) | reproduced by the reviewer | `road_proposal` and `road_open_trade` build C2's trade from the same terms; the story makes them a must for MS-P1d (its own acceptance test) | `test_c2_s_proposal_and_open_trade_carry_the_terms_own_lot_and_legs`; `MarginRoom` tests now use them |
| **Blocking:** the planted credit spread had zero risk arrays and prices, so the credit and the cap were never exercised | reproduced | a planted bull put spread with arrays and prices, rupees worked by hand in the test's docstring; the cap binds | `test_a_credit_spread_in_rupees_worked_by_hand_with_c2_s_cap_binding` (removing the cap or the `min(0, NOV)` term in C2 fails it) |
| History mode (`allow_short_option_minimum=True`) would price a file A14's daily job refuses | read; 16 recent sessions x 4 indices read in daily mode, none refused | daily mode | two new refusal cases (a GROSS minimum, no scan tiers) |
| A refused Drive sign-in or two same-named items (`RuntimeError`s) escaped the named refusal | read | any Drive failure refuses by class name | `test_a_drive_failure_refuses_by_its_class_name_only` [2] |
| A missing manifest row read as "differs from its SHA-256" | reproduced | its own message | "no manifest row" case |
| Structure and legs were not checked against each other (PDS legs labelled PCS, a ratio leg) | reproduced | `RoadTradeTerms` checks each code's shape | 8 new cases |
| E8's owner-timing record would drop the legs | read | stated as a limit in the story (the pilot has no owner timing) | - |
| The gap script skipped unlisted combinations silently | read | it counts and prints them | its rerun below |

New mutations, all 16 caught: the factories' lot and units; each shape rule (one unit, the sold leg, the width, the
type, the wings inside, the wings out, the condor's order, the fly's body, unknown codes); daily mode; the manifest
row; the Drive catch; and in C2, the cap and the credit term.

On the real 21 Oct file in daily mode, the five checks above give the same figures.

## Mutations, round 1 (strong evidence: 19 of 19 caught)

Factor dropped from the stressed margin; from the margin at entry; the broker margin stressed; a fixed lot; no cap; the
09:00 rule off (in the adapter, and `<=` in `written_in_time`); the SHA check off; the missing-file check off; plain
terms accepted; the width check off; the index check off; the parse cache off; the download cache off (caught after a
test was added); the symbol fixed to NIFTY; each of the three exception wraps narrowed; the Drive error's text kept.

## For the judges to rule on

- An open trade on its own expiry day makes the calculator refuse, so that driver account opens nothing that day.
  This is conservative: the expiry-day extra 2% ELM is not modelled (P0 probe 4).
- Any Drive failure, missing settings included, is a named refusal (class name only).
- The beginning-of-day file prices a 15:00 decision, as A14's rows do.

## Limits

- k 2.1 is measured on NIFTY monthly only; for the other indices and the weeklies it is reasoning only, labelled in
  every record (orchestrator, 22 Oct).
- The other three indices have no broker check yet; NIFTY matched Groww on 21 Oct (A14c part 2's rehearsal).
- MS-P1d must build every school proposal and open trade through `road_proposal` and `road_open_trade` (proposed to
  its builder on 22 Oct; their reply pending).

## Gates

On the head named in my message to the judges.
