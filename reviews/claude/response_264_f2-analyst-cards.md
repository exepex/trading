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

## 4. O9 and credentials (revised after F1t's rule, 16 Oct 2026)

First proposal (withdrawn): the routine saves its seal through `DataStore`, which would need the owner's Drive settings
in an AI session and would let it read any Drive file, including the books' private packs. F1t's rule is that a routine
session has no Drive credentials (as F1's isolation), and that rule is right: it closes the read risk instead of
stating it. So the design now follows the AI books exactly:
- the role's own input items travel in its pointer (capped at 64 KiB like F1t's; over the cap is `not_fired`, never
  truncated), and the collection checks the pointer's hash against the input file in Drive;
- the commitment and reveal are pushed to `main` with `GitMainTransport`, as G5 and F1t do, with receipts by F1t's
  `ObservedPushes`; they move to Drive receipts with the AI books' seal files in O9's step 4, in the same change;
- the input file, the cards file and the audit files are saved by the Actions job through `DataStore`.
No question remains for O9's owner from F2.

## 5. Agreements with F1t and F6/F7 (16 Oct 2026)

- F1t (session_01PLbKH15, `story/f1t-ai-trading-runner` 0a466db6 and 2639b915): one `analyst_cards` item in each AI
  book's pointer (role_set_version, input_sha256, every role's status line, the card when valid or not_applicable), the
  same for both books; `consulted_units` = the unit ids given; role_set_version in the books' D6 rows; F1t extracts
  the shared seal class, F2 reuses it; `CardsOfDay` takes the run's one alert sender, injected.
- F6/F7 (session_01KTAQCD, `story/f6-book3-engine` 30f42af3): `card_id` `<role>/v<n>/<day>` for `cards_used`;
  role_set_version names the registered set (`volatility/v1`, `none` with no role registered).
