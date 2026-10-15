# Judge 161: G10 story text, protocol v4 timeline: `story/g10-v4-timeline` 56948259bf2bd5c905eeac9352b3ebd688990a1b (quality rule 1, text only; claims response 152), judge A

**What I checked:**
- the G10 section;
- `PROTOCOL_v4.md` on `main`;
- the owner's rows in `docs/DESK_DECISIONS.md` (164, 166, 180, 184);
- `docs/WORK_REGISTER.md`;
- A16's expiry plan, `fno/forecast/iv30.py`, M1's and G7's inputs;
- REPLAN.

All of it under the simplicity rule and the coordination rule: a duplicate or a contradiction is a FAIL.

## The orchestrator's points

**(a) The 7 PROTOCOL_v4 changes: SOUND, and v4 is not frozen.**
- `research/forecasts/FREEZE_v4.md` does not exist, so the text may change.
- Every "15:00" the story lists is in the protocol: lines 38, 60, 64-65, 84-85, 121, 124 and 132-133.
- Change 5 lands after G9's miss rule (10% caps, lines 186-188) and leaves it unchanged. A late commitment becomes "a
  miss under G9's caps", which is consistent.
- Change 7 adds X and the go-live date to the freeze preconditions, as G8 freezes.
- Criterion 1's text-to-`terms.py` test stops drift.

**(b) The G7/M1 back-fill stays byte-identical: CREDIBLE, and criterion 5 proves it.**
- For M1 I verified it myself in judge 129 addendum 1: the probabilities use VIX and closes up to the previous regular
  session, and the events use announcement dates (no time of day). So the 14:30 cutoff changes no input.
- For G7, `baselines.py:3` reads up to `d-1`.
- Only the capture-time refusal moves, from 15:00 to 14:30.

**(c) X as the 95th percentile: FINE.** It is a flag, never a block (the owner's row), so the choice only sets how often
a day is reported apart: about 1 in 20 at the 95th, 1 in 100 at the 99th. The 95th gives a report with enough flagged
days to read. **Note 1:** compute it on A16b's own checked levels, the close of the candle ending at 14:30 and at
15:15. Those are the basis of A16's live marks, and A16b checked them against 1-minute data. The story says the
"opens" of the 14:30 and 15:15 candles, which is another basis and was checked only at 09:15.

**(d) The A2 days' single-expiry IV30: CORRECT and well stated.**
- `fno/intraday/expiry_plan.py` records the nearest weekly and the nearest monthly (2 chains).
- `iv30.py` interpolates the two monthlies around 30 days, or else uses one monthly with at least 7 days, flagged.
- So an A2 day is usually flagged, or has no value when the monthly has under 7 days left. The label carries it.
  Declining to add a third chain, about 70 more quotes a mark, is the simple choice and is stated.

**(e) "What moves" against the owner's rows: TWO CONTRADICTIONS (should-fix 1 and 2).**
- **Stocks.** The owner's row 166 reads "**Stock option chains recorded in full at about 14:20-14:53, before NIFTY**"
  (owner: "Full set, 14:20-14:53"), at about 8,000 quotes taking about 27 minutes. G10 moves stocks to **15:01-15:13**.
  - That is 12 minutes, which at the safe 5 a second (A16's measurement, `A16-intraday-quote-recorder.md:58-60`) is
    about 3,600 quotes, not the full set.
  - 14:20-14:53 itself collides with row 184's new 14:30-14:40 NIFTY capture on the same Groww key.
  - So the two owner rows now conflict, and G10 settles that silently, against the owner's "Full set". That is the
    owner's call, not a story's.
- **A4c.** G10 moves A4c (BANKNIFTY, FINNIFTY, MIDCPNIFTY, row 180) to **14:41-14:58**. That window contains A16's
  **14:45** mark: about 216 quotes, roughly 50 s, on the same key. The text says the slot "keeps clear of A16's 15:00
  and 15:15 marks" and misses 14:45. Two jobs at once on one key exceed the 5-a-second pace A16 measured as safe (8
  workers gave errors).

**(f) The G10/G11 name clash: REAL (should-fix 3).** REPLAN still names "G10 AI books on the v4 questions" in
`docs/design_v2/REPLAN.md:27,130` and `REPLAN_new_stories.md:51`. This story claims G10 and says REPLAN's becomes G11,
but leaves REPLAN unchanged. So two documents give G10 to different stories, which is the kind of clash the register
rule exists to stop.

## Other checks

- **Simplicity.**
  - One clock, one release and one deadline.
  - Flags rather than blocks.
  - No new chain.
  - v2 is left alone until v4 is live.
  - The "system late" rule is decided by one fact: no pack by 14:40.
- **Register.** G10's own row exists. Nothing else covers the v4 timeline, apart from the conflicts in (e) and (f).

## Should-fix (text)

1. **Stock chains.**
   - Remove the decision from the "what moves" table and put it to the owner as a question, with the numbers:
     - row 166's full set needs about 27 minutes at 5 a second;
     - 14:20-14:53 overlaps the new 14:30-14:40 NIFTY capture;
     - 15:01-15:13 holds about 3,600 quotes;
     - 15:17-15:30 holds about 3,900 (row 166's own figure).
   - Options, for example:
     - a full set before 14:28 (a start near 13:55);
     - a split across 15:01-15:13 and 15:17-15:30, about 7,500;
     - a smaller set.
   - G10 itself needs none of these. It only must not decide.
2. **A4c's slot.** Keep it clear of every A16 mark, 14:45 included: for example 14:41-14:44 and 14:47-14:58, or after
   15:01. Or state the pause, as the stock row does for 15:15.
3. **The name.** Update REPLAN's two files in this story (G10 becomes G11 for the AI books' v4 prompt), so no document
   gives G10 to two stories.

## Note (one line)

1. X's history should use the checked closes ending at 14:30 and 15:15, not candle opens (see (c)).

### Verdict: FAIL for 56948259bf2bd5c905eeac9352b3ebd688990a1b (story text)

- The protocol changes, the labels, the lateness rule and the A2 statement are sound.
- **Three should-fix, all text:**
  - the stock slot contradicts the owner's row 166 (owner question);
  - A4c's slot overlaps A16's 14:45 mark;
  - REPLAN still uses G10.
- **A re-check needs only the G10 section and REPLAN's two lines.** ChatGPT follows the PASS.

## Addendum 1: revision 1 at 4985c228424142f6818d75ced2139d02c8f45d25: PASS

Checked the diff 5694825..4985c22 (4 files: G-forecasts.md, REPLAN.md, REPLAN_new_stories.md, response 152). No code.

**Should-fix items:**
1. Stock chains: **MET.**
   - The 15:01-15:13 row is gone; the table now says "the stock-chain slot is decided by the owner separately".
   - Owner row 166 is no longer contradicted. The slot is still an open owner question, and G10 does not depend on it.
2. A4c and A16's 14:45 mark: **MET.**
   - A4c now runs 14:41-14:44 and 14:47-14:58. That leaves A16's 14:45 mark (about 50 s) and its 15:00 mark clear.
   - Total time is 14 minutes, against 12 before, so the A4c set still fits.
3. REPLAN: **MET.**
   - `REPLAN.md:27` and `REPLAN.md:130`, and `REPLAN_new_stories.md:51`, now say G11 with a rename note.
   - `git grep G10` on 4985c22 finds no other AI-books use outside the story itself.

**Earlier note (c):** **MET.** X now uses A16b's checked closes of the candles ending at 14:30 and at 15:15.

**The builder's added overlap** (A16's 14:30 mark and the new 14:30 capture on the same key):
- The overlap is real. A16 marks every 15 minutes, and the story sets the capture at 14:30.
- The answer is in proportion. Criterion 6's dry run measures both together, and the fallback start (about 14:31) still leaves about 9 minutes before the 14:40 retry end.

**Coordination:** WORK_REGISTER row 37 covers G10 on this branch. No other row covers the timeline, A4c's times or G11.

**Gates on the trial merge with origin/main** (tree 10592e0, clean merge):
- pytest: 5861 passed;
- `ruff check`: clean;
- `ruff format --check`: 1072 files formatted;
- `check_imports`: ok.

**Notes (one line each, no fix asked):**
- The table row label "AI books' v4 prompt (REPLAN's "G10", to be G11)" is now past tense in fact. It could read "(G11)".
- "Two sign-ins on one key coexist (checked 15 Oct)" should carry its label. It is some evidence only: once, outside market hours (`conversations/2026-10-15.md:751`, A16 checklist line 87). Criterion 6's dry run is the real test.
- The stock-chain slot remains an owner decision. It must be settled before any story that schedules stock chains.

**Verdict: PASS.** ChatGPT's review follows, before the v4 freeze.
