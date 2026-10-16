# Judge 303: F2 story text, analyst roles and finding cards (story/f2-analyst-cards at 47fcb523)

**Verdict: FAIL on the story text: 1 blocking finding, 1 should-fix and 2 minor.** The request named f7dd604b
(three roles on, one off). The branch moved to 47fcb523 at 11:26: one analyst (volatility) in v1, inputs and cards
through O9's `DataStore`, following the orchestrator's answers in response 264. I judged 47fcb523.

## The orchestrator's question: one analyst, or three on and one off?
**One analyst is simpler, and complete for v1. I agree with the text at 47fcb523** (some evidence: arithmetic on F9's
rule; reasoning for the rest). I had first leaned the other way, because the roles stay off until the books trade, so
extra roles cost nothing now. The builder's F9 argument changed my view:
- F9 withholds one unit per decision day in turn (`k mod n`), and a unit gets a verdict only after 30 changed
  opportunities. With n units, each needs about n times the decision days before its first verdict.
- Three roles therefore triple the wait for any verdict (about 21 months instead of about 7, at the text's labelled
  assumption that one card in five changes a decision).
- The mechanism (registry, validator, sealing, cards file, `CardsOfDay`) is role-generic. Adding a role later is one
  registry entry, one adapter set and one prompt, which is "added one at a time" as in `DESK_DESIGN.md` step 4 (line
  254).
- Volatility is the role whose inputs all exist today, with first-seen times: VIX, the previous pack, RV20.

The owner should hear one thing plainly: three of design 7.2's four analysts are deferred, and come only on the
owner's word.

## Findings

**Blocking 1. The routine would hold the owner's full Drive credentials.** Strong evidence.
- Section 13's "Credentials" says: "under O9 the routine needs the owner's Drive settings to read its input and save
  its seal, so it can read any Drive file, including the books' private packs (E2c)".
- That breaks design 7.5 (an AI role never "reads a credential") and F1's criterion 6 ("the session receives no secret
  and no credential", F-ai-layer.md line 68).
- It also breaks book isolation: a shared analyst could read Book 2's and Book 3's private accounts.
- F1t, on the same platform, says "the session cannot read Drive (no credentials)" and sends its inputs in the
  pointer.

Fix, without waiting for a scoped credential:
- Send the role's input in its pointer. It is small: 60 VIX closes, one pack's fields, one summary line. Carry its
  SHA-256 and the Drive receipt's hash, which the routine checks.
- Seal by pushing the commitment to the repository, as G5's forecasts do.
- Let the collecting Actions job, which already holds the Drive settings, move the revealed card into Drive and commit
  its O9 receipt.
- The routine then needs no credentials, and every file still ends in Drive with a receipt.

**Should-fix 2. The receipt rule's source of truth differs from F1t's, and the text does not say why.** Strong
evidence. F2 times seals by "GitHub's push time of the commit that first added its receipt"
(`fno/ai/history.py`/`receipts.py`). F1t uses observation by fetch at the deadline (judge 82: a commit's own date is
never trusted). Both sit behind `PushReceipts`, which is acceptable.

Fix: F2 must state which adapter it uses and why it is safe without a fetch (the Actions job's token, GitHub's
recorded push time). It must also show that the reveal time 14:40:10 and the cards file at 14:55 still precede F1t's
`ai_fire` read under the 30 s bound.

**Minor.**
1. Criterion 15 ("one mechanism") should name the shared helper F1t also extracts from `fno/ai/book.py`, after F8c,
   so the two extractions are one change, not two.
2. `previous_pack`'s first-seen time is "its committed time (the pack's receipt after O9)". Say which value is used
   before O9 moves G2's pack (the commit's committer time is not a receipt), so criterion 2's "at the cutoff" test has
   one rule.

## Owner expectations
- Every failure alerts and is recorded (row 246): criteria 8-9.
- Never blocks the books: criterion 9.
- Point-in-time only: criterion 2.
- No UI: in scope.
The credentials point is the one break.
