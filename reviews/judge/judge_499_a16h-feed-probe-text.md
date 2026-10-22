# Judge 499: A16h story text, a read-only probe of Groww's websocket feed

**Scope:** story/a16h-feed-probe at 2385ac62 (A16 builder session 01VK88LxJvV1Gi7Wbr3D4fzp), the story text only:
`docs/stories/A16-intraday-quote-recorder.md` section A16h and its register row. Judge I. Lane 1 (an outside service,
Groww), text first. Round 1 of 2.

**Verdict: FAIL.** 2 should-fixes, 2 minors. The design and the read-only guard are right; two windows put A16's own
marks, and with them the forecasts, at risk.

## Checked against the sources
| Point | Result | Evidence |
|---|---|---|
| The owner's decision | MET | DESK_DECISIONS 23 Oct, "Live data: test the Groww feed first"; research note `research/school/probes/2026-10-23-live-data-feeds.md`: buy nothing, a probe from Tue 27 Oct, never on 23 or 26 Oct |
| The allow-list matches the SDK | MET | the installed `growwapi.GrowwFeed` has exactly 20 public names: the 11 the text allows plus the 9 account-reading names it refuses. `__init__(self, groww_api: GrowwAPI)` takes the trading client, so building it only in the composition root is right |
| The pattern to reuse | MET | `fno/intraday/read_only.py` `ReadOnlyGroww` (a `__getattr__` allow-list, frozen `__setattr__`) |
| The orchestrator's two conditions | MET | `alongside` is capped at 1,000 and stops on any 429; the account names are named in a test (criterion 1) |
| No values, no schedule | MET | counts and times only; the note is written by hand; no schedule or workflow |

## Findings
1. **Should-fix: the `ramp` window sits on A16's 11:15 mark, while the text expects throttling.**
   - A16 marks every 15 minutes (A16 story line 141). A mark with no usable level voids that session's RV (line 201), the input of v4 and G14's forecasts.
   - The text's own known limit says a ramp to 3,000 "may draw throttling on Groww's side". On one shared key, that can cost the 11:15 mark, and so the day.
   - Fix expected, either:
     - ramp outside market hours, if a subscription refusal can be seen then (the text says how that is judged); or
     - ramp between two marks with a hard stop at least 2 minutes before the next one (e.g. 11:16-11:28), also stopping at once on any 429.
2. **Should-fix: `alongside` needs a go/no-go gate set by that day's morning evidence.**
   - Its 429 stop sees only the probe's own calls; the recorders' failures are invisible to it.
   - Its sign-in shares the recorders' key. Coexistence was seen only outside market hours (15 Oct).
   - A lost 3 pm capture costs a session of the desk, the school's five roads and G13.
   - Fix expected:
     - run `alongside` only if the same day's `coverage` run (which overlaps A16's 10:30 mark on purpose) left that mark and the 10:45 mark clean: no 429, nothing missing;
     - the probe signs in before 14:50 and never during 14:55-15:13;
     - a missed condition means no `alongside` that day, written in the note.

**Minor:**
- (a) `dir(GrowwFeed)` has no `place_`, `modify_`, `cancel_` or `create_` name today, so criterion 1's test of them is empty. It should also try such names itself (e.g. `place_order`).
- (b) The probe note should give coverage by class (index × expiry × option type: subscribed, ticked), not a per-strike list.

## Notes
- The terms question (whether Groww allows read-only use) stays open by the owner's choice (22 Oct). The text says so.

## Addendum 1: text round 2 at 59069906

**Verdict: PASS (text).** The code may start; the code round is judged against criteria 1-6 as now written.

- **Finding 1: ACCEPTED.** The ramp runs only from 11:17:00 to a hard stop at 11:28:00, and stops on any 429. A16's mark measures 53-57 s (A16 story, "One snapshot, measured"), so it clears the 11:15 mark with about a minute to spare, and the 11:30 mark by 2 minutes. Unfinished steps move to the next day. Choosing between marks over after-hours is reasoned: whether a refusal shows with the market closed is unknown.
- **Finding 2: ACCEPTED.** `alongside` runs only after a clean 10:30 and 10:45 A16 mark from that day's `coverage` run, signs in and subscribes before 14:50, and makes no new sign-in during 14:55-15:13. A missed condition means no run that day, with the reason noted. Criterion 3 now tests the refusal.
- **Beyond the ask:** every plan stops on its own 429 or at its hard end time (criterion 3).
- **Minors (a), (b): ACCEPTED.** The test supplies the trading names itself; coverage is reported by class.
- **For the code round:** I will plant faults on the gate (a 429 in the ledger, a missing mark, a start at 14:51), on the hard end times, and on each allowed and refused name.

## Addendum 2: the ramp's new window at f1b4fca9

**Verdict: PASS (text), with one condition for the code round.** f1b4fca9 changes only the ramp's window, as the
orchestrator directed. First choice: after the close, from 15:45, once A16's 15:30 mark is on `main`. Fallback, if Groww
refuses subscriptions after hours: 10:50:00-10:58:00 chunks, between the 10:45 mark (about 53-57 s) and the 11:00 mark.
Both windows avoid every A16 mark. Reading a refusal at 500 twice as "closed market", not as the limit, is sound.

- **Condition (to hold in the code):** A16b's candle catch-up (`intraday backfill`) also uses Groww on the shared key, from 15:33 in the daily run (CLAUDE.md, O1 step 2).
  - The after-close ramp must not start until that day's catch-up step is recorded done in `journal/runs/<date>.json`.
  - A ramp started early refuses with one named line, with a test.
  - I will plant faults on it in the code round. The builder may add the line to the text then.

## Addendum 3: the orchestrator's two questions on f1b4fca9

1. **Does 15:45 collide with other Groww users? Yes, possibly.** A16b's catch-up starts at 15:33 on the same key. That is Addendum 2's condition for the code: the ramp starts only once the day's catch-up is recorded done.
2. **Is a refusal at 500, twice, a sound reading of "market closed"? Not by itself.** It cannot tell a closed market from a real limit under 500. That day's `coverage` run already held about 400 subscriptions, so a limit between 400 and 500 would look exactly like "closed". Second condition for the code:
   - The after-close ramp's first step is small (50). A refusal at 50, twice, reads as "closed market".
   - 50 accepted but 500 refused reads as a limit under 500. The ramp then halves its way down from there (e.g. 250, 375, ...) and reports the bounds; it is never read as "closed".
   - In the fallback window, a refusal at the first step is reported as a limit, since the market is open.
   - Tests: a fake feed that refuses everything gives "closed"; one that refuses at 450 gives "limit between 400 and 450" (or the bounds reached).

## Addendum 4: instrument tokens at 214bdeb7

**PASS (text).** The tokens come from the SDK's `INSTRUMENT_CSV_URL`. In the installed SDK that is
`https://growwapi-assets.groww.in/instruments/instrument.csv`, read with a plain `requests.get` and no credentials
(`growwapi/groww/client.py:115,179`), so it spends none of the key's limits. The at-the-money strike comes from 4
`get_quote` calls through the existing `ReadOnlyGroww`, with no change to the allow-list. Two conditions for the code:

- **The URL is read in the composition root (or copied into a named constant there), never by naming `GrowwAPI` elsewhere** (criterion 2).
- **In `alongside`, the instrument list and the 4 `get_quote` calls happen before 14:50**, with the sign-in. Nothing touches the key during 14:55-15:13.

## Addendum 5: code round 1 at ef896e21 (diff 214bdeb7..ef896e21)

**Verdict: FAIL.** 3 should-fixes: the three code conditions of Addenda 2-4 are not in the code. Criteria 1, 2, 4 and
5 are met, and criterion 3 partly.

**Met (my checks):**
- **The guard:** `ReadOnlyFeed` lets exactly the 11 names through; the 9 account names and 4 supplied trading names are refused; it cannot be changed. The test pins the SDK's own name list. 4 plants caught.
- **The gate:** `feed_gate.py` reads A16's ledger (`mark_ist` "10:30"/"10:45", status, failures, recorded against expected) and runs before any sign-in. 3 plants caught.
- **The plans:** each plan's window and cap are checked; any error, a 429 included, stops the plan, unsubscribes everything and is named by class only. Plants caught: the window moved to 14:51, the cap at +1, the unsubscribe dropped, a wait past the end.
- **Gates (my run):** full `pytest -n auto` 11,705 passed, 16 xfailed, 0 failed; ruff check and format, check_imports clean.

**Findings:**
1. **Should-fix: the after-close ramp does not wait for A16b's catch-up (Addendum 2).** Nothing in `feed_cli.py` or `feed_probe.py` reads `journal/runs/<date>.json`. The `ramp` plan may start at 15:45 while the catch-up still uses the shared key.
   - Fix expected: refuse to start until that day's catch-up step is recorded done, with one named line and a test.
2. **Should-fix: the ramp cannot tell a closed market from a limit under 500 (Addendum 3).** `RAMP_STEPS` starts at 500, and a refusal at 500 is reported as plain "failed".
   - Fix expected: start at 50 after the close; a refusal at 50, twice, is "closed market"; 50 accepted with a later refusal halves down to its bounds.
   - Tests: a feed that refuses everything, and one that refuses above 450.
3. **Should-fix: a late `alongside` start signs in and quotes inside 14:55-15:13 before it is refused (Addendum 4).** `cmd_feed_probe` builds the client (`build_feed_probe`, a sign-in) and calls `get_quote` four times (`build_universe`) before `probe.run` checks the window.
   - Started at 14:56, it touches the shared key in the recorders' window and only then refuses.
   - Fix expected: check the plan's window in the command before any sign-in, as the gate already is, with a test whose clock reads 14:56 and which shows no sign-in.

**Minor:**
- Plant `while clock < end + 1 minute` hangs the tests instead of failing them (the fake clock stops at the end). A hard-end test should fail, not hang.
- `feed_cli.py` cuts `alongside` to its first 1,000 instruments instead of refusing more. That is safe, but the sample is whatever comes first in the universe; the note should say which classes it holds.

**Plants:** 11 planted: 10 caught, 1 hangs (minor above).
