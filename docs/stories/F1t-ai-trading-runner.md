# Story F1t: the AI books' trading runner (F1's trading part, Book 2 and Book 3 steps in the daily run)

**Repository:** trading · **Lane:** 1 (decides trades, outside services, schedules) · **Size:** L ·
**Builder:** session_01PLbKH15BXYucP6cT9xtoxK · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH ·
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

## Context and why (each fact marked)

- **What runs today (strong evidence: code on `main` and `story/o1-daily-run` at edb4e2b6):**
  - O1's `DAILY_RUN_STEPS` has one decision step, `book1` (`fno/constants_operations.py` on O1's branch). Books 2 and 3
    exist only as forecast routines (G5, `fno/ai/`), fired from the forecast-capture GitHub Actions job.
  - E3's `decisions` step (`fno/desk/daily_steps.py:collect_decisions`) already handles any list of books: at the 15:12
    deadline it pulls once and takes each book's first original D3 run visible then (D3b); a book without one gets a
    committed `no_decision.json`. The fills read only those runs, through one `OrderBuilder` (built at the fill) and
    C4's recorded pass (`fno/desk/recorded_c4.py`). So the AI books need no change to E3's collection or fills: they
    need a D3 run committed before 15:12.
  - E2's private packs are built only for `PACKED_BOOKS = (BOOK1_RULES,)` (`fno/desk/pack_wiring.py`) and kept in Drive
    (E2c); only their `.sha256` is committed. A routine session has no Drive credentials (and must not have any).
  - C4 fails every Book 2 and Book 3 trade closed today (`WaitsFor("envelope", "D4")`, `WaitsFor("constitution",
    "D5")`, `fno/checks/wiring.py`). D4 and D5's code is on `story/d4-envelope-code` and `story/d5-constitution-code`.
  - The forecast routines' timing on real days (strong evidence, `research/forecasts/ai_v1/2026/*_audit.json`): fired
    at 15:10:20 IST; 14 Oct no commitment at all (`no_submission`, both books); 15 Oct commitments received 15:15:12
    and 15:15:15, 12-15 s after the 15:15:00 deadline (`late`, both); 16 Oct received 15:11:26 and 15:11:59, 66-99 s
    after the fire (`on_time`, both; Book 3's model `unverified`). One of three days was usable.
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

## Scope

**In:**
1. Two O1 steps, `ai_fire` (right after `book1`) and `ai_collect` (before E3's `decisions`), each AI book gated by its
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
   the stop rule and the budget stop, each reusing `fno/ai`'s and `fno/budget`'s code.
8. End-to-end tests over the real `DailyRun` with fixture packs and fake AI answers: valid, invalid, late, missing, not
   revealed, model mismatch, exposed, refused by the decider, blocked by C4.
9. The two routines' exact prompts and the owner's checklist (`docs/stories/F1t-owner-checklist.md`).

**Out (each with its owner or reason):**
- What a book decides and its prompt: F5 (Book 2, D4/D5 owner session_01SFDjjZx7JYziM3jqJytG2z) and F6 (Book 3, the
  F6/F7 builder). F1t registers their prompt file and shape check by one line each when they land.
- Analyst finding cards (F2), matched shadows (F7), the red team and judge (F3, F4): they travel inside the answer's
  book-specific `decision` object, defined and checked by their stories. F1t passes them through unchanged.
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
| 14:58-15:10 | daily run, E3 `pack` | common pack committed; each live AI book's private pack built (Drive) |
| right after `book1` | `ai_fire` | one pointer per live AI book, fired once; not fired if the step starts after `latest_fire` 15:07:00 |
| until 15:10:00 | each routine | `brief` → decides → `seal` pushes only its commitment to `main` |
| 15:10:00 | `ai_collect` | `git fetch origin main`, observation 1 (`receipt_deadline`): a commitment counts only if visible then |
| 15:10:10 | each routine | `reveal` (`reveal_from`) pushes the answer and salt |
| 15:11:00 | `ai_collect` | fetch and merge, observation 2 (`reveal_deadline`); judge each book; accepted ones go to the decider; runs checked, then committed with the outcome records |
| 15:12:00 | E3 `decisions` | unchanged: takes each book's first original run visible and committed before the deadline |

The `ai_collect` step started more than 30 s after `receipt_deadline` (a restart) marks every fired book `late`, as E3
does (fail closed), and its step status is `refused` with that reason, so the day ends "with problems" and O8 sees it.
Values are config, so S1's measured-timing rule can move them.

**Pushed late by earlier steps (O1 builder, 16 Oct):** `pack` retries until 15:10 while the canonical snapshot is late,
and `book1` may run up to its 600 s limit. On a day the pack lands after about 15:07, every live AI book is
`not_fired` (late start). That is correct, never a trade, and it is alerted.

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

**Firing (`fno/ai_trading/fire.py`):** for each live AI book, in this order, the first that applies is recorded:
budget signal `stop` (BG1, `BudgetSignal`) → `not_fired`; no registered decision version → `not_fired`; stop rule (two
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
version's label), `common_pack_sha256`, `private_pack_sha256` and `private_pack` (the book's E2 private pack body).
Only that book's private pack is ever put in its pointer (book isolation). `brief` refuses a pointer whose fields are
not exactly these, whose version is not the book's current one, or whose private pack's canonical SHA-256 (E2's
`canonical_json`) is not `private_pack_sha256`.

**Routine side (`python -m fno.ai_trading`, standard library only):**
- `brief '<pointer>'`: checks the pointer, reads `journal/packs/<d>/common.json` from `main` and checks its SHA-256,
  checks the versioned prompt's hash, saves its private working files under `.ai_decision/` (never committed), then
  prints the prompt, `INPUT`, the common pack and the private pack. Nothing is shown unless every check passes.
- `seal <answer.json>`: the answer is `{"model_reported": <text>, "decision": {...}}`. `seal` adds the labels (book,
  day, version, both pack hashes) itself, checks the shape (F1t's base: `decision` is an object with `action` (text)
  and `reason` (one line, 1-600 characters); then the book's own shape check, registered with its version by F5 or
  F6), and publishes only the commitment, to `journal/ai_decisions/submissions/<YYYY>/<d>_<book>.commitment.json`.
  A refused answer names what to fix, so the model can fix it before the deadline.
- `reveal`: waits until `reveal_from`, then publishes answer and salt to `<d>_<book>.reveal.json`.
- The seal and reveal steps are the same as the forecast's: `fno/ai/book.py`'s publish logic moves into one shared
  helper used by both (no behaviour change for forecasts; their tests unchanged), so nothing is written twice.

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
| `model_mismatch` | `model_reported` differs from the registered model | no |
| `model_unverified` | `model_reported` is `unknown` (orchestrator ruling, 16 Oct: no trade, reason recorded; forecasts keep their rule) | no |
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
    commitment_commit: str; reveal_commit: str

class AiBookDecider(ABC):             # F5: Book 2; F6: Book 3
    def decide(self, accepted: AcceptedDecision) -> DecidedRun: ...
        # writes ONE D3 run (DecisionStore, atomic) with C2 and C4 inside, as Book 1's DecisionRun does; a blocked
        # action still gets a "no trade, blocked" run with the attempt recorded (D4 criterion 2)
        # raises DecisionRefused(reason) when no run can be written (e.g. the private pack does not rebuild)

@dataclass(frozen=True)
class DecidedRun:
    run: Path                         # journal/<book>/decisions/<d>/<run_id>/
    files: tuple[Path, ...] = ()      # other files to commit with it (C4's failure log)
```

**F1t's check of a decided run before committing it:** the run is the only run of the book's day and is under its
folder; every record passes D3's `validate_record`; every record's `book`, `common_pack_sha256` and
`private_pack_sha256` equal the pointer's (criterion 7), `model_served` equals `model_reported`, `session_id` the fire
log's link, and `served` names the decision version. A run that fails is never committed: it is removed from disk
(it was never published), its file hashes are kept in the outcome record, and the book-day is `refused`.

**Book isolation:** each book's pointer holds only its own private pack; the decider receives only its own book's
packs; each book's account is its own E1 folder (no shared cash); submissions of one book are never in another's
input. Within a session the model can still read the public repository: reading another book's files is the transcript
audit's breach kind `file_outside_input`, as for forecasts.

**Transcript audit and stop rule:** the same rule as the forecasts (every session of the first 10 fired days, then 2 a
week drawn with the same verified weekly seed), the same record and breach kinds, written to
`journal/ai_decisions/<YYYY>/<d>_<book>_transcript_audit.json` by `python -m fno ai-trading audit-record`. `fno/ai`'s
`fired_sessions`, `TranscriptAudits` and `breached_days` take the folder or path as a parameter whose default is
today's value (no forecast behaviour changes).

**Usage (F8):** each decision routine's last step records its run with F8's `record-usage --self-timed --purpose
books_and_roles --role "<book> trading decision"` (as LR1's routine does).

**Live switches:** `daily.live_from.book2_hybrid` and `daily.live_from.book3_ai`, null until the owner sets them, read
by one function beside O1's `live_dates` in `fno/daily/wiring.py` and listed in `fno/config.py`'s allowed
`daily.live_from` keys, so a typo is refused (O1 builder, 16 Oct). A live
book is added to E3's `books`, E2's packed books, `ai_fire` and `ai_collect`; a book not live is in none of them, and
with no book live the two steps record `not_live` (O8 sees every step of `DAILY_RUN_STEPS`).

**Files (new unless named):** `fno/ai_trading/` (`pointer.py`, `versions.py`, `answer.py`, `session.py`, `__main__.py`,
`fire.py`, `receipts.py`, `outcome.py`, `promote.py`, `records.py`, `steps.py`, `ports.py`, `paths.py`, `audit.py`,
`cli.py`, `wiring.py`, `book_wiring.py`); changed: `fno/ai/book.py` (shared publish helper), `fno/ai/audit_plan.py`,
`fno/ai/transcript_audit.py`, `fno/ai/stop_rule.py` (path parameters), `fno/constants_operations.py`
(`DAILY_RUN_STEPS` gains `ai_fire` and `ai_collect`), `fno/daily/wiring.py` (the two steps and per-book dispatch),
`fno/desk/pack_wiring.py` (packed books from the run's books), `config.yaml` and `fno/config.py`
(`ai_books.decision_timing`, two `daily.live_from` keys), `tests/ai_trading/`, `tests/e2e/` cases (agreed with O2's
builder). Every file under 350 lines.

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
   (fires) and 1 byte over (not), a flagged pointer, `FireFailed` (tests). The fire log is committed with `firing`
   entries before any trigger call; a process killed between the call and the step's log record, rerun, never fires
   again and records `fire_unknown`, and that book's sealed answer is still judged (test).
3. **The pointer is checked before any input is shown.** `brief` refuses a pointer with a missing or extra field, a
   wrong kind, another book's version, a private pack whose hash differs from its field, or a common pack whose
   committed bytes differ from `common_pack_sha256`, and prints nothing of the input; a good pointer prints the prompt,
   both packs and nothing else from the repository (tests; `brief` reads no file but the prompt and the common pack).
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
   every refusal or miss leaves E3's `no_decision.json` and no fill (tests with a fake decider and fake C4
   records; the real C4 modes once D4 and D5 merge).
9. **Book isolation.** Book 3's pointer, export and decider input contain no Book 2 file, hash or submission, and the
   reverse; one book's refusal, miss or decider exception leaves the other book's and Book 1's records byte-identical
   to the same day without it; each book's fills go to its own account only (tests).
10. **Errors alert and are recorded; never a silent skip.** A decider raising any exception is `refused` with the
    exception's type and message (the run goes on to E3's steps and the exits); an alert that cannot be sent is printed
    "alert NOT sent" (O1's `ReportedAlerts`); a failed commit stops the run under E3's rule (decision 44) and the rerun
    repeats nothing (tests).
11. **Timing settings.** `ai_books.decision_timing` out of order, missing a key, or not before
    `desk.timetable.decision_deadline` is refused at load with the key named (tests).
12. **Transcript audit and stop rule** for decision sessions: selection, record and stop by the forecast's rule on the
    decision fire logs; forecast audits, draws and stops unchanged (tests on both).
13. **Routine prompts and checklist.** `docs/stories/F1t-owner-checklist.md` holds the two routines' exact prompts (one
    line of JSON passed only to `brief`; stop on a refusal; never `--no-verify`; record usage), the environment
    variables' names (never values) the daily run needs, and the go-live checks below. A test checks the checklist's
    command names exist in the CLI.
14. **Real output sample.** The claims show the outcome records and alert lines of a fixture day with one promoted and
    one late book, made by the committed code in a test, with no live post.

**Go-live checks (owner, before setting a live switch; not merge criteria):** the owner creates the two routines and
puts their trigger IDs and tokens in the daily run's environment; one fire on a non-counted day proves the routine API
accepts a pointer of the measured size from the daily-run session's network, the session reaches `seal` and `reveal`,
and a transcript read shows no file outside its input (F1 criterion 1 for decisions); D3's `owner_override` refusal,
D4, D5, F5 (for Book 2) or F6 (for Book 3) are merged; at least one `paper` strategy exists (slice E's trigger).

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
| AI usage recorded (F8) | criterion 13 (prompt step) | |
| Book 2 rule default precomputed by code (F5) | | F5: inside Book 2's private pack or its decider; F1t carries the private pack whole |
| Red team, judge, cards, shadows (F2, F3, F4, F7) | carried in `decision` unchanged | Their stories |
| "Judge or AI unavailable" row of design 9 (O2) | criteria 6, 10 | O2's suite gains these cases once F1t merges (agreed with O2's builder) |

## Known limits (said plainly)

- **Timing is tight and unproven for decisions (strong evidence above):** the forecast routines answered in time on 1 of
  3 days. A pack built late (up to 15:10) leaves no time; such days are `not_fired` or `late`, never a trade. The
  timetable is S1's to freeze from measured times.
- **Isolation is detected, not prevented** (`sealed_same_day`), as for forecasts.
- **The pointer grows with the private pack** (account files grow with fills). At the measured API limit a day fails
  closed; an alert at 80% of the cap names the need for a smaller private view (a later version).
- **Two more routine runs per session day** on the owner's plan; BG1's cap applies.

## Open questions

1. The hand-over interface: F5 (session_01SFDjjZx7JYziM3jqJytG2z), F6/F7 (session_01KTAQCDjPkDBKwfCMhWphXb) and F2
   (session_01WSMMv5nK4wDdktFrudJfXv) to confirm before code; F5 to say how Book 2's rule default reaches the AI
   before it decides.

Settled (orchestrator, 16 Oct): model "unknown" is no trade; the new package `fno/ai_trading/` with default-preserving
changes to `fno/ai/` is fine (G11's owner, session_013xqaNTCbSBytKgqpfaYFqZ, told); claims in
`reviews/claude/response_263_f1t-ai-trading-runner.md`.

## Depends

O1 (merged first; F1t's code builds on it), D3 `owner_override` refusal, D4, D5, F5, F6 (for each book's go-live, not
for F1t's merge: fakes stand in), E2, E3, BG1, F8 · **Status:** story text for the judge
