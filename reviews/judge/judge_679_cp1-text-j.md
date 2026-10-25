# Judge 679: CP1 story text (measured cost pads), story/cp1-measured-pads at 5348d501 (judge J, 1 of 2, round 1)

**FAIL** (text), lane 1: 2 should-fix, 1 minor. One file, `docs/stories/CP1-measured-cost-pads.md` (122 lines), under
the 500-line limit. Each functional statement was checked against the code on main.

## The orchestrator's claims
| Claim | Verdict | My evidence |
|---|---|---|
| (1) The flat pad is B2's; `cycle_costs.py` never edited; `FlatPad` reproduces `PositionCosts` to the paisa | MET | `PAD = 1.0` is at `fno/research_engine/cycle_costs.py:24`. That file is frozen by `research/2026-10-12-experiment-1/FREEZE.md:47` and named in `research/evaluation/PROTOCOL.md:438`. A new `PaddedPositionCosts` beside it, with criterion 6's paisa test, is the right shape. The owner's decision row says "C1's flat Rs 1", and the text correctly places it in B2 |
| (2) MS-SIM-b's half-spread and bucket reused unchanged | PARTLY | Both functions exist (`spreads/learner.py:20`, `spreads/bucket.py:42`). But see S1: `relative_half_spread` is a share of the mid, not Rs |
| (3) Frozen, versioned, point in time, Drive and receipt, deterministic; under 30 sessions provisional at max(Rs 1, p75) | MET | Design 1-3 and criteria 3-5 and 8. `MIN_QUOTED_SESSIONS = 30` is at `fno/school/simulator/constants.py:13`. The dates check out on NSE's calendar: the 30th session from the first NIFTY capture (14 Oct) is 27 Nov, from 19 Oct it is 2 Dec, and from 22 Oct it is 4 Dec |
| (4) "Past results never re-read" enforced by named refusals | PARTLY | Design 6 and criterion 7 name the errors, but the interface cannot carry them (S2) |
| (5) Three owner questions | MET | Each comes with its recommendation |
| (6) Out of scope, and why | MET | Charges, G1, more than one lot, event days, the desk's and school's live fills, and stock options, each with its reason |
| One owning document; links, not restatements | MET, m1 | The ownership table links C1, B2, MS-SIM-b, A4, A16 and R1 without restating them |

## Findings
**S1 (should fix) The unit of the table contradicts the function it reuses.**
- Design 1 stores "the median of the session medians of the half-spread (Rs a unit)", and the pad is Rs a unit.
- But MS-SIM-b's `relative_half_spread` returns half the gap as a share of the mid, floored at half a tick
  (`learner.py:20-25`).
- A median of relative values times one price is not the median of rupee values. So the text must say which quantity
  the table holds:
  - **(a) Rupees:** each quote's rupee half-spread is `relative_half_spread(q) * q.mid`, which keeps the tick floor.
    The session medians are taken over rupees. This is what `research/edge2/SLIPPAGE_NOTE.md`'s rupee table shows.
  - **(b) Relative:** the pad is `relative * the leg's own price` at fill time. That scales with the premium, which
    is arguably truer for in-the-money legs, but `PadSource.pad` would then need the leg's price.
- Pick one, state the formula, and test it against the note's published medians on the same captures. For example,
  NIFTY monthly under 1%, 0-7 days: Rs 0.12.

**S2 (should fix) The refusal has no trial to refuse.**
- Design 6 says `MeasuredPad` refuses any trial registered before the table's cut-off, or naming no table or another
  SHA-256.
- But `PadSource.pad(underlying, strike, spot, expiry, kind, session, slot)` carries no trial, and nothing says where
  `MeasuredPad` learns which trial it prices. As written, the owner's rule has no point of enforcement.
- Fix: `MeasuredPad` is built for one trial, from its committed ledger row and its card (the composition root passes
  them), and it refuses at construction. A study cannot price without that object. Add a plant: a `MeasuredPad` built
  with no trial still prices.

**m1 (minor)** MS-SIM-b's `SpreadLearner` and `SpreadModel` already aggregate session medians per bucket. Say in one
line why CP1 builds its own table instead (the side and slot dimensions, rupees, a frozen record), so the two
aggregations are not read as two versions of one function.

## Plants
None (a text round). For the code round: the relative value used as rupees (S1); a trial-less `MeasuredPad` (S2); a
29-session bucket priced at its median; a capture on the cut-off read; `FlatPad` differing from `PositionCosts` by
one paisa.

## Notes
- The orchestrator reports the doc tests at 963 passed. The change is one Markdown file; I judged it by reading.
- I did not coordinate with judge B.
