# Routines and schedules audit (15 Oct 2026, about 01:00 IST)

Owner's question: do we need all ~30 routines, and can they become free GitHub Actions?
Sources: `list_triggers` (all 33), the run sessions' own cost records (`get_session`, `list_sessions`), the run
transcripts of four market-brief runs, `.github/workflows/`, `docs/DESK_DECISIONS.md` and the 13-14 Oct logs.
Evidence labels: **strong** (measured), **some** (one or two days of data), **reasoning** (no data yet).

## 1. The short answer

- **33 scheduled tasks exist:** 16 market-brief (the stock tool, not this repository), 3 recurring F&O routines,
  1 daily judge audit, 3 routines fired by GitHub Actions, 10 one-time reminders or checks.
- **The routines are not where the tokens go (strong).** Measured cost of every run:
  - market-brief runs: about **$22 a weekday**, about $1 a weekend day (13 Oct: 15 runs, $22.46). The two Opus
    "daily" runs are **$16 of the $22** (US $8.12-8.88, India $7.75-8.08).
  - F&O routines: about **$0.50 a day** (3 pm recorder $0.23, A8 watch $0.27, O6 dry-run $0.01).
  - Development sessions: the orchestrator alone is at $577 with 733k tokens of context; the judge $260 (605k);
    builders $40-145 each. In the last ~2 days of sessions listed, about $1,450 of $1,494 was development, about $45
    was market-brief runs.
  - The account's 7-day limit already shows "allowed_warning". Cutting routines helps a little; the large lever is
    development sessions with 600-760k contexts, which re-read that whole context on every turn and every reminder.
- **GitHub's schedule is not reliable on this repository today (strong).** On 14 Oct: the NSE 3 pm job started at
  about 19:35 IST instead of 14:20 and recorded nothing (`nifty_20261014.canonical` holds `None`); forecast-capture
  started at 19:26 IST (5 h 26 min late); the A8 Actions watch never ran its evening slots and ran once at 00:20 IST.
  So "move it to a cron Action" loses time-critical data until the start time is fixed (section 4).

## 2. Every scheduled task, with verdict

### A. Market-brief (stock tool, `contactexepex/agentic-stock-prediction`): 16 routines

Each one wakes the Haiku dispatcher session (cheap: $0.13 all day), which starts a fresh run session.
I could not open that repository (attaching it was refused in this session), so the verdicts come from the run
transcripts, not its code.

| # | Routine (time) | Run model, cost | What the run really does | Need AI? | Verdict |
|---|---|---|---|---|---|
| 1 | India daily (07:40 IST, Mon-Fri) | Opus, ~$8 | scripts + news reading, bull/bear cases, forecaster, 4 AI traders, report prose | partly | Keep only if the AI part earns its cost; see note |
| 2 | US daily (07:45 ET, Mon-Fri) | Opus, ~$8 | same as 1 | partly | same as 1 |
| 3-4 | India intraday 1 and 2 (11:13, 14:13 IST) | Sonnet, ~$0.55 | `intraday_check.py` flags movers, an AI writes a 60-word note per flag | mostly no | Action + template notes |
| 5-6 | US intraday 1 and 2 (12:27, 14:57 ET) | Sonnet, ~$0.3-0.6 | same | mostly no | Action + template notes |
| 7 | India post-close (17:45 IST) | Sonnet, ~$0.65 | settle trades, Slack post; AI notes only restate numbers from `eod_facts.json` | no | Action now |
| 8 | US post-close (18:15 ET) | Sonnet, ~$0.35-0.56 | same | no | Action now |
| 9 | India evening (03:00 IST) | Sonnet, $0.27 | a chain of scripts (prices, features, calibrate, predict), commit | no | Action now |
| 10 | US evening (18:30 ET) | Sonnet, $0.27 | same | no | Action now |
| 11-14 | News, both markets (10:45 IST daily; 13:45 IST Mon-Fri; 11:27 and 17:27 ET daily; 14:27 ET Mon-Fri) = 5 runs a weekday, 3 a weekend day | Sonnet, ~$0.33 | 6 turns: fetch news, write rows and clusters, validate, push | no | Action now (owner's 13 Oct principle) |
| 15-16 | India and US weekly research (Fri 19:30 ET) | Opus | research run | yes | Keep |

Note on 1-2 (some evidence, one day read): on 14 Oct the US daily cost $8.12 and made **zero** daily calls. The
forecaster abstained on all 20 tickers ("within 1 pt of base rate"), two AI traders abstained, one copied the model's
probabilities unchanged, and the news analyst wrote its own regex to batch 2,124 items. Those abstentions are a rule,
not judgement. Whether the AI adds value needs the scored record, which the run says is still empty. Cheapest honest
options: run the AI part on Sonnet, or only when the model shows an edge. That is the stock tool's decision, not
measured here.

Also: the market-brief evening run reported success after reading cut-off output it never checked. A plain script
with exit codes does not have that failure mode.

### B. F&O recurring routines: 3, plus the judge audit

| # | Routine | Cost | Free Action already there? | Verdict |
|---|---|---|---|---|
| 17 | 3 pm Groww quote recorder (14:48 IST daily, Sonnet) | $0.23 | `quote-recorder-nse.yml` (NSE data) | **Keep.** The Groww key never goes into GitHub (owner, 13 Oct). The NSE job has 0 good days so far (14 Oct: late, empty). Its push is also what starts forecast-capture on time (a push by GitHub's own token starts nothing). Could run on Haiku: it only runs commands. |
| 18 | A8 participant-OI release times (17:11 IST daily, Haiku) | $0.27, about 1 h 40 min open | yes, two: `participant-oi-watch.yml` (every 15 min) and `participant-oi-release.yml` (5-min watch) | **Keep until the Actions start on time**, then delete. Three things now measure the same file. |
| 19 | Monthly participant-OI sweep (1st, 07:07 IST, Haiku) | pennies | `participant-oi-sweep.yml` (1st, 05:37 IST) | **Delete after the Action's 1 Nov run is clean.** Timing is not critical, so a late Action is harmless. It also has no repository attached, so its push would fail anyway. |
| 20 | Judge daily lane-2 audit (17:30 UTC, judge session) | each wake re-reads the judge's ~605k context on Opus (cost per wake not measured; reasoning: dollars, not cents) | no | **Keep the audit, change the trigger:** a free Action checks `git log --grep '^Lane 2:'` and fires the judge only when there is something to audit; most days there is nothing. |

### C. Routines fired by GitHub Actions (no schedule of their own): 3

| # | Routine | Verdict |
|---|---|---|
| 21 | Book 2 Hybrid forecast (Opus) | **Keep.** AI reasoning is the experiment itself. 14 Oct failed at setup (fixed by the owner). |
| 22 | Book 3 AI team forecast (Opus) | **Keep.** Same. |
| 23 | O6 dry-run (Haiku, $0.01) | No reasoning: it reads a Drive file and writes a summary. Proof of the fetch-then-fire pipeline only. **Retire** once Books 2-3 have fired cleanly (they prove the same pipeline), or keep as a one-cent canary. |

### D. One-time reminders and checks: 10

| # | Reminder (fires) | Needed? |
|---|---|---|
| 24 | Check routine pushes reached main (15 Oct 20:00 IST) | Yes, once |
| 25 | Check 15 Oct AI books run (15 Oct 15:35 IST) | Yes (owner's audit condition) |
| 26 | Judge 88: first push-started capture (15 Oct 15:20 IST) | Yes, once |
| 27 | Check market-publish cron fired (15 Oct 07:45 IST) | Yes, once |
| 28 | Judge 64: second A13 append (15 Oct 22:30 IST) | Yes, once |
| 29 | Muhurat 2026 hours into the calendar (28 Oct) | Yes |
| 30 | Renew stressed margin before 13 Nov (6 Nov) | Yes; without it C2 and C4 refuse every trade from 16 Nov |
| 31 | Drive key expiry (19 Oct) | Yes: publishing the Google app does not extend the old token |
| 32 | Add NSE 2027 calendar (15 Dec) | Yes; the recorder stops on 1 Jan 2027 without it |
| 33 | Quarterly restore test (11 Jan 2027) | Yes |

All ten are needed and fire once each. Each wakes a big Opus session, so they cost more than they look. Pure
reminders (30, 31, 33) could be a free dated Slack line from an Action; AI only when there is work to do.

## 3. What can become a free GitHub Action

- **Already built, waiting for a reliable start:** A8 watch (18), monthly sweep (19), NSE 3 pm recorder (beside 17).
- **Can move now (stock repository):** news x4, evening x2, post-close x2 (template notes), intraday x4 (template notes).
  Saves about $5 a weekday and $1 a weekend day, about **$30 a week** (strong: measured run costs).
- **Cannot become free:** Books 2 and 3, weekly research, the judge's audit itself, and the reasoning part of the
  daily runs. An Action could run them only with Claude inside it (the subscription token or a paid API key): the same
  tokens, so no saving.
- **Biggest single saving among routines:** the two Opus daily runs, about **$80 a week**. That needs a decision on the
  stock tool's AI layer, not a move to Actions.

## 4. Before switching anything off: fix GitHub's late start

Time-critical jobs (3 pm recorder, A8 watch, forecast-capture, market-brief morning runs) cannot rely on GitHub's
cron: 4.5-5.5 hours late on 14 Oct, some slots never ran. Proposal (reasoning; lane 1, needs the judge):

1. A free outside scheduler (for example cron-job.org) calls GitHub's `workflow_dispatch` API at the exact minute.
   Manual and API starts are not queued like cron. The token is a fine-grained GitHub token for `exepex/trading` only,
   with Actions write and nothing else: it can start workflows, not change code or read secrets. It lives with that
   scheduler, never in the repository. The GitHub cron stays as the fallback.
2. The NSE 3 pm job, when done, starts forecast-capture itself (`gh workflow run`, allowed for GitHub's own token),
   so forecast-capture no longer depends on the Groww routine's push.
3. Switch off each routine only after its Action has run on time and complete for 3 sessions, as the owner decided
   on 13 Oct.

## 5. Recommended order

1. Now, no risk: nothing to delete. Every routine is either needed, or is a side-by-side whose Action has not yet had
   one good day.
2. Owner decision: the outside scheduler (section 4), yes or no.
3. After 3 on-time sessions: delete 18 (A8 routine), and 17 only if the NSE data matches Groww's (`quotes compare`);
   delete 19 after 1 Nov; retire 23.
4. Stock repository: move news, evening, post-close and intraday to Actions; decide on the Opus daily runs.
5. Judge audit: fire only when there are lane-2 merges.
6. Largest real saving: start fresh development sessions instead of growing 600-760k contexts.
