# Story FL1-1d: the forecast report in two editions, with reasons

**Status:** story text, for the judge (lane 1). Code starts after Judge E's FL1-1c verdict, and FL1-1c's merge.

**Owner:** the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd).

**Agreed with:** the orchestrator, the O1 builder (014zYLf1) and the designer (014fc2LA).

**Two parts (orchestrator, 22 Oct), each judged on its own:**
- **FL1-1d-1:** editions, the two commands, records per edition, the evening close through A4h's port, the morning
  confirmation, and O1's `lab_close` removal. Design items 1, 2, 4 (without `cues`, `why` and `levels`), 7 and 8;
  acceptance criteria 1, 2, 5, 6 and 7.
- **FL1-1d-2:** the Sections and key points, the evening levels table and the data fetches. Design items 3, 4 (`cues`,
  `why`, `levels`), 6 and 9; acceptance criteria 3, 4 and 8.
  - The release check waits for the owner the orchestrator assigns to A8's job. Until then, anything with no
    release evidence shows "not out yet", and no new schedule is added.
- **Design sign-off:** the designer's renderer is not wired until the owner signs off the design (orchestrator).

**Owner decisions (DESK_DECISIONS):**
- **`docs/DESK_DECISIONS.md` line 284:** forecast before the open, check after the close.
- **bcbbc454:**
  - a morning edition at 08:50 and an evening edition after NSE's evening files;
  - new owner scheduled tasks;
  - the US closes may be shown.
- **f9737bce:** the reasons in both editions, 2-4 key points, one page and one picture with both indices.
- **The owner's minute (DESK_DECISIONS line 287):** evening at about 20:05 (start 19:53).
- **Responses:** 303 and 304 (measured file times).

Research and paper trading only: nothing here places, changes or cancels an order. Groww is not used.

## What the owner gets

**Morning, by 08:50 IST: "Today's forecast".** One message in #fno-forecast with 3 text lines, one picture showing
both indices, and one details file. For each index:
- today's range, which is the forecast sealed the session before for today's close;
- the 3-session outlook;
- the last official close;
- the track record light;
- "Why this forecast": 2-4 points.

**Evening, about 20:05 IST: "Was today's forecast right?"** The same delivery. For each index:
- today's official close against the range sealed for today;
- the track record including today;
- "Why it was right / wrong": 2-4 points;
- the levels table: PCR, the biggest call and put OI strikes, max pain, FII and DII cash, and FII index futures.

The one-day lag of FL1-1 goes: a forecast is checked on the evening of its own target day.

## The honest limits (evidence labels as in CLAUDE.md)

1. **Until A22 lands, the morning range adds no new information.** Today's range was sealed at 15:45 the day before;
   the morning edition adds the overnight context. Reasoning only.
2. **Context is not cause.** "Why this forecast" separates two kinds of point:
   - what the forecaster actually uses, marked **used** (the option-implied range uses the option prices, and rv20,
     hist750 and ewma_t4 use past closes). **No G13b method reads India VIX or any global cue.** Checked: no file in `fno/price_ranges/` or
     `fno/price_distribution/` mentions them. So VIX is context too, even though the orchestrator's list calls the
     forecast "built from the VIX level". The implied range and VIX move together because both come from option
     prices; that is a correlation, not an input. Strong evidence: code;
   - everything else, marked **context**.

   The morning page never says a cue "means" a move. Its reasons are only facts.
3. **An evening reason is after the fact.** It is a fact in our data that crossed a stated limit, never a proven
   cause. This rule is FL1-1c's and is kept.
4. **The evening close is NSE's live index list, not the official file.** The official close file (`ind_close_all`)
   appears at 23:20; its Last-Modified time was 23:20 on all of 15, 16, 19 and 21 Oct.
   - On 21 Oct the index list, stamped 15:30, matched the file exactly for NIFTY (22,811.35) and BANKNIFTY
     (54,976.90). It did not match for India VIX: 15.70 against 15.68. Some evidence: one day.
   - So the evening close is labelled "NSE close, confirmed tomorrow", and VIX is labelled "official later".
   - The next morning confirms it against the file. If the inside/outside verdict changes, a correction line is shown
     and one #fno-desk alert is sent.

## Design

The parts already built are reused unchanged:
- FL1-1's coverage and seals;
- FL1-1c's page model, plain words, reasons, history, renderers' port, camera, poster and write-once record.

What changes or is new:

**1. Editions.**
- `Edition` has two values: `MORNING` and `EVENING`.
- `PageBuilder.build(day, now, edition, alerts, checks)`.
- **Records and keys:** one write-once record per day and edition. The record key gains the edition, so a rerun
  never posts twice; `Delivery.may_have_posted` is kept.
- **Morning:**
  - `today` holds the ranges sealed for **today**: N1 from the previous session, and N3 targets.
  - `price` is the previous session's official close, with `price_at` reading "close Fri 16 Oct".
  - If the official file is not archived yet, the price is NSE's close, labelled as such.
- **Evening:**
  - The N1 timeline's last `Outcome` is today, with `provisional=True` until it is confirmed.
  - A G13b official score, when there is one, always wins.

**2. Commands.**
- `python -m fno lab open` (morning) and `python -m fno lab close` (evening).
- Each prints one end line: `<edition> done` or `<edition> done with problems: ...` (exit 1).
- A run outside its window (morning after 09:15) posts nothing and says so with one alert.
- On a closed day each prints "not a trading day" (NSE calendar, A7).

**3. Reasons as Sections.** `Section` is an ABC: one class per source, each reading one source.
- `read(day, edition)` returns a `SectionResult`:
  - `status`: one of `available`, `not_out_yet`, `not_available` or `failed`;
  - `as_of`: the data's own date;
  - `items`: a tuple of `Cue`.
- `Cue` holds `name`, `value`, `change` (optional), `unit`, `as_of`, `role` ("used" or "context") and `text`
  (optional, for event flags).
- **Status rules:**
  - Each Section has its own **expected as-of rule**, in the table below (judge 438). A value outside its rule shows
    "not out yet", never as current.
  - Every rule has its own test.
  - `failed` is a read error. It sends one #fno-desk alert and is listed under the system line.
- **Wiring:** sections are wired in a list in `fno/forecast_lab/page_wiring.py`. Adding A17e, A22 or A19 later means
- **Expected as-of rules** (D = the edition's session day, in IST; "previous session" is from NSE's calendar):

  | Section | Morning (day D) | Evening (day D) | Shown as |
  |---|---|---|---|
  | NIFTY, BANKNIFTY close | the previous session's official close (`ind_close_all`) | D's close (NSE's index list, stamped D 15:30 or later) | value with its date |
  | India VIX | the previous session's official value | D's live value, "official later" | value with its date |
  | US closes (S&P 500, Nasdaq-100), US 10-year | the last US session before D's 09:15 IST open (A17's reader, `OPEN`, `live_only`) | the same as the morning | "US close Tue 20 Oct" |
  | USD/INR (RBI reference rate) | the latest rate dated on or before the previous session | the rate dated D, else the latest on or before the previous session, labelled with its date | value with its date |
  | Brent | the latest print at most 10 calendar days old (EIA prints lag: the newest was 14 Oct on 22 Oct) | the same | "last print Wed 14 Oct" |
  | Events, expiry flags | dated D | dated D | flag |
  | PCR, OI walls, max pain (F&O bhavcopy) | the previous session's (labelled "as of") | D only | value with its date |
  | FII index futures (participant OI) | the previous session's (labelled "as of") | D only | value with its date |
  | FII and DII cash | the previous session's (labelled "as of") | D only | value with its date |

  - A value that is older than its rule allows is "not out yet" in the evening, and "not available" in the morning.
  - Brent's 10 days is a stated limit, not evidence of a right number. It shows the latest price with its date, and
    never presents an old price as today's.
  one new class plus one line.
- **Reasons for every miss in the 30-day window** (the designer's "when it was wrong" table lists 30 days; FL1-1c
  gives reasons for 7 only). FL1-1c's `recent_misses` window widens from 7 to 30 sessions. The same direction-aware
  facts and limits apply, and each day's facts are read as known on that day.
- **Choosing the 2-4 key points** is plain code with a stated order, not a model:
  - in the morning: the used inputs first, then events, then the context cues by size of change against the cue's
    own 60-session spread, up to 4 points;
  - in the evening: FL1-1c's direction-aware reasons first, then the largest context moves the same way as the miss.
- **The levels table** (evening): a `LevelsSection` holding PCR (today and previous), call wall, put wall and max pain
  for both indices. FII cash, DII cash and FII index futures net contracts are given for NIFTY only. Each comes with
  its data date.

**4. Page model additions** (the designer reads them through `pageview.adapt`; names agreed with the designer):
- `PageView` gets:
  - `edition`;
  - `cues: tuple[SectionView, ...]`, where `SectionView` holds `name`, `status`, `as_of` and `items: tuple[Cue, ...]`;
  - `confirmation`: yesterday's close confirmed, or the correction line.
- `IndexView` gets:
  - `why: tuple[Cue, ...]`, the 2-4 chosen points, each marked used or context;
  - `levels: tuple[Cue, ...]`, evening only;
  - `backtested` (judge 434).
- `Outcome` gets `provisional: bool`.
- The record words ("right" and its split into Correct and Close call) take the designer's wording on
  `story/fl1-report-design`; FL1-1d invents no wording of its own.

**5. Picture.**
- One picture per edition, with both indices, 1100 px wide at 2x (the designer's size).
- The renderer port gains `render(view)` for each edition. The designer's renderer replaces the interim one when the
  owner signs off.

**6. Data the evening routine fetches itself.** Our GitHub jobs run too late for it: flows at 21:10, index closes at
21:11, the F&O archive about 21:41, all starting late. Each fetch uses the existing idempotent command, which writes
write-once to Drive with its receipt and manifest row and never duplicates:
- `python -m fno data-librarian fo-bhavcopy --from D --to D` (A9);
- `python -m fno data-librarian participant-oi --from D --to D` (A8);
- `python -m fno data-snapshot fii-dii-cash-by-session` (P8);
- NSE's index list through A4h's reader (see 7).

The morning routine runs `python -m fno data-librarian index-close --from D-1 --to D-1` for the official close and
VIX.

**The overnight cues are read, never fetched** (agreed with the A17 builder, 01MBnbVU, 22 Oct). Running
`global-cues fill` from the routine would put two writers on A17's append-only tables and logs, and would own the
day's once-only Cboe and Nasdaq download. The page reads instead:
- **Now:** `fno.global_cues.wiring.build_reader(include_private=True).read(cue, day, OPEN, live_only=True)`, with
  `OPEN` from `fno.global_cues.as_of`. It needs the Drive settings for the private S&P 500 and Nasdaq-100 tables.
- **After A17e merges:** `build_index_reader()` for the Nasdaq-100, plus Asia, Europe and VIX. It takes Yahoo's
  on-time close until Nasdaq's own close arrives, and marks such values.
- **Missing values:** a reading of `none` or `behind` shows as "not out yet". A17e's own `behind` alert already
  tells #fno-desk at 09:15, so this story sends none.
- **Privacy (owner, bcbbc454):** the US values may appear in the owner's Slack and in the Drive record only, never in
  a repository file. That includes test fixtures (made-up levels only), receipts (SHA-256 only) and the conversation
  log.

Each fetch belongs to another story's owner, and this story only calls it. Before code starts, each owner agrees:
A9 and A8 (through the orchestrator, since A8 has no register row), P8 (no live owner; the orchestrator assigns one),
and the owners of the morning's `data-librarian index-close` fetch (the A9 librarian's command; the O6 index-closes
job archives the same file at 21:11). A17 is agreed as read-only, above.

Two rules for every librarian fetch (from the A20/A22 builder, who last changed the librarian; reasoning only):
- **A file not published yet is not a failure.** The librarian exits 1 with "not published" while NSE has not
  released the file (the bhavcopy's Last-Modified reached 19:46 in the measured days). The routine shows "not out
  yet", with no alert. Only a different error is `failed`.
- **The manifest push can race** with `panel-days.yml`, which commits the same manifest later. The first push wins.
  A refused push is pulled and retried once (item 8's rule), and a second librarian run finds the file "already
  there".


**7. The close read (A4h, owned by the A4 builder 01MKtUHB).** A simpler design is proposed to them:
- The evening routine reads `/api/allIndices` at about 19:55 and accepts the answer only if NSE's stamp is today
  15:30 or later.
- The 21 Oct read, made hours later, still carried "21-Oct-2026 15:30" and the close values.
- If this holds, A4h needs no 15:32-15:44 window, no O1 step and no settle rule. A4h's owner decides; FL1-1d reads
  through A4h's port either way.

**8. O1** (agreed with 014zYLf1, their 4 conditions):
- `lab_close` is removed fully, and only it: from `DAILY_RUN_STEPS` and `LIVE_STEPS`, from its wiring and import,
  and the config key. The test lists are reverted.
- A test proves that no run-log reader fails on an old `lab_close` entry.
- `daily.live_from.lab_close` stays null until this story merges, so a 15:45 post can never take the evening's
  idempotent record.
- Each routine commits only its own paths (`receipts/data/forecast_lab/v1/<edition>/` and the fetchers' manifest
  rows): `git pull --no-rebase` first, the record scan on, never `--no-verify`.
  - If a push fails, the routine pulls and retries once.
  - If it fails again, it prints "receipt NOT pushed", posts one #fno-desk alert and notes it in the conversation log.
  - The Drive copy is the record, and the next run's librarian finds it ("already there") and writes the missing
    manifest row.

**9. Release check (10 sessions; the owner's request, built here; A8's owner told).**
- What is built: inside the evening routine only, from 19:53. For the F&O bhavcopy and participant OI it records each
  file's Last-Modified; for FII/DII, the first read whose date is D.
- Its log is append-only, in A8's release log format.
- The 17:00-19:53 part needs a schedule the owner has not approved, so it is **not** built. Two sources cover that
  window instead: the evening run's own reads, and NSE's Last-Modified headers, which match A8's first-seen log to
  the minute for participant OI.
- FII/DII is the one item with no Last-Modified header, so its time can only be seen by polling.
  - The cheapest route is a check added to A8's existing `participant-oi-watch` job, which runs every 15 minutes from
    16:37 to 23:22 IST. GitHub may start it late, so the time it records is the first time the job saw the figures,
    an upper bound on NSE's release.
  - A8's owner decides; until then, the evening run's own read is the only evidence.
- After 10 sessions, the evening minute is re-proposed from the evidence.

## Day 1 and later

| Item | Edition | Day 1 | Later |
|---|---|---|---|
| Today's range (G13b N1, sealed) | morning | yes | G13b's N0 cannot be ready by 08:50 (it needs the 09:09 pre-open); see the note below |
| Last official close, VIX close | morning | yes, by fetching `ind_close_all` (out 23:20 the night before) | |
| Events (RBI policy, Budget), expiry flags | both | yes (A6 events, A20a lot and expiry files) | macro dates with A20c |
| US closes (S&P 500, Nasdaq 100), US 10-year | both | normally yes: A17's 03:41 run committed at 05:30-06:40 IST on 17-21 Oct (A17 builder, measured); else **not out yet** | |
| Brent, USD/INR (RBI) | both | yes, with its own print date | |
| GIFT Nifty, pre-open | morning | not available | A22: one day file pushed at about 09:11 (A22 builder), after the 08:50 post; see the note below |
| Asia and Europe | both | not available | A17e |
| News headlines | morning | not available | A19 |
| Today's close | evening | yes (NSE index list, A4h's reader) | |
| PCR, OI walls, max pain | evening | yes if the F&O bhavcopy is out (18:40-19:46 seen), else not out yet | |
| FII index futures net | evening | yes if participant OI is out (18:36-19:38 seen) | |
| FII and DII cash | evening | when out; time not yet measured (release check) | |
| Direction-aware miss reasons | evening | yes (FL1-1c) | global markets with A17e |

**A22 timing (open, for the owner).**
- A22's day row holds GIFT Nifty (read at 08:40) and the pre-open (09:08-09:14). It is one write-once file pushed at
  about 09:11, so nothing from A22 can be in an 08:50 post.
- Options:
  - (a) A22 writes GIFT separately at about 08:42, and the 08:50 edition shows it as context;
  - (b) a short second post at about 09:12 with N0 and the pre-open, which is FL1-2's 09:15 report;
  - (c) both. The builder's recommendation is (c).
- Until the owner chooses, this story does not read A22. Its reader (O9's DriveCache, `fno.preopen.day_row`) plugs in
  behind a Section later.

## Acceptance criteria

1. **Morning:** on a session day, `lab open` posts by 09:15 with today's sealed range for both indices, the outlook,
   the last close and the light. After 09:15 it posts nothing and alerts once.
2. **Evening:** `lab close` checks today's target against today's close for both indices, labelled until it is
   confirmed.
   - The next morning, the close is confirmed against the official file.
   - A verdict change produces a correction line and one alert.
3. **Sections:**
   - Every section is in exactly one state.
   - Every Section follows its expected as-of rule (the table under design item 3). A value outside the rule is never
     shown as current. There is one test per rule.
   - `failed` alerts once.
   - A new section is one class plus one line in the wiring (shown by a test with a fake section).
4. **Key points:** at most 4 key points per index, chosen by the stated order. Each is marked used or context, and no
   morning point is a cause.
5. **Records:** one write-once record per day and edition. A rerun never posts twice; may-have-posted is kept.
6. **O1:** O1's 4 conditions are met, including the run-log reader test.
7. **Commits:** each routine commits only its own paths, with the push-failure rule above.
8. **Release log:** append-only.
9. **Size:** no file or class over 350 lines. Tests cover every state of every section and both editions end to end
   (O11's replay extended).
10. **Mutation runs:** at least 12 planted mutations, every one caught.

## Go-live conditions

1. The CLAUDE.md sections "Morning routine" and "Evening routine" are written by the FL1 builder in FL1-1d-1, from
   response 304's drafts. They are lane 1 and merge with the code.
2. The owner creates the two scheduled tasks with response 304's exact stored prompts. The orchestrator gives the
   steps to the owner (DESK_DECISIONS line 284: "the owner creates it"); no session creates them.
3. The owner signs off the designer's page, and the designer's renderer is wired.
4. A first live run of each edition is checked against its record before the next day's run.

## Judge verifies

1. The used/context split is true to the forecasters' code: no G13b method reads a cue marked "used" unless it does.
2. No section can show stale data as today's.
3. The evening close label and the confirmation path.
4. That every other story's command this story calls is agreed by its owner, and run unchanged.
5. That nothing posts outside the three F&O channels.

**Size estimate:**
- FL1-1d-1: about 400 lines of code and 450 lines of tests.
- FL1-1d-2: about 500 lines of code and 550 lines of tests.

## FL1-1d-2 as built (22 Oct), and where it differs from the text above

Each difference below was decided by the orchestrator or by measurement; none is silent.

1. **The morning's own result (orchestrator, 22 Oct: "yes").** When G13b has not scored the previous session yet
   (it scores in the 14:33 run), the morning checks the previous session's forecast against NSE's official close.
   It reads G13b's tables first, then the archived index-close file itself (`official_closes.ArchivedCloses` over
   G13b's own `IndexFileCloses`).
   - That result is `IndexView.result`, labelled "NSE's official close; G13b's score follows".
   - A day the evening could not check (no A4h close) thus gets its result the next morning. The evening's line now
     says exactly that, and nothing more.
2. **The official file's timing (the A4 builder's correction to response 304).** The index-close file's first
   version appears before 23:20: our archive committed it by 23:04 on 21 Oct. 23:20 is the rewrite's Last-Modified.
   The morning's fetch (`data-librarian index-close`) is step 1b of the routine section.
3. **The release check covers the F&O bhavcopy and FII/DII cash only.** Participant OI is already measured by A8's
   own watch job (16:37-23:22), and one builder per function means it is not checked a second time.
   `python -m fno lab release-check` is read-only and never fails. Its logs are under
   `research/data/forecast_lab/release/`.
4. **In the evening, "the same way as the miss" applies to the US equity cues only** (the S&P 500 and the
   Nasdaq-100: up for a miss above, down for a miss below). Calling any other cue's direction "the miss's way" would
   be a claim about how it moves NIFTY, which this story does not make. The other cues follow by size, labelled
   context.
5. **India VIX is not shown in the evening.** NSE's index list gave 15.70 for 21 Oct, against an official 15.68, so
   the list's value is never passed off as the close. The morning shows the previous session's official VIX, read
   from the archived file.
6. **GIFT Nifty (owner, (c) "Both").**
   - At 08:50 GIFT Nifty is a context Section that reads A22b's early file (`preopen/gift/...`), once A22b merges.
     Until then it says "not available" with why. A missing file at 08:50 is named in the edition itself
     ("GIFT Nifty: not available"), so O8 needs no 08:50 row (judge 445's minor).
   - The 09:12 post with N0 and the pre-open price belongs to FL1-2 (the 09:15 report), so no second builder makes
     it.
7. **Levels.**
   - The levels use the nearest expiry of each index.
   - A chain with one side only shows "none in the file" for the missing wall, never a made-up value.
   - A file not out yet shows "not out yet".
   - A read error is a `failed` Section: said in the system line and alerted once.
8. **The librarian's words are pinned by a test** (`test_librarian_words.py`). "not published by the source" is the
   only "not out yet" line. If A9 rewords it, the test fails, and the routine step changes with it.

Not built yet, waiting on others:
- A4h's `TodayCloses` adapter, which reads `closes/<yyyy>/<mm>/<day>.json` once A4h merges;
- the GIFT adapter, once A22b merges;
- the designer's renderer, which the designer ports and I wire with one line.
