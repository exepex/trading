# Story F1t: the AI books' trading runner (F1's trading part, Book 2 and Book 3 steps in the daily run)

**Repository:** trading · **Lane:** 1 (decides trades, outside services, schedules) · **Size:** L ·
**Builder:** session_01B3RARTgoiGJwBKXRCgGRe8 (from 25 Oct 2026; text and first code by session_01PLbKH15BXYucP6cT9xtoxK,
out of reach) · **Orchestrator:** session_01Mt6dcBU5kp2htdPN2KmiZH · **Branch:** `story/f1t-runner-v2` (from `main`
of 25 Oct; the 16 Oct code on `story/f1t-ai-trading-runner` is the source the code round re-ports, never merged as is) ·
**Replaces:** F1's "trading part later (slice 4)" in `docs/stories/F-ai-layer.md` (F1's forecast part stays as built).

**Description:** As the statistician and the risk manager, I want each AI book's daily trading decision taken in its
own isolated routine session, from the common pack and its own private pack only, sealed before a deadline, checked by
code (D3 schema, D4 envelope for Book 2, D5 constitution for Book 3, C2 risk, C4 validity) and handed to the same fills
as Book 1, with every miss, late answer and refusal recorded and alerted, so that the three books are compared on the
same day, the same data and the same fills, and no AI answer reaches a fill without code checks.

**Owner, 16 Oct 2026:** "I want the core engine to be working end to end ... rule-based, hybrid, AI, all are developed
end-to-end, validated end-to-end, tested end-to-end ... there must not be anything that is not implemented. And I
don't want any surprises. Every claim must be validated ... do not over-engineer ... Simplicity is also our priority,
but not the product quality." Errors must alert and be recorded.

**Owner, 25 Oct 2026 (through the orchestrator):** the AI books (Book 2 Hybrid, Book 3 AI team) must be able to decide
and book **paper** trades; the 22 Oct cut-list's pause on them is lifted. Their forecasting job (G11) goes live on Mon
26 Oct; this story is their trading job. Every live switch stays null until the owner sets it.

**Revision 2 (25 Oct 2026), what changed since the text PASS of 16 Oct (for the code judge):** the facts are re-read on
`main` of 25 Oct (Context); the F4 addendum is folded into the body (the judge step, `judge_failed`, criterion 16);
the timeline names the v4 forecast run of the same books beside it; the two steps' public reasons are O1-status-only
codes (criterion 17); a rehearsal never fires a routine (criterion 18); BG1's stop is read through G11's
`BudgetStop`, with the owner's "no AI budget cap" (25 Oct); known limits and go-live checks updated with the real
timing and model evidence of 15-23 Oct; round 2 (judges 621 and 623): the served model (`last_served_model`) is
the one checked, an instructions line alone is unverified, decisions stop on BG1's level alone (`LevelBudgetStop`), the
seal-before-reveal order and the reveal race stated; the owner's lifting of the 15 Oct "strategy passed" rule for paper, with
the strategy label (criterion 17b); decisions reuse G11's `RunTerms` chain as a third instance instead of the 16
Oct path parameters (Design, "The decision run's terms"). No criterion of the PASS is removed or loosened.

## Context and why (each fact marked)

- **What runs today (strong evidence: code and data on `main` of 25 Oct 2026, read by this builder):**
  - O1's `DAILY_RUN_STEPS` (`fno/constants_operations.py`) has one decision step, `book1`, after E3's `versions` and
    `pack`; before them run the quote parts, E8's owner timing, the margin check, the weather, `forecasts_v4`, G10's
    `v4_release` and G7b's `forecasts_v4_pack`. Every scheduled run publishes to `main` (`PUBLISH_BRANCH`), one run
    per day per container (O1 day lock), and the public run log keeps only a status and a closed reason code per step
    (O1-status-only, `fno/daily/reason_codes.py`); the full text goes to the #fno-desk alert and the private log.
  - E3's timetable (`config.yaml` `desk.timetable`, "proposed until S1"): `pack` 14:58, retried to 15:10 while the
    canonical snapshot is late; `decision_deadline` 15:12; `execution_snapshot` 15:15; `fills_by` 15:20.
  - E3's `decisions` step (`fno/desk/daily_steps.py:collect_decisions`) already handles any list of books: at the 15:12
    deadline it pulls once and takes each book's first original D3 run visible then (D3b); a book without one gets a
    committed `no_decision.json`. The fills read only those runs, through one `OrderBuilder` (built at the fill) and
    C4's recorded pass (`fno/desk/recorded_c4.py`). So the AI books need no change to E3's collection or fills: they
    need a D3 run committed before 15:12.
  - E2's private packs are built only for Book 1 (`fno/desk/pack_wiring.py`) and kept in Drive (E2c); only their
    `.sha256` is committed. E2e's `BookSheet` port (merged, judge 309) puts a book's evaluation sheet in its private pack
    under `"evaluation"`. A routine session has no Drive credentials (and must not have any).
  - D4 (Book 2's envelope) and D5 (Book 3's constitution and registry) are merged and switched off: C4 refuses every
    Book 2 trade until an envelope is registered in D6, and every Book 3 trade until a constitution is
    (`fno/checks/wiring.py`). None is registered today (`playbook/envelopes/` and `book3/` do not exist).
  - Book 1's playbook holds one rule, `b0-monthly-sc` v1, status `research` (`playbook/registry.csv`): no strategy has
    passed to `paper`. The owner's rule of 15 Oct (design v2 decision 10, "AI books trade on paper only after a
    strategy has passed") is **lifted for paper** (owner, 25 Oct, `docs/DESK_DECISIONS.md` rows of 25 Oct, item (1)
    and "9 yes, 10 yes, 11 yes"):
    the AI books may trade on paper before a strategy has passed, each such trade labelled "strategy not yet passed"
    and reported apart (Design, "Strategy label"). Since D2 trades only `paper` versions, Book 2 would still have no
    rule default; the owner's Q11 (25 Oct) lets Book 2 alone take D2's registered research candidates as eligible
    rule defaults under D2's unproven limit (at most 1 open trade for a strategy with fewer than 20); that is F5's
    revision, Book 1 unchanged. Book 2's envelope v1 and Book 3's constitution v1 are approved (Q9, Q10) and are
    registered in D6 when their judged branch merges.
  - The same two AI books run their **forecast** job on protocol v4 from 26 Oct (G11, merged): `v4-fire.yml` fires each
    book's forecast routine when G10's release lands (about 14:45, latest fire 14:55), deadline 15:10
    (`fno/ai/v4_fire.py`). Those are separate routines and separate records; F1t's decision routines are new ones.
  - The forecast routines on real days (strong evidence, `research/forecasts/ai_v1/2026/*_audit.json`, all read on 25
    Oct): 14 Oct fired at 19:27 IST and failed at setup (`no_submission`, both books). From 15 to 23 Oct, 12 book-days
    fired at 15:10:19-15:10:29: 7 `on_time`, 4 `late` (15 Oct both, 22 and 23 Oct Book 2), 1 `no_submission`
    (Book 3, 22 Oct). Commitments arrived 15:10:55-15:15:34 IST, 36 s to 5 min 9 s after each book's fire.
  - **Model reporting on those days (strong evidence, same files):** of the 11 answered book-days, `model_reported` was
    `unknown` on 10 and `claude-opus-5-5` (`match`) on 1 (Book 3, 16 Oct). Under the no-trade rule for an unknown model
    that is 1 usable book-day of 11. The forecast prompts (v1 and G11's v2) ask only for the session-description tool
    and fall back to `unknown`; a session's own instructions also state its exact model ID (strong evidence: this
    builder session's own system prompt names its model ID), so the decision step reads that first (Design).
  - `research/evaluation/PROTOCOL.md` (`timetable`): the desk's slots "look tight for an AI book's session"; the
    timetable is "proposed until S1".
- **What the design asks (F1, design 13.5 step 3, 12.4, 12.6):** each book decides in its own session seeing only the
  common pack and its own private pack; both pack hashes in every decision; the served model recorded, a mismatch
  unscored; a failure or usage limit gives "no decision (AI unavailable)"; output received after the receipt deadline is
  ignored; the runner outside the AI validates, runs C2 and C4 and commits before the promotion deadline, which comes
  before the execution snapshot; anything not promoted by then fails closed.
- **Isolation that the platform gives (strong evidence: F1's forecast part, judge 62 and addenda):** a routine session
  needs the repository to push its answer, so F1's "no repository, no network" mode cannot return an answer the code
  can read (Python cannot call the session tools; F8's facts). The forecast part therefore runs `sealed_same_day`
  (owner's conditions 1 and 2 of 14 Oct 2026): a sealed commitment before the deadline, the reveal after, a transcript
  audit on a random draw, and a stop after two breaches. F1t uses the same mode for decisions and labels every
  decision with it.
- **This contradicts an owner condition (found while building, 16 Oct; strong evidence: `docs/DESK_DECISIONS.md`
  row of 14 Oct, "AI books' forecast isolation", condition 3: "trading decisions (slice 4) still need full F1
  isolation").** No full F1 mode is available to code (above), and F1's own text says what happens then: "books 2 and
  3 run labelled 'isolation not enforced', and their results are not scored as an independent comparison until an
  enforceable mode exists". So F1t is built and tested, but **no live switch may be set until the owner decides**
  either (a) to accept `sealed_same_day` for paper trading decisions, labelled "sealed same day (not full F1)" and not
  scored as an independent comparison, or (b) to wait for an enforceable mode. Asked through the orchestrator.
  **Decided (owner, 16 Oct 2026, `docs/DESK_DECISIONS.md`): (a).** Every decision carries the label "sealed same day
  (not full F1)" (the version label's `isolation:sealed_same_day`), and Books 2-3 are not counted as an independent
  head-to-head until a stronger mode exists.

## Scope

**In:**
1. Two O1 steps, `ai_fire` (right after `pack`, before `book1`) and `ai_collect` (after `book1`, before E3's
   `decisions`), each AI book gated by its
   own live switch `daily.live_from.book2_hybrid` and `daily.live_from.book3_ai` (null: that book is not in the desk at
   all, so nothing changes for Book 1).
2. The decision pointer (what a routine is fired with) carrying the common pack's SHA-256 and the book's own private
   pack, fired through the existing `RoutineTrigger` (O6, `fno/pipeline/trigger.py`) into two new decision routines.
3. The routine side, standard library only (`python -m fno.ai_trading brief | seal | reveal`), reusing `fno/ai`'s
   seal (`Commitment`, `reveal_text`, `open_reveal`) and transport (`GitMainTransport`).
4. Receipts by observation at the deadline (E3's judge-82 rule), a new `PushReceipts` class behind `fno/ai`'s interface.
5. The outcome of each book-day (promoted, or a miss or refusal with its reason), one committed record and one alert per
   miss.
6. The hand-over port `AiBookDecider` (implemented by F5 for Book 2 and F6 for Book 3) that turns an accepted answer into
   a D3 run with C2 and C4 inside; F1t checks the run, then commits it before E3's deadline. Per-book `OrderBuilder` and
   `ExitRules` dispatch in the daily run's composition root, so E3's fills and exits serve each book with its own.
7. The decision versions' registry (prompt file, its SHA-256, the registered model, isolation), the transcript audit,
   the stop rule and the budget stop, each reusing `fno/ai`'s and `fno/budget`'s code (the budget stop is G11's
   `BudgetStop` reading BG1's own meter, never a copy).
7b. The judge step's port (`JudgeStep`, F4 implements it) called inside `ai_collect` before `decide()`, and the
   `judge_failed` outcome (Design, "The judge").
8. End-to-end tests over the real `DailyRun` with fixture packs and fake AI answers: valid, invalid, late, missing, not
   revealed, model mismatch, exposed, refused by the decider, blocked by C4.
9. The two routines' exact prompts and the owner's checklist (`docs/stories/F1t-owner-checklist.md`).

**Out (each with its owner or reason):**
- What a book decides and its prompt: F5 (Book 2, D4/D5 owner session_01SFDjjZx7JYziM3jqJytG2z) and F6 (Book 3, the
  F6/F7 builder). F1t registers their prompt file and shape check by one line each when they land.
- Analyst finding cards (F2): F2's own sealed routines; F1t passes F2's `analyst_cards` item (Design). Matched shadows
  (F7): inside Book 3's `decision` object, defined and checked by F6/F7. The red team and devil's advocate: T2/T3.
- The judge's checks, verdict file content and monthly AI re-check: F4 (`story/f4-ai-judge`, text not yet passed; no
  builder assigned on 25 Oct). F1t owns only the port and the call (Design, "The judge").
- E3's collection and fills, E8's owner-timing fills: unchanged. An accepted AI run is collected and filled exactly as
  Book 1's.
- D3's refusal of a non-empty `owner_override` (D4 table, owner 16 Oct): the D3 owner's code item; F1t's live switches
  may not be set before it merges (Depends).
- Scoreboards A and B reading the AI outcome and audit statuses: S2 and S3's builder (their files are in S1's
  `frozen_files`). Scoreboard B already counts E3's `no_decision.json` as no trade.
- A no-repository, no-network session: not available on the platform for an answer code can read (Context). If the
  owner wants it, a decision routine with no repository would need a way for code to read its final message, which
  does not exist in Python today.

## Design

**Timeline of a session day (IST; config `ai_books.decision_timing`, status "proposed until S1", checked at load to be
strictly in this order and before `desk.timetable.decision_deadline`):**

| Time | Who | What |
|---|---|---|
| about 14:45-15:10 | G11's forecast routines (separate, `v4-fire.yml`) | the same books' v4 forecasts: their own pointer, seal and reveal; nothing of them is read by the decision step (G11 criterion C15's `DECIDING` list gains `fno/ai_trading`) |
| 14:58-15:10 | daily run, E3 `pack` | common pack committed; each live AI book's private pack built (Drive) |
| right after `pack`, before `book1` | `ai_fire` | one pointer per live AI book, fired once; not fired if the step starts after `latest_fire` 15:07:00; starts the receipt observer |
| until 15:10:00 | each routine | `brief` → decides → `seal` pushes only its commitment to `main` |
| 15:10:00 | receipt observer (child process) | observation 1 (`receipt_deadline`): `git ls-remote origin refs/heads/main`; a commitment counts only if contained in that commit |
| 15:10:10 | each routine | `reveal` (`reveal_from`) pushes the answer and salt. Every seal deadline of the day (decision and v4 forecast, 15:10:00) comes before any reveal (decision and v4 forecast, both 15:10:10), so no book's answer of either job is readable before every commitment is in (judge 621 m1) |
| 15:11:00 | receipt observer | observation 2 (`reveal_deadline`), the same way |
| after `book1`, once observation 2 exists | `ai_collect` | fetch and merge; judge each book against the two observations; accepted ones go to the decider; runs checked, then committed with the outcome records |
| 15:12:00 | E3 `decisions` | unchanged: takes each book's first original run visible and committed before the deadline |

**Observations independent of the step order (judge 301):** `ai_fire` starts one receipt observer, a child process
through O1's `Processes` (as the 3 pm quote parts are), so a slow `book1` (up to its 600 s limit) never moves an
observation. The observer only reads the remote (`git ls-remote`, which never touches the checkout, so O1's "git only
in the run's thread" rule for the repository holds) at each deadline and writes `{deadline, started_at, ended_at,
commit}` to a git-ignored file. An observation that started more than 30 s after its deadline, failed, or is missing
(the observer died, or a rerun started after the deadline) counts as not taken: every fired book is `late` (fail
closed, as E3 does), and `ai_collect`'s status is `refused` with that reason, so the day ends "with problems" and O8
sees it. `ai_collect` itself runs after `book1`; if `book1` ends after 15:12 the books are judged on time or not by
the observations, but their runs commit after E3's deadline and are late by E3's rule (criterion 8).
Values are config, so S1's measured-timing rule can move them.

**Pushed late by earlier steps (O1 builder, 16 Oct):** `pack` retries until 15:10 while the canonical snapshot is late.
On a day the pack lands after about 15:07, every live AI book is `not_fired` (late start). That is correct, never a
trade, and it is alerted. `book1` no longer delays the fire (it runs after `ai_fire`).

**Commit time at the deadline (strong evidence, code):** E3's collector (`D3CommittedDecisions`) pulls, then reads the
checkout's own history: a run counts when its commit's committer time is before 15:12 (`committed_at >= deadline` is
late). `ai_collect` commits through the run's one `PendingCommitter` (pull, commit, push, 3 push attempts). So (a) a
commit made at 15:11:59 that pushes at 15:12:05 still counts in this checkout, as Book 1's does today; (b) a commit
made at or after 15:12 is late by E3's rule and never filled; (c) a push rejected 3 times is `CommitFailed`, which
stops the run with E3's one alert (decision 44), and the rerun after 15:12 is late. No case is silent. The worst case
in seconds cannot be bounded by code (git calls have no timeout in E3's committer); the claims show the measured
time of the step's commit on the test remote, and a test covers (a), (b) and (c).

**Alerts (O1's one sender):** neither step sends alerts itself. Each returns `ok` when every live book was fired
(`ai_fire`) or promoted (`ai_collect`), else `refused` with one reason naming each book's status and why; O1's
`Alerted` wrapper then sends exactly one line per step and the day goes on. A raise is `failed`, alerted the same way.

**Public run log (O1-status-only):** the reason a step returns is one of F1t's own message templates, each registered
in `fno/daily/reason_codes.py` as a named code (`ai:NOT_LIVE_BOOKS`, `ai:NOT_FIRED`, `ai:NOT_PROMOTED`,
`ai:OBSERVER_LOST`, `ai:REHEARSAL_NO_FIRE`), so `journal/runs/<d>.json` shows only the code and counts (`n`: the books it names), never a
book's free text; the full line goes to the alert and the private full log. Each book's own status and reason are
in its outcome record (private figures redacted, Design below).

**Rehearsal (REH1):** under a rehearsal (`fno/rehearsal/mode.py`'s `rehearsal()` is set), the AI steps never build a
real `RoutineTrigger` and never fire a routine (an outside service, as REH1's `OUTSIDE_SEAMS`): with a live book they
record `refused` with F1t's own code `ai:REHEARSAL_NO_FIRE` ("rehearsal: AI decision routines are never fired;
{books} not decided"), never a fire. Replaying the AI books' answers is the owner's separate dry-run replay story (25 Oct, a REH1
follow-up), not this one.

**Firing (`fno/ai_trading/fire.py`):** for each live AI book, in this order, the first that applies is recorded:
budget stop (judge 623 should-fix 2): a second implementation of G11's `BudgetStop` interface
(`fno/ai/budget_stop.py`), `LevelBudgetStop`, reading the same BG1 meter: trading decisions stop as soon as the
month's level is `stop` (design 7.6: the AI forecasters stop last, so decisions stop before them), whereas G11's
`MeterBudgetStop` stops the forecasters only when the books' own minutes also reach the cap. The owner set no cap on
25 Oct, so today neither stops, and a cap set later applies with no code change. A meter that cannot be read fires
the books with the reason in the alert: a deliberate fail-open on cost only (orchestrator, 25 Oct): it can cost AI
minutes but never makes a trade (every trade still passes C2, C4 and the judge), and the owner set no cap → `not_fired`; no registered decision version → `not_fired`; stop rule (two
transcript breaches in its last 20 decision session days, under that version) → `not_fired`; no common pack built →
`not_fired`; started after `latest_fire` → `not_fired` (late start); pointer over `MAX_POINTER_BYTES` (64 KiB, to be
confirmed against the routine API's real limit before go-live) → `not_fired`, never truncated; pointer text holding
anything the public-record scan (O5) flags → `not_fired`; `FireFailed` → `not_fired`. Otherwise fired, with the
session link. Every `not_fired` is named in the step's one alert line.

**Fire once, even across a crash (O1 builder, 16 Oct):** before any HTTP call, the step writes the fire log
`journal/ai_decisions/<YYYY>/<d>_fired.json` with each book's entry `firing` and commits and pushes it; only then does
it call each trigger, and it records the results in the step's own commit. A rerun that finds an entry still `firing`
never fires that book again: the entry becomes `fire_unknown` ("the container stopped during the fire"), and the
collection goes on as usual, so a routine that did start still has its sealed answer judged. A container lost before
that first commit fired nothing.

**Pointer (`DecisionPointer`, one line of JSON):** `kind: "decision"`, `book`, `day`, `version` (the registered decision
version's label), `common_pack_sha256`, `private_pack_sha256`, `private_pack` (the book's E2 private pack body),
and `analyst_cards`; `brief` prints `analyst_cards` with the two packs.
Only that book's private pack is ever put in its pointer (book isolation). **Analyst cards (agreed with F2, 16 Oct):**
the pointer also holds one item `analyst_cards`, read at `ai_fire` from F2's `CardsOfDay` port (F2's own sealed
routines; the day's cards file is in Drive by 14:55, before any book is fired, so their independence is shown by F2's
receipts): `role_set_version`, `input_sha256` (the cards file's SHA-256) and every registered role's status line with
its reason, with the card itself only when it is `valid` or `not_applicable`. The port never raises; with no cards
file, or a read that fails or takes over 30 s (F2's bound), every role reads `no_submission` and F2's one alert goes
through the run's one sender (O1's `ReportedAlerts`, injected in `fno/daily/wiring.py`). The pointer is F1t's own
(`fno/ai_trading/pointer.py`, 64 KiB cap), never `fno/ai/pointer.py`'s 4 KiB forecast parser. The session cannot read
Drive (no credentials), so the cards travel in the pointer, not by hash alone. The item is the same for both AI books (the analysts are shared, not a book's
private input). The item is `{"day", "input_sha256", "role_set_version", "roles": [{"role", "unit_id", "status", "reason",
"card_id", "card"}]}`, `card` null unless usable; the pointer refuses an item for another day. F2's code is not merged
(25 Oct), so the v1 decision versions list no role units and their item has no roles until it lands. A book whose
decision version lists no role units gets an item with no roles. Cards are never part of
a book's answer; a book may cite card IDs in its own `decision` (F6's `cards_used`), checked by its own shape check
and decider against the IDs it was given. `brief` refuses a pointer whose fields are
not exactly these, whose version is not the book's current one, or whose private pack's canonical SHA-256 (E2's
`canonical_json`) is not `private_pack_sha256`.

**Routine side (`python -m fno.ai_trading`, standard library only):**
- **Working folder:** `.ai_decision/` is added to `.gitignore` (test: a file there is never staged by the transport).
- **Two prompts, said plainly (F6, 16 Oct):** the routine's stored prompt (owner-pasted, in F1t's checklist, not
  hashed) only bootstraps `brief`, `seal` and `reveal` (the usage timing is F8c's, inside `brief` and `reveal`); the book's decision prompt (F5's for Book 2,
  F6's `agents/book3/decide_v1.md` for Book 3) is the file `brief` hash-checks against its registered version and
  prints.
- `brief '<pointer>'`: checks the pointer, reads `journal/packs/<d>/common.json` from `main` and checks its SHA-256,
  checks the versioned prompt's hash, saves its private working files under `.ai_decision/` (never committed), then
  prints the prompt, `INPUT`, the common pack and the private pack. Nothing is shown unless every check passes.
- **Model reported: the served model, not the configured one (judges 621 and 623, round 1; orchestrator's ruling, 25
  Oct):** a session's configured model and the model that actually served a turn can differ (a fallback). The
  session-description tool (`get_session` with no session ID) reports them apart: `session_context.model` (configured)
  and `external_metadata.last_served_model` (the model that ran the latest turn). `brief` prints, before the book's
  prompt, F1t's fixed answer rule: call that tool after writing the answer and report `model_reported` =
  `last_served_model`, `model_configured` = `session_context.model`, and `model_source` = `"session_tool"`; without
  the tool, `model_reported` = the model ID the session's own instructions state, `model_source` = `"instructions"`;
  with neither, `"unknown"` and `model_source` = `"none"`. `seal` refuses a `model_reported` or `model_configured`
  that is not a model ID or `unknown`, and a `model_source` outside those three. Judging (table below): `model_source`
  `instructions` or `none` is `model_unverified` (an identity line names the configured model only; the orchestrator
  ruled it not verified, because a routine session can call the tool); with `session_tool`, a `model_reported` or a
  `model_configured` different from the registered model is `model_mismatch`. Both are no trade. The model copies the
  tool's fields itself, so a false copy is possible: the transcript audit (every session of the first 10 fired days,
  then the weekly draw) compares the recorded fields with the tool call in the transcript, and a difference is a
  breach (kind `model_misreported`, under the stop rule). `last_served_model` covers the latest turn only; a fallback
  on an earlier turn of the same session is visible only in the transcript (Known limits).
- `seal <answer.json>`: the answer is `{"model_reported": <text>, "model_configured": <text>, "model_source": <text>,
  "decision": {...}}`. `seal` adds the labels (book,
  day, version, both pack hashes) itself, checks the shape (F1t's base: `decision` is an object with `action` (text)
  and a one-line `reason` of 1-600 characters; F5's `decision` is `{"action", "reason", "slots", "evidence"}`, F6's
  `{"action", "reason", "trades", "proposals", "shadow", "cards_used", "evidence"}` (`evidence` is F4's key), and
  what the rest means is the book's own); then the book's own shape check `check_decision(decision: dict) -> list[str]` (problems; empty means ok; standard
  library only: F5's `fno/book2/answer.py`, F6's for Book 3), registered with its version by F5 or
  F6), and publishes only the commitment, to `journal/ai_decisions/submissions/<YYYY>/<d>_<book>.commitment.json`.
  A refused answer names what to fix, so the model can fix it before the deadline.
- **No private account figure in the answer (judge 301; E2c, owner 15 Oct "A: move to Drive"):** the reveal is public
  in the repository, and the book's `reason` is copied into its public D3 record. Keeping the reveal in Drive is not
  possible (the session has no Drive credentials, by rule). So `seal`, and again the collection (`invalid`), refuse
  any number token in any text of the answer that appears in the private pack's account files (E2c's
  `ACCOUNT_FILES` under `journal/<book>/`: fills, ledger, positions, equity, marks, events) and does not appear in
  the common pack or the book's public files (playbook, `book3/`), counting tokens of at least 3 digits or with a
  decimal point. A strike or a price from the common pack may be named; a fill price, cash or P&L may not. The refusal
  names the token's place, never prints the figure.
- `reveal`: waits until `reveal_from`, then publishes answer and salt to `<d>_<book>.reveal.json`.
- The seal and reveal steps are the forecast's own (`fno/ai/book.py`'s `BookSession` on the decision run's terms,
  Design "The decision run's terms"); no behaviour change for forecasts, their tests unchanged; nothing written twice.

**Receipts (`ObservedPushes(PushReceipts)`):** a commit's receipt is the first observation (receipt deadline, reveal
deadline) whose fetched `origin/main` contains it; its nominal time is that deadline. Never a commit's own date. A
commit in neither is `ReceiptUnknown`, which `fno/ai`'s rules already treat as late. No GitHub token is needed.

**Judging a book-day (`fno/ai_trading/outcome.py`), first rule that applies:**

| Status | When | Trade |
|---|---|---|
| `not_fired` | the fire log says so (with its reason); a `fire_unknown` entry is judged on its submission like a fired one | no |
| `no_submission` | no commitment (AI unavailable or limited) | no |
| `late` | commitment not visible at observation 1, or `ai_collect` started late | no |
| `exposed` | another book's reveal was already visible at observation 1 (it could have been read) | no |
| `invalid` | this book's own reveal visible at observation 1 (revealed early); seal broken; answer shape or labels wrong | no |
| `not_revealed` | no reveal visible at observation 2 | no |
| `model_mismatch` | `model_source` is `session_tool` and `model_reported` (served) or `model_configured` differs from the registered model | no |
| `model_unverified` | `model_source` is `instructions` or `none`, or `model_reported` is `unknown` (orchestrator rulings, 16 and 25 Oct: no trade, reason recorded; forecasts keep their rule) | no |
| `judge_failed` | the judge's verdict blocks (Book 2 only: `fail` or `unavailable`); the decider still wrote its "no trade, judge failed" run, which passed F1t's check (below) | no (the rule default is kept as a shadow) |
| `refused` | the decider raised `DecisionRefused`, or F1t's run check failed (below) | no |
| `promoted` | the decider wrote a run that passed F1t's check | E3 collects it; fills only if C4 passed |

Each outcome is written once to `journal/ai_decisions/<YYYY>/<d>_<book>_outcome.json` (status, reason, version,
model reported and its check, both pack hashes, receipt observations, the run ID when promoted) and committed by the
step with any promoted run. Every status but `promoted` is named in the step's one alert line: "{book} {status}:
{reason}; no trade today". A rerun finds the outcome file and does nothing again.

**Hand-over port (agreed interface, to be confirmed by F5 and F6's builders before code):**

```python
@dataclass(frozen=True)
class AcceptedDecision:
    book: str; day: date; version: str; registered_model: str; model_reported: str
    session: str                      # the fire log's session link (D3 `session_id`)
    common_pack: CommonPack; private_pack: PrivatePack
    decision: dict                    # the book's own object, already shape-checked
    analyst_cards: dict               # F2's item exactly as fired (card IDs, role_set_version, input_sha256)
    consulted_units: tuple[str, ...]  # the unit IDs whose card was in that item: what was given (F9b withholds it)
    commitment_commit: str; reveal_commit: str
    judge: str                        # the judge's verdict file, repository-relative (D3 `judge`)
    judge_blocks: bool                # the verdict blocks: Book 2 writes "no trade, judge failed" (F5 criterion 11)

class AiBookDecider(ABC):             # F5: Book 2; F6: Book 3
    def decide(self, accepted: AcceptedDecision) -> DecidedRun: ...
        # writes ONE D3 run (DecisionStore, atomic) with C2 and C4 inside, as Book 1's DecisionRun does; a blocked
        # action still gets a "no trade, blocked" run with the attempt recorded (D4 criterion 2)
        # raises DecisionRefused(reason) when no run can be written (e.g. the private pack does not rebuild)

# Also per book, owned by the decider's story (judge 301): its OrderBuilder (E3's port: the run's entry orders,
# replayed from the run, as Book 1's ReplayedOrders) and its ExitRules (each open trade's exits, from its playbook
# version for Book 2, from its registered D5 spec for Book 3). Owners: F5 (Book 2), F6 (Book 3). F1t wires them,
# per book, in fno/daily/wiring.py only.

@dataclass(frozen=True)
class DecidedRun:
    run: Path                         # journal/<book>/decisions/<d>/<run_id>/
    files: tuple[Path, ...] = ()      # other files to commit with it (C4's failure log)
```

**F1t's check of a decided run before committing it:** the run is the only run of the book's day and is under its
folder; every record passes D3's `validate_record`; every record's `book`, `common_pack_sha256` and
`private_pack_sha256` equal the pointer's (criterion 7), `model_served` equals `model_reported`, `session_id` the fire
log's link, and `served` names the decision version; every file in `DecidedRun.files` is under the book's declared
write paths; every record's `judge` equals `AcceptedDecision.judge`; and when `judge_blocks` is true, no record is a
chosen trade (only "no trade" records and `mode: shadow` records), so the block never rests on the decider alone. A
run that fails is never committed, and the book-day is `refused` with the file hashes kept in the
outcome record.

**The judge (F4; agreed with F4's builder 01AN94h4 on 16 Oct; owner, 16 Oct: "Code daily + AI monthly"):** for each
book-day that passed every check before `judge_failed` in the table, and before `decide()`, `ai_collect` calls
`judged = judge_step.run(JudgeCase(book, day, registered_model, decision, common_pack.body, private_pack.body,
common_pack.sha256, private_pack.sha256))`. `run()` never raises (an error inside the judge is the verdict
`unavailable`). `decide()` then runs in every case with `AcceptedDecision.judge = judged.path` and `judge_blocks =
judged.verdict.blocks` (true only for Book 2; Book 3's verdicts are evidence and never block). A blocked book-day whose
run passes the check is `judge_failed` with the verdict's reason line, named in the step's alert; the verdict file
(`journal/ai_decisions/<YYYY>/<d>_<book>_judge.json`) is committed with the run and the outcome record on every judged
day. The judge is pure code with a 5 s budget measured inside it, so it fits `ai_collect`'s 15:11:00-15:12:00 window
beside `decide()`. **One port, one owner:** `JudgeCase`, `Judged` and the `JudgeStep` interface live in F1t's
`fno/ai_trading/ports.py`, exactly as F4's text names them; F4's code implements `JudgeStep` behind
`fno/judge/wiring.py: build_judge_step(root)` and defines no second copy (a one-line change to F4's text, for its
builder). **Until F4's code merges,** the wiring injects `NoJudge`, whose verdict is always `unavailable` with the
reason "judge not built (F4)": Book 2 is then `judge_failed` every day (fail closed, never a trade), Book 3 is
unaffected. Book 2's go-live therefore needs F4 merged (go-live checks).

**Strategy label (owner, 25 Oct: trading before a strategy has passed is allowed on paper, labelled and reported
apart):** each decider writes, in every D3 record that chooses a trade, `served["strategy_status"]`: the status of the
traded strategy at the decision commit (Book 2: the playbook rule's row in `playbook/registry.csv`; Book 3: its D5
registry row). F1t's run check refuses a promoted run with a chosen trade that lacks it. The outcome record holds
`strategy_label`: "strategy not yet passed" when any chosen trade's status is not `paper` (or a later passed status of
D6), else "strategy passed", and the step's alert line names the label. Reporting the two apart is the scoreboards'
(S2, S3; they read the outcome record), not this story's.

**Write paths and restore (agreed with F6, 16 Oct):** each book's decision version declares the paths its decider may
write (Book 3: `journal/book3_ai/`, `book3/` and `research/ledger.csv`, the one file D5's `register()` appends a
trial row to; Book 2: `journal/book2_hybrid/` and C4's failure log). F1t commits only changes under them. Just before
`decide()`, F1t snapshots the bytes of every file under those paths; when the run check fails, `DecisionRefused` is
raised, or the decider raises anything else, it puts every such file back to that snapshot (changed files rewritten,
new files deleted), so nothing half-registered (a `registry.csv` row, a spec file, a ledger row, a shadow file) can be
committed later by accident. The snapshot, not `HEAD`, is the reference: `research/ledger.csv` is shared with the
research factory, and any change made before `decide()` (by anyone) is left as it was. The daily run is one thread, so
nothing else writes these paths during `decide()`. The restore is recorded in the outcome record (test: a decider
that registers a proposal and appends a ledger row, then fails the check, leaves every file equal to its snapshot,
including a ledger row written before `decide()`).

**Role units (F2, F9):** each decision version names the role units it consults (v1: `analyst_volatility`) beside its
prompt, model and isolation, so they are part of the book's D6 version; F2 writes `agents/role_units.yaml` from them.
The book's D6 version row names F2's `role_set_version`. The outcome record holds `consulted_units` (the unit IDs
whose card was in the book's `analyst_cards` item, whatever the book says it used) and the item's `input_sha256`, and
the decider receives the item and `consulted_units` to link in the D3 record.

**Book isolation:** each book's pointer holds only its own private pack; the decider receives only its own book's
packs; each book's account is its own E1 folder (no shared cash); submissions of one book are never in another's
input. Within a session the model can still read the public repository: reading another book's files is the transcript
audit's breach kind `file_outside_input`, as for forecasts.

**Transcript audit and stop rule:** the same rule as the forecasts (every session of the first 10 fired days, then 2 a
week drawn with the same verified weekly seed), the same record and breach kinds, written to
`journal/ai_decisions/<YYYY>/<d>_<book>_transcript_audit.json` by `python -m fno ai-trading audit-record`.

**The decision run's terms (revision 2; G11's design on `main`, `fno/ai/run_terms.py`):** G11 made `fno/ai`'s whole
chain take one `RunTerms` (paths of the commitment, reveal, audits and fire log, the receipt deadline and reveal
times), with two instances, v2's and v4's. A decision run is a third instance, `decision_terms(timing)`, built in F1t's
wiring from `ai_books.decision_timing` (protocol `"decision"`, folder `journal/ai_decisions`, deadline
`receipt_deadline`, `reveal_from`, `reveal_deadline`). `read_submission`, `TranscriptAudits`, `stop_reason`,
`fired_sessions` and `BookSession`'s seal and reveal then serve decisions with no new parameter and no copy; the 16 Oct
code's path parameters (`path_of`, `commitment_of`, `folder`) are dropped. The only change in `fno/ai` beyond the
shared pieces below is `build_audit_seeds` drawing the decision terms' weeks too (one term in its union). If
`BookSession` cannot take a decision answer without forecast fields (`questions`, `envelope`), the code round extracts
the smallest shared publish helper from it, with G11's tests unchanged and passing; the claims say which was done.

**Usage (F8, agreed with F8c's owner, 16 Oct):** one mechanism, F8c's: `brief` starts `RunTiming` and `reveal`
publishes it to a role-bearing timing path (`timing_path(day, book, run="decision")`, giving
`<d>_<book>_decision.timing.json`), and `BookUsageRecorder` maps that suffix to role "<book> trading decision"
(`books_and_roles`). F8c is merged (judge 276); F1t extends its code. F8c's not-captured alert keys on fire logs, so
it also reads the decision fire log. BG1 counts a book's working minutes (brief to seal) only; the seal-to-reveal wait
is reported apart (owner, 24 Oct, "Waiting minutes - Option A"; that reader's change is its own story).

**Live switches:** `daily.live_from.book2_hybrid` and `daily.live_from.book3_ai`, null until the owner sets them, read
by one function beside O1's `live_dates` in `fno/daily/wiring.py` and listed in `fno/config.py`'s allowed
`daily.live_from` keys, so a typo is refused (O1 builder, 16 Oct). A live
book is added to E3's `books`, E2's packed books, `ai_fire` and `ai_collect`; a book not live is in none of them, and
with no book live the two steps record `not_live` (O8 sees every step of `DAILY_RUN_STEPS`).

**Files (new unless named):** `fno/ai_trading/` (`pointer.py`, `versions.py`, `answer.py`, `session.py`, `__main__.py`,
`fire.py`, `receipts.py`, `outcome.py`, `promote.py`, `records.py`, `steps.py`, `ports.py`, `paths.py`, `audit.py`,
`cli.py`, `wiring.py`, `book_wiring.py`); new shared pieces in `fno/ai/`, generic (a path, a transport, a clock; no
book in their signatures) because F2's role routines reuse them too (agreed with F2, 16 Oct): `sealed_publish.py`
(`SealedPublisher`, only if `BookSession` cannot serve a decision as is: design above), `observed_receipts.py`
(`ObservedPushes`) and `fire_once.py` (`FireOnceLog`; G5's and G11's fire code untouched); changed: `fno/ai/wiring.py`
(`build_audit_seeds`, one term), `fno/ai/budget_stop.py` (`LevelBudgetStop` beside G11's class),
`fno/ai/transcript_audit.py` (breach kind `model_misreported`; G11's records and tests unchanged), `fno/constants_operations.py`
(`DAILY_RUN_STEPS` gains `ai_fire` and `ai_collect`), `fno/daily/wiring.py` (the two steps and per-book dispatch),
`fno/desk/pack_wiring.py` (packed books from the run's books), `config.yaml` and `fno/config.py`
(`ai_books.decision_timing`, two `daily.live_from` keys), `fno/daily/reason_codes.py` (the five `ai:` codes),
`tests/ai/test_v4_not_a_money_piece.py` (`DECIDING` gains `fno/ai_trading`, as that test asks), `.gitignore`
(`.ai_decision/`), `tests/ai_trading/`, `tests/e2e/` cases (agreed with O2's builder). Every file under 350 lines.

**Found by the first builder's own reviews of the 16 Oct code and kept (each with a test):** the record scan reads
every decoded text of the pointer (JSON escapes hid a planted secret); a decider's undeclared write anywhere in the
checkout is refused and put back, except the quote parts' folder (`research/data/quotes/`, written in parallel; never
put back); the run check runs inside the guard; one book's failure is that book's `refused` record, never another's
loss; the packs handed to the decider must equal the fired labels; private figures are redacted from every recorded
and alerted reason; a leftover `firing` entry is judged on its submission; the observer's end (exit code, last line) is
reported and the observer is stopped at `ai_collect` and at exit; the fire log commits through E3's
`PendingCommitter`; a wrong AI setting fails the AI steps only, never the quotes or Book 1. **One cap:**
`ROUTINE_POINTER_MAX_BYTES` (64 KiB), already on `main` in `fno/constants_operations.py` and used by G11's v4
pointer; F1t's pointer reuses it.

## Acceptance criteria

Each names its code and test in the claims, with a broken-code proof (quality rule 4), and covers the good, bad,
boundary and empty cases (quality rule 5).

1. **Live switch.** With both switches null, `ai_fire` and `ai_collect` each record `not_live` (O1's `LiveFrom` rule)
   and every other step's record and every committed file is byte-identical to O1's without F1t on a fixture day
   (test). With one book live, only that book is fired, packed, collected and added
   to E3's books. A switch dated after the day leaves it out; on the day, in (boundary test).
2. **Firing, once.** A live book is fired once a day with a pointer holding exactly the fields above and only its own
   private pack; a rerun never fires again (fire log present). Each `not_fired` cause of the Design list is recorded with
   its reason and named in the step's one alert: budget stop, no version, stop rule (2 breaches; 1 breach fires; a breach of an older
   version does not count), no common pack, started at `latest_fire` (fires) and 1 s after (not), pointer at the size cap
   (fires) and 1 byte over (not), a flagged pointer, `FireFailed` (tests). The O5 scan of a full fixture pointer
   (realistic account files at their largest fixture size) finds nothing, and its time is in the claims. The fire log is committed with `firing`
   entries before any trigger call; a process killed between the call and the step's log record, rerun, never fires
   again and records `fire_unknown`, and that book's sealed answer is still judged (test).
3. **The pointer is checked before any input is shown.** `brief` refuses a pointer with a missing or extra field, a
   wrong kind, another book's version, a private pack whose hash differs from its field, or a common pack whose
   committed bytes differ from `common_pack_sha256`, and prints nothing of the input; a good pointer prints the prompt,
   both packs and nothing else from the repository (tests; `brief` reads no file but the prompt and the common pack).
3b. **Cards.** The pointer's `analyst_cards` item holds `role_set_version`, `input_sha256`, every registered role's
   status line and the card only when `valid` or `not_applicable`, and `brief` prints it; with no cards file every role reads `no_submission` and the book is still
   fired; a version with no role units gets an item with no roles; `consulted_units` in the outcome record lists exactly the
   roles whose card was passed (tests with a fake `CardsOfDay`); a full-size card set (every role at F2's largest
   card) with the largest fixture private pack fits under the cap, and the claims show its size in bytes.
3c. **Model reported.** `brief` prints the model rule first; `seal` refuses a `model_reported` or `model_configured`
   that is neither a model ID nor `unknown`, and a `model_source` outside `session_tool`, `instructions` and `none`.
   Judged: `session_tool` with served = configured = registered is not stopped by this check; `session_tool` with
   the served model different (a fallback) while the configured one matches is `model_mismatch`; a configured model
   different is `model_mismatch`; `instructions` naming the registered model is `model_unverified`; `none` or
   `unknown` is `model_unverified`; each no trade (tests). The transcript audit records `model_misreported` when the
   answer's fields differ from the tool call in the transcript (test with a fixture transcript). On the go-live
   non-counted fire the session must report `model_source` `session_tool` with `last_served_model` equal to the
   registered model; any other result blocks the live switch.
3d. **No private figure in the answer.** An answer whose reason, proposal or shadow text holds a fill price, cash or
   P&L figure from the private account files is refused at `seal` and `invalid` at collection, the message naming its
   place, not the figure; a strike or price that also appears in the common pack is accepted; a 2-digit number is not
   checked (boundary tests); `.ai_decision/` is git-ignored (test).
3e. **Slow Book 1.** With a fake `book1` running until 15:11:30, observation 1 is still taken at 15:10:00 and an on-time
   book is judged on time; with the observer killed before 15:10:00 every fired book is `late` and `ai_collect` is
   `refused` (tests).
4. **Seal and reveal.** `seal` adds the labels itself, refuses a wrong shape with what to fix, publishes only the
   commitment, and refuses a second seal; `reveal` waits until `reveal_from` and publishes a reveal that hashes to the
   commitment; the forecast's `seal` and `reveal` behave exactly as before (their tests unchanged and passing).
5. **Receipts by observation.** A commitment visible at observation 1 is on time; one pushed after it is `late` even if
   its commit date says 15:09; `ai_collect` started 30 s after the receipt deadline still observes, 31 s after marks
   every fired book `late` (boundary tests); no GitHub API call is made.
6. **Every status of the judging table** has a test producing it from a fixture day with fake answers (valid, invalid,
   late, missing, not revealed, early reveal, exposed, model mismatch, model unknown, decider refusal, F1t check
   failure), each with exactly one committed outcome record; a day with any status but `promoted` gives the step
   `refused` and exactly one alert naming every such book; a day with all books promoted gives `ok` and no alert.
7. **Pack hashes.** A promoted run's records carry the pointer's two pack hashes, which equal the committed common pack
   and the private pack's committed `.sha256`; a decider writing another hash, another book, another model or session,
   or a second run is `refused` and its run is never committed (tests).
8. **Accepted means filled only through E3 and C4.** End to end on the real `DailyRun`: a promoted Book 2 run whose C4
   pass is recorded fills at E3's snapshot exactly like a Book 1 run; a promoted run whose C4 failed (the action outside
   D4's envelope) never fills and its attempt is in the record; a run committed after E3's deadline is late and never
   filled; a run committed at 15:11:59 and pushed after 15:12 counts, one committed at 15:12:00 is late, a push
   rejected 3 times stops the run with E3's alert (tests);
   every refusal or miss leaves E3's `no_decision.json` and no fill (tests with a fake decider, fake C4 records and
   fake per-book `OrderBuilder` and `ExitRules`; F5's and F6's real ones, and the real C4 modes, replace them in this
   end-to-end test when they land, as part of each book's go-live).
9. **Book isolation.** Book 3's pointer, export and decider input contain no Book 2 file, hash or submission, and the
   reverse; one book's refusal, miss or decider exception leaves the other book's and Book 1's records byte-identical
   to the same day without it; each book's fills go to its own account only (tests).
10. **Errors alert and are recorded; never a silent skip.** A decider raising any exception is `refused` with the
    exception's type and message (the run goes on to E3's steps and the exits); an alert that cannot be sent is printed
    "alert NOT sent" (O1's `ReportedAlerts`); a failed commit stops the run under E3's rule (decision 44) and the rerun
    repeats nothing (tests).
11. **Timing settings.** `ai_books.decision_timing` out of order, missing a key, or not before
    `desk.timetable.decision_deadline` is refused at load with the key named (tests).
12. **Transcript audit, stop rule and budget stop** for decision sessions: selection, record and stop by the
    forecast's rule on the decision fire logs; forecast audits, draws and stops unchanged (tests on both). With BG1's
    level `stop` and the books' minutes below the cap, decisions are `not_fired` (`LevelBudgetStop`) while G11's
    forecasts still fire (`MeterBudgetStop`); level `alert` fires both; an unreadable meter fires decisions with the
    reason in the alert (tests).
13. **Routine prompts and checklist.** `docs/stories/F1t-owner-checklist.md` holds the two routines' exact prompts (one
    line of JSON passed only to `brief`; stop on a refusal; never `--no-verify`), the environment
    variables' names (never values) the daily run needs, and the go-live checks below. A test checks the checklist's
    command names exist in the CLI.
14. **Usage.** A decision session's `brief` and `reveal` write its timing file at the decision timing path; the
    recorder books it as `books_and_roles` with role "<book> trading decision"; a fired decision session with no
    timing file is reported "not captured" by F8c's check; forecast timing is unchanged (tests).
15. **Real output sample.** The claims show the outcome records and alert lines of a fixture day with one promoted and
    one late book, made by the committed code in a test, with no live post.
16. **The judge (F4).** With a fake `JudgeStep`: a passing verdict promotes as before with `AcceptedDecision.judge` set
    and every record's `judge` equal to it; a blocking Book 2 verdict gives `judge_failed`, one alert line, the "no
    trade, judge failed" run and the verdict file committed, and no fill; a decider that writes a chosen trade under
    `judge_blocks` is refused by the run check (nothing committed but the outcome); a failing Book 3 verdict (never
    blocking) still promotes; a book-day that ends before the judge (late, invalid ...) calls no judge; with `NoJudge`
    wired, a valid Book 2 answer is `judge_failed` with "judge not built (F4)" and Book 3 promotes (tests).
17. **Public run log.** On a fixture day with one book `late` and one `refused`, `journal/runs/<d>.json` holds for
    `ai_collect` only the status, the code `ai:NOT_PROMOTED` and its count, with no book reason, figure or path in it;
    the alert holds the full line; a reason not registered in `reason_codes.py` fails the existing registry test
    (tests).
17b. **Strategy label.** A promoted run whose chosen trade's `served.strategy_status` is `research` gives the outcome
    label "strategy not yet passed", one with `paper` "strategy passed"; a chosen trade with no status is `refused` by
    the run check; a no-trade run carries no label (tests).
18. **A rehearsal never fires.** With `rehearsal()` set and both books live, `ai_fire` builds no `RoutineTrigger`, makes
    no HTTP call and records `refused` with `ai:REHEARSAL_NO_FIRE`; with no book live it records `not_live` as in a
    real run (tests, the trigger factory a spy).

**Go-live checks (owner, before setting a live switch; not merge criteria):** the owner's isolation decision above
(condition 3 of 14 Oct; decided (a) on 16 Oct); for Book 2, F4's code merged (else every day is `judge_failed`); an
envelope v1 (Book 2) or constitution v1 (Book 3) registered in D6 with the owner's approval; a full git history in the
daily routine's checkout for Book 3's C4 (judge 263 addendum 1: a shallow clone is refused by design); the owner creates the two routines and
puts their trigger IDs and tokens in the daily run's environment; one fire on a non-counted day proves the routine API
accepts a pointer of the measured size from the daily-run session's network, the session reaches `seal` and `reveal`,
and a transcript read shows no file outside its input (F1 criterion 1 for decisions); D3's `owner_override` refusal,
D4, D5, F5 (for Book 2) or F6 (for Book 3) are merged. (A `paper` strategy is no longer needed: owner, 25 Oct.)

**Build rounds:** round 1, the three shared pieces with their tests (judged on their own, since F2's code waits on
them); round 2, `fno/ai_trading/`, the O1 steps, the wiring and the end-to-end tests.

## Test plan

Unit tests per module with fakes (trigger, transport, git observations, clock, alert sender, decider); session-side
tests run with the standard library only (a test imports the routine side in a subprocess with `-I` and no
third-party path); end-to-end tests in `tests/e2e/` over the real `DayRunner` and `DailyRun` with fixture packs, a
local bare git remote, fake routines that push commitments and reveals at chosen times, and a fake decider writing D3
runs with recorded C4 passes and failures. Broken-code proofs per criterion. No network, no Slack, no Drive.

## Judge verifies

Fires a fixture day with both books live; plants a late commitment, an early reveal, a wrong pack hash in a decided
run, a second run, a decider exception and a C4 failure; checks no planted case fills and each has one record and one
alert; checks that both switches null leaves the day byte-identical; reads the routine prompts and the checklist.

## Gap list (quality rule 2)

| Requirement (source) | Covered by | Or out, with the reason |
|---|---|---|
| Own session per book, no shared conversation or files (F1, 13.5 step 3) | design (one routine per book), criterion 9 | Same-platform memory or cache: not controllable by code; transcript audit, criterion 12 |
| Sees only the common and its own private pack (F1) | criteria 3, 9 | Reading the public repository is detected (audit), not prevented: `sealed_same_day` (Context) |
| No repository, no network (F1 revised design) | | Out: no way for code to read an answer from such a session (Context); the owner may decide otherwise |
| Input by export with hashes verified before sending (F1) | criteria 2-3 | |
| Export over the limit is a failed day, never truncated (F1) | criterion 2 | |
| Output received after the receipt deadline ignored (F1 criterion 3) | criteria 5, 6 | Server receipt time replaced by E3's observation rule (judge 82) |
| Not promoted before the promotion deadline fails closed (F1 criterion 3) | criterion 8 (E3's 15:12 deadline is the promotion deadline) | |
| Served model recorded; mismatch unscored (F1 criterion 4, D6) | criteria 6, 7 | Mismatch is also no trade (fail closed) |
| Failed or limited session is "no decision (AI unavailable)" (F1 criterion 5) | criterion 6 (`no_submission`) | Scoreboard A exclusion: S3's builder |
| No secret or credential in the session; prompt scanned (F1 criterion 6, O5) | criteria 2 (scan), 13 | |
| Both pack hashes match the committed packs (F1 criterion 7) | criterion 7 | |
| Tool-call breach audit (F1 defence in depth) | criterion 12 | |
| D3 schema, D4 envelope, D5 constitution, C2, C4 (task) | port (F5, F6), criteria 7-8 | The checks themselves: D3, D4, D5, C2, C4 stories |
| Refusals and misses recorded with reasons and alerted (task) | criteria 6, 10 | |
| Accepted decisions go to E4/E8 fills (task) | criterion 8 | E8 itself: its story |
| Book isolation: no shared cash, no other book's pack (task) | criterion 9 | |
| Reuse `fno/ai` fire, collect, seal (task) | design (trigger, seal, transport, receipts interface, audit) | |
| Live switch off until the owner turns it on (task) | criterion 1 | |
| Budget cap stops AI roles (BG1, design 7.6) | criterion 2 | |
| AI usage recorded (F8) | criterion 14 | |
| Book 2 rule default precomputed by code (F5) | | F5 (agreed 16 Oct, revised after E2c's privacy point): at E2's pack step code runs D2 for Book 2 at the cutoff and puts the rule default and eligible set inside Book 2's private pack as its "evaluation" sheet (no journal file); it travels in F1t's pointer under `private_pack_sha256` with no change here. C4 reads the sheet, never the AI's answer; D3's replay must reproduce it |
| Analyst cards and consulted units (F2, F9) | criterion 3b | The cards themselves: F2 |
| Shadows (F7) | carried in Book 3's `decision` unchanged | F6/F7 |
| AI judge (F4) | Design "The judge", criterion 16 | The verdict's checks and file content: F4 |
| Public run log keeps codes only (O1-status-only) | criterion 17 | |
| A rehearsal touches no outside service (REH1) | criterion 18 | The AI books' dry-run replay: the owner's REH1 follow-up (25 Oct) |
| "Judge or AI unavailable" row of design 9 (O2) | criteria 6, 10 | O2's suite gains these cases once F1t merges (agreed with O2's builder) |

## Known limits (said plainly)

- **Timing is tight and unproven for decisions (strong evidence above):** the forecast routines answered in time on 7
  of 12 book-days (15-23 Oct) with a 5-minute window, 36 s to 5 min 9 s after the fire; the decision window is about
  10 minutes on a normal day (fire after the 14:58 pack, seal by 15:10), less when the canonical snapshot is late. The
  model was reported on 1 of 11 answered book-days: unless the decision prompt's identity-line rule fixes that (to be
  shown on the non-counted fire), the books will almost never trade.
- **Four routine sessions overlap** from about 15:00 to 15:11 (two forecast, two decision); the platform's limit on
  concurrent routine runs is not documented to this builder and is measured on the non-counted fire.
- **Four reveal pushes race at 15:10:10** (two forecast, two decision), beside the daily run's own pushes to `main`.
  Each push retries on a rejected push; a reveal still not on the remote at observation 2 (15:11:00) is
  `not_revealed`, never a trade. The non-counted fire records each reveal's push time.
- **The served model is the latest turn's** (`last_served_model`): a fallback on an earlier turn is caught only by the
  transcript audit, which reads every session of the first 10 fired days and 2 a week after. A pack built late (up to 15:10) leaves no time; such days are `not_fired` or `late`, never a trade. The
  timetable is S1's to freeze from measured times.
- **Isolation is detected, not prevented** (`sealed_same_day`), as for forecasts.
- **The pointer grows with the private pack** (account files grow with fills). At the measured API limit a day fails
  closed; an alert at 80% of the cap names the need for a smaller private view (a later version).
- **Two more routine runs per session day** on the owner's plan; the owner set no AI budget cap (25 Oct).

## Open questions

1. **F4 (assigned to this builder on 25 Oct):** F4's text takes `JudgeCase`, `Judged` and `JudgeStep` from
   `fno/ai_trading/ports.py` (one port, Design).

Settled: the interfaces with F5 (16 Oct; F5 text PASS, judge 307 add. 5), F6 (16 Oct; F6 text PASS, judge 302 add.
2), F2 (16 Oct; F2 text PASS, judge 303 add. 1) and F4 (16 Oct, judge 308.1 waits only on this text); model "unknown"
is no trade (orchestrator, 16 Oct); the new package `fno/ai_trading/` reuses G11's `RunTerms` chain (merged
712386480) with one more instance and no new parameter, and G11's tests stay unchanged and passing.

## Depends

Merged: O1, E2, E2e (`BookSheet`), E3, F8c, BG1, D3's `owner_override` refusal, D4, D5, G11. Not merged, needed only for
a book's go-live (fakes stand in for F1t's merge): F5 (Book 2), F6 (Book 3), F4 (Book 2), F2 (cards; optional).
**Status:** text PASS (judge 301 addendum 1, 16 Oct); revision 2 (25 Oct) for the code judge.

## Claims

Text round (revision 2): every fact in Context was re-read on `main` of 25 Oct by this builder (files named beside
each); the AI audit counts come from all 16 `*_audit.json` files of 14-23 Oct (`status`, `model_reported`,
`fire.fired_at`, `commitment_received_at`). Code claims follow in the code round.

Round 2 (answers to judges 621 and 623, all accepted; each fix is text):
- 621 SF1 / 623 SF1 (the served model): Design "Model reported", the judging table, criterion 3c, go-live check 6 and
  the checklist's test fire. `last_served_model` is checked and `model_configured` recorded beside it; an instructions
  line alone is `model_unverified` (the orchestrator's ruling); a false copy is a transcript-audit breach.
- 623 SF2 (the budget rule): `LevelBudgetStop`, a second implementation of G11's `BudgetStop`, stops decisions on
  BG1's level `stop` alone. Criterion 12 has the case "level `stop`, books below the cap: decisions not fired,
  forecasts fired".
- 621 m1: the timeline row at 15:10:10 states every seal before any reveal; Known limits and the test fire name the
  reveal race.
- 621 m2 / 623 minor: the unreadable meter is a deliberate fail-open on cost only (orchestrator, 25 Oct). It costs
  minutes, never a trade.
