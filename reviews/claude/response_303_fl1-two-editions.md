# Response 303: FL1 in two editions (owner decision c3231785)

From the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd), to the orchestrator, 21 Oct 2026.

The owner's rule is "forecast BEFORE the open, check AFTER the close". This response answers the three questions:
1. what changes in FL1-1 and FL1-1c;
2. the new data part that reads the close after 15:30;
3. what must run at about 08:50 IST, and the stored prompt for it.

Judge E's review of FL1-1c at `2ed6405e` stays valid. Every piece it covers is reused unchanged: the page model, the
plain words, the reasons, the history, the renderers' port, the camera, the poster and the records.

## Points the owner should hear first

1. **Until A22 exists, the morning edition adds no new information.** (Reasoning only; it follows from the data
   flow.)
   - The N1 range for today is sealed at 15:45 the day before, from the 3 pm chain.
   - At 08:50 nothing newer exists: A22 (GIFT Nifty and the pre-open auction) is paused under the owner's scope freeze,
     and judge 407's FAIL stands.
   - So for now the morning post repeats a forecast the system already had at 15:45 the evening before.
   - It is still worth having for one reason: it sits where the owner looks before the open.
   - It costs a new scheduled session every trading day.
   - The owner should choose with this known. Option (b) below is the cheaper route until A22 is built.
2. **The evening check is provisional for a few hours.**
   - NSE's official close reaches our archive only with the evening file. The index-closes job runs at 21:11 IST, and
     G13b scores against that file.
   - The 15:45 check therefore uses NSE's own index list, read after 15:30, and labels the result "provisional".
   - The next evening edition confirms the earlier result against the official file, or alerts on any difference.
   - Whether the index list's 15:3x value always equals the official closing value is **not yet tested**.
     - I expect it to match, because NSE fixes an index's close at 15:30 from the last half hour's prices. (Reasoning
       only.)
     - The first 10 live days will show it. Every disagreement is printed and alerted, never hidden.
3. **No scheduled task is created by me.** The stored prompt below is a draft for the owner to create.

## 1. Changes to FL1-1 and FL1-1c

**Evening edition, about 15:45: "was today's forecast right?"**
- This is today's `lab_close` step, kept at 15:45 and last in `DAILY_RUN_STEPS`. It runs inside the 14:33 daily
  routine, which is already alive until then, so it needs no new schedule.
- The one-day lag goes. The forecast issued at 15:45 on day D-1 for day D (N1), and the N3 forecast that targets day
  D, are checked against day D's provisional close on day D.
- `PageBuilder` gains an `edition` argument with two values, `MORNING` and `EVENING`, and `PageView` gains an
  `edition` field.
  - The evening build adds today's `Outcome` from the provisional close, flagged `provisional=True`.
  - The renderers show the flag as the word "provisional"; it is never shown by colour only.
- Misses and their reasons work as today (`reasons.py`), applied to today's miss.
- The light and the record over 30 days include today, marked provisional until confirmed.
- New port `ProvisionalCloses` (an ABC with one adapter, wired in `page_wiring.py`). `HistorySource` stays as it is.
  - The builder merges today's provisional point only when G13b has no official score yet.
  - When G13b's official score exists, it wins. If its inside/outside verdict differs from the provisional one, the
    page says so in a "correction" line and one alert goes to #fno-desk.
- `CloseReport` and `MatchSection` (FL1-1's coverage) cover today instead of the previous session. The rule "sealed
  before the next regular session's 09:15" is unchanged.
- If the close read failed: the evening edition still posts with "today's close: not read (reason)", one alert goes
  to #fno-desk, and nothing is guessed.

**Morning edition, about 08:50: "today's forecast"**
- New command `python -m fno lab open`. It runs `LabOpen` (new class, about 120 lines) over the same `PageBuilder`
  (`edition=MORNING`), `ReportMaker`, `SlackFilesPoster` (#fno-forecast) and write-once records.
- Each record is keyed by day plus edition, so the two editions never collide and a rerun never posts twice. The
  existing `Delivery.may_have_posted` rule applies.
- Content:
  - today's N1 range, as issued the previous session, with its seal time shown;
  - the N3 outlook, meaning the forecasts whose target falls in the next 3 sessions;
  - the light;
  - "All systems normal" or the problems;
  - "Research only. Not a trade tip."
- When A22 lands, G13b's N0 (sharpened with GIFT Nifty and the pre-open auction) replaces N1 as "today's forecast"
  behind the same `RangeSource` port. N1 then stays in the details file as the comparison. Nothing in `LabOpen`
  changes.
- If today's forecast is missing or unsealed, the edition says so in words and posts one alert to #fno-desk.
- It is not an O1 daily step: `daily run` starts at 14:33. It is its own command, run by the morning routine (part 3).
- `DAILY_RUN_STEPS` is unchanged.

**Text lines (`plain.slack_lines`).** These become two functions, one per edition, keeping the same word rules:
"most likely" for the 50% range, "almost certainly" for the 90% range, outward rounding to 10 points, and
"tomorrow" only for the next calendar day.
- Evening, for example: "NIFTY closed 25,840 (provisional): inside 'almost certainly' ✓. Right 26 of the last 30
  days."
- Morning, for example: "NIFTY today: most likely 25,780-25,900; almost certainly 25,650-26,020."

**Renderers.** These come from the designer, who is redoing both editions. `PageRenderer` gains an
`edition` parameter. The interim renderer is used only until the owner signs off the design.

**Config.**
- `daily.live_from.lab_close` stays. The owner's switch-on question (f2293cea against the f21a8966 hold) is still
  open.
- A new `lab.open_live_from` key for the morning edition, `null` until the owner sets it.

**Size.**
- About 450 lines of code: `LabOpen`, the edition paths in the builder and plain words, `ProvisionalCloses`, the
  correction rule, the CLI and the wiring.
- About 500 lines of tests.
- Lane 1, on branch `story/fl1-1d-two-editions`, after Judge E's FL1-1c verdict, because it builds on that code.

## 2. New data part: the close read after 15:30

**Story text (draft).** Proposed story id **A4h** for the orchestrator to confirm; it is a data part, not FL1.

> **A4h: the index close read after 15:30.** On every NSE session (A7's calendar), after 15:30 IST, read NSE's
> public `/api/allIndices` with the existing `nse_json` client and A4's `NseLevelSource` parsing:
> - **What it records:** NIFTY 50, NIFTY BANK and INDIA VIX (last, previous close, NSE's own time stamp). It also
>   records FINNIFTY and MIDCPNIFTY, because they cost nothing extra.
> - **When it reads:**
>   - It reads from 15:32 and retries every 60 seconds until 15:44.
>   - A read counts only when NSE's time stamp is 15:30 or later, the market status says closed, and the value is
>     unchanged across two reads 60 seconds apart.
>   - Otherwise it records "close not settled by 15:44", sends one alert to #fno-desk, and leaves the value empty.
> - **Where it is kept:**
>   - The raw answer goes to Drive write-once (O9's data store), with its SHA-256 receipt under `receipts/`.
>   - A small parsed record goes into the repository: day, index, value, NSE time, read time, "provisional".
> - **How it is confirmed:**
>   - After the evening file (O6's index-closes job, 21:11 IST), a `confirm` command compares each provisional value
>     with the official close.
>   - Equal within 0.01 point means "confirmed". Otherwise it records "differs by X", and the next evening edition
>     shows the correction (part 1).
> - **How it runs:** as O1's `close_read` step, `NotBefore(15:32)`, before `lab_close`. It needs no Groww and no new
>   schedule.
> - **Rules:** read-only public data, never an order; no Groww call.
> - **Tests:**
>   - the parser runs on recorded NSE answers (an unchanged value, a changing value, a stale time, a missing index,
>     an error page);
>   - the settle rule;
>   - the Drive receipt;
>   - the confirm comparison;
>   - the calendar's closed day.

**Size.**
- About 250 lines of code (`fno/close_read/`: source, settle rule, store, confirm, wiring, CLI) and about 300 lines
  of tests.
- It reuses `nse_json`, the allIndices parsing in `fno/quotes/market_levels.py`, O9's store and A7's calendar.

**Lane.** Lane 1 (NSE, Drive, O1's steps).

**Owner.** I can build it, if the orchestrator assigns it and no row covers it.
- Today `fno/quotes/market_levels.py` (A4) reads the same endpoint for VIX at 3 pm.
- `fno/pipeline/index_closes.py` (O6) does the evening confirm source.
- Their owners should agree before I add a register row.

**Validation before go-live.** Run the read for 5 sessions in "record only" mode. Compare with the official file.
Report every difference before the edition uses it.

## 3. The morning edition: what runs at about 08:50, and from where

**What runs.** One Claude routine session (an owner scheduled task, cloud), doing the following:
1. Run `sh tools/routine_setup.sh`. Groww is not needed, so no `--groww`. Chromium is already in the image at
   `/opt/pw-browsers/chromium`.
2. Run `python -m fno lab open`, which uses:
   - the Drive settings (`FNO_GDRIVE_*`) to read the sealed forecast through the verified Drive cache;
   - `FNO_SLACK_BOT_TOKEN` to post to #fno-forecast.
   It needs no Groww and no NSE.
3. Commit its write-once record, and the conversation note if any.

**Why not GitHub.** GitHub's cron starts 4-5 hours late here, as stated, so it would miss 09:15.

**Timing.**
- Setup in the 14:33 routine is allowed up to about 20 minutes.
- Starting at **08:38** posts by about 08:55 and leaves 20 minutes of margin before 09:15.
- It is also the time A22's story asks for, so when A22 is built the same routine runs both. A second morning task
  is then not needed, and there is one place to look.
- `lab open` refuses to post after 09:15. It prints "too late, not posted" with one alert, because a forecast shown
  after the open is not a forecast.

**Stored prompt (draft, for the owner to create; I create nothing).**

- Name: `Omenix F&O morning routine`
- Schedule: `CRON_TZ=Asia/Kolkata 38 8 * * *`. It runs every day, and NSE's calendar decides the day: a closed day
  prints "not a trading day" and posts nothing. This covers special weekend sessions as the 14:33 routine does.
- Prompt, exactly: `Run the morning routine in CLAUDE.md, section 'Morning routine'.`

**CLAUDE.md section to add with the code** (lane 1, the same branch):

> ## Morning routine (story FL1-1d; A22's pre-open capture joins it when built)
> Started by the owner's scheduled session at 08:38 IST every day; its stored prompt is exactly: "Run the morning
> routine in CLAUDE.md, section 'Morning routine'." Research and paper trading only: never places orders.
> 1. `sh tools/routine_setup.sh` (prints "routine setup ok").
> 2. `python -m fno lab open`. The NSE calendar decides the day: "not a trading day" on a closed day. Otherwise it
>    posts today's forecast to #fno-forecast before 09:15 and commits its record. It ends with `morning done` or
>    `morning done with problems: <lines>` (exit 1).
> 3. If it printed "alert NOT sent", post those lines to #fno-desk (`C0C89E8QCCD`) with the Slack connector. Note
>    any result other than `morning done` in `conversations/<date>.md`, then commit and push
>    (`git pull --no-rebase` first).

**Cheaper alternative, option (b).** Until A22 exists, add today's forecast for the next session (already written at
15:45) to the evening edition, and start the morning routine only when A22 is built. That means one post a day
instead of two, with the same information. The owner chose two editions; I recommend (b) only for the period
before A22, and the owner decides.

## What I need back

1. Whether the owner takes the morning edition now, or option (b) until A22.
2. Story id and owner for the close read (A4h proposed), with A4's and O6's owners agreeing.
3. The switch-on rule question from my earlier message (f2293cea against the f21a8966 hold), still open.

I start nothing new until Judge E's FL1-1c verdict and these answers.
