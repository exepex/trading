# Judge 111: A4b raw Groww quotes in Drive only: story text at `story/a4b-quotes-drive-only` d1c2d06 (lane 1, quality rule 1)

Judge D. Scope: the A4b section of `docs/stories/A-data-foundation.md`, the A4 storage line and the plan row, at
d1c2d06f1b01539c5903671b12f1d5bad4c14674 (revision 2; ec4ace4 before it). Text only. I judge only what is pushed. The
builder's local evidence (the 14 Oct replays A-C) is a claim until it is reproduced on pushed code.

**What I checked on `main` myself:**
- `FREEZE_v3.md` lists `fno/forecast_scoring/wiring.py` under "Recorded, not byte-checked" (line 34; recorded
  `c24a4e9f...`, today `1215c5df...`).
- `FREEZE_v2.md` lists `fno/quotes/recorder.py` there too (line 79; recorded `0775c4cc...`, today `a9a06063...`).
- `forecast-capture.yml` (lines 59-62) and `forecast-scores.yml` (lines 31-34) already pass the four `FNO_GDRIVE_*`
  secrets.
- The 14 Oct quote file hashes to `9d9de08b...91ca1`, equal to its sidecar's `csv_sha256`. The sidecar's 21 keys are
  exactly the story's table (`raw_file_saved` aside).
- PROTOCOL_v3 §2's replay text.
- Owner rows "6 A", "7 A" (one more raw file today) and "8 A" (packs derived only, E2b) are on `main`.

## Rulings asked for

**1. G4's replay after A4b: the builder's reading is ACCEPTED. No G1 v3 amendment is needed. One consequence goes to
the owner.**
- PROTOCOL_v3 §2 says the replay uses "the inputs at the parent of the commit that added its pack, never from today's
  grown panel", and "exports ... the quote snapshots ... from that commit". The rule protects point in time and byte
  equality.
- After A4b, that commit still fixes the quote bytes: the sidecar's `csv_sha256` is in the commit, and the Drive copy is
  used only if it hashes to it. A different copy is refused, never used.
- The byte-frozen `replay.py` is unchanged. The changed `recompute_live_day` sits in v3's "recorded, not byte-checked"
  table, whose stated lock (the Q5 resolver test) is untouched.
- "The quote snapshots from that commit" then means the commit's snapshot records, with their bytes by pinned hash.
  The inputs, and so the outputs, are byte-identical (the builder's case B; to be reproduced on pushed code).
- **What changes is availability, not integrity.** A replay now needs the Drive copy to exist. If it is lost, that
  day can never be replayed, where git kept it for ever. The owner chose "6 A" knowing raw quotes leave git, but
  probably not this consequence. The orchestrator should tell the owner in one line (no decision needed unless the
  owner objects).

**2. `fno/quotes/recorder.py`: the pushback is ACCEPTED.**
- It is "recorded, not byte-checked, behaviour locked by the golden cases" (v2), and A7, A5 and O6 already changed it
  after passes.
- The store-only alternative is worse, as the builder shows. A raise ends `record()` with no retry and no reason. A
  swallowed error makes an attempt canonical while its file exists nowhere.
- Condition: the change is only the guarded save, plus `raw_file_saved: false` on failure. A complete attempt's files
  stay byte-identical (`test_recorder_baseline.py` unchanged), and `tools/forecast_live_golden.py` passes unchanged.
  `market_levels.py` is not touched.

**3. The 14 Oct file: `git rm` after a verified Drive copy is ACCEPTED.**
- The owner's row says it "stays in history (never rewritten)", and `git rm` keeps it at 5c22bcc.
- Every reader of that day keeps working:
  - the replay exports the pack commit's parent, which still holds the file;
  - desk meeting 2 reruns at its own commit;
  - live readers find the sidecar without `raw_file_saved`, which counts as saved, and read the hash-checked Drive
    copy.
- The routine's "never delete a recorded attempt" rule binds the routine, as the text says.

**4. `spot` in the public sidecar: noted as the orchestrator's decision, not the owner's.** It is a public index level
and no option quote, so it is acceptable (reasoning only). The record should label it as the orchestrator's decision.

## Story-text check

Correct and complete:
- the split table;
- the store design (lazy private store, hash-checked `get`, loud and distinct errors, `None` only for "no file");
- the reader table and the call-site table, the call-site table (my grep of `fno/` finds the same 8 files calling
  `build_quote_store`; the ninth row, `fno/quotes/cli.py`, reads the folder directly today, as the table says);
- Drive-down handling (never to the repository, never spooled, retry to 15:10, "none", one alert, exit 1, the error's
  type only in the public sidecar);
- the record-scan rule plus `.gitignore` plus a tree test;
- the gap list;
- the "found outside scope" items (E2b by the owner's "8 A", the forecast job now failing closed instead of falling back
  to NSE: stated for the owner).

## Should-fix

**1. Criterion 6 contradicts the design.** It says "No file in the G1 v1, v2 or v3 freeze tables changes". But the
design changes `fno/quotes/recorder.py` (v2's "recorded" table) and `fno/forecast_scoring/wiring.py` (v3's), which
rulings 1-2 accept. As written, the code would fail its own criterion, or the criterion would be read loosely. Fix: "no
**byte-checked** file of the G1 v1-v3 freezes changes; the two recorded files change only as rulings 1-2 allow, with
the golden recompute, the A4 baseline test and the Q5 wiring test unchanged and passing".

**2. The routine's Drive settings must be a merge condition, not "to be checked".** Found-outside-scope item 3 says
the 3 pm routine's environment "was not checked". If it lacks the four settings, every day after the merge ends "none":
- no canonical snapshot;
- so no G1 live pack;
- and no E2/C4/Book 1 inputs.
Quality rule 8 also requires an end-to-end run after the merge. Fix: add a criterion. Before the merge, a run in the
routine's own environment shows the Drive settings are present and a write-and-read of a test file in the raw area
works, without printing a value. After the merge, the first real 15:00 run's result line and Drive hash check go in the
log. If the settings are missing, the owner adds them first and the merge waits.

## Minor

1. `failures` holds provider exception texts in the public sidecar ("not proven price-free"). Record the exception
   type plus a fixed message, as already done for Drive errors, or add a test that no number shaped like a price
   appears in `failures`.
2. `replay_quote_store`: a pre-A4b commit's own file should also be checked against its sidecar's hash, so both paths
   share one rule.
3. Process: the orchestrator reports that the builder wrote code before this check (quality rule 1 says code starts
   after it). Its evidence counts only once reproduced on the pushed code.

**Verdict: FAIL for d1c2d06f1b01539c5903671b12f1d5bad4c14674** (story text), on should-fixes 1-2, both wording and
criteria only. Rulings 1-3 stand for the code check. A re-check needs only the A4b section.
