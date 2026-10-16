# Response 264: F2 analyst cards, text round (16 Oct 2026)

Builder: session_01WSMMv5nK4wDdktFrudJfXv. Branch `story/f2-analyst-cards`. Story: `docs/stories/F-ai-layer.md`, F2.
Text only so far; the code claims will be added to this file after the judge's text check passes.

## 1. Orchestrator's answers to the four open questions (16 Oct 2026), and what changed

| Question | Answer | Effect on the text |
|---|---|---|
| (a) 14:00 cutoff or a morning run | 14:00 | Item 8 unchanged |
| (b) Model | The books' model for v1 | Item 1: `registered_model` is the books' model |
| (c) F9's cost rule | Agree it with F9's owner (session_01SFDjjZ, paused while it builds F5; text only) | Item 10; section 3 below |
| (d) Repository or Drive | O9's rule: inputs and cards through `DataStore`, receipts in the repository | Items 3, 6, 9, criterion 16; section 4 below |

## 2. One analyst first (the O11 plan's suggestion), with the evidence

Accepted. The first text enabled three roles; the revised text enables one (volatility) and adds the others one at a
time. Reasons:
- **Rule:** `DESK_DESIGN.md` step 4 says AI roles are "added one at a time", each kept only if it adds net value; F9's
  own gap list cites it (design 10).
- **Sample size (F9a's code):** the rotation ablates unit `k mod n` on the k-th decision day, and a verdict needs 30
  changed opportunities. With n units each gets 1/n of the days. Assuming a card changes the decision on 1 day in 5
  (reasoning only; no data yet), the first verdict comes after about 150 decision days with one unit and about 450 with
  three.
- **Cost:** one routine session a day, not three, while books 2-3 record "no trade" until a strategy is approved.
- **Why volatility first (reasoning only):** Books 2 and 3 choose structures and widths (D4's envelope), which depend
  most on implied versus realised volatility; all its v1 inputs are captured today with first-seen times. Positioning
  waits on A8's release-time measurement; equity research has no point-in-time input (A12 keeps no first-seen time,
  A19 not merged).
- **What stays general:** the registry, validator, sealing, collection and cards file take any number of roles, and
  the end-to-end test runs several test-only roles, so adding the next role is one registry entry, its adapters and
  its prompt.

## 3. F9 cost rule (for F9's owner, text only)

F9a charges each consulted unit an equal split of the book's allocated cost, because it assumed roles run as
sub-agents inside the book's session. F2 runs each role in its own routine session, shared by Books 2 and 3. Proposal:
a role's cost per day is its own session's allocated usage (F8 writes one usage row per session), split equally
between the books that consulted its card that day; the book's own session cost is no longer split across units.
Until F9's owner changes the rule, F9a's current rule overstates the units' cost (still an upper bound, as labelled).

## 4. O9 and credentials (for O9's owner)

Following O9 section 5, the seal moves to receipts: the routine saves its commitment and reveal through `DataStore` and
pushes their receipts; the receipt's first push time is the receipt time. The routine therefore needs the owner's
Drive settings, so it could read any Drive file, including the books' private packs (E2c). The store is write-once,
so records cannot be changed; reading is the risk. Proposal: a read-only Drive credential scoped to the `data/` area,
plus a write path limited to the analysts' folder, for AI routines. Until then the limit is stated in the role
version's `isolation` field, as F1 does.
