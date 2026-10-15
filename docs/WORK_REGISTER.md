# Work register: who is building what (owner, 15 Oct 2026)

Owner, 15 Oct 2026: "make sure that no two agents are trying to implement or develop the same functionality or same
functionality but contradictory implementation".

**Rule for every session (orchestrators, builders, judges, ChatGPT):** before starting a story, a fix or a design
change, read this file on the latest `main`. If another row already covers the same function, files or rule, do not
start: message that row's owner (or write a `reviews/claude/response_<n>` note) and agree who builds it. Then add or
update your own row in the same commit as your first change (lane 3, status rows). Mark a row `done` when merged and
closed; delete it a day later. One row per story; the owner session is the one that builds it.

Sessions on two accounts work on this repository and cannot all message each other, so this file is the shared
channel. Orchestrator of the stories below marked (O): session_01VG1RqxLFUVdvvPuMRYZtDH.

## Active (15 Oct 2026, 16:00 UTC)

| Story | What it builds | Owner session | Branch | Main files or areas | State |
|---|---|---|---|---|---|
| Status refresh (O) | Stale status lines in docs/stories, IMPLEMENTATION_PLAN, BUILD_MAP set from judge PASS and merge evidence; no rule text | 01Vm1WnH8i9waM8EJG8zwWqg | story/status-refresh | docs/stories/*.md status lines, docs/IMPLEMENTATION_PLAN.md, docs/BUILD_MAP.md | done (merged 293974e2, lane 3) |
| E2c (O) | Paper fills, marks, equity history and private packs to Drive; one shared download per run; public daily totals only | 0134MoC6f7aAJVcHRBiyATo6 | story/e2c-fills-to-drive | fno/desk/, fno/books/account*, journal/ | text PASS (judge 148 add. 1); code started |
| E5b (O) | Book 1 commit-failure handling; one Book 1 decision a day | 0134MoC6f7aAJVcHRBiyATo6 | story/e5b-book1-commit-failure | fno/books/book1* | after E2c |
| E4c (O) | Entry refused if a protective leg cannot fill; every leg checked before any fill | 0134MoC6f7aAJVcHRBiyATo6 (moved from 013xqaNTCbSBytKgqpfaYFqZ, 15 Oct) | story/e4c-protective-leg-refusal | fno/desk/entries* | after E2c |
| STR1b-2 (O) | Activates STR1 structures (exits, settlement, legging; per-code C4 refusal end-to-end test) | 01BYjW9auJnoiMQoH2WYVwYJ | not started | fno/strategies/, fno/risk/ | needs the owner's dated margin check per structure |
| A4b rule 8 (O) | First live 3 pm run with raw quotes in Drive only | judge D 01Pb8z2koLuxty7mbujFpgZa | merged | research/data/quotes/ | check 16 Oct after 15:10 IST |
| A16 routine (O) | 15-minute recorder routine (owner creates it) | A16/G8 builder 01VK88LxJvV1Gi7Wbr3D4fzp reads the first runs | docs/stories/A16-owner-checklist.md | research/data/intraday/ | waits for the owner |
| G6 freeze | Protocol v4 freeze; V6b stays scored (owner, 15 Oct, report-only withdrawn) | 01MgTu3L1T3y6R18ATTwbFub | story/g6-protocol-v4 | research/forecasts/PROTOCOL_v4*, FREEZE_v4.md | waits for the G6 session |
| G9 (project thread) | Protocol v4 miss rule (misses, input failures, 10% caps, operations-undecided) | 01H1CmuWzBtbtjzoQNJUz2Dz | story/g9-miss-rule | fno/forecast_v4/misses.py, fno/forecast_scoring/v4/ (comparison, look, render, cli, scoring), PROTOCOL_v4.md section 4 | done (merged f3835aba, judge 150 add. 1 PASS) |
| E8a (project thread) | Fill-timing study: 15:00 entry vs E8's next-session 10:15 fill, and 14:00 vs 15:00, 2024-26, Groww expired-option 15-minute candles (read-only), raw to Drive; then a live check against A16 | 01H1CmuWzBtbtjzoQNJUz2Dz | story/e8a-fill-timing | docs/stories/E-paper-desk.md (E8a), research/2026-10-16-fill-timing/, research/ideas/FT1.md, ledger trial 54, DATA_SPEND row | story text with the judge; code waits for the orchestrator's go |
| 26-week weather check (O) | Every 26 weeks of live v4 forecasts: weather_vix_v1's V6 vs v0 and the base rate; a loss gives the owner a keep-or-switch row, never an automatic switch | M1 builder 013xqaNTCbSBytKgqpfaYFqZ (routed by the orchestrator) | none | fno/weather/, G8 V6 scores | not started on purpose: story text near the first check (about 26 weeks after the v4 freeze) |
| Backfill test (O) | `tests/forecast/test_backfill.py` compares the decompressed CSV, not gzip bytes (response 144 step 7) | A16/G8 builder 01VK88LxJvV1Gi7Wbr3D4fzp | story/x-backfill-test-decompressed | tests/forecast/test_backfill.py | built, with the orchestrator |
| Handover / routines | Routine schedules, NSE in the 3 pm routine, late-data ladder | 01Mt6dcBU5kp2htdPN2KmiZH | story/O7-routine-setup | CLAUDE.md 3 pm section, routine prompts | please add your rows |
| NF step 4 (O) | EQ2 earlier forecast-pack release (protocol v2 amendment route first) | Handover noise fairness 01MGqsxHq19U4mCNWEd4Y4RH (proposed) | not started | fno/forecast capture, forecast-capture.yml, PROTOCOL_v2 amendment | awaiting the session's reply |
| NF step 5 (O) | One timing-consistency test replacing fno/timeline.py | Handover noise fairness 01MGqsxHq19U4mCNWEd4Y4RH (proposed) | not started | fno/timeline.py, tests | awaiting reply |
| NF step 6 (O) | O8: daily 17:51 IST health check, one message to #fno-desk | C5/E1b builder 012eM7Ti8ZaSVowgyMkgoGmM | story/o8-health-check | fno/health/ (new), .github/workflows/health-check.yml (new), research/ops/health_runs.csv | code PASS (judge 170); O1 contract: O8 merges first, so O1 moves `DESK_RUN_STEPS` (fno/health/desk_checks.py) to `constants.DAILY_RUN_STEPS`, O8 imports it, and the source-parsing test goes |
| NF step 7 (O) | Back-fill test compares decompressed content | A16/G8 builder 01VK88LxJvV1Gi7Wbr3D4fzp | story/x-backfill-test-decompressed | tests/forecast/test_backfill.py | go given |
| NF step 8a (O) | All-F&O recording, indices first (3 pm routine, Drive only) | A4b builder 01MKtUHByHsR9cNwaP5KhFYH | story text | fno/quotes/, 3 pm routine | text go given; code after text PASS and A4b rule 8 |
| NF step 9 (O) | Scorecard measures: do-nothing gate, net without best trade, profit factor, t-check warning, missed runs, random control | R2/G7 builder 0185gR5DmoDh2zBAvgRU4CEB | story/s6-scorecard-measures | S6 in docs/stories/S-scoreboards.md (S3 text amended); later PROTOCOL.md, fno/evaluation/protocol.py, fno/scoreboard/ | text PASS (judge 158 add. 1); code waits for E2c's merge and the orchestrator's go |
| S1 text (O) | Owner of research/evaluation/PROTOCOL.md draft items (S3 and S6 feed S1); other builders propose edits here. S1 pending edits: (1) S6's five items (do_nothing_benchmark, scorecard_measures, t_check, missed_runs, random_control); (2) S3: Holm via bootstrap p-values, A's series days; (3) F9 (01SFDjjZx7JYziM3jqJytG2z): frozen_files line, percentiles and block size, Holm across a book's roles (owner 15 Oct); (4) RM1 (01CHxE3ywfyCMxFLx6HGLwRo): the gate in frozen_files, after S6; (5) G10's two timetable lines (done) | R2/G7 builder 0185gR5DmoDh2zBAvgRU4CEB | lands with S3/S6 code branches | research/evaluation/PROTOCOL.md, fno/evaluation/protocol.py | collecting |
| G10 v4 timeline (O) | v4 timeline (14:30 cutoff, pack 14:32, 15:10 deadline, 15:15 snapshot), skill vs money scores, flag-not-block, late rule, EQ2/EQ5, day-quality labels, into PROTOCOL_v4 before the freeze | A16/G8 builder 01VK88LxJvV1Gi7Wbr3D4fzp | story/g10-v4-timeline | research/forecasts/PROTOCOL_v4.md, fno/forecast_v4*, capture timing | text PASS (judge 161 add. 3) at 8fb2742, with the orchestrator to merge; build and the v4 freeze (response 157) next; open: S1's timetable still says 15:00 and 15:12 (judge 161 add. 3 note 3), settled when S1 is decided |
| BR1 breadth track (O) | Fast-evidence design: cross-sectional predictions across all recorded F&O underlyings, pre-registered tests, held-back period, luck control, three families in parallel | M1 builder 013xqaNTCbSBytKgqpfaYFqZ | design proposal first | reviews/claude/response_<n>, docs/stories (new epic) | proposal go given; judge + ChatGPT + owner before any code |
| A17d (O) | FBIL's USD/INR table to Drive (private flag, overlap without rates, file removed in its own commit; adopt after the merge) | A16b/A17 builder 01MBnbVU4sundxNjs5u4xCsP | story/a17d-fbil-drive | fno/global_cues/ (other_sources, checks), research/data/global-cues/, tests/global_cues/ | done (merged 7dd6490a, judge 162 add. 2 PASS; rule 8 fill: FBIL to Drive only) |

## Known overlaps to settle (15 Oct)

- **3 pm routine:** A4b (merged, raw quotes to Drive) and the handover session's "NSE moved into the 3 pm routine" both
  change that routine. The handover session should confirm its change matches CLAUDE.md's A4b steps.
- **Protocol v4 (checked 15 Oct: G9 agrees with G8; A16/G8 builder, 210 tests together):** G9 (merged by the project thread) and the G6 freeze (G6 session), G8 scoring and M1 weather
  (orchestrator (O)) all touch v4. The G6 session checks G9 against its text before freezing.
- **Weather:** the project thread's "26-week weather colour check" decision and M1 (weather_vix_v1 operative,
  unproven; decision 71) must use the same records (fno/weather/).
