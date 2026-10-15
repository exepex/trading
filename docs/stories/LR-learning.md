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
Monday summary (`forecast-scores.yml`); LR1 carries that function's text and replaces the Monday post, so the owner
gets one weekly report, not two (owner, 15 Oct 2026, LR1 question 1). As the REPLAN says, an AI writer turns the
code-built lines into a short summary in plain words and the devil's advocate checks it (owner, 15 Oct 2026, question
2: both in v1, the simple way). The devil's advocate is two things (owner, 15 Oct 2026): an exact code check of every
number in the summary, and a second AI step that reads the report and raises objections (REPLAN's devil's advocate,
the role T3 will use daily, issue #105). The code-built lines stay the source of truth and are always posted. Both AI
steps run in one routine fired through the AI books' existing fire path, with F8's usage record; no second AI caller is
built, and the objecting AI is built once, behind one port, for T3 to reuse.

**Scope.** In:
- `python -m fno postmortem weekly [--week-ending YYYY-MM-DD] [--post]`. The week is the A7 regular sessions from
  Monday to Friday of the week that ends on that Saturday (default: the latest Saturday on or before today, IST).
  Without `--post` it is a dry run: it prints the lines and writes, fires and posts nothing. With `--post` it writes
  the lines to `research/postmortems/<YYYY>/<week-ending>.md` and `.json`.
- `python -m fno postmortem fire [--week-ending YYYY-MM-DD]`: fires the post-mortem routine (below), run by the job
  only after the lines are pushed to `main`, so the routine always finds them (code round: a separate command, because
  firing inside `weekly --post` would start the routine before the lines are committed).
- `python -m fno postmortem publish [--week-ending YYYY-MM-DD]`: one hour later, reads the writer's prose if it came,
  runs the number check, reads the objections if they came, and posts once to #fno-desk (`FNO_SLACK_BOT_TOKEN`, through the existing alert
  sender of `fno/composition.py`), in this order: the checked prose (or one line saying why it was dropped), the
  objections section (or "advocate not run: <reason>"), then the lines.
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
  - daily card (T1): "ok", or T1's own `misses` lines for the day (the same words the next card uses: no card on
    record, not sent, not saved, a clock warning); a TEST delivery is not the card, as in T1;
  - v4 forecasts: G8's miss lines above already count missed days; data health does not count them again;
  - 15-minute recorder (A16): the number of live session rows in `research/data/intraday/rv/`; below 20 sessions it
    says "not enough data yet (n of 20)", the V1 minimum of the REPLAN;
  - one completeness line: sessions with a complete capture, a card and a weather record, out of the week's sessions.
- **The AI routine: one routine, two steps** (the "post-mortem writer" and "devil's advocate objections" roles of
  design 7.6's stop order; one routine keeps the owner's setup to one routine and two secrets):
  - fired by `postmortem fire` through the existing `RoutineTrigger` interface (`fno/pipeline/trigger.py`,
    `RoutineFireTrigger`, as the AI books in `fno/ai/fire.py`), with a one-line pointer: the week's Saturday and the
    SHA-256 of the committed lines file. Only the pointer is sent, never data;
  - its routine (created by the owner from `docs/stories/LR1-owner-checklist.md`; two repository secrets,
    `FNO_ROUTINE_POSTMORTEM_TRIGGER_ID` and `FNO_ROUTINE_POSTMORTEM_TOKEN`) reads the committed lines file, checks its
    SHA-256 against the pointer, then:
    - step 1, writer: at most 150 words to `research/postmortems/<YYYY>/<week-ending>_prose.md`, the lines' SHA-256
      on its first line; plain words, every number in digits and copied from the lines, no advice, no trade, no
      forecast of its own;
    - step 2, objections: reads only the committed lines file and the step-1 prose, and writes
      `research/postmortems/<YYYY>/<week-ending>_objections.md`: the lines' SHA-256 on its first line, then at most 5
      objections, each one sentence of at most 40 words starting with the lines-file line number it questions
      (`[L12] ...`), aimed at what the numbers may not show (too few days, a miss pattern, a missing input, a claim in
      the prose the lines do not support). Objections never give new numbers, advice or a trade;
    - records its own run once with F8's `python -m fno budget record-usage --self-timed --purpose books_and_roles
      --role "weekly post-mortem: writer and devil's advocate"` (F8's `role_or_bundle`), and pushes both files;
  - not fired (so neither step runs), and the lines posted with "summary: <reason>" and "advocate not run: <reason>",
    when: the month's BG1 signal (`accounting/budget/<YYYY-MM>_signal.json`) is `stop` (design 7.6: at 100% every AI
    role stops; code keeps running), the routine's secrets are missing (`UnconfiguredTrigger`), or the fire fails (`FireFailed`'s reason);
  - the fire is logged once per week in `research/postmortems/<YYYY>/<week-ending>_fired.json` (the routine's session
    link, for F8's audit), as `fno/ai/fire.py` does; never retried.
- **The number check** (code, run by `publish`; the exact half of the devil's advocate): the prose is posted only when
  all of these hold, else it is dropped (the objections and lines are still posted) and one alert line names the first
  failed rule:
  1. the prose file exists and its first line is the SHA-256 of the committed lines file;
  2. at most 150 words, no link, no Slack mention (`<@`, `<!`, `<#`), no code block;
  3. every number token in the prose appears as a whole number token in the lines: one regex splits both texts into
     number tokens (digits with their decimal point, sign and `%`, dates as one token), and the prose's tokens must be
     a subset of the lines' tokens; never a substring match ("4" does not match "40%", judge 167 addendum 1);
  4. no number written in words (zero to twenty, "half", "double", "twice"), so rule 3 cannot be dodged.
  Matching each number exactly is a rule, so it is code (reasoning only: cheaper and surer than an AI for this).
- **The objections** (the AI half of the devil's advocate), behind a reusable port in a new package `fno/advocate/`:
  - `Advocate` (interface): `objections(subject: AdvocateSubject) -> AdvocateResult`; `AdvocateSubject` is the subject's
    name, its committed lines file and that file's SHA-256; `AdvocateResult` is either the checked objections or "not
    run" with a reason;
  - `RoutineFileAdvocate` (adapter): reads `<subject>_objections.md` that a routine wrote beside the lines file and
    applies `ObjectionCheck`: the SHA line matches; 1 to 5 objections; each at most 40 words, starting with `[L<n>]`
    for a line that exists; no link, mention or code block; rules 3 and 4 of the number check (numbers only as whole
    tokens of the lines, none in words);
  - no file, or any rule failed: "advocate not run: <reason>", and nothing else in the report changes;
  - posted as their own section, headed "Devil's advocate objections (AI; they change no number and decide no
    trade)"; the numbers in the lines are never edited because of them;
  - T3 (daily card objections) reuses `Advocate`, `RoutineFileAdvocate` and `ObjectionCheck` with its own subject and
    never builds a second objecting AI (work register row).
- **Nothing the AI writes can decide a trade:** only `fno/learning/publish.py` reads the prose and objections files
  (through `Advocate` for the objections), and only to post them; an AST test fails if any other module names those
  paths, and neither `fno/learning/` nor `fno/advocate/` imports from `fno/desk/`, `fno/books/`, `fno/risk/` or
  `fno/checks/`.
- **The owner's setup (one routine, two secrets; checklist `docs/stories/LR1-owner-checklist.md`, written with the
  code):**
  1. Create one Claude Code routine "Omenix F&O weekly post-mortem" on this repository, with an API trigger (`/fire`)
     and no schedule of its own (the workflow fires it), its prompt copied from the checklist (the two steps above,
     the SHA check, the `record-usage` line, push to `main` with the public-record scan on).
  2. Add the trigger's id and token as repository secrets `FNO_ROUTINE_POSTMORTEM_TRIGGER_ID` and
     `FNO_ROUTINE_POSTMORTEM_TOKEN`.
  3. Run the workflow once by hand (`workflow_dispatch`, test week) and check that #fno-desk shows the three sections.
  Until steps 1-2 are done, every week posts "summary: writer not configured" and "advocate not run: not configured".
- A week with no regular session (all holidays) gives one line, "no NSE regular session this week", and is still
  written and posted.
- The report is a record: written once per week. The same bytes again change nothing; different bytes for a week
  already written are refused with one line (re-run after a late file: the next week's report shows the change).
- A scheduled plain job (no AI in the job itself), `.github/workflows/postmortem-weekly.yml`:
  - Saturday 10:41 IST (owner, 15 Oct 2026): run G8's own `forecast-v4-scores report --as-of <Saturday>` (so a current
    v4 report exists), commit `research/forecasts/v4_scores/` and the lines files, then `postmortem weekly --post`
    and commit and push the lines, then `postmortem fire` and commit the fire log, with the public-record scan on;
  - Saturday 11:41 IST: pull, `postmortem publish`, commit nothing but the publish record
    (`<week-ending>_posted.json`: which text was posted and why).
- `forecast-scores.yml`: its Monday summary post (cron `41 3 * * 1` and its step) is removed; G4's daily scoring and
  the `forecast-scores summary` command stay.

Out (each with where it goes):
- The daily card's objections (T3, slice B): T3 reuses `fno/advocate/` with the card as its subject.
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
    marker and sidecar), `IntradaySessions`; each a small class behind an interface so a test fakes it. Card
    deliveries are T1's own `DeliveryLog` and `misses`.
  - `report.py`: `PostMortemBuilder` (joins the sections, puts the EXPLORATORY line first before the v4 freeze) and
    `PostMortemRecords` (write once).
  - `writer.py`: `WriterPointer` (the one-line pointer, a `FiredText`) and `PostMortemRoutine` (budget signal, fire
    through a `RoutineTrigger`, fire log).
  - `publish.py`: `Publisher` (the three sections, one alert per dropped part, the publish record).
- `fno/advocate/` (reusable, for T3): `numbers.py` (`number_tokens`, the one tokenizer, and `NumberCheck`, the four
  rules, returning the first failed rule), `port.py` (`Advocate`, `AdvocateSubject`, `AdvocateResult`),
  `routine_file.py` (`RoutineFileAdvocate`, `ObjectionCheck`).
  - `cli.py` (the three commands) and `wiring.py` (composition root: the folders, `WeatherRecords`, G7's series, the A7
    calendar, the alert sender, the routine's trigger from its two secrets, the budget signal file,
    `RoutineFileAdvocate`).
- Reuse, not a second version: `RoutineTrigger`/`RoutineFireTrigger`/`UnconfiguredTrigger` and `FireFailed`
  (the AI books' fire path), F8's `record-usage --self-timed`, BG1's signal file, G4's `weekly_summary`, G8's report JSON and `EXPLORATORY`, M1's `WeatherRecords`, G7's
  `big_move_outcomes`, the A7 calendar, the existing alert sender. Each file under 350 lines.

**Acceptance criteria:**
1. `postmortem weekly` without `--post` prints the report and writes and posts nothing.
2. With `--post` it writes the `.md` and `.json` for the week and fires the writer once; `publish` posts once to
   #fno-desk; a Slack failure prints "alert NOT sent" and the files are still written.
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
13. The workflow runs on Saturday at 10:41 and 11:41 IST, never places orders, uses only `FNO_SLACK_BOT_TOKEN` for Slack, and
    commits with the public-record scan on (no `--no-verify`); `forecast-scores.yml` no longer posts on Mondays.
14. The writer is fired once per week with only the pointer; a second `weekly --post` for the same week fires nothing
    ("already fired").
15. The writer is not fired when the BG1 signal is `stop`, or its secrets are missing; the fire failing is logged with
    `FireFailed`'s reason; in each case `publish` posts the lines with "summary: <reason>" and "advocate not run:
    <reason>".
16. `publish` posts the prose only when all four number-check rules pass (whole number tokens only); otherwise it
    drops the prose with one alert line naming the first failed rule; the lines are posted in every case.
17. No prose file by 11:41: "summary: no summary received"; the objections and lines are still posted.
18. Only `fno/learning/publish.py` reads the prose and objections paths (AST test); neither `fno/learning/` nor
    `fno/advocate/` imports the desk, books, risk or checks.
19. The owner checklist names the one routine, its two-step prompt, its two secrets and its `record-usage` line.
20. Objections are posted, in their own labelled section, only when `ObjectionCheck` passes; no file, a failed rule,
    a `stop` signal or a missing configuration gives "advocate not run: <reason>" and changes nothing else.
21. `Advocate` is an interface with one adapter (`RoutineFileAdvocate`); `publish` depends only on the interface.

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
10. Writer: a fake `RoutineTrigger` receives exactly the pointer (Saturday and SHA-256, nothing else); `stop` signal,
    `UnconfiguredTrigger` and `FireFailed` each give their line and no fire; a second fire for the week is refused.
11. Advocate, one test per rule: a matching prose passes; a wrong SHA line, 151 words, a link, `<!channel>`, a number
    not in the lines (`41%` where the lines say `40%`), a changed sign (`-0.0042` vs `+0.0042`) and "three days" each
    fail with their rule named.
12. Publish: all three sections; prose dropped (objections and lines kept); objections not run (prose and lines
    kept); no files; Slack failure.
13. Whole tokens (judge 167 addendum 1): prose "4 sessions" against lines holding only "40%" fails rule 3; "40%"
    passes; "2026-10-16" passes only when the lines hold that date.
14. Objections, one test per rule: a passing file; wrong SHA line; 0 and 6 objections; 41 words; `[L99]` for a line
    that does not exist; a link; a number not in the lines; "twice".
15. Port: `publish` works with a fake `Advocate` (both results), so T3 can plug in its own subject.

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
- The advocate checks numbers, not meaning: a prose that copies every number right but draws a wrong conclusion in
  words ("the model is better") passes. The lines are always posted below it as the source of truth; T3's objections
  come in slice B.
- The writer's run is counted in F8 by its own timing record only; BG1's coverage check reads the AI books' fire
  logs, not LR1's, so a missed timing record makes the books-and-roles minutes look lower (one short run a week).
- The routine and its two secrets are the owner's step; until then every week is "summary: writer not configured" and
  "advocate not run: not configured".
- One routine writes and then objects, so the objections are not fully independent of the summary (same session). The
  step-2 prompt reads only the committed files; the owner chose one routine to keep setup small. Reasoning only: a
  separate routine would be more independent and cost one more routine and its secrets; T3 may revisit it.
- The objections are checked for form and numbers only, not for whether they are fair; they are labelled AI and change
  nothing.

**Depends:** G4, G8, M1, T1, A4b, A7, F1/G5 (fire path), F8, BG1 · **Size:** S · **Status:** text PASS (judge 167 addenda 1-2); code on `story/lr1-weekly-postmortem`, with the judge
