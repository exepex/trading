# A16: the owner's checklist for the 15-minute recorder routine

The owner creates this routine; no builder or orchestrator creates, changes or deletes a schedule. It records NIFTY
spot, the near future and the weekly and monthly chains every 15 minutes from 09:15 to 15:30 IST (26 marks). Raw quotes
go to the owner's Google Drive. Only derived files go in the repository: slot rows, the session's realised variance and
the heartbeat. It is research data only: it never places, modifies or cancels an order. Design and rules:
`docs/stories/A16-intraday-quote-recorder.md` (trigger design, criterion 15, amendments 1-3, A16c, A16e).

## 1. Settings the routine's environment needs (names only; values are never written in a file or in chat)

| Name | What it is for |
|---|---|
| `GROWW_API_KEY`, `GROWW_TOTP_SECRET` | Groww sign-in. The recorder makes read-only market-data calls only, through an allow-list |
| `FNO_GDRIVE_FOLDER_ID`, `FNO_GDRIVE_OAUTH_CLIENT_ID`, `FNO_GDRIVE_OAUTH_CLIENT_SECRET`, `FNO_GDRIVE_OAUTH_REFRESH_TOKEN` | The owner's Drive, where the raw snapshots are stored (A9). Without all four the run stops before the first mark and alerts "stopped with RuntimeError" (it prints the class name only, never an error's text) |
| `FNO_SLACK_BOT_TOKEN` | Alerts to #fno-desk (`C0C89E8QCCD`) |
| Push access to `main` of `exepex/trading` | The run commits and pushes its own files after every mark |

The 3 pm recorder's environment already holds these (its Groww and Drive settings are the same names), so the
simplest choice is the same environment.

## 2. Schedule (IST)

**Seven fires a day, each at 52 minutes past the hour, from 08:52 to 14:52 IST, every day of the week:**

    CRON_TZ=Asia/Kolkata 52 8-14 * * *

- **Why :52 and not :00:** each fire must be running before its hour's first mark. Starting 8 minutes early leaves room
  for the setup (about a minute) and for the scheduler's own delay. The run waits for each mark itself.
- **Why every day, like the 3 pm recorder:** NSE's session calendar (A7) decides the day. Special weekend sessions are
  recorded; a holiday, weekend or muhurat-only day prints "not a trading day" and exits within the setup time. Weekdays
  only (`1-5`) would miss special weekend sessions (6 in 2017-26, 4 with normal timings). **Cost:** 14 short sessions a
  week that do nothing. If the owner prefers weekdays only, say so; the trial then notes any special session missed.
- **Overlap (the story's design):** each fire covers its hour's marks plus the next hour's first mark, so every hour
  boundary has two runs. The fire at H:52 runs to (H+2):05 IST; the last fire (14:52) runs to 15:35. A fire that starts
  late or dies loses at most the marks only it covered.
- Each fire runs about 73 minutes. The longest allowed routine session is not documented anywhere I could read; the
  trial measures whether runs finish.

## 3. The routine prompt (paste as written)

> Omenix F&O 15-minute recorder (story A16). Research data only: never place, modify or cancel orders; never print or
> store a secret. In `exepex/trading` on `main`:
> 0. First, before anything else: `git fetch -q origin main && git checkout -q --detach origin/main`. If it fails,
>    post its error line to #fno-desk (`C0C89E8QCCD`) and stop (story DR1, owner 23 Oct 2026).
> 1. `sh tools/routine_setup.sh --groww` (installs and checks the Groww SDK; it stops loudly if it cannot).
> 2. `git pull --no-rebase origin main`.
> 3. Work out the end time and run the recorder in the background, then wait for it to finish:
>    `H=$(TZ=Asia/Kolkata date +%-H); if [ "$H" -ge 14 ]; then UNTIL=15:35; else UNTIL=$(printf '%02d:05' $((H + 2))); fi; python -m fno intraday run --until "$UNTIL"`
>    It waits for each 15-minute mark up to that time. After each mark it writes the slot row and the heartbeat, and it
>    commits and pushes its own files in `research/data/intraday/` (`slots/`, `rv/`, `heartbeat.json`). At the 15:30
>    mark it also writes the session's realised variance. On a day that is not a session it prints "not a trading day"
>    and stops.
> 4. If a line says "NOT committed" (and not "NOT pulled or committed"), commit and push only the recorder's own paths
>    by hand: `git pull --no-rebase origin main`, then (push with `git push origin HEAD:main`)
>    `git add -- research/data/intraday/slots research/data/intraday/rv research/data/intraday/heartbeat.json`, commit,
>    push. Never add the whole folder; never bypass the record scan (`--no-verify`).
> 5. If a line says "NOT pulled or committed: ... staged that are not the recorder's", change nothing: the run has
>    already alerted, and the owner clears the other files.
> 6. If the command exits 1, post its lines to #fno-desk (`C0C89E8QCCD`) only if it printed "alert NOT sent" (the
>    recorder posts its own alerts otherwise). Note any failure in `conversations/<IST date>.md`, then commit and push it.

## 4. What reaches #fno-desk, and when

The recorder sends these itself (with `FNO_SLACK_BOT_TOKEN`); the routine posts only when a line says "alert NOT
sent":
- **Two bad marks in a row** (missed, late, stale, failed or incomplete): "check the 15-minute recorder (is its routine
  running, does Groww sign in?)". Gaps stay gaps; they are never filled.
- **The run stopped:** "check the 15-minute recorder (story A16): it stopped with <error class> ...", for any
  unexpected error, missing settings included. Only the class name is sent, never an error's text, which could carry a
  secret. If it says `RuntimeError` before the first mark, check the four Drive settings first.
- **A commit refused** because another writer staged files in the checkout (A16e): one alert a run.

## 5. How the first runs are read (by the builder; the owner only tells the orchestrator when the routine exists)

**A16e, rule 8 part 2 (the first live fire):** the first commit the routine pushes to `main` under
`research/data/intraday/` is shown with `git show --stat <commit>`. Pass: it holds only `slots/...` rows and
`heartbeat.json` (plus `rv/...` at the 15:30 mark), and the run printed no "NOT pulled or committed" line. The builder
records it in `conversations/<date>.md` and tells the orchestrator and judge D.

**The trial (criterion 15): the first 5 consecutive recorded sessions.** Nothing counts as recorded history until it
is reported. From the committed files and their git history the builder reports, per session:
- each mark's status (good, missed, late, stale, failed, incomplete) and the session's void share;
- each fire's start delay and run length (from the heartbeat's run times in each commit), and any fire that did not run;
- the pre-open comparison: the close of the last pre-open 1-minute candle minus NSE's official open, or "no pre-open
  value" (amendment 3).
- the day's 3 pm recorder result (recorded, complete or not) and any Groww sign-in error in either run (judge 157:
  the 14:52 fire signs in while the 3 pm recorder runs). Checked once on 15 Oct 2026 at 21:38 IST, outside market
  hours (some evidence): two TOTP sign-ins 35 s apart gave different tokens and both kept answering quotes for a
  minute after the second, so a second sign-in did not end the first. The trial confirms it in market hours.

**Consequence:** if more than 5% of the trial's sessions are void (and later of any 20), the sampling or the trigger
gets a new version and the host question goes back to the owner (design 5.2 and 6.6). The result goes in response
108's claims.

## 6. Owner's steps, in order

1. Create the routine in the same environment as the 3 pm recorder, with the prompt of section 3 and the schedule of
   section 2.
2. Tell the orchestrator it exists, and on which day it first runs.
3. Delete the leftover branch `wip/a16-groww-15min-code` (the builder's session cannot delete remote branches).

## 7. Owner question (24 Oct 2026): step 3 of the routine prompt must name its time limit

**Why.** Since A16i (`fno/intraday/cover.py`, on `main`) the recorder runs one hour past `--until`, up to 15:35. That
makes each fire last up to about 2h43m. The 08:22 fire, for example, now runs to 11:05, and the 08:52 to 12:52 fires
about 2h13m each. Step 3 says only "run the recorder in the background, then wait for it to finish". It names no
time limit, and the session's tool stops a background command at its default limit:
- 23 Oct (`conversations/2026-10-23.md`, "15-minute recorder (story A16), scheduled run"): "First recorder run was
  killed by the default background limit (~10 min) after the 15:00 mark; restarted at 15:05 with a long timeout."
- A run in the foreground is no way out: a foreground command stops after 10 minutes.
- Even the longest background limit, 2 hours, is shorter than a 2h13m or 2h43m fire.

So the step needs the longest limit **and** an immediate rerun when the limit stops it. A rerun is safe: each mark
has one claim, so a rerun skips the marks already taken and never takes one twice. If a fire is cut short with no
rerun, its extra hour is lost and the marks fall back to one fire each (the 23 Oct failure). [some evidence: the
23 Oct log; the 2 h limit is the tool's documented maximum]

**Current step 3 (as stored in both A16 routines, "Omenix F&O 15-minute recorder (A16)" and "A16 recorder 08:22
backup (copy)"):**

> 3. Work out the end time and run the recorder in the background, then wait for it to finish: H=$(TZ=Asia/Kolkata date +%-H); if [ "$H" -ge 14 ]; then UNTIL=15:35; else UNTIL=$(printf '%02d:05' $((H + 2))); fi; python -m fno intraday run --until "$UNTIL" It waits for each 15-minute mark up to that time. After each mark it writes the slot row and the heartbeat, and it commits and pushes its own files in research/data/intraday/ (slots/, rv/, heartbeat.json). At the 15:30 mark it also writes the session's realised variance. On a day that is not a session it prints "not a trading day" and stops.

**Proposed step 3 (replaces it word for word; steps 0-2 and 4-6 unchanged):**

> 3. Work out the end time once: H=$(TZ=Asia/Kolkata date +%-H); if [ "$H" -ge 14 ]; then UNTIL=15:35; else UNTIL=$(printf '%02d:05' $((H + 2))); fi; echo "$UNTIL" — and keep that value for the whole fire. Then run python -m fno intraday run --until <that UNTIL> in the background with the longest time limit the tool allows (2 hours, 7200000 ms), never the default limit, and wait for it to finish. Do not run it in the foreground (a foreground command stops after 10 minutes). The recorder runs one hour past UNTIL, up to 15:35 (story A16i), so a fire can last about 2h45m. If the tool says the command was stopped at its time limit, run the same command with the same UNTIL again at once, the same way, and repeat until it ends by itself. A rerun is safe: it skips the marks already taken and never takes a mark twice. It waits for each 15-minute mark up to that time. After each mark it writes the slot row and the heartbeat, and it commits and pushes its own files in research/data/intraday/ (slots/, rv/, heartbeat.json). At the 15:30 mark it also writes the session's realised variance. On a day that is not a session it prints "not a trading day" and stops.

The same text goes in section 3 above once the owner has changed the routines. No builder or orchestrator changes a
routine.
