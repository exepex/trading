# Judge 596: G14 Amendment 1 (story text), story/g14-v5-v1-candle-2 at 2f98d36c5 (judge J, round 1 of 2)

**FAIL**, lane 1 (text): 2 should-fix, 1 minor. The diff touches only `docs/stories/G14-v5-v1-candle.md` (+86 -5).
Doc-reading tests with `FNO_SLACK_BOT_TOKEN` set: 853 passed, 15 xfailed. I take over from judge 497's session, so
this is a new report.

## Criteria
| Item | Verdict | My evidence |
|---|---|---|
| Lifted gates (section 1) | MET | DESK_DECISIONS line 341 names "G14's v5 side-by-side step (built and judged first)" among the held items; line 323 lifts the other "after sign-off" gates |
| Criterion 2 vs FREEZE_v4 | MET | `freeze_check.BYTE_CHECKED_GLOBS` (and the freeze story's new globs: `fno/v4_pack/*.py`, G11's files) match neither `fno/forecast_v5_v1/` nor `research/forecasts/v5/`. The O1 step's three files are outside them |
| Merge order (section 3) | MET | it follows from FREEZE_v5_v1 hashing G7 files that G7b still changes. The freeze story's text has `Frozen on: 2026-10-25` and first counted 26 Oct |
| Criterion 12 | PARTLY | FREEZE_v4 has one row per byte-checked file (`freeze_check.table`), so equality is testable for `fno/forecast_v4_rules/*.py`; see S2 for files with no row |
| One reader (5, criterion 11) | MET | `CandleRvTable` exists (`fno/intraday/candle_rv_table.py:16`); the W8 text on `story/g7b-completion` is the one pairing; criterion 11 is testable |
| Gap table | MET | recomputed from `research/data/intraday/rv/2026` and `rv-candle/2026`: 0.962, 0.997, 1.009 (19, 21, 22 Oct); 16 Oct void live, candle ok; 23 Oct void live, no candle row |
| Live date (4) | MET | DESK_DECISIONS line 340: next NSE session after a judged switch; the 26 Oct `v5c_trailing` gap follows from 23 Oct's void live row |
| Decision-56 statement | NOT MET | S1 |

## Findings
**S1 (should fix) Decision 56's scope is misstated.**
- Response 113 row 56 is general: "rows with provenance backfilled never count as live forecast inputs". It is not limited to v4.
- So "allowed here only because G14 is never a v4 member" has no source.
- The authority for G14's input is the owner's own 23 Oct row (DESK_DECISIONS line 316, "v5 trial ... same V1 forecasters fed by ... candle 2020-2026", owner: "Yes, start it"). That row overrides an orchestrator decision for this trial.
- Fix: cite line 316 as the basis. Say plainly that decision 56 as written also covered v5, and that the owner's row excepts this one measurement. Keep the safeguards: point in time by `first_seen_at`, labelled, never a v4 member.

**S2 (should fix) The freeze misses part of the new input path.**
- With W8, G14's candle input runs through G7b's reader and A16b's `fno/intraday/candle_rv_table.py`.
- `candle_rv_table.py` is in neither of the freeze's lists (`BYTE_CHECKED_GLOBS`, `RECORDED_NOT_CHECKED`, nor the freeze story's section 2). FREEZE_v4 has no row to compare.
- FREEZE_v5_v1 hashes only "this package's files and the imported G7 files". So an edit to `candle_rv_table.py` would change G14's input mid-measurement with nothing refusing it.
- Fix: FREEZE_v5_v1 hashes every file on G14's input path, `candle_rv_table.py` and `rv_table.py` included. Criterion 12 then reads: equal to FREEZE_v4 where FREEZE_v4 has a row, hashed in FREEZE_v5_v1 alone where it has none, with a test listing each.
- Note for the orchestrator: W8's v4 baseline reads the same unhashed file; that is the freeze builder's call.

**m1** Section 5 says the W8 reader "sits in v4's byte-checked files" before G7b has named its module. Write "if it lands in `fno/forecast_v4_rules/` (byte-checked)" until G7b names it.

## Plants
0 (text round).

## Notes
- The "no partial v5" open item (section 6) is stated plainly and routed to the orchestrator and owner; not a finding.
