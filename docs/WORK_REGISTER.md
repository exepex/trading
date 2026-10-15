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
| E2c (O) | Paper fills, marks, equity history and private packs to Drive; one shared download per run; public daily totals only | 0134MoC6f7aAJVcHRBiyATo6 | story/e2c-fills-to-drive | fno/desk/, fno/books/account*, journal/ | text PASS (judge 148 add. 1); code started |
| E5b (O) | Book 1 commit-failure handling; one Book 1 decision a day | 0134MoC6f7aAJVcHRBiyATo6 | story/e5b-book1-commit-failure | fno/books/book1* | after E2c |
| E4c (O) | Entry refused if a protective leg cannot fill; every leg checked before any fill | 013xqaNTCbSBytKgqpfaYFqZ | story/e4c-protective-leg-refusal | fno/desk/entries* | after E2c |
| STR1b-2 (O) | Activates STR1 structures (exits, settlement, legging; per-code C4 refusal end-to-end test) | 01BYjW9auJnoiMQoH2WYVwYJ | not started | fno/strategies/, fno/risk/ | needs the owner's dated margin check per structure |
| A4c (O) | The traded index options (BANKNIFTY, FINNIFTY, MIDCPNIFTY) recorded after NIFTY in the 3 pm routine (response 144 step 8a) | 01MKtUHByHsR9cNwaP5KhFYH | story/a4c-all-indices | fno/quotes/ (recorder, cli), CLAUDE.md 3 pm section (proposed) | story text for the judge |
| A4b rule 8 (O) | First live 3 pm run with raw quotes in Drive only | judge D 01Pb8z2koLuxty7mbujFpgZa | merged | research/data/quotes/ | check 16 Oct after 15:10 IST |
| A16 routine (O) | 15-minute recorder routine (owner creates it) | A16/G8 builder 01VK88LxJvV1Gi7Wbr3D4fzp reads the first runs | docs/stories/A16-owner-checklist.md | research/data/intraday/ | waits for the owner |
| G6 freeze | Protocol v4 freeze; V6 report-only (owner, 15 Oct) | 01MgTu3L1T3y6R18ATTwbFub | story/g6-protocol-v4 | research/forecasts/PROTOCOL_v4*, FREEZE_v4.md | waits for the G6 session |
| G9 (project thread) | Protocol v4 miss rule (misses, input failures, 10% caps, operations-undecided) | 01H1CmuWzBtbtjzoQNJUz2Dz | story/g9-miss-rule | fno/forecast_v4/misses.py, fno/forecast_scoring/v4/ (comparison, look, render, cli, scoring), PROTOCOL_v4.md section 4 | done (merged f3835aba, judge 150 add. 1 PASS) |
| E8a (project thread) | Fill-timing study: 15:00 entry vs E8's next-session 10:15 fill, and 14:00 vs 15:00, 2024-26, Groww expired-option 15-minute candles (read-only), raw to Drive; then a live check against A16 | 01H1CmuWzBtbtjzoQNJUz2Dz | story/e8a-fill-timing | docs/stories/E-paper-desk.md (E8a), research/2026-10-16-fill-timing/, research/ideas/FT1.md, ledger trial 54, DATA_SPEND row | story text with the judge; code waits for the orchestrator's go |
| 26-week weather check (O) | Every 26 weeks of live v4 forecasts: weather_vix_v1's V6 vs v0 and the base rate; a loss gives the owner a keep-or-switch row, never an automatic switch | M1 builder 013xqaNTCbSBytKgqpfaYFqZ (routed by the orchestrator) | none | fno/weather/, G8 V6 scores | not started on purpose: story text near the first check (about 26 weeks after the v4 freeze) |
| Handover / routines | Routine schedules, NSE in the 3 pm routine, late-data ladder | 01Mt6dcBU5kp2htdPN2KmiZH | story/O7-routine-setup | CLAUDE.md 3 pm section, routine prompts | please add your rows |

## Known overlaps to settle (15 Oct)

- **3 pm routine:** A4b (merged, raw quotes to Drive) and the handover session's "NSE moved into the 3 pm routine" both
  change that routine. The handover session should confirm its change matches CLAUDE.md's A4b steps.
- **Protocol v4 (checked 15 Oct: G9 agrees with G8; A16/G8 builder, 210 tests together):** G9 (merged by the project thread) and the G6 freeze (G6 session), G8 scoring and M1 weather
  (orchestrator (O)) all touch v4. The G6 session checks G9 against its text before freezing.
- **Weather:** the project thread's "26-week weather colour check" decision and M1 (weather_vix_v1 operative,
  unproven; decision 71) must use the same records (fno/weather/).
