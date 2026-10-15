# Epic LR: the learning loop (layer 8)

Roles: statistician, risk manager (owner), F&O trader, behavioural finance. Goal: learn from every outcome without
fooling ourselves (design v2 `04_layers_card_monitor_learning.md` section 4.3; `REPLAN_new_stories.md` LR1-LR3;
`REPLAN.md` section 2, S4 row: S4 splits into the weekly post-mortem LR1, slice A, and the monthly report S4, slice C).
Story template and definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## LR1. Weekly post-mortem v1: forecasts, weather and data health only

**Repository:** trading · **Issue:** #106 · **REPLAN:** slice A, item 13 · **Lane:** 1 (new story; Slack; a schedule)

**Description:** As the owner, I want one short report every Saturday in Slack #fno-desk and in the repository that
says how the forecasts and the weather scored, which weather days were wrong, and whether the week's data arrived, so
that I see each week whether the tool is progressing (ChatGPT review 96: "the owner needs a periodic score/data-health
report"), without reading the daily records one by one.

**Context and why:** Design 4.3 lists the full post-mortem (cards and outcomes, open positions, loss reviews, budget,
factory status, drift alarms). Slice A has no paper trades, no loss reviews (LR2) and no drift detection (LR3), so v1
covers only the three parts named in the REPLAN: forecasts, weather, data health. It **reports and never decides a
trade**. Every score is **read** from the committed G4 and G8 reports, never recomputed a second way. G4 already posts a
Monday summary (`forecast-scores.yml`); LR1 reuses that function's text and, if the orchestrator agrees (claims file
question 1), replaces the Monday post so the owner gets one weekly report, not two.

**Scope.** In:
- `python -m fno postmortem weekly [--week-ending YYYY-MM-DD] [--post]`. The week is the A7 regular sessions from
  Monday to Friday of the week that ends on that Saturday (default: the latest Saturday on or before today, IST).
  Without `--post` it is a dry run: it prints and writes nothing. With `--post` it writes
  `research/postmortems/<YYYY>/<week-ending>.md` and `.json` and posts the text to #fno-desk
  (`FNO_SLACK_BOT_TOKEN`, through the existing alert sender of `fno/composition.py`).
- **Forecasts section.**
  - Protocol v4 (G8): the latest committed report `research/forecasts/v4_scores/<d>.json` with `d` on or before the
    week's end. Per question: its status; per forecaster its scores as the report states them; per comparison with
    the primary baseline its scored count, D, relative improvement against the minimum effect and its miss line (G9),
    copied from the report. "New this week" = that report's scored count minus the scored count of the latest report
    on or before the previous Saturday (a subtraction of two committed numbers, not a score). No report: "no v4 score
    report yet".
  - Protocol v1-v3 (G4): the lines of `weekly_summary` (`fno/forecast_scoring/score_report.py`) of the latest G4 report
    on or before the week's end, unchanged.
  - Before `research/forecasts/FREEZE_v4.md` exists the report's first line is G8's `EXPLORATORY` line.
  - Questions whose data needs A16 (V1) or are not started (V4, V5) show the status G8 gives them ("not enough data
    yet", "not started"), never a failure (ChatGPT review 96).
- **Weather section** (M1's records, `research/forecasts/v4/weather/<YYYY>/<d>.json`, read through `WeatherRecords`):
  - per session of the week: the operative colour, the v0 colour beside it, the record's label (live or back-fill) and
    status; a session without a record is "missing";
  - the next-session V6a outcome (absolute close-to-close move of at least 2%) from G7's one rule,
    `fno/forecast_v4_rules/series.py` `big_move_outcomes`; an outcome not yet known is "unresolved";
  - **weather misses** (design 4.3's confident miss for weather): every GREEN day followed by a 2% move, listed by day;
    and per colour the week's days and days with a 2% move (a count, no score);
  - the RED share and `over_alarming` mark of the week's latest live record, as M1 wrote them (M1 says "not enough
    data yet" below 250 live records);
  - weather's scores (weather_vix_v1 and weather_checklist_v0 against the base rate) are in the forecasts section,
    from G8's report, not here.
- **Data health section** (layer 1 metrics, design 2.1), per session of the week, from committed files only:
  - 3 pm quotes (A4, A4b): the day's `.canonical` marker present; its attempt's sidecar `complete` and `finished_at`;
    lateness = `finished_at` minus 14:55 IST in minutes; no marker: "none";
  - daily card (T1): a non-test delivery record in `research/cards/deliveries/<YYYY>/<d>-*.json` present;
  - v4 forecasts: G8's miss lines above already count missed days; data health does not count them again;
  - 15-minute recorder (A16): the number of live session rows in `research/data/intraday/rv/`; below 20 sessions it
    says "not enough data yet (n of 20)", the V1 minimum of the REPLAN;
  - one completeness line: sessions with a complete capture, a card and a weather record, out of the week's sessions.
- A week with no regular session (all holidays) gives one line, "no NSE regular session this week", and is still
  written and posted.
- The report is a record: written once per week. The same bytes again change nothing; different bytes for a week
  already written are refused with one line (re-run after a late file: the next week's report shows the change).
- A scheduled plain job (no AI), `.github/workflows/postmortem-weekly.yml`, Saturday 10:41 IST: run G8's own
  `forecast-v4-scores report --as-of <Saturday>` (so a current v4 report exists), then `postmortem weekly --post`, then
  commit `research/forecasts/v4_scores/` and `research/postmortems/` with the public-record scan on.

Out (each with where it goes):
- An AI writer and the devil's advocate review (REPLAN LR1 text): out of v1. The text is code-built lines only, so
  there is nothing for an advocate to check yet and no AI cost against BG1's budget. They come with T3 and the F
  roles in slice B (claims file question 2).
- Cards with trade outcomes, open positions, loss reviews (LR2), drift alarms (LR3), budget and factory status: slice
  B or later, when those records exist.
- Groww-vs-NSE agreement and A11 revisions (design 2.1 metrics): not in v1 (Known limits).
- Any change to a trade, a rule, a forecast or the weather: never. LR1 imports nothing from `fno/desk/`, `fno/books/`,
  `fno/risk/` or `fno/checks/`.

**Design:**
- `fno/learning/` (design 4.3 names `fno/learning/wiring.py`):
  - `week.py`: `Week` (week-ending Saturday and its A7 regular sessions; the calendar behind its existing interface).
  - `sections.py`: `PostMortemSection` (interface: `lines(week) -> list[str]` and `data(week) -> dict`), with
    `ForecastSection`, `WeatherSection` and `DataHealthSection`, one class each.
  - `readers.py`: `ScoreReports` (latest committed G4 and G8 JSON on or before a day), `CaptureMarkers` (the 3 pm
    marker and sidecar), `CardDeliveries`, `IntradaySessions`; each a small class behind an interface so a test fakes
    it.
  - `report.py`: `PostMortemBuilder` (joins the sections, puts the EXPLORATORY line first before the v4 freeze) and
    `PostMortemRecords` (write once).
  - `cli.py` (the command) and `wiring.py` (composition root: the folders, `WeatherRecords`, G7's series, the A7
    calendar, the alert sender).
- Reuse, not a second version: G4's `weekly_summary`, G8's report JSON and `EXPLORATORY`, M1's `WeatherRecords`, G7's
  `big_move_outcomes`, the A7 calendar, the existing alert sender. Each file under 350 lines.

**Acceptance criteria:**
1. `postmortem weekly` without `--post` prints the report and writes and posts nothing.
2. With `--post` it writes the `.md` and `.json` for the week and posts the `.md` text once to #fno-desk; a Slack
   failure prints "alert NOT sent" and the files are still written.
3. Every score line equals the number in the committed G4 or G8 report it names (the report's file name is printed);
   LR1 contains no scoring formula (test 7).
4. "New this week" is the difference of two committed reports' scored counts; with no earlier report it is the full
   count, labelled "first report".
5. The G4 part equals `weekly_summary` of that report, line for line.
6. Before the v4 freeze the first line is G8's `EXPLORATORY` line; after it, it is not.
7. V1, V4 and V5 show G8's status ("not enough data yet", "not started"), never an error.
8. Weather: each session's colours, label and status come from its M1 record; a missing record is "missing"; each
   GREEN day with a 2% next-session move is listed as a weather miss; an unknown outcome is "unresolved".
9. Data health: per session, the 3 pm capture state and lateness, the card's delivery and the weather record; A16's
   session count with "not enough data yet (n of 20)" below 20; a delivery with `test: true` is not counted as a card.
10. A week with no regular session gives "no NSE regular session this week".
11. A second write of the same week with the same bytes changes nothing; with different bytes it is refused with one
    line and exit code 1.
12. No module of `fno/learning/` imports from `fno/desk/`, `fno/books/`, `fno/risk/` or `fno/checks/` (an AST test in
    `tests/learning/`, as test 7).
13. The workflow runs on Saturday at 10:41 IST, never places orders, uses only `FNO_SLACK_BOT_TOKEN` for Slack, and
    commits with the public-record scan on (no `--no-verify`).

**Test plan:** fakes for Slack, the calendar and each reader; planted committed reports and records in a temporary
folder.
1. Positive: a full week (5 sessions, G4 and G8 reports, 5 weather records, 5 captures, 5 cards) gives the expected
   text and JSON (hand-written fixture).
2. Negative: a refused second write (different bytes); a Slack failure ("alert NOT sent", files written).
3. Empty: no G8 report, no G4 report, no weather records, no captures, no A16 rows, a holiday week: each gives its
   stated line, never an exception.
4. Reuse: the G4 part equals `weekly_summary(document)`; the v4 numbers equal the planted report's (criterion 3).
5. Weather miss: a hand-computed fixture with a GREEN day followed by a 2.1% move (listed) and an AMBER day followed by
   a 2.1% move (counted, not listed), and a day whose next session is not yet in the closes (unresolved).
6. Lateness: a sidecar finished at 15:05:41 gives 10.7 minutes; an incomplete capture gives `complete=False`.
7. No second scoring: a test fails if any `fno/learning/` module imports G4's or G8's scoring modules
   (`scores`, `scoring`, `comparison`, `block_bootstrap`); only report JSON and `weekly_summary` are read.
8. Exploratory line before and after a planted `FREEZE_v4.md`.
9. A TEST card delivery is not counted.

**Judge verifies:** runs `python -m fno postmortem weekly --week-ending 2026-10-17` on the repository and checks every
number against the committed report or record it names; reads the import rule; checks the workflow's schedule,
secrets and commit step.

**Known limits:**
- Before the v4 freeze every v4 number is exploratory; until M1's live capture is scheduled (at the freeze) the weather
  rows are back-fill records, labelled so.
- G8's report is cumulative; "new this week" is a difference of counts, not a weekly score (a weekly score on 5 days
  would be noise).
- A file committed after Saturday's run shows in the next week's report, not this one (the report is written once).
- Groww-vs-NSE agreement and A11 revisions are not reported in v1.
- If Slack is down on Saturday the report is still in the repository; there is no retry.

**Depends:** G4, G8, M1, T1, A4b, A7 · **Size:** S · **Status:** story text, waiting for the judge
