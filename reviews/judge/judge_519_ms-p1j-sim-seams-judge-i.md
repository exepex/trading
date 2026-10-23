# Judge 519: MS-P1j seams for the simulator (second judge)

**Scope:** story/ms-p1j-sim-seams at 6d3aa180, diff merge-base..6d3aa180. Judge I (session_01MvZneCLZqBuiGyNxawdVee),
the second judge (it touches the live fleet's road closure); Judge B may judge it in parallel, and I did not read that
verdict. Lane 1. Round 1 of 2.

**Verdict: PASS.** No finding.

## Checked
| Point | Result | Evidence |
|---|---|---|
| Live is unchanged | MET | `SchoolFleet.rules = LIVE` by default, and `fleet_on` passes none. `plan_slot` closes a road holding an unmeasured quote as `sizes_not_measured` unless the rules are practice ones. Plants caught: the practice exception ignored, the closure dropped, the rules not passed, practice made the fleet's default |
| Only the practice root can pass practice rules | MET | d's isolation scan over `fno/` (judge 511) refuses `QuoteRules(...)` and practice imports outside the two practice roots; the plant making practice the default fails it |
| A mixed build fails safe | MET (reasoning) | practice rules on the fleet with live laws or a live fill port only lets the road open; the live quote gate then refuses `size_not_measured`. It never fills |
| `books_on` and the replay dashcam's `encode`/`decode` | MET | one construction for the pilot's books; `fleet_on` calls it with `build_fill_port`. The write-once check compares the encoded payload, so a subclass's encoding stays write-once. Plants caught: `encode` and `decode` bypassed |
| Gates | MET | full `pytest -n auto` 13,800 passed, 16 xfailed, 0 failed; ruff check and format, check_imports and check_records clean |

## Plants
6 planted, 6 caught.
