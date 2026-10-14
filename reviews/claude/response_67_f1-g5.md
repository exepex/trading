# Response 67: stories F1 and G5, the Hybrid (Book 2) and AI team (Book 3) daily forecasts (design note and claims)

Stories: `docs/stories/F-ai-layer.md` F1 (forecast part only) and `docs/stories/G-forecasts.md` G5. Builder: Claude,
13 Oct 2026, after the owner's decision to start Books 2 and 3's forecasts before the pause (`docs/DESK_DECISIONS.md`).
Research data only; nothing here places, modifies or cancels orders.

## 0. The verdict in two lines

Both AI books can answer the five G1 questions every session day from the same frozen v2 pack, each in its own
routine fired by the existing `forecast-capture` GitHub Actions job, with server-side receipt times and nothing
imputed. **Isolation from the other AI book's same-day answer is enforced (sealed answers); full F1 isolation (no
repository, no network) is not**, because the owner's design gives each routine the public repository; section 3 says
exactly what that leaves open and why I still recommend starting (reasoning only).

## 1. Design

### 1.1 Timeline of one session day (IST)

| Time | Who | What |
|---|---|---|
| 14:55-15:10 | 3 pm recorders | the A4 snapshot (unchanged) |
| 15:10-15:13 | `forecast-capture.yml` | builds the v2 pack, the baselines and Book 1 (unchanged code, frozen); **commits the pack only** and keeps Book 1's records on the runner |
| right after | same job, `python -m fno ai fire` | fires the two routines, one pointer each (section 1.3); one Slack line per failure |
| about 15:11-15:14 | each routine | starts `pip install` in the background, `python -m fno.ai brief` (no install needed) → reasons → `python -m fno.ai seal` pushes a **sealed commitment** (a SHA-256 of its answer and a random salt) to `main` |
| **15:15:00** | GitHub's server clock | **receipt deadline**: a commitment whose push GitHub logged after 15:15:00 is late |
| from 15:15:10 | each routine | `python -m fno.ai reveal` pushes the answer and the salt (its hash must match the commitment) |
| 15:16-15:30 | the Actions job, `python -m fno ai collect` | waits for both reveals (at most until 15:30), reads each push time from GitHub's activity log, validates, writes the records; then commits Book 1's and the AI books' records together and prints one receipt line per book |

The protocol v2 rules stay: the forecasts' cutoff is 15:00:00 (the pack), the deadline 15:15:00 (`ForecastRecordV2
.on_time`, with `generated_at` = the commitment's server receipt time), write once.

### 1.2 The per-book prompt (versioned in the repository) and its inputs

- **Prompt files:** `agents/forecast/book2_hybrid_v1.md` and `agents/forecast/book3_ai_v1.md`. Their SHA-256 is
  registered in `fno/ai/versions.py`; `brief` refuses to run if the file's bytes differ from the registered hash, so a
  prompt can change only as a new version (`v2` file plus one registry line). The version label in every record is
  `book2_hybrid/v1/sha256:<prompt hash>` (like Book 1's `book1/v1/sha256:<method hash>`).
- **The routine's pasted prompt** is only a bootstrap: pull `main`, run `python -m fno.ai brief '<fired text>'`, and
  follow the versioned prompt that command prints. So the routine reads its version from the repository.
- **Common input (both books), built by code and hashed (`export_sha256`):** the day's v2 pack exactly as committed
  (15:00 spot, 15:00 VIX, futures, each expiry's ATM IV, IV30 and its status, the problems list), the official NIFTY
  and VIX closes of the last 260 sessions before the day (no 2019-2023 row: the holdout stays closed), and three
  derived facts from those numbers (trailing RV20 with the 15:00 spot as today's close, the 15:00 change against
  yesterday's close for NIFTY and VIX). The five questions' exact definitions are in the prompt.
- **Hybrid only (its private input):** the rules' numbers for the day, i.e. the three baselines and Book 1's
  probability per question, and its **envelope**: per question, from 0.10 below the lowest available baseline to 0.10
  above the highest, inside [0, 1]. No baseline for a question means no envelope and Hybrid must answer "no forecast".
  Hybrid's answer outside its envelope is refused for that question (recorded as "no forecast (outside envelope)"
  with the attempted value kept in the audit file), never replaced by the rule default (that would be imputing).
- **AI team only:** nothing more. It never receives the rules' numbers.
- **Answer (JSON, both books):** book, day, pack and export hashes, version, the model it reports, and per question a
  probability (or null for "no forecast") with a reason of at most 600 characters.

**One conflict with the owner's words, stated openly:** "Hybrid = the AI decides inside the rules' envelope" needs the
rules' numbers, and Book 1 is the mean of the baselines, so Hybrid effectively sees Book 1's forecast. Story F5 does
the same (the rule default in Hybrid's private pack). I built it that way; "never sees Book 1's" holds for the AI team
only. If the owner wants Hybrid blind to the rules too, the only change is an empty `rules` input, but then Hybrid and
the AI team are the same experiment.

### 1.3 The fired text (untrusted data to the routine)

One line of JSON, under 2 KB, never instructions: `{"book", "day", "pack_sha256", "version", "rules"}` (`rules` only
for Hybrid). `brief` parses it strictly (known book, registered version, a 64-hex pack hash that matches the committed
pack, rules only for Hybrid, probabilities in [0, 1]) and refuses anything else before printing a word of input. The
pasted prompt also refuses a text with a single quote or more than one line (as O6). The rules cannot be checked
against the repository at 15:11 (they are not committed yet, on purpose); `collect` rebuilds the export from the
committed files and refuses an answer whose `export_sha256` differs.

### 1.4 Isolation mechanism

| Leak | How it is stopped | Strength |
|---|---|---|
| The other AI book's same-day answer | sealed commitment before 15:15:00, answer revealed only after 15:15:00; a reveal GitHub logged before the other book's commitment marks the other book `exposed` (unscored) | **prevented** (a SHA-256 with a 128-bit salt reveals nothing) |
| Book 1's and the baselines' same-day records (AI team) | not in the repository before `collect` (after 15:15); never in the AI team's input | prevented as files; see section 3 for recomputation |
| Credentials | a new cloud environment with no environment variables, no connectors; the only write path is the session's own Git push | prevented |
| Older days' records of other books, the live market after 15:00, re-running the public forecast code | forbidden by the versioned prompt; the session link is recorded so the judge can read the transcript | **detected only, not prevented** |

### 1.5 Record schema

- `research/forecasts/ai_v1/<YYYY>/<d>_<book>_forecasts.csv`: five rows in the frozen v2 schema
  (`fno/forecast/schema_v2.py`, unchanged): `book, date, cutoff (15:00 IST), question, probability (empty = no
  forecast), method_or_version (book version and prompt hash), pack_sha256, input_mode (live_1500_proxy), iv30_status,
  generated_at (the commitment's receipt time from GitHub, or the collection time when there is none)`.
- `research/forecasts/ai_v1/<YYYY>/<d>_<book>_audit.json`: the status (`on_time`, `late`, `not_revealed`,
  `invalid`, `not_fired`, `no_submission`), per question the outcome and the attempted value, every reason, the
  commitment and reveal commits with their GitHub receipt times, the model the book reported against the registered
  one, `exposed`, the fire's session link and the isolation label (`sealed_same_day`). Strategy internals (reasons)
  are recorded here for audit; screens must not show them (dashboard rule).
- `research/forecasts/ai_v1/submissions/<YYYY>/<d>_<book>.commitment.json` and `.reveal.json`: what the book pushed.

### 1.6 Failures (all recorded, never imputed)

| Case | Record |
|---|---|
| fire refused, token expired, routine not configured | five "no forecast" rows, status `not_fired`; one #fno-desk line from the fire step |
| the session fails, hits a usage limit, or never pushes | `no_submission` (F1's "AI unavailable") |
| commitment received after 15:15:00 | `late`: five "no forecast" rows, the answer kept in the audit file |
| no reveal by 15:30, or a reveal that does not hash to the commitment | `not_revealed` / `invalid` |
| wrong pack, export, version or book; malformed JSON | `invalid` |
| one question outside Hybrid's envelope, or not a probability | that question "no forecast", the rest stand |
| a reported model different from the registered one | records kept, audit `model_mismatch: true`; G4 must not score them (F1 criterion 4) |
| GitHub's activity log cannot be read | receipt unknown, treated as late (fails closed) |
| not a trading day | nothing fired, nothing recorded (the capture prints "not a trading day") |

### 1.7 Cost per day in routine runs

**2 routine runs per session day** (about 42 a month), on the owner's subscription, no API key. Estimate (reasoning
plus one measurement): O6's dry-run session, 4 turns, cost USD 0.13 at list price on Sonnet, mostly fixed start-up
context. A forecast session has about 8-10 turns and a few thousand output tokens, so roughly USD 0.3-0.5 a run on
Sonnet and USD 1-2 on Opus at list price, i.e. about USD 15-80 a month of plan usage, not a bill. The sessions also
sleep about 1-3 minutes waiting for 15:15 (no tokens). The plan's daily routine-run limit must cover these 2 plus the
existing F&O routines (owner to check on the Routines page).

## 2. What was built

- **`fno/ai/`**, two sides with their own composition roots:
  - routine side (`python -m fno.ai brief | seal | reveal`, standard library only, so it runs before any install;
    `fno/ai/book_wiring.py`): `pointer.py` (the fired text, checked field by field), `versions.py` (registered
    prompt, hash, model, envelope width), `export.py` (the allowlisted input and its hash), `envelope.py`,
    `answer.py` (one check used by `seal` and by `collect`), `seal.py` (commitment and reveal), `transport.py`
    (`SubmissionTransport` interface; `GitMainTransport` pushes one file to `main`, through the O5 hook), `book.py`;
  - Actions side (`python -m fno ai fire | reveals-ready | collect | coverage`; `fno/ai/wiring.py`): `fire.py` (O6's
    `RoutineTrigger`, one pointer per book, fire log), `receipts.py` (`PushReceipts` interface;
    `GitHubActivityReceipts` reads GitHub's push log), `history.py`, `submissions.py`, `outcome.py` (statuses),
    `collect.py`, `record_writer.py` (frozen v2 schema, written once), `rules.py`, `coverage.py`, `timing.py`.
- **Prompts:** `agents/forecast/book2_hybrid_v1.md`, `agents/forecast/book3_ai_v1.md`.
- **Workflow:** `.github/workflows/forecast-capture.yml` now commits the pack alone, fires, waits for reveals (until
  15:30), collects, then commits Book 1's, the baselines' and the AI books' records together. The frozen v2 code is
  untouched (`require_version_frozen` passes at this commit).
- **Small changes elsewhere:** `fno/pipeline/trigger.py` takes any pointer with `to_text()` (a `FiredText` protocol;
  no behaviour change); constants for the four secret names and `AI_BOOKS`; `fno/cli.py` registers `ai`;
  `.gitignore` ignores the routine's `.ai_book/` working folder.
- **Owner checklist:** `docs/stories/F1-G5-owner-checklist.md` (environment, 2 routines with their exact prompts,
  4 secrets, what each problem looks like).
- **Tests (31, `tests/ai/`):** pointer and prompt checks, export allowlist with planted files, envelope, the routine's
  brief/seal/reveal with a fake transport, a real Git push to a bare remote, end-to-end fire → fake routines →
  collect for every status, GitHub's activity log with a fake HTTP client, coverage, and the workflow's step order.

## 3. Doubts and limits (read before trusting the comparison)

- **Full F1 isolation is not met.** The routines have the public repository and network: the AI team could re-run
  the public forecast code and so recompute the baselines, read earlier days' records of every book, or look at the
  live market after 15:00. The prompt forbids all three; only a transcript read can catch them. F1's own rule says
  such results are labelled "isolation not enforced" and are not an independent comparison until an enforceable mode
  exists. My recommendation (reasoning only): accept `sealed_same_day` for the forecast contest, because the baselines
  are deterministic functions of the same pack (public information, not another book's judgement), the other AI
  book's judgement is sealed, and the questions look 10-20 trading days ahead, so a few minutes of live market after
  15:00 adds little. Keep the full F1 design (no repository, no network, output read from the session log) for the
  trading decisions of slice 4. **The owner decides; G4's report must carry the label either way.**
- **The timing is tight (some evidence).** The pack exists at about 15:10-15:13 (protocol v2 waits until 15:10), and
  the commitment must reach GitHub by 15:15:00: about 2-4 minutes for session start, install, reading, reasoning and a
  push. The O6 dry-run session took 75 s for a trivial job. Expect some late days; they are recorded as late, never
  rescued. If more than 1 day in 5 is late in the first two weeks, the options are a faster model, a lighter install
  or a protocol version 3 with a later AI deadline (a frozen change, so ChatGPT and the judge first).
- **The receipt time is GitHub's activity log** (`GET /repos/{owner}/{repo}/activity`, server time of each push). I
  have not called it from a runner yet (some evidence: GitHub's documented API). If the first live day shows it
  unusable, every AI record is late (fails closed) and the fix is one class (`fno/ai/receipts.py`).
- **Model identity is self-reported** (the session reads its own `get_session` if the tool exists in routines); the
  session link from `/fire` lets the judge check it. A mismatch flags the day; an unknown model is flagged
  `model_unverified`.
- **Branch pushes:** both routines push to `main` (the path the 3 pm recorder routine already uses). Either routine
  could in principle overwrite the other's files; `collect` reads each file's first commit and its push time from
  GitHub, so a later rewrite cannot change a receipt.

## 4. Claims per criterion (status: awaiting judge)

### F1, forecast part (trading decisions stay for slice 4)

1. **Real isolated session: other books' data unreachable through every tool.** **NOT MET, by design.** The owner's
   design gives each routine the public repository, so another book's older records and the public code stay
   reachable; only the other AI book's same-day answer is made unreachable (sealed). Labelled `sealed_same_day` in
   every audit file; the owner decides whether the comparison counts (checklist step 7). The judge can read the first
   live sessions' transcripts (links in the audit files' `fire.session`).
2. **The export lists only allowed items; a planted file is refused.** MET in tests:
   `test_the_ai_teams_export_has_no_rules_and_no_planted_file_of_another_book` (Hybrid's commitment, reveal and
   records planted: the AI team's export hash unchanged, no rule number in it; a rules export for the AI team is
   refused) and `test_a_pointer_survives_its_text_and_every_wrong_field_is_refused` (the AI team's pointer with rules,
   unknown book, wrong version, extra field, out-of-range rule, not JSON, oversized).
3. **Late output ignored; not promoted in time fails closed.** MET in tests: a commitment GitHub received at 15:15:01
   records five "no forecast" rows (`test_a_commitment_received_after_1515_is_late_and_records_no_forecast`); a reveal
   missing from GitHub's log is `not_revealed` (`test_a_reveal_that_never_came_or_does_not_match_records_no_forecast`);
   an unreadable log fails closed (`test_an_unreadable_log_or_an_unknown_commit_fails_closed`). No fill exists for a
   forecast; the "promotion" is the collection, which waits at most until 15:30.
4. **A different served model leaves the day unscored.** PARTLY MET: the model is self-reported by the session (its
   own `get_session`), not read from the platform; a different model gives `model_mismatch` and five "no forecast"
   rows, an unknown one is flagged `unverified`
   (`test_a_different_served_model_leaves_the_day_unscored_and_unknown_is_flagged`). Reading the served model from the
   session record needs a Claude session with the session tools (not available to Actions); the judge can check it.
5. **A failed or limited session gives "no decision (AI unavailable)".** MET in tests: `no_submission` and
   `not_fired` each record five "no forecast" rows and the fire failure posts one #fno-desk line
   (`test_a_routine_that_never_answers_or_was_never_fired_records_no_forecast`). Scoreboards do not exist yet.
6. **No secret or credential; export and prompt scanned (O5).** MET by design, reasoning plus the scan: the fired
   text holds a day, hashes, a version and probabilities only; the books' environment has no variables (checklist
   step 1); every commitment and reveal is committed through the O5 hook (never `--no-verify`); `check_records.py`
   passes on every new file. Not testable before the owner creates the environment.
7. **Both pack hashes in the collected decision match the committed packs.** MET in tests: every record's
   `pack_sha256` is the committed pack's SHA-256 and the answer's `pack_sha256` and `export_sha256` must equal those
   rebuilt from the committed files (`test_on_time_sealed_answers_become_five_records_each_with_the_packs_hash`).

### G5

1. **Five probabilities per session day, or a recorded "no forecast".** MET in tests: every status writes exactly five
   v2 records; Hybrid loses only an out-of-envelope question
   (`test_a_hybrid_answer_outside_its_envelope_loses_that_question_only`). A day without a v2 pack records nothing for
   any book, Book 1 included (same rule as G3).
2. **Forecasts received after the receipt deadline are ignored.** MET (F1 criterion 3's tests).
3. **G4's report shows each book's coverage.** PARTLY MET: `python -m fno ai coverage` and `fno.ai.coverage` give pack
   days with a counted forecast per book, with "not yet running" days counted as missing
   (`test_coverage_counts_pack_days_with_a_counted_forecast`). **Gap:** G4 (`fno/forecast_scoring/`, built by another
   session the same night and with the judge) scores `research/forecasts/live_v2/` only, verified against the
   capture's Drive receipt. The AI books' records live in `research/forecasts/ai_v1/` and are verified differently
   (sealed submissions plus GitHub's push log, re-checked by `collect`). G4 needs one more source class for them and
   the coverage line in its report; I did not change G4 while it is with the judge. Until then, G4 shows no AI book
   at all, which is correct ("not yet running") but not yet the comparison.

Gates (14 Oct 2026, merged with main at 9931ef3): `python -m pytest -q` 1673 passed; `ruff check fno tests tools`, `ruff format --check`,
`tools/check_imports.py` and `tools/check_records.py` all pass; the v2 freeze check passes.

## Addendum 1 (14 Oct 2026, 02:15 IST): owner set up the routines and secrets; isolation recommendation

**Recommendation: accept `sealed_same_day` for the forecast contest, on three conditions** (reasoning only; no
live data yet):
1. **Every session's transcript is audited** for the first 10 session days, then 2 sessions a week chosen at random.
   A breach (opening any file other than what `brief` printed, any network use except the two Git pushes, running
   `fno.forecast` code, reading `research/forecasts/`) makes that book's day unscored, and two breaches in 20 days
   stop the contest for that book until the prompt or the design is fixed.
2. **The label stays on every record and every report**: "isolation: sealed same day (not full F1)".
3. **Trading decisions (slice 4) do not inherit it**: they need full F1 isolation (no repository, no network).

Why, by role: the statistician's real worry is one AI copying the other's judgement, and that is prevented. What
stays open is either public information (the baselines are a fixed function of the same pack; Book 1's past forecasts
are public) or a breach the transcript shows (a peek at the market after 15:00). The volatility trader's view: 10-20
trading-day questions barely move on 10 minutes of extra market. The red team's counterpoint, kept: a "fully AI"
book that quietly reruns the baselines is not fully AI; the audit catches it, and the scores would show it as
near-identical to Book 1.

**Owner's decision (14 Oct 2026):** "yes, accept sealed_same_day with your three conditions" (`docs/DESK_DECISIONS.md`).

## Addendum 2 (14 Oct 2026, about 03:30 IST): the owner's conditions 1 and 2 enforced (judge 62)

Judge 62 found conditions 1 and 2 written but not enforced. Checked against the code: correct on both. Built:

- **Condition 2, label on every record:** the isolation mode is now part of each book's registered version (D6 says
  the environment's isolation belongs to the version), so every record's `method_or_version` reads
  `<book>/v1/sha256:<prompt hash>/isolation:sealed_same_day`, and the audit JSON keeps `"isolation"`. The frozen v2
  schema is unchanged. (Before the first live run, so no sealed answer carries the old label.)
- **Condition 1, audit recorded:** `fno/ai/transcript_audit.py`: one record per audited book-day,
  `research/forecasts/ai_v1/<YYYY>/<d>_<book>_transcript_audit.json`, written once: session, version, auditor, time,
  `clean` or `breach` with named kinds (`file_outside_input`, `network_beyond_pushes`, `ran_forecast_code`,
  `read_other_records`) and the evidence. Command: `python -m fno ai audit-record --day --book [--breach KIND]
  --evidence --auditor`.
- **Which sessions:** `fno/ai/audit_plan.py`: every fired session of the first 10 fired session days, then 2 a week
  drawn with a seed fixed by the ISO week, drawn only after the week ends. `python -m fno ai audits-due` lists what is
  missing; its count rides in the daily #fno-desk line.
- **Unscored for the scorer:** `fno/ai/scoring_gate.py` `scoring_status(root, day, book, today)` is the one rule G4's
  AI reader must call: `scored` only when the collection said `on_time` and no breach was recorded; `unscored` for a
  breach (or any non-`on_time` status); `pending` while a selected session is unaudited or its week is still open to
  the draw. The records themselves stay write-once evidence; the unscored mark is the audit file beside them, read
  through this one function (the same pattern as G4's receipt check beside Book 1's records).
- **Stop after two breaches:** `fno/ai/stop_rule.py`: two breaches by a book in its last 20 session days, under its
  current version, and the fire step does not fire it, records `not_fired` with the reason and posts one #fno-desk
  line. A new registered version (the fix) starts clean.
- **Tests** (`tests/ai/test_owner_conditions.py`, planted breaches): the label on every record; written once and
  named kinds; a planted breach makes the day unscored while a clean one scores; a due audit keeps the day pending;
  two planted breaches stop Book 3's fire with the line while Hybrid (one breach) still fires; a new version is not
  stopped; the draw (all of the first 10 days, then exactly 2 per finished week, independent of order).

**For G4's session (fields to read, no code duplicated):** for each `research/forecasts/ai_v1/<YYYY>/<d>_<book>_forecasts.csv`
(v2 schema), call `fno.ai.scoring_gate.scoring_status(ROOT, day, book, today)`; score only `scored`; count `pending`
and `unscored` (with `reason`) in coverage; print `isolation` ("sealed same day, not full F1") beside the AI books;
coverage from `fno.ai.coverage.coverage`.

Gates: `python -m pytest -q` 1717 passed; ruff check and format clean; `check_imports` clean.

## Addendum 3 (14 Oct 2026, about 03:30 IST): the weekly draw's seed (judge 62 addendum 1)

Judge 62 addendum 1 found that the weekly draw's seed was the ISO week label alone, so a routine with the repository
could compute whether its session would be audited. Checked: correct. A commit SHA as the seed would be no better (both
routines push to `main`). Fixed:
- **Seed** (`fno/ai/draw_seed.py`): the week label, the date of the week's last session and NSE's official NIFTY 50
  close that day, taken from `research/data/nifty-panel/warmup_closes.csv` as written (O6 appends each close once,
  from the first archived version). Nobody controls the close, and nobody knows it until the week is over.
- **Only after the week:** a week gets a seed only once a later week's close is in the file, so its last close is final.
  Until then the draw does not run, and its sessions stay `pending` for the scorer.
- **Recorded:** `python -m fno ai audits-due` writes each new draw once to
  `research/forecasts/ai_v1/draws/<YYYY>-W<ww>.json`, holding the seed inputs and the sessions drawn. The forecast-capture
  job runs it before its records commit, so draws are committed and anyone can redraw them.
- **Tests** (`tests/ai/test_owner_conditions.py`):
  - no draw before a later close exists;
  - the same inputs give the same draw (in either order);
  - a different close gives a different seed;
  - 2 drawn per seeded week;
  - draws are recorded once with their seed inputs.
- `scoring_status(root, day, book)` lost its `today` argument; nothing outside `fno/ai` called it yet.
- The fire path is unchanged in this addendum.

Gates: `python -m pytest -q` 1784 passed; ruff clean; `check_imports` clean.

## Addendum 4 (14 Oct 2026, about 05:00 IST): the draw's close comes from the Drive archive (judge 62 addendum 2)

Judge 62 addendum 2: the draw ran after Monday's routines had push access to `main`. A routine could have edited
Friday's close in `warmup_closes.csv` and steered the draw. I checked this and the judge is right. While testing it I
found two more ways in that the judge did not name, and fixed them too:
- **blanking the close**, which made the reader skip the row;
- **deleting the row.**

Either one silently moved the seed to Thursday's close.

What changed:
- **Source** (`fno/ai/close_archive.py`): `CloseArchive` is an interface. Its `DriveIndexCloseArchive` adapter reads
  the index-close file in Drive's raw area, which holds the first archived version. Routines have no Drive access.
- **Checks** (`fno/ai/draw_seed.py`). The repository file names only the day and the archived file's SHA-256. A week is
  refused, and so not drawn, when:
  - the archived file's hash differs from that SHA-256;
  - the closes file's close differs from the archive's;
  - a close is blank or unreadable;
  - Drive holds a later session of that week that the closes file lacks.

  The seed is the archive's close. Each refused week posts one #fno-desk line from the capture job's `audits-due` step.
  Without Drive settings no week is drawn, and those sessions stay pending (fails closed).
- **Only the weeks needed are checked:** those with fired sessions after the first 10 days, so about one Drive read a
  week.
- **Callers pass the verified seeds:** `audits_due(root, seeds)`, `record_draws(root, seeds)`,
  `scoring_status(root, day, book, seeds)`. G4's `ai_forecasts` now takes `seeds`, and its wiring passes
  `fno.ai.wiring.build_audit_seeds(root)`; this was a 3-line change to keep `main` green after G4 adopted the gate.
- **Tests** (`tests/ai/test_draw_seed.py`), each with a planted edit:
  - edited close: refused, not steered;
  - edited hash: refused;
  - blank or unreadable close: refused;
  - deleted last-session row: refused;
  - no archive, or no Drive settings: refused.

  Also tested: the seed is the archived close; the same inputs give the same seed; a week waits for a later close; only
  the needed weeks are checked; draws are recorded once with their seed inputs.

Gates: `python -m pytest -q` 1863 passed; ruff and `check_imports` clean. The fire path is unchanged.

## Addendum 5 (14 Oct 2026, 15:45 IST): the first live day did not run (GitHub's schedule)

**What happened (strong evidence: GitHub's run list, read at 10:12 UTC):**
- `forecast-capture.yml` has **never run**. Its 14:00 IST (08:30 UTC) schedule has not started 1 h 42 min later.
- The NSE recorder (`quote-recorder-nse.yml`, 14:20 IST) has never run either.
- So there is no v2 pack for 14 Oct, no Book 1 forecast, and the AI books were never fired. No routine session ran,
  so there was no transcript to audit.
- The Groww 3 pm snapshot exists only because the Claude routine recorded it (5c22bcc).

**Root cause:** GitHub's scheduled events were hours late today, across the repository:
- `market-publish` (01:40 UTC) started at 06:41 UTC, 5 h late;
- `index-closes` (06:11 UTC) started at 07:30 UTC; its 02:11 UTC run does not appear at all.

GitHub documents that scheduled runs can be delayed or dropped under load. A job that must act between 15:00 and 15:15
cannot depend on `schedule` alone. This is a design gap in the capture's trigger, not in F1/G5's code. It hits Book 1
the same way.

**If the delayed run starts later today:** the capture writes Book 1's records with a `generated_at` after 15:15. Scoring
ignores them. It then fires both routines, and their commitments arrive after 15:15, so both are recorded `late`. Nothing
is imputed, and today counts as missing for every book. The two late sessions would still be audited (first 10 days).

**Proposed fix (needs the judge; the fire path is not touched without the orchestrator):** start the capture from an
event, not the clock. The 3 pm snapshot's commit to `main` (by the routine, about 15:00) is a `push` that GitHub
delivers at once. `forecast-capture.yml` gains an `on: push` trigger limited to the canonical snapshot path
(`research/data/quotes/**/nifty_*.canonical`) and keeps its cron as a fallback. The concurrency group plus the
write-once capture stop a double run. Reasoning plus some evidence: today's push-triggered `checks` runs all started
within seconds. One open point: pushes made with the workflow's own `GITHUB_TOKEN` do not trigger workflows, so if the
NSE recorder in Actions makes the snapshot commit, that commit would not start the capture. Today it was the routine.

## Addendum 6 (14 Oct 2026, evening IST): push-triggered capture, branch `story/f1-push-trigger` (for the judge)

The orchestrator approved addendum 5's fix. Built on the branch. Not on `main` until the judge passes it.

- **Trigger:** `forecast-capture.yml` now also starts `on: push` to `main` with
  `paths: research/data/quotes/**/*.canonical`, so the 3 pm canonical snapshot's commit starts the run. The cron (14:00
  IST) stays as the fallback, and `workflow_dispatch` stays.
- **At most one capture a day:** a new `gate` job runs first. It checks out the newest `main` and runs
  `python -m fno.pipeline.capture_gate --event <event>` (standard library only, no install). `capture` runs only when the
  gate says `run=true`. The workflow's concurrency group (`cancel-in-progress: false`) runs a second run's gate only after
  the first run has finished. The gate stops:
  - any run when the day's v2 pack is already on `main`;
  - a push-started run after 15:13 IST (protocol v2's last snapshot pull), which could only add late records. The cron
    run remains the fallback that records a missed day, late and unscored.
- **Unchanged:** the capture steps, the fire/collect path, the commit order (pack alone, then the records), and every
  frozen file.
- **Tests:** `tests/pipeline/test_capture_gate.py` checks:
  - both triggers;
  - the gate job, its `ref: main`, and the capture's `needs`/`if`;
  - the concurrency group;
  - a captured day is never captured again, for every event;
  - a push run at 15:13 still goes ahead, at 15:14 it stops;
  - a late cron still runs;
  - the gate imports no installed library.
- **Gates:** `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q` 3113 passed; ruff check and format clean;
  `check_imports` clean.
- **Limit (stated in the workflow):** a snapshot committed by an Actions run's own `GITHUB_TOKEN` starts nothing. Today
  the routine or the orchestrator's session makes that commit, so the trigger fires; the cron covers the other case.

**Re-check, 19:00 IST (13:30 UTC):** `forecast-capture.yml` still has no run; 14 Oct's schedule never started at all.
14 Oct has no records for any book and no AI session to audit. The push trigger (addendum 6) is on `main` from
`e3639f5` (judge 88 PASS).

**Judge 88 addendum 1 (14 Oct 2026):** `story/f1-gate-stdlib-test` d6d72df PASS, merged into `main` as 3534fe2 (3122
passed with the token unset; ruff and `check_imports` clean). Minor follow-up recorded, not built: the test imports and
calls `main()` instead of running `python -m fno.pipeline.capture_gate` as the workflow does, so a problem only in the
module's `__main__` entry would not show. A later small story can run the module by `-m` under `-S -I`.

## Addendum 7 (14 Oct 2026, 19:50 IST): the late run, and a setup-script fault that blocks every AI session

**The late run (Actions run 38576145173, strong evidence: GitHub's job steps).** GitHub started the 08:30 UTC schedule
at 13:56 UTC, 5 h 26 min late, after my 13:30 UTC check.
- The gate let it through (cron run, no pack yet).
- The capture built the pack and Book 1's and the baselines' records with `generated_at` 19:27:39 IST, after 15:15, so
  scoring ignores them.
- The job then fired both routines at 19:27:47 and 19:27:49.
- The reveal wait ended at once (it stops at 15:30). `collect` ran 3 s later and found no commitment, so both AI books
  are `no_submission`, with five empty records each.
- Nothing was imputed, and nothing from 14 Oct is scored.

**Both routine sessions failed before Claude started** (session records and full event logs:
session_01KArozSaT7wCoYmLbni7XUY and session_015U1QA1DHnhXtz7XvJozzba). The environment's setup script failed:
`ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'`. It ran 0 model
turns, cost USD 0, and pushed nothing.
- **Root cause:** my checklist told the owner to put `python -m pip install -q -r requirements.txt` in the
  environment's setup script, but setup scripts do not run in the repository folder. It is my error.
- **Fix:** leave the setup script empty. The routine prompt's step 1 already installs in the background. The checklist
  is corrected.
- **Must happen before 15:00 IST on 15 Oct,** or every AI session fails the same way and records `no_submission`.
  Only the owner can edit the environment.

**Transcript audits (first-10-days rule): both recorded `clean`.** Neither session ran a model turn, read a file, used the
network or pushed. Files: `research/forecasts/ai_v1/2026/2026-10-14_<book>_transcript_audit.json`; `audits-due` now
shows 0.

**One more point for the judge (reasoning only).** On a late cron run, the AI books are still fired even though the
collection is certain to record them `no_submission` within seconds. That wastes two routine runs. A sound fix is for
`fire` to skip when it is already past 15:13 IST, the same rule as the push gate. It touches the fire path, so it waits
for the orchestrator.
