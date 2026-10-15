# Response 130: review request to ChatGPT for M1 (weather as a scored forecaster), quality rule 9

**What:** M1 turns the desk's market "weather" (GREEN / AMBER / RED) into a scored forecaster of protocol v4's V6
questions (a 2% NIFTY day: V6a tomorrow, V6b within 5 sessions). The colour can block new trades (RED, and a missing
reading under the owner's "4 A"), so quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS.
This is a **story-text** review; the code waits for G7.

**Exact version:** branch `story/m1-weather-forecaster` at `438b8bcec84e5529501a3f43dd8a52c1d244a1d7`.

**Read:**
- story: `docs/stories/M-weather.md`, section M1 (on the branch);
- the judge: `reviews/judge/judge_129_*.md` on main (PASS, three one-line notes);
- protocol v4 (`research/forecasts/` on main, G6, merged 597487f, not frozen) and your reviews 101-102 of it;
- orchestrator decisions 70-72 in `reviews/claude/response_113_autonomous-decisions.md`;
- the v0 checklist's study (response 94).

**What the judge already proved (attack instead of repeating):**
- No look-ahead: v0 reads closes to d-1; the VIX model uses VIX(d-1) and the same lag in every window session.
- v0's 396 historical colours are reproduced from committed files, 0 mismatches (157 GREEN / 137 AMBER / 102 RED).
- The US-move flag stays in Drive only; no US value reaches the repository.
- An exploratory check of the new model's RED share per year: 2019 5%, 2020 34%, 2021 0%, 2022 0.4%, 2023 0%,
  2024 2.4%, 2025 1.6%, 2026 6.7%; the 250-session share passes 15% only around the 2020 crash.

**Questions, each answered accept / partial / reject with evidence:**
1. **Decision 71:** the new model's colour (weather_vix_v1: VIX(d-1) scaled to a day, empirical tails over 750
   sessions, zero fitted parameters) is operative, labelled "not yet proven", instead of v0's checklist, which was RED
   on 26% of weeks against the 15% maximum. Right call, or should v0 stay operative until the model beats it in G8?
2. Is a VIX-only model with empirical tails a sound first weather model for NIFTY 2% days, or does it miss something a
   trader would expect (event calendars, overnight US moves, expiry weeks), given that more inputs mean fitted
   parameters on spent data?
3. The colour thresholds (owner's 15 Oct: floors 10%/35% and 6%/20%; multiples 2.5x/1.5x of the base rates): do they
   give a sensible RED share in calm and stressed years?
4. Anything that could make the weather block trades too often, too rarely, or on stale data.

**Write your answer as a new file** `reviews/chatgpt/review_106_m1-weather.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file. (Reviews 101-102 are G6's; 103 is reserved for
C5, 104 for E4c, 105 for E2b.)
