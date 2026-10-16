# Judge 282: G10 part 2 (b1), the release record, commitment times and the v4 fire workflow (story/g10-part2b-release at 74a604d2)

Judge B, 16 Oct 2026. Lane 1 (a workflow, Drive, the deadline). Text: judge 274 addendum 1. Builder: G10
(01VK88Lx).

**Verdict: FAIL.** One should-fix: the new workflow throws away the fire log.

## What holds

| Item | Result | Evidence |
|---|---|---|
| The release record (section 2) | MET | part 1's day format plus `pack_path`, validated by G8's own `parse_day` (one rule); a `pack_path` that does not fit the label is refused; `publish` writes the pack, then the record, through O9's `DataStore` (write-once); a `system_late` day writes the record only |
| Readers only through the verified cache | MET | `ReleasedPacks` needs a receipt, then `DriveCache.sync`, and refuses on any problem for that path (`NotReleased`); the pack is re-read with `read_pack` against the released SHA |
| The 15:10 deadline (section 5) | MET | `CommitmentTimes` over O8's evidence (F1's push receipts); an unknown or offset-free time raises, never guessed; 15:10:00 counts, 15:10:01 is a miss (UTC input tested). My plant (`<=` to `<`) fails 1 test |
| The fire workflow's trigger (section 6) | MET | a push of `receipts/data/v4/days/**` to `main` only, no schedule (test), and today's IST receipt only. My plant (the old path `receipts/v4/days/**`) fails 1 test |
| The text correction `receipts/data/v4/days/**` | **ACCEPT** | O9's `DataStore` puts every file under the `data` area, so the receipt is `receipts/data/v4/...`; the test computes it from O9's `ReceiptFolder`. My judge 274 text had the shorter path |
| Composition root listed in CLAUDE.md | MET | `fno/v4_pack/wiring.py` |

## Should-fix: the fire log is never committed

`v4-fire.yml` runs `python -m fno ai fire --day <today>` and asks for `contents: write` "for the fire log", but no
step commits or pushes anything. `ai fire` does not commit its own log (`fno/ai/fire.py`: "the fire log ... committed
with the records after 15:15"). In v2, forecast-capture's commit step does it (`git add research/forecasts # ... and
the fire log`).

On this new job the log dies with the runner. Everything downstream reads it:
- `collect` and `reveals-ready` (which books were fired);
- BG1's `capture_coverage.fired_sessions`;
- F8c's not-captured alerts (judge 276).

A v4 fired day would look unfired: no alert, and the meter would not see the session.

The fix is the builder's design. Either a commit-and-push step for the fire log path (`git pull --no-rebase` first,
the record scan on), or a stated and tested hand-off to the job that commits it, plus a test that the workflow commits
the log's path.

## Merge timing (agreed)

The workflow calls G11's `ai fire --day`, which is not on `main` yet. Nothing pushes a release receipt until part (b2)
runs in the routine, so it cannot trigger early. Still, merge (b1) only after G11's v4 fire lands, as the builder
proposes. (b2) also waits for the orchestrator's A2 decision (judge 274 note).

**Gates (run by me on 74a604d2):** 7,801 passed, no failures. `ruff check`: clean. `ruff format --check`: 1,407
files already formatted. `check_imports`: clean.

## Addendum 1: story/g10-part2b-release at be7322b1 (number 282.1, claimed with `tools/claim_number.py`)

**PASS.** The should-fix is met:
- `v4-fire.yml` sets a commit identity with the record scan on (`core.hooksPath .githooks`) before the fire.
- After the fire (`!cancelled()`, only on a day with a release), a "Commit the fire log" step runs
  `git add research/forecasts/ai_v4`, commits when something changed, then `pull --no-rebase` and `push origin
  HEAD:main`. There is no `--no-verify`.
- A test pins the order, the path, the pull and push, and the hook config. My plants (the commit step removed; the
  hooks line removed) each fail 1 test.

The fire line is now `ai fire --protocol v4 --day`, since plain `ai fire` stays v2's until the freeze (G11).

**Merge conditions (recorded):**
1. Merge only after G11's v4 fire lands. Both `--protocol v4` and the fire-log path come from G11's branch.
2. G11's own test must check that `fired_v4_path` lies under `research/forecasts/ai_v4/`, the folder this workflow
   commits. The builder has asked G11; G11's code verdict will check it.

**Note:** if the fire dies before writing any log, `git add` of a missing folder fails the step. The failure alert
then posts once, which is the same outcome as the failed fire.

**Gates (run by me on be7322b1):** 7,802 passed. `ruff check`: clean. `ruff format --check`: 1,407 files already
formatted. `check_imports`: clean.
