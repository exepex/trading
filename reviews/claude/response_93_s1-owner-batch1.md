# Response 93: S1 owner batch 1 (the owner's decisions of 14 Oct 2026): builder's claims

Branch `story/s1-owner-batch1`, lane 1. Builder: Claude, 14 Oct 2026. Exactly the orchestrator's three items, from the
owner's rows in `docs/DESK_DECISIONS.md` (main 3ad96bc).

## 1. `research/evaluation/PROTOCOL.md`: five items decided by the owner

| Item | Decision | Text change |
|---|---|---|
| `uncertainty_criterion` | 120 trading days, as proposed | status only. The reason now records that the owner chose this against the orchestrator's one year plus t-check, and keeps the known weakness: about 6 blocks of 20 days, so the bootstrap claims too often (some evidence). The t-check is not added: it is with the owner. |
| `catastrophic_loss_strategy` | as proposed, the cumulative rule included | status only |
| `ai_cost_allocation` | usage share, as proposed | status only |
| `reporting_per_version` | open question 1, option A | new first bullet: version 1 is frozen only once the S2, S3, F8 and F9 code exists, and every decision before that freeze is pilot evidence |
| `frozen_files` | open question 1, option A | the hashes-only version 2 path is removed: the S2, S3, F8 and F9 code is listed before the freeze, and version 1 is not frozen until all of it exists. The reason is rewritten to match. |

The header and the open-questions section are updated:
- Question 1 is decided (option A).
- Question 2 is decided as 120 days. Whether to add the t-check alongside is still open with the owner.

The other 13 items stay "proposal, owner decides".

**Checks:**
- `python -m fno evaluation check` exits 0 ("complete").
- `--decided` exits 2 and lists the 13 open items.
- `tests/evaluation/test_completeness.py` now pins exactly those 5 decided items (it previously asserted that nothing
  was decided).
- S2's test that ties `fno/scoreboard/uncertainty.py` to this text still passes.

## 2. The cumulative strategy pause: it was not built; now it is

**Not built before this change.** E6's `fno/scorecard/pauses.py` had only the per-trade catastrophic-loss rule and the
live-feature drift.

**Built:** `cumulative_losses` in `fno/scorecard/pauses.py`, wired in `fno/scorecard/run.py` next to the existing
rules, so it uses the same `AutoPauser`: `paper -> paused` by `hard_loss_rule`, with one #fno-desk line. The rule
counts exactly the trades the per-trade rule counts:
- for an approved version, its **book** trades (completed or unwound) closed on or after its latest approval, in
  every book together;
- it fires at realised C1 net `<= -3 x catastrophic_loss_rs` (`CUMULATIVE_CAPS = 3`; Rs 30,000 at Rs 10,000);
- for a shadow (research) version, its own trades are counted, and it is alerted only on a day one of them closes,
  never paused.

**Tests** (`tests/scorecard/test_cumulative_pause.py`):
- five losses of about Rs 6,600 each, across two books, pause the version; four do not;
- exactly 3 caps pauses, and a paisa less does not;
- losses closed before the latest approval do not count;
- an approved version's shadow-account trades do not count;
- a shadow is alerted on a closing day only, and never paused;
- a rerun pauses nothing twice.

**Mutations:** 7 of 7 caught, plus removing the wiring:
1. 4 caps instead of 3;
2. `<` instead of `<=`;
3. no approval-date filter;
4. no sum across books;
5. a shadow alerted every day;
6. no shadow alert;
7. shadow trades counted for an approved version.

The first round caught 5 of 7. The boundary and shadow-trade tests were added for the two survivors.

## 3. `risk.stressed_margin`: multiplier 1.45, by hand

`config.yaml`:
- `multiplier: 1.45`;
- `source: "reviews/claude/response_77_a14-nse-margins.md (largest held-position rise over three crisis windows)"`;
- `as_of: 2026-10-14`;
- `max_age_days: 30` (unchanged).

**C2 now accepts a valid proposal.** `tests/risk/test_manager.py` runs the app's own wiring with the repository's
stressed-margin settings unchanged, plus a fresh margin row as a fixture. The trade opens, and the record names
multiplier 1.45 and as_of 2026-10-14.

**What `max_age_days: 30` means, plainly:**
- The factor is valid while (day - as_of) is at most 30 days. So it is valid from 14 Oct up to and including
  **Friday 13 Nov 2026**; a test proves a trade opens that day.
- From **Saturday 14 Nov** (so in practice from the next session, Monday 16 Nov), C2 refuses every new trade in every
  book. The reason is "stressed margin multiplier of 2026-10-14 is not valid on <day>", and a test proves it.
- This is fail-closed: nothing is placed and exits still run. It is silent beyond the refusal reason: there is no
  advance alert.
- To keep trading, someone (the owner, or a monthly recompute from the 2020 archive as the decision row suggests)
  must enter a new `as_of` (and factor) before then.
- C4 reads the same setting with the same age rule, so it refuses too.

**Plainly, today:** even with the factor set, **a real trade is still refused**, because
`research/data/margins/margins.csv` holds only its header. A run of the real wiring gives "no margin recorded for SF
width 200 on or before 2026-10-13". Rows arrive once A14's job writes them (its broker check passed today). So the
factor is no longer the blocker; the margin rows are.

## 4. Gates

Full suite (token unset), `ruff check fno tests tools`, `ruff format --check` and `python tools/check_imports.py`:
the results are in the commit message and the message to the orchestrator.

## 5. Noticed, not changed (outside the three items)

`research/data/margins/README.md` still says MarginRoom "leaves exactly what a broker that nets the premium leaves
free". Since the funds-at-entry change (response 90), C2 also requires Groww's funds at entry. This is a one-line doc
fix for lane 2.

## Addendum 1: judge 94 (FAIL on one must-fix): should-fix 2 done, the must-fix waits for the owner

- **Must-fix (the cumulative pause's window):** the judge is right that the window is implied, not decided. The code
  counts trades since the version's latest approval, so an owner's re-approval restarts the count; the protocol text
  does not say so. The orchestrator has put the question to the owner (restart the count, or a lifetime total).
  **Not changed yet.** Once the owner answers, I write the window into `catastrophic_loss_strategy`'s value, or
  change `cumulative_losses`.
- **Should-fix 2 (done):** `config.yaml` now names the rule and the windows behind 1.45, so the 13 Nov renewal can
  recompute it:
  - the rule: the largest rise of a held position's NSE margin over its holding, any structure and width, on NSE
    `i1` SPAN files, rounded up to the next 0.05;
  - the windows: Jan-Apr 2020 COVID (1.265), May-Jun 2024 election (1.407 on BF 300 entered 5 Jun, the largest),
    and Sep-Oct 2026 calm (1.127);
  - where it is written: response 77, section "Stressed-margin factor". The `source` value names that section.
