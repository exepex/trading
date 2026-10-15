# Judge 108: A16 15-minute quote recorder: story text at `story/a16-groww-15min` db26fd7 (lane 1, quality rule 1)

Judge D. Scope: `docs/stories/A16-intraday-quote-recorder.md` and response 108 (part 1) at
db26fd7a329fc6605438db839ac8a66ad1634db3, parent `main` 32262d4. Text only; no code is pushed.

**What I did:**
- read the story and claims in full;
- checked them against design v2 (REPLAN_new_stories A16, 2.1, 4.2, 4.4, 5.2, 6.5, 6.6), the owner's 15 Oct rows (host
  "1 - A", Groww terms, "6 A" raw quotes Drive only) and `fno/providers/groww.py`;
- checked every criterion for good, bad, boundary and empty cases.

I cannot repeat step 0 myself. This session has no Groww key, and `requirements-groww.txt` does not install here
(`clint`/`args` wheels fail). So step 0's numbers rest on the builder's word: some evidence.

## What is right

- **The RV definition matches design 5.2.**
  - 26 marks, k = 0..25, and 25 intraday squared log returns.
  - An overnight return from the previous recorded session's 15:30 to 09:15, with muhurat skipped.
  - Units: a daily variance, not annualised, with `vol_pct = 100 sqrt(RV)` (0.0001 is 1.00%, correct).
  - Void, never interpolated. The 120 s staleness limit is design 5.2's 2 minutes. The 5% void flag is there.
  - It is a versioned strategy (`rv-quote-15m-v1`), labelled `quote_snapshot`.
- **Gaps are never filled.** `missed` is never taken later, every due slot gets one ledger row, and the 120 s boundary
  is tested at, 1 s under and 1 s over.
- **Raw data stays private.** Raw quotes go only to the owner's Drive, with first-version-wins and A11 revisions. The
  repository holds no price, bid, ask or level (criterion 11, owner "6 A").
- **Clock contract (4.4) in full:** UTC with offset, the source time kept apart, skew checks against GitHub and Slack,
  5 s WARNING, `clock_unchecked`, `source_ahead_of_host`.
- **Alerts and heartbeat:** one alert per streak, at most one an hour, with the 60-minute boundary stated; a heartbeat
  check at 30 minutes (4.2).
- **Gap list complete.** Every requirement of the A16 paragraph and of 4.4 maps to a criterion or to a stated
  out-of-scope reason.
- **The candle finding is useful and honest.** Index 15-minute candles exist from 1 Jan 2020, with holes listed. A
  candle-close RV is a different measure, so A16b is rightly separate.
- **The doubts are stated:** the routine is untested, the checker is not independent, the install fails.

## Should-fix

**1. The freshness rule, on which criteria 5 and 6 depend, is not yet defined.** "Groww's own timestamp for the index,
rule fixed by the in-session check": the index `last_trade_time` was empty pre-market, and the in-session check is
"to be added". Until it is written, the `stale` status and the void rule cannot be judged or tested. Fix: run the
in-session check, write the exact source-time rule into Definitions, and write what happens if Groww gives no index
time (the builder's candidate is the latest 1-minute candle's time). Re-check that commit before code.

**2. "A level identical to the previous slot is stale" biases the target.**
- NIFTY prices in steps of 0.05, and a 15-minute move is often 20-30 points. So two equal levels 15 minutes apart are
  rare, but real: at roughly 0.1% per interval, about 2% of sessions would have one (reasoning only; the rate depends
  on volatility).
- Treating equality as stale voids exactly the calmest intervals. That removes zero returns, biases the kept RV
  sessions upward, and spends the 5% void budget on calm days.
- Fix: decide staleness by the source time (should-fix 1). Report a repeated value as a flag, without voiding, unless
  its source time is also old.

**3. The trigger design is not yet shown to be reliable enough for the target, and its prompt cannot run as written.**
- **The arithmetic.** Seven hourly fires at HH:10 each record their own hour, and nothing overlaps. One fire that
  starts more than about 7 minutes late, or fails, loses 1-4 marks. Any lost mark voids that session's RV
  (`RV_intraday` needs all 25 intervals). With 7 fires a day, design 5.2's 5% void ceiling needs each fire to fail less
  than about 0.7% of the time (5% / 7), before any API failure. Nothing measures that. The owner's 14 Oct forecast
  routine ran hours late (DESK_DECISIONS 15 Oct, "8 A").
- **The prompt.** It runs `pip install -r requirements-groww.txt`, which the builder says fails in a container. The
  maximum length of a routine session (about 55 minutes are needed) is not stated.
- Fix, in the text:
  - (a) Overlap: fire earlier (for example HH:00, running to HH+1:05), so each boundary mark has two runs. The
    first-version store and "already recorded" already make the second run harmless, and that should be tested.
  - (b) A tested install line (or a fixed `requirements-groww.txt`, its own lane-1 change).
  - (c) A measured trial before the recorder counts as live: for example 5 sessions through the routine, with slots
    good / missed / late and void sessions reported.
  - (d) The stated consequence: if the void share stays above 5%, design 5.2's "new version" applies and the host
    question returns to the owner. Design 6.6 allows option (b) only "if Groww offers a data-only key".

**4. The no-order guard is a deny-list over one folder, but the client it wraps can trade.**
- `GrowwProvider` holds a full `GrowwAPI` object (`fno/providers/groww.py:115-127`), and that SDK has order methods.
  Design 6.6: "A key that can trade".
- Criterion 10 only greps `fno/intraday/` for order words and fakes an API whose order methods fail. Neither stops a
  call through the shared provider or any other module the package imports.
- Fix:
  - A read-only allow-list wrapper: the intraday source gets an object exposing only the named read calls (`get_quote`,
    `get_option_chain`, `get_expiries`, `get_contracts`, plus sign-in). Any other attribute raises.
  - Tests: the wrapper refuses every other attribute; the source can reach the client only through it; and the grep
    covers the whole import closure of `fno/intraday/`.

**5. Drive failure is not defined.** The snapshot's only home is the owner's Drive, but no criterion says what a failed
Drive write does. Fix: the slot is `failed` with a named failure (`drive_write`, the error type only, as in A4b); the
raw document is never written to the repository and never spooled inside the checkout; one alert, through criterion 7's
streak rule. Add a test, and add the Drive settings to the routine prompt's prerequisites.

## Minor

1. **Process (quality rule 1).** The orchestrator reports that this builder wrote code locally before this check. Rule 1
   says code starts only after the story check passes. Nothing unpushed is judged. Any evidence taken from it must be
   reproduced on the pushed code.
2. **The heartbeat checker runs on the same platform** (stated). The text should say that GitHub's push receipt of
   `heartbeat.json` is the off-platform witness the post-mortem reads.
3. **For the orchestrator, not this story.** Groww's index candles from 2020 (step 0) could give V1's intraday HAR
   baseline its 250 sessions at once, instead of about a year after A16 goes live (design 5.3). Prioritising A16b, and
   letting G6 decide the label, is worth considering (reasoning only).

## Project rules

- Lane 1: a new story, outside services.
- New composition root `fno/intraday/wiring.py`. `fno/storage/wiring.py` is at 345 lines; I checked, it is 345 on main.
- Constants and env names placement stated; files under 350 lines planned. No secrets or model names in the text.

**Verdict: FAIL for db26fd7a329fc6605438db839ac8a66ad1634db3** (story text), on should-fixes 1-5. Code may not start until
a revised text passes. A re-check needs the story file and response 108 only.

## Addendum 1 (15 Oct 2026): story text revision at 83f3614886f0ebe9d4c63f20f7511679662fb71a (db26fd7..83f3614)

One commit: the story file and response 108 part 1b. Text only. The work-in-progress code on
`wip/a16-groww-15min-code` (5355b29) is not judged; see the process note.

| Item | Status | Evidence |
|---|---|---|
| Should-fix 1: source-time rule | PARTLY (see should-fix A) | Primary: the index quote's `last_trade_time` (seconds, or milliseconds above 10^11). Fallback: the end of the latest 1-minute index candle. Neither: stale (`index_time_missing`), never assumed fresh; `index_time_basis` is recorded; both branches built and tested. The rule is now fixed before code |
| Should-fix 2: repeats | MET | `index_repeated` is a flag and voids nothing; only an old or missing source time is stale |
| Should-fix 3: trigger | MET as a design, with one new defect (should-fix B) | Seven fires at HH:00, each running to HH+1:05, so every hour boundary is covered twice. The trial (criterion 15: 5 consecutive sessions, per-mark statuses, void share, each fire's delay and length) runs before anything counts. The consequence above 5% is stated, alternatives are left to the owner, and the routine's unknown maximum length is to be measured. The install line is stated as tested, with fixing `requirements-groww.txt` named as its own change |
| Should-fix 4: read-only guard | MET | `ReadOnlyGroww` exposes `get_quote`, `get_option_chain`, `get_expiries`, `get_contracts`, `get_historical_candles` and constants; anything else raises `ReadOnlyViolation`. It is built only in the composition root, and the source never holds the client. Tests: refusal over the SDK's public names, a whole session with a fake whose order methods fail, and a grep over the import closure |
| Should-fix 5: Drive write failure | MET | `failed` with `drive_write: <type>`; the document is dropped, never in the repository or the checkout; the loop goes on; the streak alert fires; test with a raising store |
| Additions | ACCEPTED | `heartbeat-check` reads GitHub's copy, so a host whose pushes fail looks silent. `rv` settles an unfinished previous session. Alert holds and retries are stated. Per-chain emptiness counts. Dry run refused inside the repository. The commit refuses without `core.hooksPath` |

## Should-fix

**A. In the fallback, the level and its time come from two different calls.** The level is the quote's `last_price`,
while its "source time" is the end of a 1-minute candle fetched in a separate call. A live candle feed proves the
feed is running, not that this quote's value is fresh. A frozen quote beside fresh candles would be called fresh, and
catching that is exactly what the staleness rule is for (design 5.2, "a stale quote repeated"). Fix, one of:
- in fallback mode take the level from the same source as its time (the latest 1-minute candle's close, labelled
  `candle_1m_close`, which is also sampled at the minute mark);
- or require the quote's level to lie inside that candle's low-high range, else `stale`.

Also state that the candle's start time is IST text without an offset (step 0) and how it is parsed.

**B. Two overlapping runs live in two different checkouts, and the ledger has no rule for that.**
- Each fire is a separate routine container with its own clone. At every boundary mark (HH:00) both runs take the
  mark and both append that slot's row to the same daily `slots/.../nifty_<day>.csv`, then pull and push.
- Two appends at the end of one file conflict in git (no `merge=union` there). The story's commit "aborts a failed
  pull's merge", so the push fails, "NOT committed" follows, and the hand-commit step runs, every hour.
- Even a clean merge would leave two rows for one mark, against criterions 1 and 5's "exactly one ledger row". The test
  "two recorders on one store and ledger" shares one ledger, so it cannot show this.
- Fix: define the reconciliation and test it with two git clones of one bare repository:
  - for example, the ledger row for a mark is written only by the run whose Drive put created the first version (the
    `FirstVersionStore` already decides this); the other run records nothing for that mark;
  - or the slots file is merged by slot with the first-stored row kept (a merge driver or a union merge plus a
    dedupe), so a conflict never blocks a push.

## Process note (quality rule 1)

The builder kept writing code after the first FAIL and pushed it to `wip/a16-groww-15min-code` (5355b29). Rule 1 says
code starts only after the story check passes. Pushing to a separate branch, which nobody merges or judges, keeps the
story branch clean. It is still a breach of the rule's intent, now in two builders (A4b too). Not blocking, because
nothing unjudged reaches `main` and the code will be judged fresh. The orchestrator should tell builders to stop
writing code until the text passes.

**Verdict: FAIL for 83f3614886f0ebe9d4c63f20f7511679662fb71a** (story text), on should-fixes A and B. Should-fixes
2-5 of judge 108 are met, and 1 is met apart from A. A re-check needs only the Definitions (source time) and the trigger
design and criteria 1 and 5 (ledger reconciliation).

## Addendum 2 (15 Oct 2026): story text at 27f7b55419b74874420180d8462052dda9752e8c (83f3614..27f7b55)

The story file and response 108 part 1c only. Text only.

| Item | Status | Evidence |
|---|---|---|
| Should-fix A: fallback level and time from one record | MET | In fallback the level is the latest **finished** 1-minute candle's close and its time is that candle's end. A candle still forming is never used. The quote's `last_price` is kept but never the level. Naive candle text gets an explicit +05:30, and text with an offset or unparseable text is `index_parse`. `index_basis` is on the document and the ledger, and `basis_counts` on the RV row, so a session that mixes the two sources is visible |
| Should-fix B: two checkouts, one ledger | MET | One file per mark, per RV session and per revision index, so the runs never append to the same file. A taken mark's row is written only by the run whose Drive write made the first version (`FirstVersionStore.put` reports it). A pull comes before settling marks. A same-path race (both writing one `missed` row or the heartbeat) merges with GitHub's copy winning (`-X theirs`, in this committer, which commits only this folder, so it can only decide between two first versions of one file). Criterion 1's test uses two clones of one bare repository: one row per mark on `origin/main`, no conflict markers, both commits succeed |

I traced the races:
- A run takes a mark and the other later settles it as missed: the second run sees the Drive file and skips it.
- Both runs fail one mark: the first push wins, and both rows were bad anyway.
- Both write the heartbeat: the first pushed wins. Both runs are alive then, so the silence check is unaffected.

`-X theirs` cannot touch files outside this folder, because the committer stages only this folder, so only this
folder can conflict. That makes it safe as scoped.

**Verdict: PASS for 27f7b55419b74874420180d8462052dda9752e8c** (story text). Code may start on the story branch. The code
check covers every criterion, the trial (criterion 15) and the in-session amendment. The work-in-progress code on the
side branch is judged only once it is on the story branch.
