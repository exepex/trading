# Judge 586: G11 code, story/g11-ai-books-v4 at d8aabba4c (judge J, round 1 of 2)

**FAIL**, lane 1, one judge (C15 agreed): 2 should-fix, 3 minor. Code = merge 562718c5; the two later commits touch only
`G-forecasts.md` (checked). Gates on a trial merge with main 88d94efb8: 15,566 passed, 1 skipped, 14 xfailed; ruff, format, check_imports (2,620), check_records (9,072), check_numbers clean.

## Criteria
| C | Verdict | My evidence |
|---|---|---|
| C1-C4 | MET | 5 questions (`versions.py:21`); caps reproduced from closes (0.0193/0.0287/0.0641); history `d < day` and V2 close-proxy (my P2, P24 caught); envelope recomputed at brief (P7, P14 caught) |
| C5-C7 | MET | 9-min cap and 15:01:10 boundary (P5), v4 reveal 15:10:10 (P20), whole-second 14:55 (P6), not-today refused (P21) |
| C8 | MET | both owner defaults are one line each, `budget_stop.py:47,51` (P4, P16 caught); meter not signal file: no workflow writes `accounting/budget/` |
| C9 | PARTLY | guard at `v4_rows.py` unit-tested; end to end not (F2) |
| C10 | MET | `received > deadline` with V4_DEADLINE; my P1 (`>=`) caught at 15:10:00 (m3) |
| C11, C19 | MET | system_late refused at collect (P11), too-early (P17), lost log (P10), unknown receipt (P22), pending (P15) |
| C12 | PARTLY | unit stop rule tested; the firer's v4 window not (F2) |
| C13 | PARTLY | order, freeze, 09:15 (P12) MET; late go-live branch not built (F1) |
| C14 | MET | replay re-run: 10 rows, Hybrid V1 `invalid` (V1 `not_started` on 22 Oct), fire log 2,539 bytes |
| C15 | MET | 6 packages, AST and text; direct imports only (note) |
| C16 | MET | pre-go-live run on this host: `ai fire --protocol v4` "no go-live date", exit 0; `collect` "not live", exit 0; `reveals-ready --protocol v4` exit 0; commit step skips a missing folder |
| C17, C18 | MET | cost report empty before go-live; largest file 350 lines (`constants.py`) |

## Findings
**F1 (should fix) C13's late go-live branch is not built.** The passed text and `v4_register.py:7` say sessions between `effective_start` and a later `ai_books_v4` become `not_fired` rows, with a daily count from `ai fire`. `V4BookCollector.collect` starts at `live_from` (`v4_collect.py:71-73`), and no count is printed. Probe: start one session early, go-live on DAY; collect wrote no audit for the early session. G8's reconciliation (`reconcile.py:49-50`) then refuses every v4 look. Fix: collect from the earliest AI `effective_start`, writing `not_fired` for days before go-live; print the count; one test.

**F2 (should fix) Three v4 wiring paths are untested (my plants survived, 507 tests green each time):**
- P18: dropping `mark_exposures` from the v4 collect. `exposed` is a C11 outcome.
- P23: taking `released_sha256` from the fire log, not the release record. This defeats the "two sources" guard, which is C9's bad case end to end.
- P25: dropping the v4 session window in the firer's `stop_reason` call (`v4_fire.py`). After go-live, v2's pack days stop, so the v4 stop rule would never fire. The test patches `stop_reason` with `*args`.

Fix: one test each, through the collector and the firer.

**m1** Stale docstrings: `v4_input.py:4-5` ("the collection rebuilds it") and `tests/ai/test_v4_collect.py:1-4` contradict change 6.
**m2** `answer.py:3-5` and change 1 say an annualised figure is refused. For V2 it passes below VIX ~22.4 (0.15^2 = 0.0225 < 0.05). Fix the wording or name the gap.
**m3** C10's reason is wrong: no book-side module imports `outcome.py`. Ruling: the pin is enough (same constant, P1 caught at the boundary); only the reason needs correcting.

## Rulings on the 9 changes
1. Accepted: caps reproduced; see m2.
2. Accepted: no workflow writes the signal file.
3. Accepted: rule rows are `live` only from 22 Oct; the back-fill ends 15 Oct.
4. Accepted.
5. Accepted: P8 caught; the owner text is in the checklist.
6. Accepted: P3 caught.
7. Accepted, but someone must record v4's first 10 transcript audits, or every v4 day waits.
8. Accepted: the start is never after first-eligible.
9. Accepted: P10 caught.
The 4 blocking self-review fixes are present (P3, P11 caught; pipefail and the folder guard read in `v4-fire.yml`).

## Plants
25 planted, 22 caught, 3 survived (F2).

## Notes
- G10 (5bde718c1) conflicts only in `config.yaml` (adjacent keys: keep both) and `forecast_scoring/v4/wiring.py`. There, keep G10's body with G11's `build_slot_registry` name. My resolved three-way tree: ai, v4_pack, e2e, scoring_v4, budget, daily and rehearsal tests, 925 passed. G10 changes no name G11 reads (`ReleasedPacks.release`/`pack`/`pack_bytes` unchanged).
- Before go-live, the daily #fno-desk line gains two "v4 not live" lines.
- Each 18-19 KB pointer is retyped by the model, up to three tries: a time and cost risk for 15:10 (reasoning only).
