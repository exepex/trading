# Story REH1: rehearsal mode, a recorded day replayed through every real step

Owner: the O1/O2 builder (session_014zYLf18PgCzR7YoHs1X5Dp). Lane 1 (Drive, Slack and git): two judges, as the
orchestrator set. Ordered by the orchestrator on 24 Oct 2026 from the owner's direct ask:

> "Once all issues are fixed. Then run dry-run again. I want dry-run to be run successfully and generate all type of
> data and reports ... and send to slack for review."

The owner's two choices (through the orchestrator, 24 Oct):

1. Rehearsal data goes to a separate Drive folder, `dryrun/`, which the real system never reads.
2. Reports go to the normal channels: the card and alerts to #fno-desk, the forecast editions to #fno-forecast and the
   intraday lines to #fno-intraday. Every post's first line is bold: "DRY RUN, <day> replay, not a real trading day".

## Why (strong evidence: `docs/dryruns/DRY1_2026-10-23.md`)

DRY1 could check 23 Oct only by re-reading outputs. It could not run the day, for three reasons:
- `daily run` has no dry-run mode (W2);
- every time window is on the wall clock (W1);
- every writer writes the real record (W6).

Its 56 rows are verifications, not a run. REH1 makes "run the day again" one command that is safe by construction, not
by a guard bolted on afterwards.

## The commands

```
python -m fno daily run --rehearse --day 2026-10-23
python -m fno rehearse preopen --day 2026-10-23     # A22's two commands, as the 08:36 routine runs them
python -m fno rehearse morning --day 2026-10-23     # FL1-1d's morning steps (1b and 2)
python -m fno rehearse evening --day 2026-10-23     # FL1-1d's evening steps (1c and 2)
```

Each prints a run id first: `rehearsal <day> <run_id>`, with run_id = UTC time plus 6 hex characters. A rehearsal of
a day that is not a session refuses with one line, as the real run's calendar rule would.

## Design: one rehearsal composition, nothing spread through the steps

**The rule (design for change):**
- Every difference from a real run is an adapter chosen in the composition roots, at the seams O2's end-to-end suite
  already names (`tests/e2e/harness.py`, `OUTSIDE_SEAMS`): the clock, Slack, the owner's Drive, the shared Drive,
  NSE's archive, Groww's capture, the child commands, and the quote store.
- No step, rule or record code asks "am I rehearsing?". A `grep` test pins it: the rehearsal module's name appears only
  in the composition roots and `fno/rehearsal/`.

**How the mode reaches child processes.** `daily run` starts most steps as `python -m fno <command>` children. The
mode is one environment variable, `FNO_REHEARSAL` (name in `fno/constants.py`), set by the rehearsing parent and
inherited by every child. It holds the day, the run id and the replay clock's file. Each composition root that builds
an outside service reads it through one function, `fno/rehearsal/mode.py`'s `rehearsal()`, which returns None in a
real run.

### 1. The replay clock

- **One clock per rehearsal.** It is the real time plus an offset, kept in one file that every process of the
  rehearsal reads (the parent and its children). The offset is set so that the run starts at the routine's time on the
  day: 14:05 IST for the daily run, 08:36 for the pre-open, 08:38 for the morning and 19:53 for the evening.
- **Accelerated waits (reasoning only; owner question Q1).** When the parent waits (the `AnnouncedWaiter`'s waits) and
  no child is inside a capture window, it moves the offset forward instead of sleeping. Every process sees the jump
  together. So a day that takes 14:05-16:05 in real time runs in minutes. Inside a window (14:38-15:13 for the 3 pm
  parts, the 15-minute marks, the pre-open reads) time runs at real speed, so each window behaves as on the day.
- **The seam.** `fno.models.now_ist` gains one injectable clock, set once at process start by the rehearsal wiring.
  This is the single shared change outside the composition roots, and it is a tested, one-line hook. Today's
  `datetime.now(IST)` stays the default.

### 2. Inputs only from the day's recorded, receipted data

- **Drive reads come only from the real root, through a point-in-time reader.** A file is served only if its receipt
  on `main` (O9) was committed before the replay clock's "now".
  - So at 14:05 the rehearsal cannot see the 23 Oct close recorded at 15:40.
  - With no receipt, or a receipt that is too late, the file is "not recorded by <time>", never fetched.
  - The commit times come from git, as O8's push evidence reads them (strong evidence that they exist: O8 and G13b use
    them).
- **Groww's 3 pm and 15:15 captures, NSE's chain, A22's pre-open answers and the 15-minute candles are served by
  recorded-source adapters.** Each implements the same port the live source does (`Provider`, the pre-open sources,
  the candle source) and answers from that day's receipted Drive files. Each answers with the times recorded on the
  day.
- **No live source is reachable.**
  - The rehearsal wiring never builds a Groww, NSE or global-cue HTTP client.
  - A guard adapter on the HTTP layer the sources share refuses any outbound call that is not to Google's Drive read
    or token endpoints, or to Slack's post endpoint.
- **A step whose input was never recorded says so.** It reports `refused` with the code `rehearsal:NOT_RECORDED`
  (O1-status-only's registry), naming the input. It never fetches.

### 3. Every write under `dryrun/<run_id>/`, and git only on a rehearsal branch

**Drive:**
- The rehearsal's owner-Drive store has two parts:
  - a write-once store rooted at `dryrun/<run_id>/`, for every put and every index replace;
  - the point-in-time reader of section 2, for reads of the real record.
- A read checks the rehearsal's own `dryrun/<run_id>/` first, so a step reads what an earlier step of the same
  rehearsal wrote.
- The real root is wrapped read-only: `put` and `replace_contents` raise `RehearsalWriteRefused` before any request is
  made.
- The real system never reads `dryrun/`. A test pins that no real wiring names it.

**Receipts:** receipts are written in the rehearsal checkout, so they go only to the rehearsal branch, never main.

**Git:**
- The rehearsal runs in its own git worktree on the branch `rehearsal/<day>-<run_id>`. The branch starts from
  `main`, with the real day's run commits reverted on it, so the current code meets the day's state before its run.
- "The real day's run commits" are those whose subject starts `Desk run <day> step`, plus the 3 pm parts' commits of
  that day (their subjects are fixed by O1). The list is printed before the run starts.
- `Git.target` (O1-publish-branch's constant, already a constructor argument) is the rehearsal branch. So are
  `GitManifestRecorder`'s, the numbering's and the AI transport's targets, which gain the same injectable target
  (each one line in its composition root).

### 4. Every Slack post labelled

- One decorator per Slack port puts "*DRY RUN, <day> replay, not a real trading day*" as the bold first line of every
  post:
  - `AlertSender` (#fno-desk alerts);
  - `CardPoster` (T1's card);
  - `ReportPoster` (the lab's editions in #fno-forecast);
  - the intraday lines' poster (#fno-intraday).
- Each decorator is a small class in `fno/rehearsal/`, chosen in that port's builder (`build_alert_sender`,
  `build_card_poster`, `build_forecast_poster`, and the intraday builder).

### 5. The guard (acceptance 1-3), in code and in a test

- `fno/rehearsal/guard.py` builds every outside service through the real composition roots with `FNO_REHEARSAL` set,
  and checks four things:
  - every Drive store it gets is the dryrun store, with the real root read-only;
  - every git committer's target starts `rehearsal/`;
  - every Slack sender is a labelled decorator;
  - no live HTTP source was built.
- `daily run --rehearse` and the three `rehearse` commands call the guard before the first step. Any failure stops
  the rehearsal with one line, before anything is written.
- The test plants each of the four breaks and shows the guard catches it.

## What it does not do (said plainly)

- **It cannot replay a source that was never recorded.** For 23 Oct, DRY1 lists these:
  - A22's 09:09 candles (Groww has none);
  - three of A16's marks (the recorder was down 14:15-14:45);
  - Taiex in the global cues.

  Those steps report `rehearsal:NOT_RECORDED`. That is the honest outcome.
- **It does not prove timing under real load.** The accelerated clock skips the waits.
- **It does not test GitHub's push-time checks (W3),** because the rehearsal never pushes to main.
- **It does not replace O11.** O11 is the test suite's replay with fakes, in `tests/e2e_acceptance/`, and it stays.
  REH1 is the production command on the day's real recorded data (split below).

## Split with O11 (one builder per function, to be agreed with session_01FWkBH4zNAEFSEpjUzVEgnd)

- **O11 keeps:**
  - `tests/e2e_acceptance/`: a test-only replay with planted fakes and strict xfails per unbuilt stage;
  - the acceptance list of what is not implemented.
- **REH1 owns:**
  - `fno/rehearsal/`: the mode, the clock, the point-in-time reader, the recorded sources, the label decorators and
    the guard;
  - the composition roots' one-line choices;
  - the `--rehearse` and `rehearse` commands.
- **Shared later, if O11 wants them:** REH1's recorded sources live in `fno/`, so O11's replay can use them in place of
  its own fakes. That is O11's call; REH1 will not edit `tests/e2e_acceptance/`.

## The forecast lab's editions: one composer (agreed with O11's and FL1's owner, 24 Oct)

- `rehearse morning|evening` builds each edition through `fno/forecast_lab/wiring.py`'s `build_composer`, the composer
  the real edition and `lab preview` (FL1-1f) use. REH1 adds no second lab wiring; its label decorator wraps the
  lab's `ReportPoster`.
- So a rehearsal, a preview and the real edition cannot drift apart.
- If REH1 comes to cover all of `lab preview`, the preview can become a thin call into REH1. That needs the FL1
  owner's say first; until then both stay.

## Dependencies

- **O9's read-only index-close fix (DRY1 problem 3)** must land first. Without it, `lab preview` and the lab's close
  source archive a missing file on read. In a rehearsal that write would be refused (section 3) and fail the step,
  rather than write; so REH1's acceptance run waits for that fix.
  - The same holds for the lab's `IndexFileCloses` and `VixSection`, which fetch from NSE and archive a missing file
    (the FL1 owner's note).
  - In a rehearsal both are stopped twice: the HTTP guard refuses the NSE fetch before it is made, and the real
    root's read-only wrapper would refuse the archive write. Nothing is ever written outside `dryrun/`.
  - On a day whose file is not archived, the step reports refused until O9's fix lands.
- **DR1's staging model** does not block REH1. Rehearsal writes go to `dryrun/<run_id>/` and never reach staging or
  the record.

## Owner questions (through the orchestrator)

- **Q1. The clock.** Accelerated waits (the day in minutes; windows at real speed), or real time throughout (the daily
  run takes its full two hours)? Recommended: accelerated (reasoning only). It makes repeat rehearsals cheap, and the
  windows, where timing matters, still run at real speed.
- **Q2. Which day first.** 23 Oct, DRY1's day? Its gaps are known, so its rehearsal can be checked row by row against
  DRY1.
- **Q3. Clean-up.** Keep `dryrun/<run_id>/` folders and `rehearsal/*` branches, or delete them after the owner's review?
  Recommended: keep them, write-once like the rest, and list them in the rehearsal's last line.

## Parts and estimate (reasoning only)

- **REH1a, the safe frame:** the mode, the clock, the dryrun Drive store with the read-only real root, the git target,
  the four label decorators, the guard and its test, and `daily run --rehearse` for the steps that read only Drive and
  git (the pack, Book 1, decisions, the G13 family, the card). About 2 days of building, then the judges.
- **REH1b, recorded sources:** Groww's and NSE's 3 pm and 15:15 captures, the candles and the closes, so the quote
  parts, the snapshot, fills, exits and A4h's reads run on the day's data. About 2 days.
- **REH1c, the other routines:** `rehearse preopen`, `morning` and `evening`, with A22's and A17e's recorded sources.
  About 1.5 days.
- **REH1d:** the first full rehearsal of 23 Oct, posted to Slack, with a report beside DRY1's comparing it row by row.
  About half a day.

Each part has its own judge rounds. The total is about 6 working days of building, plus judging.

## Acceptance

1. **No real-root Drive write.** With `FNO_REHEARSAL` set, the real root's `put` and `replace_contents` raise before
   any request. Every write lands under `dryrun/<run_id>/`, write-once. Test: a full rehearsal over a fake Drive shows
   the real root's file set unchanged.
2. **No main push.** Every committer's target is `rehearsal/<day>-<run_id>`, and the guard refuses a target of `main`.
   Test: a rehearsal over a local origin leaves `main` unchanged and makes the rehearsal branch.
3. **No unlabelled post.** Every post through each of the four ports starts with the bold label. Test: each port, with
   a planted unlabelled sender, is refused by the guard.
4. **No live source.** The rehearsal builds no Groww, NSE or cue HTTP client. The HTTP guard refuses any other host.
   Test: a planted live call raises.
5. **No look-ahead.** A Drive file whose receipt was committed after the replay clock's now is not served. Test: at
   14:05 the 23 Oct close is "not recorded by 14:05"; at 15:41 it is served.
6. **The recorded day runs.** Over O2's fixture day as a recorded day, `daily run --rehearse` ends `day done` with every
   step that has recorded input, and `rehearsal:NOT_RECORDED` for the rest.
7. **The real run is unchanged.** Without `FNO_REHEARSAL`, every composition root builds what it builds today. The full
   suite passes untouched, and the grep test shows no step reads the mode.
8. **REH1d:** 23 Oct's rehearsal, its Slack posts and its report.

## Claims

To be written per part, with each part's gate results, before its judge.
