# Epic F: AI layer for books 2 and 3 (cloud routines)

Roles: head of desk, all judgement roles, red team, judge, statistician, tax and cost accountant. Goal: Book 2 (AI
inside the authority envelope) and Book 3 (fully AI under the constitution) decide every day in isolated cloud
sessions, their AI roles' work is recorded as evidence, and each AI role is kept only if it adds net value after its
cost (design sections 3, 7, 8.1, 10, 12, 13.5, 13.6). Owner decision D4: AI roles run as scheduled Claude Code cloud
sessions; no AI API keys. Story template, definition of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

**Status note:** design section 12 and 13 are approved; the owner decides when books 2 and 3 start (design 12.9: D4
runtime decided; the start date and the owner's recorded monthly plan cost come before the first counted decision).

---

## F1. Isolated AI book sessions

**Repository:** trading

**Description:** As the statistician, I want each AI book to decide in its own cloud session that can see only the
common pack and its own private pack, with the model it actually used recorded and any breach detected, so that the
comparison between books is fair and the firewall is proven, not assumed.

**Context and why:** Design 13.5 step 3: each book decides in its own isolated sub-session with no shared
conversation, cache, memory, temporary files or another book's findings; both pack hashes in every decision. Model
identity: the served model is recorded; a mismatch with the registered version is "AI unavailable, unscored" (D6).
Failure or a usage limit gives "no decision (AI unavailable)". Cloud sessions can be created from a routine with the
`create_session` tool (the stock tool's routines already dispatch sessions this way); a session's served model and
transcript can be read back (`get_session`, `list_events`).

**Scope.** In: creating the per-book session, what it can see, collecting its decision, model identity, breach audit,
failure handling. Out: what the book decides (F5, F6).

**Expected design (revised after ChatGPT review 26):** isolation is **preventive**, not only detected afterwards.
A sparse checkout does not stop git from reading other paths from history, and both repositories are public during
development, so any session with internet access could read another book's records. Therefore:
- **No repository, no network.** Each AI book session is created **without a source repository** in a dedicated cloud
  environment (set up by the owner) whose network access is the most restrictive level offered: none, or only the
  domains in the book version's source contract (never `github.com`). It has no credentials of any kind.
- **Input by export.** `fno/ai/export.py` builds an allowlisted export for the book: the common pack, that book's
  private pack, its prompts and its version's allowed sources, with a manifest of every item and its SHA-256, verified
  by code before sending. The export is delivered inside the session's prompt (the story measures the size limit; an
  export over the limit is a failed day, never a truncated one).
- **Output by message.** The session returns its decision record, role cards, forecasts and (Book 3) shadow decisions
  as one JSON block in its final message. `fno/ai/session_runner.py` (outside the AI) reads it from the session's
  event log, whose server-side timestamps are the **receipt time**: an output received after the **receipt deadline**
  is ignored ("no decision (late)"). The runner validates the output, runs C2 and C4, and commits it before the
  **promotion deadline**, which comes before the execution snapshot (E3); anything not promoted by then fails closed.
- **Defence in depth.** The runner still reads the session's tool calls and marks any network or file access outside
  the export as `firewall breach, unscored`.
- **Model identity:** the served model is read from the session record; a mismatch with the registered version gives
  `unscored` and pauses scoring (D6). A failed or limited session gives "no decision (AI unavailable)".
- **If the platform cannot enforce this isolation** (for example no network-free environment), the limitation is
  written down, books 2 and 3 run labelled "isolation not enforced", and their results are **not** scored as an
  independent comparison until an enforceable mode exists.

**Acceptance criteria:**
1. On a **real** isolated session (not a fake), attempts to read another book's data fail before the model sees it,
   through **every network-capable tool the environment exposes** (shell commands, any fetch, browser or search tool):
   the public repository's raw file URL, a `git clone` of this repository, and a read of any path outside the
   export (recorded transcript). If the version allows source domains, one allowed domain is reached and several
   forbidden ones are refused. A network-free environment is preferred for counted decisions; the environment's
   identity and network policy are recorded in the version (D6).
2. The export manifest lists only allowed items; a test plants another book's file and confirms the export refuses it.
3. An output whose server receipt time is after the receipt deadline is ignored and "no decision (late)" is committed;
   an output not validated and promoted before the promotion deadline fails closed (no fill).
4. A served model different from the registered version gives `unscored` and pauses scoring (D6).
5. A failed or limited session gives "no decision (AI unavailable)", counted as no trade on scoreboard B and excluded
   from judgement scores on scoreboard A.
6. The session receives no secret and no credential; the export and prompt are scanned (O5).
7. Both pack hashes in the collected decision match the committed packs.

12. The report prints each unit's worst month of paired differences and its mean one-lot maximum-loss difference, by
    hand on the constructed example. Changing only those figures (same nets) leaves every verdict and p-value unchanged
    (test). A `drop proposed` is printed as a proposal for the owner, never acted on.

**Test plan:** unit tests with a fake session API (event logs, served model, receipt times); the real-session
isolation test of criterion 1 on a non-counted day, recorded in the conversation log.

**Judge verifies:** re-runs the real isolation test; reads one session's event log; checks receipt times and hashes.

**Depends:** D3, D6, E2, E3 · **Size:** L · **Status:** forecast part built: seal PASS (judge 62); owner's conditions 1-2 met (judge 62 addendum 1); audit seed (0688ad5, 567ceea) and G4's gate (22ace2f, 44090c1) PASS (judge 62 addenda 2-3); first live run 14 Oct 2026 ~15:10 IST. Trading part later (slice 4)

---

## F2. Analyst roles and finding cards

**Repository:** trading

**Description:** As the head of desk, I want the AI team's analyst roles (volatility, macro and global cues,
positioning, equity research), added one at a time, each to write a short, checkable finding card from point-in-time
data, sealed before the books decide and handed to Books 2 and 3, so that each field's view reaches the decision
independently, every number in it can be traced to captured data, and F9 can measure whether each role earns its cost.

**Context and why:** Design v2 `07_ai_team.md` section 7.2 (one routine prompt per role, versioned; analysts feed Books
2-3 and never decide trades), 7.5 (what an AI role must never do), 7.6 (cost, F9 value, BG1's stop order: analysts stop
first). `DESK_DESIGN.md` step 4: AI roles are added one at a time, each kept only if it adds net value. REPLAN cut F2
to these analyst roles (the first-plan text with eight roles inside the book's session is replaced). Owner, 16 Oct
2026: Books 2 and 3 engines are built and judged now and stay switched off until a strategy or idea qualifies; the
core engine is "validated end-to-end, tested end-to-end", "no surprises", "do not over-engineer"; every failure alerts
and is recorded; every data file is write-once in Drive with a SHA-256 receipt in the repository (O9). Orchestrator's
answers to the text's open questions (16 Oct 2026, response 264): 14:00 cutoff; the books' model; F9's cost rule agreed
with F9's owner; inputs and cards through O9's `DataStore`.

**Honest note (reasoning only):** there is no evidence that analyst cards improve a decision; the books could read the
same data themselves. The cards' value is that each view is independent, written down before the outcome and
separately removable, so F9's paired ablation can test it. If F9 finds no value after its cost, the owner drops the
role. The roles cost AI minutes every session they run, so they stay off until the books trade (criterion 12).

**Why one analyst first (response 264).** F9 removes one unit per decision day in turn (`k mod n`), and a unit gets a
verdict only after 30 changed opportunities. With n units, each needs about n times as many decision days: if a card
changes the decision on one day in five (an assumption, reasoning only), one unit needs about 150 decision days (about
7 months) and three units about 450 (about 21 months) before the first verdict. One analyst also costs one session a
day, not three. So v1 enables **one role, volatility** (the closest to an options structure choice, and its inputs are
all captured today); the code takes any number of roles, and each later role is added as a new registry entry and a
new book version (D6) on the owner's word, with its own input adapters and prompt then.

**Scope.** In: the roles registry and the volatility prompt, the volatility inputs (point-in-time), the finding-card
schema and its validator, firing, sealing and collection through the existing `fno/ai` mechanism, the day's cards file
the books' trading runner (F1 trading part, "F1t", session_01PLbKH15BXYucP6cT9xtoxK) reads, alerts and records for every
missing or refused card, the live switch. Out: the other three roles' inputs and prompts (added one at a time, above),
the book's decision and how it uses cards (F1t, F5, F6), F9b's shadow decision with one card withheld (F9b), F9's cost
rule (F9's owner, item 10), the devil's advocate on the daily trade card (T3), red team (F3), AI judge (F4), screens and
any UI-facing API (owner, 16 Oct 2026).

### Expected design

**1. Roles registry.** `fno/analysts/roles.py` holds one `RoleVersion` per role and version, in the pattern of
`fno/ai/versions.py`: `role`, `number`, `prompt_file` (`agents/analysts/<role>_v<n>.md`), `prompt_sha256`,
`registered_model` (the books' model), `inputs` (the input item kinds it may see), `unit_id` (`analyst_<role>`, F9's
unit name). v1 registers `volatility` v1 only; the planned roles and their order (macro, positioning, equity research)
are listed in the module's docstring, not registered, so nothing unbuilt can be fired. A prompt changes only as a new
version; the routine refuses a prompt whose bytes differ from the registered hash.

**2. Inputs, point-in-time.** `fno/analysts/inputs.py` defines `AnalystInput` (interface): `items(day, cutoff) ->
list[InputItem]`, each item with `item_id`, `kind`, `source`, `first_seen_at` and `lines` (plain text, one fact per
line, built by code). An item is admitted only when its **first-seen time** (when this project first recorded it: a
`first_seen_at` column, an O9 receipt's time, an A4 sidecar's `finished_at`) is at or before the cutoff; a content date
never stands in for it. An input with no first-seen time, or none at or before the cutoff, is `missing` with its reason,
never filled. v1 adapters for volatility (one class each, wired in `fno/analysts/wiring.py`), read through O9's
verified Drive cache once their files have moved there and from the checkout until then (one adapter line each):

| Item | Content (computed by code) | Source and first-seen time |
|---|---|---|
| `vix_daily` | India VIX closes, last 60 sessions before the day | A15 `india_vix_daily.csv`, its `first_seen_at` |
| `previous_pack` | The previous session's 15:00 fields: ATM IV per expiry, futures, VIX | G2's v2 pack, its committed time (the pack's receipt after O9) |
| `vol_summary` | Trailing RV20 from official closes; the VIX and front ATM IV percentile over the 60 sessions shown | warm-up closes and the two items above |

**Skew** is not in v1: no daily skew summary is captured (E2b dropped per-contract items); it comes as a new input and
a new prompt version once captured. Same-day intraday data is not in v1 (A16's slots are not a committed summary yet).

**3. The day's analyst input.** The Actions job (item 7) builds every registered role's items at the cutoff and saves
one file through O9's `DataStore` (`fno/storage/data_wiring.py`, writer `analyst-cards`): `analysts/<YYYY>/<d>_input.json`
in Drive's `data` area, with its receipt committed under `receipts/` before any role is fired. The file holds, per role,
its items and a manifest (item id, kind, source, first-seen time, SHA-256 of its lines), the cutoff and the missing
inputs with their reasons; derived summaries only, never raw broker quote rows (A4b). **A routine session has no Drive
credentials (F1t's rule, as F1's isolation), so each role's own items travel in its pointer** (F2's own pointer,
`fno/analysts/pointer.py`, one line of JSON, capped at 64 KiB like F1t's; an input over the cap is `not_fired`, never
truncated), with the role's `input_sha256` (canonical JSON of that role's part of the input file). The collection checks
that hash against the Drive file read through the verified cache, which refuses bytes that differ from the receipt.

**4. The finding card.** The routine writes only the draft; code adds the labels (`role`, `day`, `as_of` = the cutoff,
`version`, `input_sha256`, `card_id`) so the model cannot mislabel them. Schema version 1:

```
{"schema_version": 1, "role": "...", "day": "YYYY-MM-DD", "as_of": "<cutoff, ISO>", "version": "<role version label>",
 "input_sha256": "...", "card_id": "<role>/v<n>/<day>", "model_reported": "...",
 "not_applicable": null | "<one-line reason>",
 "claims": [{"text": "<one line>", "evidence": ["<item_id>", ...], "label": "strong" | "some" | "reasoning"}],
 "view": {"direction": "up" | "down" | "range" | "no_view", "volatility": "rising" | "falling" | "stable" | "no_view",
          "horizon_sessions": 1-20 | null},
 "confidence": "strong" | "some" | "reasoning",
 "counter_evidence": "<one line>", "proves_wrong": "<one line: the measurable condition that would prove the view wrong>"}
```

**5. The validator** (`fno/analysts/card_check.py`; the same check at seal and at collection, as `fno/ai/answer.py`
does). A card is refused, with the first rule it breaks in F2's own words, when:
1. its fields or labels differ from the pointer and the input (exact field set; labels equal);
2. it has 0 claims and no `not_applicable` reason, more than 5 claims, or claims together with `not_applicable`;
3. a claim's text is not one line of 1 to 40 words, or holds a link, mention or code block (`fno/advocate/numbers.py`
   `form_failure`, imported, unchanged; its message is reworded for the card);
4. a `strong` or `some` claim cites no evidence, or any evidence pointer is not an item id of this role's input;
5. a number in a claim is not a whole number token of the cited items' lines, or a number is written in words ("one",
   "half"; the prompt says to write digits) (`number_tokens`, `number_failure`, imported, unchanged); a claim citing no
   item may hold no number;
6. `confidence` is above the best claim label (strong > some > reasoning);
7. `view` values are outside their lists, `horizon_sessions` is outside 1-20 while a direction or volatility view is
   given, or a view other than `no_view` is given with `not_applicable`;
8. `counter_evidence` or `proves_wrong` is missing, empty or not one line (both may say "none found");
9. `model_reported` is not short text (as F1's answer check).
A `not_applicable` card (claims empty, view `no_view`) is valid: "nothing applies today" is an answer, never a number
invented to fill the card.

**6. Sealing (the books' mechanism, unchanged).** Before the commitment deadline the routine pushes only a commitment
(the SHA-256 of a random salt and its card, `fno/ai/seal.py`) to `main` with `fno/ai`'s `GitMainTransport`, at
`research/analysts/submissions/<YYYY>/<d>_<role>.commitment.json`; after the reveal time it pushes the reveal (card and
salt) beside it. This is the same path the AI books use (G5 today, F1t for decisions), because a routine cannot write to
Drive; when O9's step 4 moves the AI books' seal files to Drive receipts, the roles' move with them, in the same
change. Receipt times come from the same `PushReceipts` adapter the books use (F1t's `ObservedPushes`: a `git fetch` at
each deadline, no token), and a later rewrite never counts (`submissions.py`, first publication). So no role can read
another role's card before its own commitment is in, and no card can change once sealed.

**7. Firing and collection: the existing `fno/ai` mechanism, extended, never copied.** The trigger (`RoutineTrigger`,
one routine per role, two repository secrets each, an unconfigured role is `UnconfiguredTrigger`), the seal, the
transport, the receipts, the first-publication reading, the model check (`outcome.model_check`) and the fire-once log
are shared. F1t builds three generic pieces in `fno/ai/` (agreed 16 Oct 2026; names may change in its review):
`SealedPublisher` (commitment, wait, reveal; extracted from `BookSession`), `ObservedPushes(PushReceipts)` and
`FireOnceLog` (writes `firing` entries before any trigger call, records results, turns a leftover `firing` into
`fire_unknown`). F2 uses them and never makes another copy; G5's `fno/ai/fire.py` stays untouched. F2's code round
starts after they are on `main`. The routine runs
`python -m fno.analysts brief '<pointer>'`, `seal <card.json>`, `reveal` (standard library only, as `python -m fno.ai`).
The input file, the cards file and the audit files are saved by the Actions job through `DataStore`; records are
written once.

**8. Timetable (IST, `config.yaml` `analysts.timetable`, PROPOSED until S1 freezes it, like `desk.timetable`).** Cutoff
14:00; latest fire start 14:15 (a run starting later fires nothing: "late start", recorded and alerted); commitment
receipt pushed by 14:40:00; reveal from 14:40:10; reveal deadline 14:50; the day's cards file and its receipt pushed
by 14:55, before the desk's common pack at 14:58 (`desk.timetable.pack`) and the books' decision deadline 15:12. The
job is scheduled well before the cutoff and waits for it, because GitHub's schedule has started hours late (14 Oct,
response 67 addendum 5). Only days the session calendar marks as recorded sessions are run; any other day records
"not a trading day" and fires nothing.

**9. The day's cards file and the books.** The collection saves `analysts/<YYYY>/<d>_cards.json` once through
`DataStore` (receipt pushed): per role its status (`valid`, `not_applicable`, `refused`, `late`, `not_revealed`,
`no_submission`, `not_fired`, `fire_unknown`, `model_mismatch`, `exposed`), the reason, the receipt times, and the card itself only
when `valid` or `not_applicable`; the refused draft goes in the audit file beside it (`<d>_<role>_audit.json`, also
through `DataStore`). `CardsOfDay` (interface) with one adapter reading that file through the verified cache gives F1t
`cards(day) -> {role: CardStatus}`, the input file's SHA-256 and `role_set_version`. **The hand-off (agreed with F1t
and F6, 16 Oct 2026):** cards are not part of a book's answer. F1t's export gives each AI book one item,
`analyst_cards`: every registered role's status line, and the card when `valid` or `not_applicable`, the same for
Books 2 and 3. Each card carries a stable `card_id` (`<role>/v<n>/<day>`, set by code); a book's answer may cite only
those ids (F6's `cards_used`, refused otherwise by the book's own check). `role_set_version` is the registered role
versions in role order (`volatility/v1`; a later set `macro/v1+volatility/v1`), or `none` when no role is registered;
it names the registered set, never the day's availability, and goes into D6 version rows and Book 3's registry. F1t
records `consulted_units` (F9's column): the unit ids of the roles whose card was in the book's `analyst_cards` item
(given, whatever the book says it used; F9b's ablation withholds exactly that). A missing, late or refused card is a
status line, never a block: the books decide without it.

**10. F9 fit.** Each registered role is one F9 unit (`unit_id`, never a control role); F2 adds the entries to
`agents/role_units.yaml` when F1t registers the trading versions of Books 2 and 3 (D6), and a test checks that every
registered role's unit id is accepted by F9's `RoleSet`. The cards file and `consulted_units` are F9b's inputs.
F9a's declared cost split assumes roles run inside the book's session; here each role has its own session, shared by
both books, so its cost is that session's own usage. That is F9's rule to change (text agreed with F9's owner,
session_01SFDjjZx7JYziM3jqJytG2z; response 264); F2 changes no F9 code.

**11. Alerts and records (owner, 16 Oct 2026).** Every role whose day is not `valid` or `not_applicable` gets one
#fno-desk line through `AlertSender` (`FNO_SLACK_BOT_TOKEN`), naming the role, the status and the reason, never card
text. A missing input, a Drive save that fails, or a receipt push that fails is one line too, and the run ends with a
failure status. Every case is in the cards file, or, when the cards file itself cannot be saved, in the run's alert
and log, never silent.

**12. Budget and the live switch.** The firer reads BG1's month signal (`accounting/budget/<YYYY-MM>_signal.json`);
when it says `stop_ai_roles`, no role is fired ("analysts" are first in `AI_ROLE_STOP_ORDER`), recorded and alerted;
an unknown level fires as normal and says so in the fire log. The fire log keeps each session's link for F8's usage
capture. `config.yaml` `analysts.live_from` (a date or null, null on merge): before it, the job runs only with
`--dry-run` (no fire, no save, prints the input and what would be fired). Setting the date is the owner's call when
Books 2-3 trade.

**13. What a role never does (7.5).** Places or prepares an order, reads a credential (the routine has no Drive,
Slack or broker settings and receives only its pointer), sees an outcome (the card is sealed before the books decide),
edits a record (write-once store and first-publication reading; a later collection only says whether it would differ),
changes a rule, posts anywhere (alerts come from the Actions job only), names a model on a screen.

### Gap list (design requirement → criterion, or out with the reason)

| Requirement (source) | Where |
|---|---|
| Volatility analyst: chain, term structure, realised vs implied (7.2) | 2, crit. 3; skew and intraday out (not captured as summaries; added with a new version) |
| Macro and global-cues, positioning, equity research analysts (7.2) | Out of v1: added one at a time (`DESK_DESIGN.md` step 4; the F9 sample argument above), each a new registry entry, input adapters and prompt, on the owner's word |
| Writes a finding card; never decides trades (7.2) | 4, 5, crit. 4-6; crit. 13 |
| One routine prompt per role, versioned in D6's registry (7.2) | 1, crit. 1; D6 rows: F1t registers book versions naming the role versions (crit. 10) |
| Feeds Books 2-3 (7.2) | 9, crit. 9 |
| Feeds idea cards and weather drivers (7.2) | Out: v1 feeds the books only; R1 and M1 take cards later as new inputs |
| Analysts start only with the books' trading (7.2; owner 16 Oct: built now, off) | 12, crit. 12 |
| Never: orders, credentials, outcomes, editing records, rules, posting, model on a screen (7.5) | 13, crit. 13 |
| Cost allocation F8, value F9, budget stop order (7.6) | 10, 12, crit. 10, 14; F8 usage capture of role sessions out (F8 part 2's owner; the fire log keeps the links) |
| Fired from GitHub Actions, routines on the owner's plan (7.1) | 7, crit. 7 |
| Point-in-time data only (brief) | 2, crit. 2 |
| Card: role, as_of, claims with evidence pointer and label, view, confidence (brief) | 4, crit. 4-5 |
| Sealed before the decision deadline (brief) | 6, 8, crit. 7-8 |
| Fire and collect through `fno/ai`, no second mechanism (brief) | 7, crit. 15 |
| Missing or invalid card: alert and record, never blocks the books (brief; owner 16 Oct) | 9, 11, crit. 8-9 |
| Cards scored later through F9 (brief) | 10, crit. 10; scoring each card's view against outcomes: out (descriptive only, a later story if wanted) |
| Data files write-once in Drive with receipts (O9; orchestrator's answer d) | 3, 9, crit. 16; the seal files follow the AI books' git path until O9's step 4 moves both (item 6) |
| Independence between roles (design 3.3) | 6, crit. 7 (matters from the second role on; built and tested now) |
| Observation, source and time known; counter-evidence; what proves it wrong; "not applicable", never invented numbers (design 3.1) | 4-5, crit. 4-6 |
| Role matrix of every design 3.4 role (old F2 criterion 6) | Out: design v2's 7.2 table replaced it |
| T3 boundary: devil's advocate on the trade card | Out: T3's owner; F2 imports `fno/advocate/numbers.py` only, unchanged (agreed with its owner, 16 Oct) |

### Acceptance criteria

1. **Registry.** The registered role's prompt file has the registered SHA-256; `brief` refuses a changed prompt, an
   unknown role and an unknown version. Tests: good; one byte changed; unknown role; unknown version.
2. **Point-in-time inputs.** An item first seen after the cutoff is not admitted; one exactly at the cutoff is; one
   without a first-seen time is `missing` with its reason; an empty source gives `missing`, not an empty item. A
   role's input holds only the kinds its registry entry lists (a planted item of another kind is refused). Tests per
   adapter with fixture files: before, at and one second after the cutoff, and empty.
3. **Input content.** Each v1 item's lines are computed by code and checked by hand on a fixture (RV20, VIX percentile,
   ATM IV percentile, the previous pack's fields); no raw quote row appears in the input.
4. **Card validator.** Each of the nine rules of item 5 refuses a card breaking only that rule and passes the same card
   without the break (one test per rule, plus boundaries: 5 and 6 claims, 40 and 41 words, `40%` against `4`, horizon
   1, 20, 0 and 21).
5. **Not applicable.** A `not_applicable` card with empty claims and `no_view` is valid; with any claim or view it is
   refused.
6. **Labels fixed by code.** A draft cannot set `role`, `day`, `as_of`, `version`, `input_sha256` or `card_id`; a reveal whose
   labels differ from the pointer and input is refused at collection.
7. **Sealing and independence.** A card counts only when its commitment was visible on `main` at the commitment
   deadline's observation, its reveal by the reveal deadline's, and the reveal hashes to the commitment; no reveal is
   pushed before the reveal time; a commitment pushed after another role's reveal was readable is `exposed`. Tests with fake
   receipts at, before and one second after each deadline, and an unknown receipt time (late).
8. **Every failure is recorded and alerted.** Not fired (unconfigured trigger, fire refused, late start, budget stop),
   fire outcome unknown (a leftover `firing` entry),
   no submission, late, not revealed, refused (with the rule), model mismatch, exposed: each gives one status in the
   cards file and one #fno-desk line (fake sender) without card text. A missing input, a failed Drive save, a failed
   receipt push and an input over the pointer cap each give one line and a failure exit.
9. **Never blocks the books.** `CardsOfDay` returns every registered role's status even when no card exists or the
   cards file is missing, fails its receipt check, or cannot be read within 30 seconds (`no_submission` with the
   reason, and one #fno-desk line through the alert sender it is given: the caller's, e.g. O1's one `ReportedAlerts`,
   never one it builds), and never raises for a missing card. Its `card_id`s are unique and stable (same file, same ids), and `role_set_version` is `none` with an empty
   registry and `volatility/v1` with the v1 registry (tests).
10. **F9 fit.** Every registered role's `unit_id` is accepted by F9's `RoleSet.of` and is not a control role (test
    against the imported F9 code).
11. **Only registered roles fire.** A role not in the registry is never fired and a pointer naming one is refused.
12. **Live switch.** With `analysts.live_from` null or after the day, a run fires nothing and saves nothing (only
    `--dry-run` output); from the date on, it fires. A malformed key is refused at config load.
13. **Never-do rules.** The pointer carries no secret (O5 scan on a real pointer); the routine side of `fno/analysts`
    imports no Slack, Drive, Groww or order code (import test); records are write-once (a second collection that differs
    says so and saves nothing).
14. **Budget.** A month signal with `stop_ai_roles: true` fires no role and records `not_fired: budget stop`; an unknown
    or missing signal fires and says so in the fire log.
15. **One mechanism.** No second trigger, seal, receipt, submission or model-check code: `fno/analysts` imports them
    from `fno/ai` (test); G5's existing forecast tests pass unedited after any extraction.
16. **O9.** The input, cards and audit files are saved only through `DataStore` (one receipt each, matching SHA-256);
    a planted changed file in the cache is refused with an alert; the only analyst files in the repository are those
    receipts and the seal files of item 6 (the AI books' own exception until O9's step 4).
17. **Not a trading day / late start.** A closed day records "not a trading day" and fires nothing; a run that starts
    after the latest fire start fires nothing and alerts once.
18. **End to end (fake AI).** One test runs a whole day with a fake Drive, fake triggers and fake routine answers (a
    valid card, a not-applicable card, a refused card, a late one, across test-only roles) from input to cards file and
    alert lines; the real-data dry run (`--dry-run` on the latest session) is recorded in the claims file.

**Test plan:** unit tests per adapter, rule and status; the day-long test of criterion 18 with fakes; for each
criterion the builder breaks its code on purpose and shows the test failing (quality rule 4); positive, negative,
boundary and empty cases as listed per criterion (rule 5). Real output sample: one dry-run input and one fake-answer
cards file, labelled as made by a test or a dry run (rule 6).

**Judge verifies:** plants mutations in the validator, the cutoff rule, the deadlines and the status writer; reads a
dry-run input and checks each item against its source and first-seen time; confirms nothing is fired while
`live_from` is null and that G5's tests are unedited.

**Depends:** F1 (forecast part, merged), F1t's `SealedPublisher`, `ObservedPushes` and `FireOnceLog` (on `main` before
F2's code round), O9 parts 1 (`DataStore`, verified cache), A15, G2, BG1; F1t reads the cards
file · **Size:** M (one role) · **Status:** story text rewritten to design v2 (16 Oct 2026), revised for the
orchestrator's answers (response 264); waiting for the judge's text check; code after its PASS

---

## F3. Red team

**Repository:** trading

**Description:** As the owner, I want a red team on a different model from the author attacking every Book-2 and
Book-3 decision and every research thesis, so that luck, flattering periods and disaster cases are found before money
is at risk.

**Context and why:** Design 7 (a different model from the author; attacks every thesis), 12.3 (for Book 3 objections
are recorded evidence, not hard blocks). The red team cannot block a trade; only the judge and risk can.

**Scope.** In: attacks on daily AI decisions (inside the deadline) and on research theses (in the research loop).
Out: blocking (F4, C2, C4).

**Expected design:** `fno/ai/red_team.py`; runs as its own session (F1 pattern) on a model different from the book's
registered author model, reading the book's decision draft and cards; output: objections, each with the test or data
check that would settle it, status `open` or `resolved` (with evidence), the red team's model and the author's model.
Daily objections are committed with the decision; research objections in the research folder.

**Acceptance criteria:**
1. A red team model equal to the author's model makes the run fail and is reported.
2. Every objection names a test or data check; open objections stay visible to the judge, the dashboard and the
   monthly report, never silently dropped.
3. A red team that misses the deadline leaves the decision without objections and records "red team unavailable";
   it never delays the deadline.

**Test plan:** orchestration tests with fakes.

**Judge verifies:** confirms objections were answered or recorded as open.

**Depends:** F1, F2 · **Size:** M · **Status:** later

---

## F4. AI judge (parts 2 and 3) and the monthly audit

**Repository:** trading

**Description:** As the owner, I want research sufficiency and interpretation checked by a model different from the
author and the judge itself audited monthly, so that the judge stays honest. I never override a paper decision
(owner, 16 Oct 2026, DESK_DECISIONS "D4/D5: the five design questions accepted as recommended" item 4).

**Context and why:** Design 7: three checks (hard validity is code, C4); the judge can block anything; fail = no trade
or back to the author; no one overrules hard validity or a judge verdict on a paper decision (DESK_DECISIONS "D4/D5: the
five design questions accepted as recommended" item 4; design v2 03 leaves the owner only S1's safety stop; C2's written
restart of a stopped book's drawdown brake is a risk control, not a decision override; both stay, outside this story);
monthly audit of a stratified sample plus seeded known-answer cases. Per book: Book 2's judge failure means no trade
(the account keeps no position; the rule default is recorded as a shadow); Book 3's judge verdicts are recorded
evidence, not blocks (12.3); Book 1's strategies were judged at approval and its daily trades are checked by C4 only.

**Scope.** In: verdicts for Book-2 and Book-3 decisions inside the deadline and for research theses; the audit. Out:
hard validity (C4); owner overrides (none on paper: D3 refuses a non-empty `owner_override` in every book).

**Expected design:** `fno/ai/judge.py` as its own session (different model from the author); verdict JSON `check
(sufficiency | interpretation), pass, reasons, what_to_redo, model`. No override path: a judge verdict stands, and
D3's record keeps `owner_override` null. (`journal/<book>/owner_overrides.csv` is C2's file for the owner's written
brake restart, not a judge override.) Monthly audit command `python -m fno judge audit <month>`: 20% of approvals, 20%
of rejections, 20% of abstentions (at least 5 of each when available), re-checked by the other model against
recalculated evidence; plus 10 seeded known-answer cases. A failed audit (any false approval on a seeded case, or a
false-approval rate above 10%) suspends the AI judge's approvals: Book 2 then takes no new AI-chosen trades until fixed.

**Acceptance criteria:**
1. A judge model equal to the author's model is refused.
2. A Book-2 decision failing the judge opens no trade; the same failure on Book 3 is recorded and does not block.
3. There is no override of a judge verdict or a C4 failure on any paper decision: a record with a non-empty
   `owner_override` is refused (D3), and nothing in F4 writes one.
4. The audit reports false approvals and false rejections on the seeded cases; a failed audit suspends approvals
   (test).
5. A judge missing the deadline counts as a failed check for Book 2 (no trade) and "judge unavailable" for Book 3.

**Test plan:** tests with fake verdicts and seeded cases.

**Judge verifies:** (by the other model) the monthly audit numbers.

**Depends:** C4, F1, F2 · **Size:** M · **Status:** later

---

## F5. Book 2: AI decisions inside the envelope

Rewritten to design v2 in `docs/stories/F5-book2.md` (16 Oct 2026), which replaces the text that stood here: Book 2's
day sheet in its private pack, the answer shape, and the decider writing one D3 run with C2 and C4 inside.

---

## F6. Book 3: the fully AI system and its pilot

**Repository:** trading

**Description:** As the owner, I want Book 3 to invent its own registered strategies and decide daily under its
constitution, starting as a labelled pilot, so that we learn whether a complete AI system makes more net money under
the same risk budget.

**Context and why:** Design 12.1 (Book 3 answers a whole-system question; a Book-3 win is never claimed as "AI daily
judgement beats rules" unless scoreboard A shows it), 12.3 (constitution, strategy identity), 12.6 (common start;
earlier trades are pilot evidence), 12.11 (Book 3 starts as a pilot once its constitution, decision records, fills
and costs, C2 and C4 Book-3 mode, role agents and the forecast protocol exist). Book 3's strategies cannot be tested
on history (a model knows what happened later).

**Scope.** In: Book 3's decider, strategy proposal and registration flow, pilot labelling. Out: the constitution
itself (D5), matched shadows (F7).

**Expected design:** inside Book 3's session (F1): read the packs and cards; to use a new strategy, write its full
spec, which code registers (D5) **in a commit before the decision commit**; a strategy proposed today can be traded
at the earliest at the next session (registration precedes its first trade by at least one day, so no same-day
invent-and-trade, design 4). Decision record with `strategy_id` and spec hash; C2 and C4 (constitution mode). Every
Book-3 record before the common-start date (S1) is labelled `pilot`.

**Acceptance criteria:**
1. A Book-3 trade with an unregistered or same-day-registered strategy is blocked.
2. A strategy spec breaking the constitution (naked short, horizon over 3 weeks, non-NIFTY) is refused at
   registration.
3. Records before the common start are labelled `pilot` and excluded from head-to-head scoring (S2, S3) but kept and
   reported.
4. Red-team and judge objections are attached as evidence and never block a Book-3 trade; C2 and C4 do block.

**Test plan:** tests with fake sessions: new strategy, reused strategy, refused spec, pilot labelling.

**Judge verifies:** checks registration commits precede first trades for every Book-3 strategy in a month.

**Depends:** C2, C4, D5, D6, F1, F2, F3, F4, G1 · **Size:** L · **Status:** later

---

## F7. Matched shadow decisions for scoreboard A

**Repository:** trading

**Description:** As the statistician, I want Book 3 to commit, every day, a shadow decision on the common opportunity
set, so that all three books appear on scoreboard A, judged on the same opportunities.

**Context and why:** Design 12.5: scoreboard A compares decisions on the same eligible opportunities, same approved
strategy universe, same cutoff, fill model and costs, each committed independently and scored on a standardised
shadow account; books 1 and 2 meet this naturally; Book 3 also commits a matched shadow decision on the common
opportunity set every day. Owner requirement: all three books on both scoreboards.

**Scope.** In: Book 3's shadow decision on each common opportunity (take or skip, and the choice among the approved
strategies' permitted variants), committed with its real decision. Out: scoring (S3).

**Expected design:** the common opportunity set from E2; Book 3's session writes `shadow_decisions.json` (one entry per
opportunity, same action vocabulary as Book 2's envelope, without envelope limits) committed with its real decision
before the deadline; validated by code; missing entries count as "no decision" for scoreboard A.

**Acceptance criteria:**
1. Every common opportunity of the day has a Book-3 shadow entry or a recorded "no decision".
2. Shadow entries committed after the deadline are ignored.
3. Shadow entries never affect Book 3's real account.

**Test plan:** validation tests with fixture opportunity sets.

**Judge verifies:** compares a day's shadow file with that day's common opportunity set.

**Depends:** E2, F6 · **Size:** S · **Status:** later

---

## F8. AI usage and cost attribution

**Repository:** trading

**Description:** As the tax and cost accountant, I want each AI book's and role's usage measured and the owner's plan
cost allocated by a frozen formula, shown apart from any actual cash spend, so that AI costs count against profit
honestly.

**Context and why:** Design 8.1 (three ledgers; each AI role must earn more than it costs), 13.6 (three labelled
figures, never merged: actual cash spend, allocated plan cost "not a bill", incremental value from F9). Cloud routines
draw on the owner's Claude plan, not per-call billing (13.5). C1 already has `accounting/operating_costs.csv`.

**Scope.** In: usage capture per session (duration, sessions, tokens where available), the allocation formula, ledger
entries per book. Out: deciding to keep a role (F9, owner).

**Expected design:** `fno/ai/usage.py` reads each AI session's usage (`get_session`, `list_events`) into
`accounting/ai_usage.csv` (`date, book, role_or_bundle, session_id, model, minutes, tokens_if_available`); the owner
records the monthly plan cost (rupees) in `accounting/operating_costs.csv`; the allocation formula (frozen in S1) splits
it by measured usage; C1's account ledger shows allocated cost per book labelled "allocated, not a bill" and actual
cash spend separately.

**Acceptance criteria:**
1. Allocated costs for a month sum exactly to the recorded plan cost (test).
2. Allocated cost and cash spend are separate fields everywhere (ledger, scoreboards, dashboard).
3. A month without a recorded plan cost is flagged and allocated cost shown as unknown, never zero.

**Test plan:** unit tests on aggregation and allocation.

**Judge verifies:** recomputes one month's allocation.

**Depends:** C1, F1 · **Size:** S · **Status:** split (design v2, 15 Oct 2026): the minimal part below is done (judge 104, merged 757c20d); **F8 part
2, later**, keeps the per-book lines in C1's account ledger, the scoreboards' and dashboard's separate fields (criterion 2)
and filling S2's `AiCostAllocation` port (judge 87: "latent until F8 fills the port"), once books 2 and 3 trade

### F8 minimal (design v2 slice A, 15 Oct 2026; built with BG1, response 104)

**History:** the text above is F8 as first written (later slice). Design v2 (`docs/design_v2/REPLAN.md` row F8: "keep,
**move earlier** (slice A)... The budget cap (BG1) needs it, and S1's freeze needs its code") moved a minimal F8 into
slice A, built together with BG1 (`docs/stories/BG-budget.md`). Revised after judge 104 (FAIL on eddd035).

**Facts checked on 15 Oct 2026 (builder and judge B, response 104 and judge 104), the base of this design:**
- A cloud session's `result` events (`list_events`, kind `result`) carry per turn `duration_ms` (wall time),
  `num_turns` and `usage` (`input_tokens`, `output_tokens`, `cache_read_input_tokens`,
  `cache_creation_input_tokens`) of the main loop; `get_session` gives the id and `configured_model`. Nothing else is
  read and nothing is estimated.
- **Page envelope (judge 104):** a page with older events carries `has_more: true`; the last page omits `has_more`
  (and, when empty, `data`).
- `cse_<id>` and `session_<id>` name the same session (judge 104, checked on the judge's own id).
- The session tools exist only inside a Claude session; GitHub Actions has no such API.
- **The AI books' routine sessions cannot be read from other sessions** ("not found"), and `list_sessions` omits
  trigger-fired runs.
- **A routine cannot read its own run's usage at its end:** a `result` event is written when a turn ends, and a fired
  routine runs one turn (reasoning only, from the event model; to be confirmed on the first run). So the owner's "5 A"
  (15 Oct: "the routine records its own usage at the end of each run") is met by the routine timing its own run.
- `duration_api_ms` can exceed `duration_ms` (parallel calls), and `modelUsage` includes side calls: minutes are wall
  minutes of turns, tokens are main-loop tokens, both labelled.

**Scope.** In:
- `SessionUsageReader` (interface) with two readers:
  - `ExportFileUsageReader`: a Claude session saves, into one JSON file outside the repository, `captured_at` (with its
    zone), `get_session`, and every page of `list_events(kinds=["result"])` newest first, each with the `before_id`
    cursor it was read with; only numbers are taken (never message text), one row per session per IST day;
  - `SelfTimedUsageReader` (owner's "5 A"): a routine's own record of its run (`session_id` from `get_session` with no
    id, `model`, `started_at`, `ended_at`): its wall minutes on the IST day it ended, tokens unknown;
- `accounting/ai_usage.csv`, written once per (session, day): `date, purpose, book, role_or_bundle, session_id, model,
  minutes, turns, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, tokens_basis, source,
  captured_at`. `purpose` is `books_and_roles` (counts against the cap), `development` (builders, orchestrator,
  judges) or `data_routines` (code jobs a Claude routine runs, such as the 3 pm and 15-minute recorders, whose host the
  owner chose on 15 Oct 2026 with "cost measured by F8"; never against the AI cap);
- `accounting/ai_session_roster.csv`: the development sessions, from a chained `list_sessions(mine=true)` export
  (ids and times only), so a session never captured is known (judge 104 must-fix 3);
- the allocation, S1's decided `ai_cost_allocation` (14 Oct 2026): the month's plan cost from
  `accounting/operating_costs.csv` (item `Claude subscription`) x minutes / all minutes, to the paisa, the remainder to
  the largest share (ties: first in name order); development shown as "development, not a book cost"; "allocated,
  not a bill"; a warning when book shares are over- or understated by missing sessions;
- the owner's plan cost, INR 20,000 a month (owner, 15 Oct 2026): recorded for October 2026 citing its row, and held as
  one config value citing it (`budget.plan_cost`), applied to every month from October 2026 (`plan_cost.py`);
- `python -m fno budget record-usage [--self-timed] | record-roster`, refusing an export inside the repository.
Out: reading sessions itself (Python cannot call the session tools), changing the books' routine prompt to write the
timing record (a new registered book version, F1/G5: the orchestrator's call), and F8 part 2 (above).

**Acceptance criteria:**
1. Allocated costs for a month sum exactly (to the paisa) to the recorded plan cost, the remainder going to the largest
   share with the stated tie-break (tests pin which share gets it); a negative plan cost is refused.
2. Allocated cost and cash spend are separate fields everywhere this story writes them (meter lines, signal data);
   development's part reads "development, not a book cost".
3. A month without a recorded plan cost is flagged and every allocated cost shows "unknown", never zero (test).
4. Export rows come only from the session's own figures: minutes = sum of `duration_ms` of that IST day's `result`
   events (a turn counts on the day its result was written); tokens = sums of their `usage`, blank when any event of
   the day lacks them; no message text is kept. Self-timed rows: end minus start, tokens unknown (tests).
5. An export that could under-count is refused, never read as less: a page not read with the newer page's `first_id`,
   a page after one without `has_more: true`, a last page with `has_more: true`, an event without a `uuid`, a duration
   that is not a number of 0 or more, a time without a zone, or no result events at all. A real envelope (last page
   without `has_more`) is accepted (tests).
6. A (session, day) in the ledger is never rewritten; only the `session_<id>` form is accepted; only days the reader
   calls complete are recorded (an export: before both today and its capture day; a self-timed run: its end day); each
   row keeps when it was read; a damaged ledger is refused; the file is replaced whole (tests).
7. Coverage is shown: each fired AI book session before today with no usage row counts as "not captured"; each
   development session active in the month counts as captured only with a reading taken after its last activity (or
   after the last complete day), and only when a roster was read after that day; a fire log or roster of another shape
   is refused (tests).

**Test plan:** unit tests with the real field names and page envelope of 15 Oct, constructed rosters, the ledger, the
allocation (uneven, tie, no cost, no usage), the coverage, and the CLI refusals.

**Judge verifies:** recomputes one month's allocation by hand from the two CSV files; feeds a real export, one with a
missing middle page and one taken mid-day; checks no text field reaches a ledger.

**Depends:** C1, F1, S1 (`ai_cost_allocation`) · **Size:** S · **Status:** done: judge 104 addendum 3 PASS
(4fcea00), merged 757c20d (addendum 4)

---

## F9. Role-value evaluation (does each AI role earn its cost?)

**Repository:** trading

**Description:** As the portfolio manager, I want each AI role or role bundle evaluated by a fixed, paired comparison
with and without it, so that a role is kept only if it adds measurable net value after its allocated cost.

**Context and why:** Design 3.1 (paired shadow decisions with and without a role; abstentions count), 10 (roles added
one at a time, kept only if they add net value), 13.6 (ablation where safe; inseparable roles evaluated as a bundle;
keep or drop only at predeclared review dates; control roles scored on prevented invalid actions, not profit).
ChatGPT review 24: allocated cost alone cannot prove value. REPLAN (`docs/design_v2/REPLAN.md`, slice B): S1 v1 is
frozen only once F9's code exists (owner's option A, 14 Oct 2026), so F9's **scoring code** is built now and
**reports only once books 2-3 trade** (slice E). Response 166 holds the claims, the answers to judge 172 and the owner
questions.

**Two parts.**
- **F9a (now, slice B): the scoring code S1 hashes.** The rotation, the record checks, the per-unit score, the
  interval and Holm, the review gate, the control-role counts and the report, all on records. No AI session, no shadow
  firing.
- **F9b (slice E, with F1's trading part and F2):** the book's session produces the shadow decision with the unit's
  card withheld and writes the rows F9a reads. Its story text is written when slice E starts.

**Scope (F9a).** In: `fno/role_value/` (new package, its own composition root `fno/role_value/wiring.py`) and
`fno/evaluation/review_dates.py`:
- **Units.** `RoleSet`: a book version's registered AI roles and declared bundles (D6's registry entry; F2's
  `agents/roles.yaml`), each unit with an identifier. A role inside a declared bundle is never a unit on its own.
  Mandatory control roles (C1, C2, C3, C4, the CUSUM and stop-rule meters) are never a unit.
- **Rotation** (S1 `role_value_schedule`). For books 2 and 3, from the common start (or a new version's first day), the
  k-th day the book commits a real decision (k from 0) ablates unit `k mod n` of that version's n units, in identifier
  order. A no-trade decision is a real decision and advances the cycle. A day without a committed decision ("AI
  unavailable", late, missed) has no row and does not advance it.
- **Rows.** `PairedDecisionSource` (interface), one adapter reading `journal/<book>/role_value/paired.csv`, one row per
  day the book committed its real decision: `day, book, version, unit, consulted, real_decision_id,
  shadow_decision_id, real_packs_sha256, shadow_packs_sha256, real_snapshot_id, shadow_snapshot_id, status`
  (`scored`, `shadow_unavailable`, `unscored`).
- **Checks on each row** (refused with the day and the unit): packs hashes differ; the two snapshot ids differ, or
  differ from the day's execution snapshot in E3's committed run log (read through S3's
  `fno/scoreboard/committed_runs.py` `CommittedRuns.snapshot_ids`, imported, not copied); the unit is not the one the
  rotation schedules; the unit is a role inside a bundle.
- **Valuation.** Each action, real and shadow, is valued by **importing S3's standard unit**
  (`fno/scoreboard/standard_unit.py`: one lot, E4 touch fills at the day's execution snapshot, C1 charges, the
  version's time exit, E7 settlement), never re-implemented or changed here (orchestrator, 15 Oct 2026). Its outcomes
  carry over: a no-trade (skip) and a "not filled" entry are 0; a pair where either action is still open is cut from
  the score and listed until both close.
- **Score per unit** over a period: applicable opportunities (scored rows where the unit's card was consulted),
  changed opportunities (the real and shadow decisions differ, including a trade against a no-trade either way),
  paired differences (with the unit minus without it, in rupees, unchanged opportunities 0), cost per opportunity (next
  item) and the net value per opportunity (difference minus cost).
- **Cost per opportunity: a declared split** (judge 172 blocking 1). A unit runs as a sub-agent inside the book's one
  session, and F8 writes one usage row per (session, day), so no unit has minutes of its own. The rule: the book's
  allocated cost for a day is F8's month allocation of the book's `books_and_roles` shares times that day's minutes of
  those shares over their month's minutes (F8's `allocate` and its ledger rows, imported, not copied); it is split
  equally across the units whose cards were consulted that day, rounded down to the paisa, the paise left going to the
  first unit in identifier order (F8's rounding rule). **Each scored opportunity is charged its own day's portion**
  (ChatGPT review 124 Q1): its net value is its paired difference minus that portion, so the cost covers the same
  dates as the tested net. The mean of the unit's portions over every day its card was consulted is printed apart as
  "operating cost, all consulted days" and never enters the test. The book's decider gets no portion, so each unit's
  cost is an upper bound: labelled "conservative cost allocation (declared split, upper bound; allocated, not a
  bill)". A scored date with no usage row, or in a month with no recorded plan cost, makes the unit's cost and net
  value "unknown", and it gets no verdict; an unknown day that was not scored only makes the operating cost
  unknown.
- **Interval and test.** The series is the unit's net values per applicable opportunity in date order. S3's moving-block
  resampler (`fno/scoreboard/uncertainty.py`, revision 2: the resampler and its one-sided p-value reader, imported) runs
  on it with a risk column of 1 (the mean), blocks of 20 opportunities, 10,000 resamples, seed 20261014. The printed
  interval is the nearest-rank 5th and 95th percentiles. It is shown only; the verdict comes from Holm.
- **Holm** (owner, 15 Oct 2026, via the orchestrator; S3 revision 2's definition and code). At a review, **every unit
  of the registered role set** contributes two one-sided claims: "earns its cost" (p = the reader on the series: the
  share of resampled means at or below 0) and "drop" (p = the reader on the negated series). A unit without a known
  cost or 30 changed opportunities stays in the family with p = 1. The family is therefore fixed at 2m claims for the
  book's m registered units: one unit becoming testable never moves another's threshold (the flaw ChatGPT review 120
  found in S3; response 237). The 2m claims go into S3's Holm step-down at 0.05/(2m − i + 1), as one plain list. At most one claim per unit can pass. For a single unit this is about as strict as a two-sided 5% test,
  stricter than S1's "one-sided 95%" (response 166, question 7).
- **Verdict** (S1 `role_value_minimum_sample`; profit only): `drop proposed` (its drop claim passes Holm; a proposal the
  owner can overrule), `earns its cost` (its
  earns claim passes) or `inconclusive, stays`. It is produced only with `--review` on a review date and with at least
  30 changed opportunities. Otherwise `no verdict: <reason>` (not a review date, `<m> of 30 changed opportunities`, cost
  unknown).
- **Risk shown, never deciding** (owner, 15 Oct 2026: "money only, risk shown"). Beside each unit's verdict the report
  prints two risk effects: the worst calendar month of the paired differences (the lowest monthly sum, with the unit
  minus without it), and the mean difference in one-lot maximum loss at entry over changed opportunities (the same
  maximum loss scoreboard A computes from the one-lot entry fills, taken from S3's code, imported, not copied). Neither
  enters Holm or the verdict. A risk-adjusted rule could only come as a new S1 item before the freeze.
- **Review dates.** S1's `review_dates` rule has no code today. F9a adds one pure function, `review_dates(common_start,
  calendar, through)`: the last NSE session of the sixth full calendar month after the common start, then every 3
  calendar months on that month's last session. The NSE calendar is `fno/research_data/calendar.py`'s
  `SessionCalendar`. The common start is an input (`--common-start`) until S1 fixes it in its record. It lives in
  `fno/evaluation/review_dates.py` (S1's package, hashed with S1; S1's text owner agreed, 15 Oct 2026), built by F9a.
  It codes only the scheduled-review rule of S1's current `review_dates` item, not the weekly post-mortem or the
  stop-rule review that REPLAN section 4 adds.
- **Control roles.** From C4's failure log (`journal/<book>/validity_failures.csv`), per book and period: caught
  violations (failed-check rows) and prevented invalid actions (distinct `(day, opportunity_id)`), never a profit
  figure.
- **Report.** `python -m fno role-value report --book <2|3> --from <date> --to <date> --common-start <date>
  [--review]`: a Markdown report, one row per unit (applicable, changed, mean difference, cost on scored dates, net
  value, interval, Holm p-values, verdict or reason, risk effects, operating cost), each block's calendar span and the
  observations per month, the open pairs (count and age) and excluded rows listed, every figure labelled with its
  protocol version (S1 `reporting_per_version`).

**Design requirements, where each goes (quality rule 2; judge 172 blocking 2):**

| Requirement (source) | In F9a | Or out, with the reason |
|---|---|---|
| Paired with and without the role, same packs and snapshot (design 3.1; 13.6) | criteria 1, 8 | |
| Net after the role's own running cost (3.1) | criteria 3, 5 (declared split) | |
| Abstentions and rejected trades count (3.1) | criterion 9: a no-trade is valued 0 and counts as a change | |
| Only opportunities where the role applies (3.1) | `consulted`, criterion 3 | |
| Joint tests where roles interact (3.1) | declared bundles only, criterion 2 | Pairwise ablations of two separate roles: out. They need a second shadow a day (twice the extra usage) and a sample already years long. Roles expected to interact are declared as one bundle in the version (F2's matrix) |
| Lower risk can justify lower profit (3.1) | criterion 12: risk effects printed beside the verdict | Out of the verdict (owner, 15 Oct 2026: "money only, risk shown"); a risk-adjusted rule only as a new S1 item before the freeze |
| Roles added one at a time (design 10; DESK_DESIGN step 4) | | Out: a rollout order for slice E (F2, F5, F6), not scoring. Each added role is a new version (D6) with its own rotation and record |
| Inseparable roles as a bundle (13.6) | criterion 2 | |
| Keep or drop only at predeclared review dates; owner decides (13.6) | criterion 4 | Automatic removal: out (owner decides) |
| Control roles on prevented invalid actions (3.1; 13.6) | criterion 6 | C3 refusals: Known limits |
| Results per protocol version (S1) | report labels | |

Out: firing the shadow session and withholding the card (F9b); any change to S3's `standard_unit.py`,
`uncertainty.py` or `committed_runs.py` (through the orchestrator to S3's builder); adding F9a's files to S1's
`frozen_files` (S1's text owner, register row "S1 text"); removing a role (the owner decides at a review).

**Acceptance criteria:**
1. A row is refused, with its day and unit, when: its real and shadow packs hashes differ; its two snapshot ids differ
   or differ from the run log's execution snapshot for the day; or its unit is not the one the rotation schedules (a
   no-trade day advances the cycle; a day without a row does not) (tests).
2. A role that belongs to a declared bundle is never a unit: a row naming it is refused, and the report has no row for
   it (test).
3. On constructed records with a known answer (changed count, mean difference, daily cost portions, cost per
   opportunity, net value), the report reproduces the hand computation to the paisa. The interval and the p-values
   with the fixed seed are pinned by a test on a fixed short series.
4. No verdict appears without `--review`, on a date that is not a review date, or below 30 changed opportunities; the
   reason is printed instead (tests on the day before and the day of a review, with 29 and 30). `review_dates` is
   tested on a constructed calendar, including a month whose last calendar day is a holiday.
5. A unit with a scored date that has no usage row, or is in a month with no recorded plan cost, shows cost and net
   value "unknown" and gets no verdict; it stays in the Holm family with p = 1, so it never loosens another unit's
   threshold (tests). An unknown day that was not scored leaves the
   verdict possible and only the operating cost unknown (test). Each scored opportunity's net value uses its own
   date's portion: on scored dates of different cost, each net value and the exact series given to the resampler
   are checked (test). The daily split sums exactly to the book's daily allocation (test).
6. Control roles show caught violations and prevented invalid actions from C4's log, and no profit figure (test).
7. Holm: the family is every registered unit's two claims, an untestable unit at p = 1; an ineligible unit becoming
   eligible leaves every other unit's verdict unchanged (test with a mutation check). On constructed p-values the
   claims that pass match a hand computation of the step-down over the 2m claims,
   and the verdict follows the passing claim, not the printed interval (test). The function used is S3's (a test
   asserts the import is `fno.scoreboard.uncertainty`'s, not a copy).
8. Both actions of a pair are valued by `fno/scoreboard/standard_unit.py` (a test asserts it is that function), on the
   row's snapshot; an open action cuts the pair and lists it (test).
9. A no-trade on either side is valued 0: a real trade against a shadow no-trade, and the reverse, count as changed
   and enter the difference with their signs (tests).
10. Rows with status `shadow_unavailable` or `unscored` are excluded from the score and counted apart (test).
11. The constants (block 20 opportunities, 10,000 resamples, seed 20261014, minimum 30, printed percentiles 5 and 95,
    the cost denominator) match S1's text. A test reads both, so an edit of one alone fails. These values enter S1's
    text through its owner (register row "S1 text", pending edit 3) before F9a's code round. Until then they are
    provisional, to be confirmed at the S1 freeze.

**Test plan:** unit tests with constructed role sets, paired rows, run logs, a C4 log, F8 usage rows and a calendar;
the CLI on a temporary journal; a known-answer example worked by hand in the test file's docstring.

**Judge verifies:** recomputes one unit's changed count, the two one-lot nets of one pair (through the standard unit),
the mean difference, the daily cost portions, the Holm step and the verdict from the constructed records by hand.
Feeds a row with a wrong snapshot id, one naming a bundled role, and a consulted day with no usage row.

**Known limits (owner's simplicity rule, 15 Oct 2026):**
- Until books 2-3 trade there are no rows: the report prints "no paired decisions yet" (some months at least).
- **No "earns its cost" or "drop" verdict is shown as evidence until F9b's end-to-end card-withholding test passes**
  (review 124, Q4): every verdict is labelled provisional until then. Open pairs are reported with their count and
  age, never scored as 0.
- With n units each is ablated once every n trading days, so 30 changed opportunities can take years. Every report
  says so.
- F9a trusts the rows' packs hashes. That the shadow really withheld the card is F9b's end-to-end test.
- The declared cost split charges the whole book session to its consulted units (the decider is not charged), so each
  unit's cost is an upper bound. Measured per-sub-agent minutes (F9b) can replace it, as a new protocol version.
- On ablation days the shadow decision runs inside the same book session, so its usage is part of that day's cost and
  cannot be shown apart (response 166, question 3, revised).
- C3's data-check refusals are not counted (C3 alerts but keeps no per-book refusal log). C2's limits are counted
  through the C4 checks that enforce them.

**Depends:** F8, S1 (text, with F9a's pending edits), S3's `standard_unit.py`, `uncertainty.py` (revision 2) and
`committed_runs.py` merged (the code round starts after them) · F9b: F1, F2, E4 · **Size:** M (F9a S) · **Status:**
F9a story text revised after judge 172 on `story/f9-role-value` (response 166); F9b later
