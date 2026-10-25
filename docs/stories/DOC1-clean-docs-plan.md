# Story DOC1: one clean, current set of documents (plan, for two judges and the owner)

**Lane:** 1 (it rewrites rule documents and the documents every routine and judge reads; DESK_DECISIONS
"Rule-document guard"). **Builder and orchestrator:** session_01Mt6dcBU5kp2htdPN2KmiZH. **Status:** plan only; nothing
is moved or deleted until two judges pass this plan and the owner approves it.

## 1. Why (owner, 25 Oct 2026)

> "I want a clean documentation on main branch ... Either merge them together, but first they analyze what is correct
> and what is not ... Nobody can keep track of daily summary, and sometimes certain decisions happen on a specific day
> and later on they get upgraded and changed ... Different agents read different documents, and then according to
> their which document they read, they make wrong decisions."

Evidence that the problem is real (strong evidence, counted on main 25 Oct):
- 1,296 Markdown files. `docs/` alone holds 108 files and 44,865 lines; 23 of them are over 500 lines (33 over
  350), the largest 5,057 (`docs/HANDOVER_2026-10-16.md`). `docs/stories/` has 75 files, 21 over 500 lines. Across the
  repository 37 Markdown files are over 500 lines.
- The same subject lives in several places that disagree. Book 2: `DESK_DESIGN.md` section 12 (AI inside an envelope
  around Book 1's strategies) against the owner's 13 Oct words in `DESK_DECISIONS.md` line 29 ("the AI team analyses
  and researches inside rule-based limits"), recorded as "already matches" without a check.
- The market school (`reviews/claude/response_325`) replaced the three-book plan, yet `IMPLEMENTATION_PLAN.md`,
  `BUILD_MAP.md` and `DESK_DESIGN.md` still describe the old plan, and an audit on 25 Oct read Book 1 as the old desk.
- Statuses are stale: `IMPLEMENTATION_PLAN.md` (16 Oct) lists built stories (B2, B3, O1, F5) as "later";
  `DATA_USE_MAP.md` and `research/LEDGER.md` lag the code.

Root cause: decisions are recorded by date (daily logs, handovers, a decisions table, responses), not by subject, and
superseded text is never removed. Judges check code against a story, never a story against the owner's intent.

## 2. Target: what main holds when DOC1 is done

Principles (owner, 25 Oct 2026: "let us make our documentation review strong like we have for code ... We do not
care much about the structural issues as long as the functionality and the functional documentation is correct ...
no document is more than 500 lines ... each concrete document is responsible for a specific type of functionality,
and other documents simply a reference to that document"):
1. **One functionality, one owning document.** Each functionality (for example Book 1's daily decision, the school's
   safety laws, the real-money gate) is described in exactly one document, which says what is true now. Every other
   document that mentions it gives one line and a link to the owner document, never a second description. History is
   git.
2. **No document over 500 lines**; a test enforces it. Functional documents are grouped by category (the folders below).
3. **Functional correctness first.** Judges check that each functional statement is true (against the owner's intent
   and the code), that no functionality has two owner documents, and that every reference points to the owner. Layout
   and style findings are minors only.
4. **Document changes are judged like code** (from now on, not only in DOC1): a change to a functional document needs a
   judge PASS before main, in the lane of the functionality it describes; a functional document's lane is never lower
   than its code's.
5. **The owner's intent is written down per area and approved by the owner**, with the owner's exact words and dates.
   Every design and story must cite the intent line it serves; judges check the story against it.
6. **Update in place; never a new dated summary.** A decision that changes replaces the old line in its subject
   document. No handovers, no daily summaries as a source of truth.
7. **One entry point:** `docs/README.md` lists every current document and its single purpose.

Layout (categories; each file under 500 lines):

| Folder | Holds | Replaces |
|---|---|---|
| `docs/README.md` | the index: every document, one line each | nothing today |
| `docs/intent/` | one page per area, owner-approved: what the owner wants, quoted | owner words scattered over 36 logs, DESK_DECISIONS paraphrases |
| `docs/design/` | the current design per area | DESK_DESIGN, CLEAN_SLATE_DESIGN, design_v2/, CORE_ENGINE_PLAN, the current parts of responses 325/327 and other design responses |
| `docs/decisions/` | the current rules per area (one table each), each row with the owner's words and date | DESK_DECISIONS.md (345 rows, superseded rows removed) |
| `docs/status/` | `ROADMAP.md` (stages, done, pending) and the work register split by area | IMPLEMENTATION_PLAN, BUILD_MAP, CORE_ENGINE_GAP_AUDIT, WORK_REGISTER, HANDOVER_*, MIGRATION_PLAN |
| `docs/operations/` | routines, data sources, Groww and NSE rules, runbooks | the long routine sections now in CLAUDE.md (kept there in step 6 until the owner re-pastes prompts), DATA_SOURCES, DATA_USE_MAP |
| `docs/process/` | lanes, judge, merge procedure, numbering | JUDGE.md and process parts of CLAUDE.md/AGENTS.md |
| `docs/stories/` | one story per file | the multi-story files (A, B, E, G, MS ...) split |

Areas (one intent page, one design page or more, one decisions table each): Book 1 (rules), Book 2 (hybrid), Book 3
(AI team), market school (the strategy finder for all three books), forecasts and the forecast lab, recommender and the
real-money gate, risk and money limits, data and capture, daily operations and routines, dashboard and publishing,
process (lanes, judges, logs).

Not in scope (records, never rewritten): frozen and hashed files (`research/forecasts/PROTOCOL_v4.md`,
`FREEZE_v4.md`, `research/evaluation/*`, every file named by a freeze hash), `research/ledger.csv`, study results, judge
reports and responses in `reviews/` (the merge evidence; commit messages cite them), receipts, journals. They stay as
records; `docs/README.md` says they are history, not a source of truth for decisions.

## 3. How (phases; each phase ends on a gate)

| Phase | Who | What | Gate |
|---|---|---|---|
| P0 plan | orchestrator | this file | two judges PASS, owner approves |
| P1 scan | one scanner agent per area, read-only, in parallel | lists every statement about the area (rule, decision, design, status) in every document and log, with file, line, date and author (owner or session) | the scan file names every document it read fully, searched, or skipped |
| P2 reconcile | one reviewer agent per area, independent of its scanner | marks each statement current / superseded (by what) / conflicting / unknown; checks status claims against the code on main and real records | conflicts and unknowns become owner questions, never guesses |
| P3 owner gate | owner | reads the area's intent page (under 500 lines, plain words, quotes) and its question list; confirms or corrects | owner's "approved" for that area |
| P4 write | one writer agent per area | writes the area's new documents from the approved intent and the reconciled table; names each functionality's owner document | under 500 lines each; every superseded statement accounted for; no functionality described twice |
| P5 judge | two judges per area (existing judge sessions, independent) | check each new document against the intent page, the reconciled table and the code; plant check: a judge removes a current rule from the new document and confirms the reconcile table exposes it | both PASS (two rounds at most, then the owner decides) |
| P6 switch | orchestrator | one merge per area: new documents in, replaced files removed, links and doc-reading tests updated, `docs/README.md` updated | full gates; switched outside 08:30-20:30 IST so no routine reads a half-switched set |
| P7 rule | orchestrator, two judges | CLAUDE.md and AGENTS.md slimmed to point at `docs/README.md`; the update-in-place rule; tests that every Markdown file under `docs/` is under 500 lines and listed in the index, and that the index names one owner document per functionality | both PASS, owner approves |

Order: Book 1 and the market school first (the audit in progress), then Book 2 and Book 3, then the rest. Agents per
area: one scanner, one reviewer, one writer, two judges; at most three areas at once.

## 4. Safety rules for the switch (strong evidence: these break things if ignored)

1. The owner's scheduled routines name CLAUDE.md sections by title ("Daily desk routine", "Morning and evening
   forecast routines", "Pre-open capture (story A22)"). Those sections stay in CLAUDE.md, word for word, until the
   owner re-pastes new prompts; DOC1 never changes a stored prompt.
2. 95 test files read documents (`grep -rlE "docs/|\.md['\"]" tests`), and code reads some (`docs/DESK_DECISIONS.md`
   18 references). Each move updates its readers in the same merge, and the full gates run.
3. Frozen files and records listed in section 2 are never edited or moved.
4. Nothing is deleted without its replacement merged in the same commit; git keeps every removed file.
5. PROC1 planned a docs archive for Mon 26 Oct (`docs/stories/PROC1-process-cuts.md` item 3). DOC1 takes that item
   over, agreed with PROC1's builder before P1, so there is one builder for documents.

## 5. Questions for the owner (recommendation first)

1. **Daily conversation logs** (`conversations/`, 36 files, 9,511 lines; CLAUDE.md requires them today). (A,
   recommended) The owner's exact words move into the intent and decisions pages of the area they concern; the daily
   logs are then removed from main (git keeps them) and the CLAUDE.md log rule becomes "add the owner's words to the
   area page". (B) Keep them as a raw archive that no session reads for decisions.
2. **Reviews folder** (`reviews/`, about 950 files): keep as records (recommended; merge commits cite them), or move to
   an archive folder.
3. **Order of areas:** Book 1 and the market school first (recommended).

## 6. Claims (for the judges)

- Every number in section 1 was counted on main at 8edc21139 with `git ls-files` and `wc -l`.
- Revision 2 (owner, 25 Oct): 500-line limit, one owning document per functionality, functional correctness first,
  documents judged like code. The interim rule is added to CLAUDE.md ("Code") and AGENTS.md ("Documents") in this
  branch so every session follows it before DOC1 finishes; no routine section of CLAUDE.md is changed.

## 7. Known conflicts reported by builders (25 Oct; inputs for P1)

Ruling until DOC1 reaches each area: work already in review lands in its current file, so no review changes
mid-round; any new piece starts its own document (under 500 lines) with a one-line link from its parent; nobody
moves, splits or deletes an existing document outside DOC1.

| File or pair | Problem | Reported by |
|---|---|---|
| docs/stories/REH1-rehearsal-mode.md (2,000 lines) | over 500; REH1r code and REH1n round 3 add about 75 | REH1 builder |
| docs/stories/REC1-recommender.md (857) | over 500; mostly round-by-round Claims | REC1 builder |
| docs/stories/F1t-ai-trading-runner.md (775, branch), F5-book2.md (542, branch) | over 500 | AI books builder |
| docs/stories/E3-fills-by-book.md (46, on main) vs E-paper-desk.md's E3 section | one functionality, two documents | AI books builder |
| docs/stories/O1-daily-run.md lines 52-65 vs A-data-foundation.md "A14c part 2" | A14c part 2 described twice (the follow-up replaces O1's copy with a link) | A14c builder |
| reviews/claude/response_291 claims tables vs A-data-foundation.md | design restated | A14c builder |
