# Judge 104: F8 (minimal) and BG1 budget meter: `story/f8-bg1-budget` eddd0353c3067884b497a7082b365bf5e5f5697e (lane 1, response 104)

Judge B.

**What I did:**
- Read every changed file in full (31 files, +1,564): both story texts, the claims file, `fno/budget/*`,
  `fno/alerts/dry_run.py`, the config, constants, CLI and every test.
- Checked the stories against design v2 sections 6.5, 7.6, 8.1 and 8.2, REPLAN's F8 and BG1 rows, S1's decided
  `ai_cost_allocation` item, and the owner's 15 Oct budget and stop-rule rows (quality rule 1, story check first).
- Checked the builder's three "blocked" claims with the session tools myself.
- Built a real session export from my own session's `get_session` and `list_events(kinds=["result"])` pages and fed it
  to `record-usage`.
- Ran 12 planted mutations and about 40 probe cases: good, bad, boundary and empty or missing input.
- Ran the gates on the exact SHA and on a trial merge with `main`.

## Gates

- **At eddd035 (full history, Slack token unset):** 3,249 passed, as claimed. `ruff check` passed, `ruff format --check`
  passed (727 files) and `check_imports` is clean (737 files).
- **Trial merge with `origin/main`:** the merge is clean (3ce2aa3 adds only the branch's 31 files). 3,249 passed, and
  ruff, format and `check_imports` are clean.
- **Size:** the largest new file is 107 lines.
- **Composition root:** `fno/budget/wiring.py` is listed in `CLAUDE.md`.
- **Constants:** names live in `fno/constants.py`; message templates sit at the top of their modules.

## The builder's three blockers, checked

| Blocker | Result | Evidence |
|---|---|---|
| (1) The books' routine sessions cannot be read | CONFIRMED | `get_session` on both `session_01KArozSaT7wCoYmLbni7XUY` and `cse_01KArozSaT7wCoYmLbni7XUY` (book2's 14 Oct fire) returns "the requested resource was not found" |
| (2) Plan minutes are not measurable | CONFIRMED | My own session's `rate_limit_info` holds only `status`, `rateLimitType: five_hour`, `resetsAt` and `isUsingOverage`, with no minutes or share used. (`external_metadata.usage` gives cumulative tokens, not minutes) |
| (3) Python cannot call the session tools | CONFIRMED | The tools exist only as model tools of a Claude session |

**The `cse_` / `session_` match (F8.7, "reasoning only") is now strong evidence.** `get_session("cse_01YEVAEMygZa9VgBATxsZrXQ")`
returns my own session, `session_01YEVAEMygZa9VgBATxsZrXQ`. So both prefixes name the same session, and
`session_key` is right.

## Must-fix

**1. A complete real export is refused, so `record-usage` can never record a real session (F8 criteria 4-5 NOT MET on real data).**
- Paging my own session back to the oldest event, the last page is `{"ccr": {"first_id": ..., "last_id": ...}}`: no
  `data` and **no `has_more` key at all**. A false value is omitted, not written as `false`. Pages that still have
  older events carry `has_more: true`.
- `usage_export._results` requires `page.get("has_more") is False`. My faithful export of 3 real pages and 6 real turns
  (reply texts dropped) gives:
  `refused: the export has no page with has_more false: older result events are missing, so nothing is recorded`
  (exit 1).
- The test exports write `"has_more": False` explicitly. That is not the real shape, so "real field names from 15 Oct"
  holds for the event fields but not for the page envelope.
- With the last page patched to `has_more: false`, the reader gives 4.61 minutes, 6 turns and 18,315 output tokens.
  That equals my hand sum: 276,804 ms / 60,000 and 8,857 + 2,746 + 5,430 + 779 + 235 + 268.
- Fix: treat a missing `has_more` on a page as false. Add a test built from the real envelope, including a last page
  with no `data` key, and record in the claims that this shape was read on 15 Oct.

**2. A missing middle page is accepted and under-counts silently (against criterion 5's own aim, "never under-counted silently").**
- Probe: newest page (has_more true), middle page dropped, oldest page (has_more false). Accepted with 20.0 minutes,
  against 30.0 true. An export holding only the oldest page is also accepted (10.0 minutes).
- Fix: prove the chain is complete. Store each page's request cursor (`before_id`) with the page and require page k+1's
  cursor to equal page k's `first_id`. The first page must have no cursor, and the last must have `has_more` false or
  absent. Refuse anything else. Add a missing-page test, which the orchestrator asked for.

**3. The cap level and the books' allocated share are biased by the development sessions that are never captured, without warning.**
- Under the default basis, `pct = books / (0.5 × (books + development))`. No routine or story records development
  sessions (builders, orchestrator, judges); each would need a Claude session to save its own export.
- Probe: one recorded book row and no development rows gives **200.0%, level `stop`, `stop_ai_roles: true`**. The
  branch's own `test_meter` asserts exactly that ("= 200.0%; level stop") without any warning line.
- The reverse case: development rows and missing book captures give **0.0%, level `ok`**. The signal file says
  `"level": "ok"` with `missing_captures: 2`. A routine reading the level would act on a figure the meter itself calls
  "not a bound".
- S1's decided allocation divides by "all measured Claude session minutes on the plan that month", so missing
  development sessions also inflate every book's allocated cost.
- Fix:
  - Count development capture coverage too. `list_sessions(mine: true)` from a Claude session lists them, so the same
    export step can save that list.
  - The level is `unknown`, never `ok` or `stop`, while either coverage is incomplete. With the owner's
    `plan_minutes_per_month` set, only book coverage matters.
  - The allocation says "development not fully captured: book shares overstated" when that holds.

**4. The rounding rule differs from S1's decided item.**
- `research/evaluation/PROTOCOL.md`, `ai_cost_allocation`, was decided by the owner on 2026-10-14: "to the paisa, with
  the remainder added to the largest share".
- The branch uses largest-remainder rounding (`_split`). The sums are exact either way (my 20,000 random cases: 0
  mismatches), but the parts differ. Rs 1,700 over three equal shares gives 566.67 / 566.67 / 566.66 here; the decided
  rule gives the remainder to one share.
- The docstring calls the formula "to be frozen by S1", so this is the code S1 will hash.
- Fix: implement the decided rule (and its tie-break, stated), or put the change to the owner as a change to a decided
  item. Add a test that pins which share receives the remainder. My mutation that hands paise to the smallest
  remainders survived all 53 budget tests.

**5. Gap list (quality rule 2): requirements in neither "covered" nor "out of scope".** The claims file has no gap list.
Checking the cited design paragraphs myself:
- 8.1, GitHub Actions and Drive: "storage reported monthly". Missing from the meter, and not listed as out of scope.
- 6.5, SYSTEM alert "a stop-rule date reached". Neither covered nor out of scope. (The 80% and 100% alerts are
  dry-run, as stated.)
- Original F8 criterion 2 ("ledger, scoreboards, dashboard") and its per-book lines in C1's account ledger. Judge 87
  left S2's AI-cost port "latent until F8 fills the port". The original F8 is marked **"superseded"**, so this
  remaining scope has no owner story. Mark it "later (F8 part 2)" instead, and name S2's port.
- S1's "development shown as 'development, not a book cost'". The meter prints "development builder: Rs ..."; use the
  decided label.
- Fix: add the gap list, listing each item as covered or out of scope with its reason.

## Should-fix

1. **Tests that pin what the claims rely on.** These of my mutations survived all 53 budget tests:
   - `build_budget_alert_sender` returning `SlackChannelAlerts`. BG1.4 cites `wiring.py:35` as the guarantee, and no
     test pins it.
   - `v4_freeze_date` ignored in the wiring, so setting the freeze date would change nothing and no test notices.
   - Weekend fallback removed. Every tested month ends on a weekday. July 2027 ends on a Saturday, so a freeze in
     January 2027 must give Friday 30 Jul 2027; the code does, untested.
   - The report's token "known" check removed.
2. **The new-cost rule accepts any text containing "DESK_DECISIONS".** A cost with `source` "not in DESK_DECISIONS" is
   not flagged (my probe), and the judge-verifies step ("plant a cost without a decision") passes a fake citation.
   Require the cited row (date and bold title) to exist in `docs/DESK_DECISIONS.md`. A negative amount also escapes
   (minor).
3. **Quality rule 3:** the claims file does not report a self-review by independent review agents.

## Minor

1. `alert_text` rounds the % with `:.0f`. At 99.6% (level `alert`) it says "used 100% of their cap; at 100% AI roles
   stop". Use one decimal, as the meter does.
2. A malformed `--month 2026-13` ends in a traceback (`ValueError`), not a "refused" line.
3. Config numbers are not checked: alert 120 above stop 100 is accepted, and share 0 gives `unknown`. Check
   `0 < alert <= stop` and `0 < share <= 100` when loading.
4. The export holds reply texts. The CLI says "outside git" but does not refuse a path inside the repository; refuse it.
5. `DryRunAlertSender` sits beside the existing `NoAlertSender`. Acceptable, since it records what would be sent; say
   why in its docstring.
6. A turn that crosses midnight IST counts on its end day (`created_at` of the result event). State it.
7. Special Saturday sessions count as "sessions" for the review date. Design 8.2 does not say; immaterial for May.

## Per-criterion table

| Criterion | Builder's claim | My evidence | Result |
|---|---|---|---|
| F8.1 Allocation sums exactly | largest remainder | 0 mismatches in 20,000 random cases; but not the decided rule | **NOT MET** (must-fix 4) |
| F8.2 Cash and allocated apart | meter and data | Separate lines and fields; label differs from S1's for development | PARTLY (must-fix 5) |
| F8.3 No plan cost: unknown | `None` | Probe and real meter: "no Claude plan cost recorded; allocation unknown", no "Rs 0.00" | MET |
| F8.4 Usage from session figures per IST day, no text | real field names | Event fields right; IST day mutation caught; my real turns sum by hand; but a real export is refused | **NOT MET** (must-fix 1) |
| F8.5 Incomplete export refused | `has_more` false | Real complete export refused; missing middle page accepted | **NOT MET** (must-fixes 1, 2) |
| F8.6 Written once, complete days | key and `day < today` | Mutation `>` caught; re-record leaves bytes unchanged | MET |
| F8.7 Fired sessions without rows counted | count, match reasoning only | Count right on the real fire log (2); `cse_` = `session_` proven on my own id | MET |
| BG1.1 Every 8.1 item, "not recorded" | six items | Real meter shows all six as "not recorded"; storage line missing | PARTLY (must-fix 5) |
| BG1.2 Levels | boundaries | 79.98 ok, 80.0 alert, 99.98 alert, 100.0 stop, empty unknown | MET in code; levels mislead with partial coverage (must-fix 3) |
| BG1.3 Basis and limits | measured or owner | Both bases and the limit line printed; development coverage not shown | PARTLY (must-fix 3) |
| BG1.4 Signal data and dry run | dry-run sender | Signal file fields right; nothing sent (network blocked); Slack wiring untested | MET with should-fix 1 |
| BG1.5 New cost flagged | citation | Uncited flagged; fake citation passes | PARTLY (should-fix 2) |
| BG1.6 Review date | 31 May 2027 projected | Hand count: Nov 2026 to May 2027 (Mon); Dec 31 to 30 Jun 2027; Jul 2027 to 31 Jan 2028; Aug 2027 to 29 Feb 2028 (Tue); "projected" with its dependency; tests "not computable yet" | MET |
| BG1.7 Missing captures, not a bound | note | Note printed, but the signal's level reads `ok` | PARTLY (must-fix 3) |

## Claims vs reality

- **"Nothing is scheduled, nothing is posted to Slack."** True. No `requests`, `urllib` or Slack import in
  `fno/budget`, and the wiring returns the dry run. Not pinned by a test (should-fix 1).
- **"F8.4 strong evidence (real orchestrator turns)."** The figures are real, but the page envelope is not; see must-fix 1.
- **"13 mutations, all caught."** Not re-run as theirs. 4 of my 12 survived, listed above. 8 were caught: missing usage
  as zero tokens, today counted, unknown as ok, `has_more` check removed, development left out of the basis, unknown
  items hidden, UTC day.
- **"Real output on the repository today".** Reproduced line for line (meter, stop-rule; the signal says `unknown`).
- **Known limits 1-6 and owner choices 1-3.** Accurate and candid.

**Verdict: FAIL for eddd0353c3067884b497a7082b365bf5e5f5697e.**
- Must-fixes 1 and 2: the export reader refuses every real complete export and accepts a gapped one.
- Must-fix 3: the cap level and the allocation silently assume complete development capture.
- Must-fix 4: rounding differs from S1's decided rule.
- Must-fix 5: gap list.
- Should-fixes 1-3.

The stop-rule tracker, the ledger's write-once rule, the item lines and the dry-run signal are sound.
