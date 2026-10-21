# O11. End-to-end acceptance replay: one recorded day through the whole engine

**Lane 1** (a new story; its code is new tests only). Owner session: session_01FWkBH4zNAEFSEpjUzVEgnd. Orchestrator:
session_01VG1RqxLFUVdvvPuMRYZtDH. Plan: `docs/CORE_ENGINE_PLAN.md` (expectations E11 and E15).

## Why

Owner, 16 Oct 2026 (DESK_DECISIONS row 246): "No broken code should be there ... there must not be anything that is
not implemented. And I don't want any surprises. Every claim must be validated that it is fixed and implemented."
Every stage has its own tests, but no test runs one day from captured data to the scoreboards. So nothing proves the
stages fit together, and nothing lists what is still missing. O11 is that test. Its expected-missing rows are the
"not implemented" list, and the suite is complete only when that list is empty.

## Scope

In: one pytest package, `tests/e2e_acceptance/`, that replays 16 Oct 2026. Each built stage runs in the day's order and
its output is checked against the stage before it. Each failure the day can really have is shown to be recorded, and
alerted where the code alerts today. Each stage that is not built yet is a strict `xfail` naming its story.

Out: new behaviour, new production code, a new framework, a second daily runner (O1 owns the routine; O2 owns outages
and kill-and-rerun), UI.

## The recorded day and what is real

| Input | Source | Real? |
|---|---|---|
| 3 pm NIFTY chain (188 contracts, 23 Nov and 27 Oct expiries, spot 23,103.80) | `research/data/quotes/nse/.../nifty_20261016_145500.csv`, NSE's public chain recorded by the 3 pm routine | **Real.** The only quote rows committed to this public repository; Groww's rows stay in Drive (A4b) |
| Contract IDs | NSE's `OPTIDXNIFTY23-11-2026CE21950.00` restated as `NIFTY261123...CE` | Restated (see finding 2); prices, sizes and times unchanged |
| Closes and VIX to 15 Oct, events, session calendar, intraday RV | the committed files the live jobs read | **Real** |
| Margins and stress factor | `research/data/margins/` | **Real** |
| Execution snapshot at 15:15 | the same real rows, timed 15:15:00-15:15:40 | Real prices, re-timed (no 15:15 capture is committed) |
| NSE F&O file of 15 Oct (C4 listing, lot size) | built from the real expiries and strikes, lot 65 | Synthetic (the real file is in Drive) |
| Strategy | one approved test version (short condor, 30-38 days, Rs 10,000 cap) | Test only: **no strategy is approved yet**, so a real one cannot be replayed |
| Live features (B7) | fixed values | Test only |

Three outside services are replaced at their composition-root seams: Drive's quote store becomes a local folder, NSE's
F&O archive becomes one file, and the playbook's git approval becomes one approved version. The day runs through
**O1's daily run** (`DailyRun` with O1's `day_steps`, in `DAILY_RUN_STEPS` order) built as `fno/daily/wiring.py`
builds it, with three differences. Git, Drive and Groww's recorder are replaced as `tests/timetable` already replaces
them. O1's command steps (`weather`, `forecasts_v4`, `book1`) call their command's own function in-process behind O1's
`DayStep`, because a child process could not see the replay's seams; they keep O1's outcome rules. O1's real
`Alerted` and `ReviewsStep` wrap them. The clock starts at **14:05**, the agreed O1 start (the stored 14:33 start is
tested as a failure below). Everything else is the code on `main`, from its composition roots.

## Stages

| # | Stage | Built on main? | Checked |
|---|---|---|---|
| 1 | O1 `weather` (M1) and `forecasts_v4` (G7) steps at 14:05 | yes | step ok; record and rows for the day, label live; only V1 waits (20 A16 sessions) |
| 2 | Packs (E2) at 14:58 | yes | the pack records the real snapshot's ID and SHA-256 and the 15 Oct close |
| 3 | O1 `book1` step: D2, C2/C5 risk, C4 validity | yes | chosen trade, risk ok, every C4 check ok, the record names the pack's SHA-256 |
| 4 | Collection (E3), C3 data checks, execution snapshot | yes | collected on time, snapshot valid |
| 5 | Fills (E4), exit review, trade marks (E2d) | yes | 4 legs filled from the snapshot, held, valued, equity row |
| 6 | O1 `reviews` (E6), scorecard, scoreboards B (S2/S6) and A (S3) | yes | the same trade ID, maximum loss and day in each |
| 7 | The day's chosen trade checked by C4 as Book 2's and Book 3's (D4, D5) | yes | refused: no envelope permits it, no constitution registers it |
| 8 | Go-live switches: `daily.live_from` dates, the 14:05 start, the card's weather from M1, the card step in the replay | no | xfail: owner, O1 follow-up, T1c, O11 part 2 |
| 9 | Book 2 and Book 3 packs, decisions from a fake AI answer, model reporting, orders and exits | no | xfail: D4/D5/F1t, F1t+F5, F1t+F6, F1t, F5+F6 |
| 10 | Owner-timing fills | branch | xfail: E8 |
| 11 | v4 scores of the day's rows; AI books' v4 rows | no | xfail: G6, G11 |
| 12 | Capture failure rows, a never-started job alerted as stale, valuation record, analyst card, usage per routine, card objections | no | xfail: O10, O10+A14, G13, F2, F8c, T3 |

## Failures on the day

| Failure | Expected now (all built under O1's run) |
|---|---|
| No 3 pm capture | pack not built, with the reason in the run log; the `book1` step failed, recorded and alerted; the book is "no decision" with its record; the run goes on to the reviews |
| The 15:15 capture fails | snapshot invalid in the run log, alerted word for word; no fill |
| No NSE F&O file | C4 blocks the trade (record and `validity_failures.csv`); C3 alerts |
| A commit fails mid-run | the run stops and alerts once |
| An owner override in Book 1's decision (D3) | the `book1` step failed ("the owner never overrides a paper decision"), alerted; no decision, no fill |
| The stored 14:33 start | both forecast steps refused (after the 14:30 cutoff), recorded, alerted, nothing written; the desk's day goes on |

## Findings while building (one line each, for their owners)

1. A daily-run restart after 15:00 logs the pack step "built: False, already holds a different pack". The private
   pack holds the book's decisions folder, which changes at 15:00. No trade is affected. For O2's kill-and-rerun.
2. NSE's contract IDs parse as underlying `OPTIDXNIFTY` in C5's bucket map, so a desk fed from NSE's chain (the
   owner's "Groww, then NSE" fallback) would refuse every trade. It matters only if the fallback feeds the desk.
3. At the routine's stored 14:33 start, no live forecast can be made. This is the known O1 follow-up (the 14:05
   start).
4. The card's weather is `PendingWeather` ("M1 pending", "no new trades") although M1 is merged, and no story wires
   it (M1's text: "T1 change: Out"). The plan names it T1c.

## Acceptance criteria

1. `python -m pytest tests/e2e_acceptance` passes on `main`: every built stage green, every missing one a strict xfail
   naming its story, no skips.
2. Each built stage asserts its output exists and agrees with the stage before it (pack ↔ snapshot hash, decision ↔
   pack hash, fill ↔ decision and snapshot, marks and boards ↔ fill trade ID and maximum loss).
3. Each failure row above is a test that asserts the record (and the alert where built).
4. A missing stage turning real makes its strict xfail fail. Its builder then replaces the xfail with the real check
   in the same branch, so the list cannot go stale.
5. No network, no credentials (the suite's guards stay on), each file under 350 lines, gates green.
6. The go-live gate (DESK_DECISIONS row 247) starts its 10-day count only after this suite holds zero xfails and is
   judged.

## Judge verifies

Run the suite. Read the inputs table against the files: is anything called real that is not? Break one stage (for
example, make C4 skip the listing check) and see a test fail. Check that each xfail names the right story from
`docs/CORE_ENGINE_PLAN.md`.
