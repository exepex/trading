# O13: proposed routine-instruction changes (for the owner's approval; nothing applied yet)

Owner, 23 Oct 2026: "if you make a change in any of the routine instruction, first confirm with me, including the time
of the routine." This file is that confirmation request. **No routine time changes.** No step is removed or
reordered; each command is only run through the logger, which passes its output and exit code through unchanged.

## 1. Times (unchanged, read from the live routines on 23 Oct, about 22:00 IST)

| Log name | Routine (as named in claude.ai/code/routines) | Time IST | Days (who decides) |
|---|---|---|---|
| `a16-backup` | A16 recorder 08:22 backup (copy) | 08:22 | every day (NSE calendar) |
| `pre-open` | Omenix F&O pre-open capture | 08:36 | every day (calendar) |
| `morning-forecast` | Omenix F&O morning forecast | 08:38 | every day (calendar) |
| `a16-recorder` | Omenix F&O 15-minute recorder (A16) | 08:52, 09:52 ... 14:52 | every day (calendar) |
| `daily-desk` | F&O 3 pm quote recorder (daily 14:33 IST; calendar decides) | 14:05 | every day (calendar) |
| `participant-oi` | participant-OI release times (A8) | 17:11 | every day (calendar) |
| `evening-forecast` | Omenix F&O evening forecast | 19:53 | every day (calendar) |
| `participant-oi-sweep` | participant-OI rewrite sweep (monthly) | 07:07 on the 1st | monthly |

The watcher expects a run only on NSE session days (the sweep: the 1st of each month). Not covered: the triggered
runs (Books 2 and 3, O6 dry-run, weekly post-mortem; their prompts are hash-checked or fired by GitHub and have no
fixed time) and the stock tool's routines (read-only repository).

Two things I found while reading them (your call):
- The desk routine's name still says "daily 14:33 IST"; it runs at 14:05. Rename it? (name only, no effect)
- The A8 routine's step 4 has a garbled paste: `Commit research/data/participant_oi/release_checks.csv and push to
  main” to “Commit the whole folder research/data/participant_oi/ (git add research/data/participant_oi/) and push to
  main.` The intended text is the part after "to": proposed below.

## 2. CLAUDE.md (lane 1, judge after your yes)

A new section after "Pre-open capture (story A22)":

> ## Routine run logs (story O13)
>
> Every scheduled routine logs its run to Drive (`logs/routines/<IST day>/<log name>/<HHMMSS-id>/`), so any session
> can read it, and posts to #fno-desk the moment a command fails. After setup (step 1; setup itself is not logged,
> the packages are not there yet) and before anything else: `python -m fno routine-log begin --routine <log name>`.
> Then each command of the routine runs as `python -m fno routine-log run --routine <log name> --step <short name> --
> <the command, unchanged>`; the last one adds `--last` (it closes the run even if the session ends first). A routine
> that ends early (not a trading day, a stop) runs `python -m fno routine-log end --routine <log name> --note "<its
> line>"`. The logger prints the command's output live and exits with the command's own exit code, so every rule
> above about that output still applies. A line "routine log NOT saved to Drive" never stops the routine: note it
> with the day's other problems. `routine-watch.yml` checks every hour (at :17) for runs missing, stuck or failed.

One line at the top of each of the three existing sections:

- Daily desk routine: "Log this run as `daily-desk` (section 'Routine run logs'); `daily run` is the last step."
- Morning and evening: "Log this run as `morning-forecast` or `evening-forecast` (section 'Routine run logs');
  `lab open` is the morning's last step, `lab release-check` the evening's."
- Pre-open capture: "Log this run as `pre-open` (section 'Routine run logs'); the background part runs through
  `routine-log run` too (`... --step global-cues -- python -m fno global-cues preopen &`); after both are done:
  `routine-log end --routine pre-open`." (No `--last` here: two parts run at once.)

## 3. Prompts you paste (API-created routines; I cannot edit them)

Only the lines that change. Everything else stays word for word.

**A16 recorder (08:52 hourly) and its 08:22 backup**, after step 1, a new step 1b, and step 3's command:

> 1b. `python -m fno routine-log begin --routine a16-recorder` (the backup: `--routine a16-backup`).
>
> 3. ... `python -m fno routine-log run --routine a16-recorder --step recorder --last -- python -m fno intraday run
> --until "$UNTIL"` (the backup: `--routine a16-backup`). It prints the recorder's lines as before ...

**A8 participant-OI (17:11)**, after step 2 a new step 2b, step 3's command, and step 4 fixed:

> 2b. `python -m fno routine-log begin --routine participant-oi`.
>
> 3. Run `python -m fno routine-log run --routine participant-oi --step watch --last -- python -m fno participant-oi
> watch --until 23:30 --every 5`. ...
>
> 4. Commit the whole folder research/data/participant_oi/ (git add research/data/participant_oi/) and push to main.

**A8 monthly sweep (07:07 on the 1st)**, step 3:

> 3. Run `python -m fno routine-log begin --routine participant-oi-sweep`, then `python -m fno routine-log run
> --routine participant-oi-sweep --step sweep --last -- python -m fno participant-oi sweep`. ...

## 4. What it costs and what it cannot do

- Each command's output is written to Drive once, after the command ends (up to 2 MB kept); the live lines are
  unchanged. A command killed mid-way (the session limit) leaves `begin.json` and the earlier steps, and the watcher
  calls it stuck after the routine's maximum time (A16: 160 minutes, the backup 185, the desk 150).
- A routine that fails before `begin` (step 0 or setup) leaves no log: the watcher says "missing" and points to
  claude.ai/code/routines for that session.
- GitHub's hourly schedule can run hours late, so the immediate in-run line is the fast path; the watcher is the net.
