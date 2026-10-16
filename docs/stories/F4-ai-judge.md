# F4. The judge of the AI books' daily decisions, and its monthly audit (design v2)

**Repository:** trading · **Lane:** 1 (decides whether a trade happens) · **Size:** M ·
**Builder:** session_01AN94h4cY98oYa3CF2MZfak · **Judge:** E · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH ·
**Replaces:** the F4 text in `docs/stories/F-ai-layer.md` (amended 16 Oct), which now points here.

**Description:** As the owner, I want every AI book's sealed daily decision checked, before it is promoted, for
whether the evidence it cites is really in its own pack and whether the numbers it quotes are the pack's, with a
recorded pass or fail, reasons and what to redo, so that Book 2 never trades on an invented fact or number, Book 3's
record shows where it did, and the judge itself is audited every month. I never override a paper decision (owner,
16 Oct 2026, DESK_DECISIONS "D4/D5: the five design questions" item 4): a verdict stands.

**Owner, 16 Oct 2026:** "Build F4 first (Recommended)" (DESK_DECISIONS "F4, the AI judge, is built before Book 2
switches on"); and "developed end-to-end, validated end-to-end, tested end-to-end ... no surprises. Every claim must be
validated ... do not over-engineer ... Simplicity is also our priority, but not the product quality."

## Context and why (each fact marked)

- **Design 7 (strong evidence: `F-ai-layer.md` F4 as amended):** three checks; hard validity is code (C4); the judge
  checks sufficiency and interpretation; fail = no trade; Book 3's verdicts are evidence, not blocks (12.3); Book 1's
  strategies were judged at approval and its days are checked by C4 only; a monthly audit of a stratified sample plus
  10 seeded known-answer cases; a failed audit suspends the judge's approvals.
- **The time window (strong evidence: F1t's story at `story/f1t-ai-trading-runner` 13653f05, "Timetable" and
  "Context"):** each book reveals at 15:10:10; observation 2 is at 15:11:00; `ai_collect` then judges, decides (F5's
  budget 30 s) and commits before E3's 15:12:00 deadline. F1's measured fire-to-answer time for a routine session was
  66-99 s on 16 Oct (its best day) and about 5 minutes on 15 Oct (late).
- **So the daily judge is code, not an AI session (decision, strong evidence on timing):** an AI judge session would
  need to start after 15:10:10 and answer before about 15:11:30; no measured session has done that, and a judge that
  misses counts as a fail for Book 2 (criterion 5), so an AI judge would make Book 2 a no-trade book on most days.
  The code judge is pure (no input or output) and takes well under a second.
- **What code can and cannot check (reasoning only):** code can prove that each cited fact exists in the book's own
  pack and that every number the decision writes is the pack's number. It cannot judge whether the reasoning is sound
  ("the action fits the reasons" in meaning). For Book 2 the room for unsound reasoning is narrow: its envelope allows
  only following the rule, a veto, a narrower set (width, fewer lots) or another eligible version, all then checked by
  C2 and C4 (D4, F5). Checking meaning needs a model different from the author's, outside the daily window: that is
  **F4b** (out, below; an owner question).
- **Reuse (strong evidence: code):** `fno/advocate/numbers.py` already compares whole number tokens and refuses numbers
  written in words (judge 167 addendum 1); the judge uses it unchanged.

## Scope

**In:**
1. The evidence citation format inside each AI book's `decision`, and its shape check (standard library only), called
   by F5's and F6's shape checks so `seal` refuses a malformed list before the deadline.
2. The code judge: two checks (sufficiency, interpretation), a time budget, the audit suspension, the per-book rule
   (Book 2 blocks, Book 3 records), one verdict file per book-day, written once.
3. The port F1t's `ai_collect` calls (agreed below), with timing.
4. The monthly audit command `python -m fno judge audit <YYYY-MM>`, its record, its alert and the suspension.
5. The 10 seeded known-answer cases.

**Out (each with its owner or reason):**
- **F4b, a model re-check of meaning** (a monthly AI routine on a model different from the author's, reading the
  audit sample with its packs and judging whether each action fits its reasons): needs a routine and a schedule;
  owner question 1. Until then the audit's re-check is code (criterion 7 states what that does and does not find).
- **Research theses:** no story produces a thesis to judge yet (Book 3's proposals register as `research` under D5's
  guards and trade only after their own tests). Judged when the research loop exists.
- **The red team / devil's advocate:** T2, T3 (objections never block).
- **Hard validity:** C4. **Owner overrides:** none (D3 refuses a non-empty `owner_override` in every book).
- **The answer shapes and prompts themselves:** F5 (Book 2) and F6 (Book 3) add the `evidence` key and the prompt
  lines below to their own files. **The runner, sealing, receipts, outcome records and commits:** F1t.
- **Scheduling the monthly audit:** the orchestrator (builders never create scheduled tasks); the prompt is in the
  claims file.

## Design

**1. Evidence citations (`fno/judge/evidence.py`).** Each AI book's `decision` has a top-level `evidence` list of 0 to
20 items `{"pack": "common" | "private", "pointer": "<RFC 6901 JSON pointer>"}`. No value is copied into the answer,
so no private pack value becomes public through the reveal (the reveal is public; the private pack stays in Drive).
`evidence_problems(evidence) -> list[str]` lists shape problems (not a list, over 20 items, an item with other keys,
a pack other than the two, a pointer that is not a JSON pointer string of at most 300 characters, a duplicate item);
an empty list means the shape is acceptable. F5's and F6's `check_decision` call it.
`resolve(body, pointer)` follows the pointer in a pack body (`~1` and `~0` escapes, list indices) and returns the
value or raises `Unresolved`.

**2. The checks (`fno/judge/checks.py`), each giving `{check, passed, reasons, what_to_redo}`:**
- **Sufficiency:** every cited pointer resolves in the named pack of this book-day (the book's own private pack, the
  only private pack the judge receives) to a scalar (number, text of at most 200 characters, true, false, null): a
  whole object, list or file text is not a citation. A decision that departs from the rule (Book 2: `action` is
  `change`; Book 3: `action` is `trade`) cites at least one item. What to redo: "cite each fact as a pointer to one
  value in your own pack".
- **Interpretation:** every number token (`numbers.py`'s tokenizer) in every text under a key named `reason`, at any
  depth of the decision, is a token of a cited value or of a JSON number in the decision itself (a slot's width or
  lots); no number is written in words (`numbers.py` rule 4). What to redo: "quote each number exactly as the pack
  writes it, and cite where it comes from". Reasons name the pointer and the token, never a private pack value.

**3. The verdict (`fno/judge/verdict.py`).** `status`: `pass` (both checks passed), `fail` (a check failed),
`unavailable` (the judge did not decide: an exception, its model equal to the author's, or over its 5 s budget; an
abstention). `blocks` is true exactly when the book is Book 2 and the status is not `pass`; for Book 3 it is always
false (verdicts are evidence) and `unavailable` reads "judge unavailable". While approvals are suspended (design 5),
a Book 2 `change` decision that passes both checks becomes `fail` with the reason "judge approvals suspended by audit
<YYYY-MM>". Fields: `schema_version`, `kind: "judge_verdict"`, `book`, `day`,
`judge` (`code:f4-v1`), `author_model` (the registered model), `status`, `blocks`, `reason` (one line), `checks`,
`suspended_by`, `elapsed_ms`, `decision` (the judged decision object, already public in the reveal),
`decision_sha256`, `common_pack_sha256`, `private_pack_sha256`. Written once to
`journal/ai_decisions/<YYYY>/<d>_<book>_judge.json` (the same bytes again are accepted; different bytes are refused).
The verdict carries no private pack value.

**4. The port and its timing (`fno/judge/port.py`, `fno/judge/step.py`, `fno/judge/wiring.py`):**

```python
@dataclass(frozen=True)
class JudgeCase:
    book: str; day: date; registered_model: str
    decision: Mapping; common: Mapping; private: Mapping   # accepted.decision, common_pack.body, private_pack.body
    common_sha256: str; private_sha256: str

class JudgeStep:                                          # build_judge_step(root) in fno/judge/wiring.py
    def run(self, case: JudgeCase) -> Judged: ...         # Judged(verdict, path); never raises for a bad case
```

F1t's `ai_collect`, for each book-day that passed its own checks and before `decide()`: (1) `judged =
step.run(case)`; (2) if `judged.verdict.blocks`, the book-day's outcome is `judge_failed` (no trade, `decide()` not
called), its reason the verdict's; (3) otherwise `decide()` runs, with `AcceptedDecision.judge` set to the verdict
file's repository path, which F5 and F6 write into D3's existing `judge` field; (4) the verdict file is committed with
the outcome record. The judge reads nothing from disk except the audit records (for the suspension), so it adds no
network time to the 15:11:00-15:12:00 window; its 5 s budget is measured, and over budget is `unavailable`.
(Agreement with F1t, F5 and F6: response 271, "Coordination".)

**5. The monthly audit (`fno/judge/audit.py`, `fno/judge/sample.py`, `fno/judge/seeded.py`, `fno/judge/cli.py`).**
`python -m fno judge audit <YYYY-MM>`:
1. Reads the month's verdict files of both AI books.
2. Draws, per status (`pass` approvals, `fail` rejections, `unavailable` abstentions), 20% rounded up and at least 5
   (all when fewer), with a seed fixed by the month (SHA-256 of `judge-audit:<YYYY-MM>`), so the draw is
   reproducible.
3. Re-checks each drawn verdict against recalculated evidence: the decision from the verdict (its SHA-256
   re-checked), the packs re-read from their stores (the common pack from the repository, the private pack through
   E2c's Drive files) and refused unless their SHA-256 equals the verdict's; then the current checks, without the
   budget or the suspension. A recorded `pass` that re-checks as `fail` is a false approval; a recorded `fail` that
   re-checks as `pass` a false rejection; an abstention reports what the check would have said. A verdict whose
   packs cannot be re-read is counted and named as "not re-checked", never dropped.
4. Runs the 10 seeded known-answer cases (5 that must pass, 5 that must fail, one per failure kind).
5. Fails when any seeded case is falsely approved or when false approvals exceed 10% of the re-checked approvals;
   false rejections are reported, not failing (the amended text).
6. Writes `journal/judge/audits/<YYYY-MM>_<n>.json` (next free `n`, written once), prints the numbers, sends one
   #fno-desk line through `AlertSender` when it fails or when anything was not re-checked, and exits 1 on a fail.
**Suspension:** while the latest audit record (by month, then attempt) failed, every Book 2 `change` decision fails
(above). `follow_rule` decisions are judged as usual: they take the rule's own trade, not an AI-chosen one. A rerun of
the audit after a fix that passes lifts it.

## Acceptance criteria

1. **Different model.** A judge whose model equals the author's registered model is refused: the verdict is
   `unavailable` with that reason (Book 2: no trade). The code judge's model is `code:f4-v1`.
2. **Book 2 blocks, Book 3 records.** A Book 2 decision failing a check gives `blocks: true` and, through F1t's
   port, no `decide()` call (no run, no fill); the same failure on Book 3 gives `blocks: false` and the verdict file.
3. **No override.** Nothing in F4 writes or reads `owner_override`; a verdict file has no override field, and the only
   way past a `fail` is a new decision on a later day.
4. **Sufficiency.** Each refusal: a pointer that does not resolve, a pointer into the other pack, a pointer to an
   object, list or long text, a `change`/`trade` decision with no evidence; and each pass: a `follow_rule` or
   `no_trade` decision with no evidence, a valid pointer with `~1` escapes and list indices.
5. **Interpretation.** A reason quoting a number not in its cited values fails ("4" never matches "40%" or "14"); a
   number in words fails; numbers of the decision's own fields pass; a reason quoting a cited value passes; reasons at
   any depth (Book 2 slots, Book 3 trades, proposals and shadow entries) are read; a proposal's `spec` text is not.
6. **Late or broken judge.** A judge over its 5 s budget, or one that raises, gives `unavailable`: Book 2 no trade,
   Book 3 "judge unavailable"; `JudgeStep.run` never raises for a bad case.
7. **Audit.** Sample sizes at the boundaries (0, 1, 5, 25 and 26 verdicts of a status); a planted edited verdict
   counts as a false approval; a pack whose SHA-256 differs is "not re-checked", named; a seeded case falsely approved
   fails the audit; 10% false approvals passes, just over 10% fails; a failed audit suspends Book 2's `change`
   approvals (and not `follow_rule`), and a later passing attempt lifts it. What the code re-check finds: edited or
   corrupted records, packs that no longer match, and a changed judge that now judges differently; not unsound
   reasoning (F4b).
8. **Written once, private values never.** The verdict file is written once (same bytes accepted, different refused);
   no verdict or audit record contains a value read from a private pack (test with a private pack holding a marker
   value cited by a failing decision).
9. **Shape check at seal.** `evidence_problems` refuses each malformed list in the test plan and accepts an empty
   list and a list of 20 valid items; it imports the standard library only (F1t's `seal` runs in the routine).
10. **Time.** The judge on a realistic pack (the largest fixture common pack and a private pack with a full day
    sheet) takes under 0.5 s on the test machine (measured and reported in the claims file).

## Test plan

- Fake AI answers through `JudgeStep` (the orchestrator's four: pass, fail, late, invalid), for each book: a valid
  cited answer (pass), an invented number (fail), a judge over budget (late, unavailable), a malformed `evidence`
  list reaching the judge (invalid: sufficiency fail) and an exception inside a check (unavailable).
- Each criterion's positive, negative, boundary and empty cases (JUDGE.md quality rule 5); mutation proof per
  criterion in the claims file.
- The audit over a fixture month with planted verdicts, packs from a fake store, the seeded cases and a fake
  `AlertSender`.

## Gap list (each requirement of the amended F4 text and design 7)

| Requirement | Where |
|---|---|
| Sufficiency and interpretation checked, by a model different from the author | criteria 1, 4, 5 (code daily); meaning: F4b, out, owner question 1 |
| Verdict JSON `check, pass, reasons, what_to_redo, model` | design 3 (`checks` items, `judge`), criterion 8 |
| Fail = no trade (Book 2); Book 3 recorded, not blocking; Book 1 by C4 only | criterion 2; Book 1 is not judged (no change to Book 1) |
| No override path; D3 keeps `owner_override` null | criterion 3; D3's refusal is `story/d3-no-owner-override` |
| Judge missing the deadline = fail (Book 2), "judge unavailable" (Book 3) | criterion 6 |
| Monthly audit: 20% of approvals, rejections, abstentions, at least 5; re-checked against recalculated evidence | criterion 7; the re-check by another model: F4b |
| 10 seeded known-answer cases; failed audit (seeded false approval or rate over 10%) suspends approvals | criterion 7 |
| Verdicts for research theses | out: no thesis producer yet |
| Inside the deadline | design 4, criterion 10 |

## Open questions (to the orchestrator, then the owner)

1. **F4b, a model re-check of meaning, monthly (recommended: yes, after Book 2 has a month of decisions).** The daily
   judge is code because an AI session cannot fit the window (strong evidence: F1's latencies). Does the owner accept
   that Book 2's daily gate checks facts and numbers only, with meaning re-checked monthly by another model? Reasoning
   only on how much meaning-checking adds, since Book 2's actions are bounded by its envelope, C2 and C4.
2. **Strictness costs trades (some evidence: the rule is strict by design).** Every number in a reason must be cited;
   one uncited "2" in a `follow_rule` reason fails Book 2's day. The prompts (F5, F6) say so, and the audit reports
   false rejections. Accept, or let `follow_rule` days pass the interpretation check with a recorded warning?
   Recommendation: keep it strict, measure the first month's fail rate, revisit with the numbers.

**Depends:** F1t (the port and `judge_failed`), F5 and F6 (the `evidence` key and prompt lines), E2/E2c (packs), D3
(`judge` field, no override) · **Status:** story text for judge E
