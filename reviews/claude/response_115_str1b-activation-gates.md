# Response 115: STR1b activation gates (story text; claims follow with the code)

Branch `story/str1b-activation-gates`. Story text: `docs/stories/B-research-engine.md`, section STR1b.

## History of the text

- **53abdc0:** first text. Judge 115 FAIL, with 7 should-fix.
- **0462f71:** revised. The 7 should-fix were met, and addendum 1 added should-fix 8.
- **6b62348:** should-fix 8 added. Judge 115 addendum 2 PASS.
- **This revision:** trimmed under the owner's rule of 15 Oct 2026, "keep the design simple" (`docs/DESK_DECISIONS.md`),
  by the orchestrator's decision 65. Kept: the capital split, per-code approval dates, the margin-row check and the
  activation gate. The five guards that only a hand-made or buggy caller could need are dropped to Known limits.

## The dropped guards and ChatGPT review 100 (for ChatGPT and the owner)

Response 114 accepted all four points of review 100. Each dropped item, whether it traces to review 100, and why the
owner's rule now covers it:

| Dropped guard | Traces to | Why it now falls under "keep the design simple" |
|---|---|---|
| C2 rebuilds the labelled structure from the legs (with the "zero margin reads" spy) | **Yes:** review 100 point 1, the "better follow-up: have C2 derive bought-only status and the structure shape from legs" | A mislabel needs a proposal built by hand. In the normal running of the system, D2 builds every proposal through B2, so its label always matches its legs. If one did not, C4's independent shape check would refuse it, and E3 fills only on a recorded C4 pass. Review 100 itself called C4 "the safety boundary" and asked only that this be documented and tested, which judge 106 did. |
| Binding the C4 pass by hash to the exact proposal, book, version and rule | **Yes:** review 100 point 1, "a recorded C4 PASS bound to the exact proposal hash/legs, margin row and head snapshot" | E3 reads each order from the same committed D3 record that C4 checked, and the record's files are hash-checked against their commit (`DecisionStore.edited`). A different proposal under the same pass needs a hand edit, and the edit check already refuses it. **The margin-row part of the point is kept** (scope 3): A14 really appends rows between decision and fill. |
| A pass object at the fill primitive (`VerifiedPass`) | **Yes:** review 100 point 1, "an integration test that bypass attempts cannot open a trade" | The only code path that records an entry fill is E3's gate, through `EntryDesk.enter`. A bypass means new code that calls the fill directly, which would be reviewed by the judge as a lane-1 change anyway. |
| Static test listing every fill call site | **No:** judge 115 should-fix 6 (it narrows review 100 point 1's bypass test) | Same reason as the row above. |
| `apply_fill` refuses a close or settle that adds risk | **No:** judge 115 addendum 1, should-fix 8 | E4's exits and E7's settlement close only the holdings they read from the account. A risk-adding "close" needs a hand-built fill. |

**Evidence:** reasoning only, from reading the code paths: `fno/desk/daily_steps.py` `_fill_one`,
`fno/desk/recorded_c4.py`, `fno/desk/exits.py`, `fno/desk/execution.py` and `fno/books/account.py`. Judge 106 probed
the C4 boundary (54 planted naked shorts, every mislabelled shape refused).

**If ChatGPT or the owner disagrees:** the guard for points 1 and 3 of the table was fully specified in the text that
passed judge 115 (6b62348), so it can be restored from there.

## STR1b-1 build claims (branch `story/str1b-activation-gates`)

Built on `main` after C5 (a8379e6); the story text passed judge 126 at 5e20bbc, and its notes are in 8fde18f. Every
case tested below is a real path, per the owner's rule. Real data: NSE's 14 Oct 2026 `i1` SPAN file, downloaded again
from NSE's public archive (SHA-256 `d85b883ae4ca…0e8b5b`, equal to judges 77 and 106). The app's own A14 builder turns
it into `tests/risk/fixtures/margins_2026-10-14.csv` (47 rows: 9 codes x 5 widths, plus LC and LP at width 0), via
`research/2026-10-15-str1b-samples/real_rows.py`. The rows equal judge 106's published figures to the paisa.

### One correction to the passed text, found while building (strong evidence)

The passed text capped the stressed SPAN figure at `max(0, worst loss - net debit)`. Built that way, the cap also cut
the broker's own unstressed figure:
- On the real CCS 100 row, Groww blocks SPAN `scan - NOV` = 2,957.50 + 3,935.75 = **6,893.25** (the same basis as
  judge 77 addendum 3's SF check), while the cap is 100 x 65 - 3,935.75 = **2,564.25**.
- Capping the broker figure would make C2 looser than the broker at entry, which addendum 3 forbids.

**Fix:** the cap applies only to the stress extra, and never takes the figure below `max(0, scan - NOV)`. On every real
row the credit spreads' broker figure already exceeds the cap, so their stress reserve is 0 as well (sample below).
Story scope 1 is updated, and I am telling the orchestrator.

Criterion 2's wording is also corrected: a CDS's capital is its exposure plus the **bought leg's** premium plus charges,
not its debit. Groww credits the sold premium only after settlement (judge 77 addendum 3), which is today's
`entry_funds`.

### Criteria (STR1b-1)

| # | Claim | Code | Test | Mutation (fails its test) | Evidence |
|---|---|---|---|---|---|
| 1 | LC, LP, CDS and PDS carry no stress reserve. A credit spread's stress extra is capped at width minus credit, never below the broker's figure. SF, SC and BF are exactly unchanged on all 15 real rows. C4's figure equals C2's on all 47 real rows | `fno/risk/capital.py:16`, `fno/risk/margins.py:103-108,148`, `fno/checks/validity_margin.py:81-100` | `tests/risk/test_capital.py`, `tests/checks/test_validity_capital.py` | 1a no cap, 1b no broker floor, 1c cap on SF/SC/BF, 1d C4 uncapped | strong (real NSE rows) |
| 2 | C2 records `capital_rs` (broker margin, premium paid, stress reserve, total funds, capital tied). An LC's capital tied equals premium plus charges. S2 counts capital tied, and reports `stress_reserve_days_rs` apart | `fno/risk/rules.py:156-190`, `fno/scoreboard/entry_facts.py:21-45`, `sections.py:37-46` | `test_capital.py::test_margin_room_records_an_lc...`, `::test_capital_tied...`, `tests/scoreboard/test_capital_figure.py`, `test_whole_system.py` | 2 reserve counted as capital; 2b S2 reads total funds | strong |
| 3 | Per-code approval dates: a code is written from its own `passed_on` on and printed the day before; adding a code moves no other date; the old shape, an unknown code, no date, no source, a non-map and a list are refused; `config.yaml` holds only SF, SC and BF with the recorded 14 Oct check | `fno/nse_margins/broker_approvals.py`, `job.py:103-110`, `config.yaml` (risk.margins) | `tests/nse_margins/test_broker_approvals.py`, `test_job.py` | 3 approval only after its day; 3b no date or source check | strong |
| 4 | C4's `margin_room` names the row it used, and a row A14 appends later changes nothing | `fno/checks/validity_margin.py:66-79,123` | `test_validity_capital.py::test_c4_names...`, `::test_an_appended_row...` | 4 row not named | strong |
| 5 | The activation gate: an STR1 version cannot be registered as a shadow (gate STR1b-2) or approved to paper (STR1b-2, E8), and nothing is written. An unregistered draft file still loads. SF, SC and BF are unaffected. With STR1b-2 removed, a shadow is allowed and paper still waits for E8. D2 takes shadows and approved versions only from the loaded playbook, so the loader's check covers D2 | `fno/constants.py:101-105`, `fno/playbook/activation.py`, `fno/playbook/loader.py:113-115` | `tests/playbook/test_activation_gate.py` | 5a shadow use not detected; 5b gate ignored | strong |
| 6 | No file or class over 350 lines (`constants.py` is 330); `composition.py` unchanged | n/a | `tests/test_code_size.py` | n/a | strong |

Mutation script: `python research/2026-10-15-str1b-samples/mutate.py` (results below).

### Real output (quality rule 6)

From `python research/2026-10-15-str1b-samples/samples.py`, a dry run on the committed code
(`research/2026-10-15-str1b-samples/output.txt`). It gives the margin at entry per lot, at 1.45, on NSE's real 14 Oct
rows, in rupees:

```
LC    0 |  15,828.64 |       0.00 |       0.00 |      0.00     (before | now | broker | reserve)
LP  300 |   5,950.91 |       0.00 |       0.00 |      0.00
CDS 200 |  33,111.42 |  29,538.53 |  29,538.53 |      0.00
PDS 300 |  32,160.79 |  29,538.53 |  29,538.53 |      0.00
CCS 100 |  37,762.65 |  36,431.78 |  36,431.78 |      0.00
PCS 100 |  36,840.57 |  35,237.08 |  35,237.08 |      0.00
SF  100 |  66,340.33 |  66,340.33 |  65,970.32 |    370.01
SC  300 |  81,580.59 |  81,580.59 |  77,747.67 |  3,832.92
BF  300 |  59,077.07 |  59,077.07 |  59,077.07 |      0.00
Status change to research refused: ... PCS cannot be used for shadow while these activation gates are open: STR1b-2
Status change to paper refused: ... PCS cannot be used for paper while these activation gates are open: STR1b-2, E8
```

SC 300's Rs 81,580.59 equals response 92's "81,581". The four-leg rows are unchanged.

### Known limits

- The cap uses the margin row's NOV (NSE's beginning-of-day prices), not the trade's own 15:00 entry prices. That is
  the same source as every other margin figure, and it lets a held trade be capped like a new one.
- The rest are listed in the story's Known limits (the guards dropped under the owner's rule).

### What the judge should test hardest

1. The broker floor on CCS/PCS against Groww's basis (judge 77 addendum 3), and the CDS 200 and CCS 100 splits by hand.
2. SF, SC and BF are unchanged on the real rows.
3. Adding a code to the approvals map.
4. An STR1 version refused at registration and at paper.
