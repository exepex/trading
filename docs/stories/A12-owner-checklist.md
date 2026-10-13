# A12 filings archive: the owner's one-time steps

The filings archive runs by itself in GitHub Actions (`.github/workflows/filings-archive.yml`), every 6 hours until
the 3-year backfill is complete, then once a day. It needs the same Drive and Slack settings the cloud environment
already has, added once as **repository secrets**. Nobody else can add them: secrets are never written to a file or
sent in chat.

## Checklist (about 10 minutes, once)

1. [ ] **Publish the Google OAuth app** (or the upload stops every 7 days). Google Cloud console, the project of the
   "Desktop app" client, *Google Auth Platform → Audience* (older screens: *OAuth consent screen*), **Publish app**.
   While the app is in "Testing", Google expires the refresh token after 7 days and every run fails with
   "Google refused the Drive upload sign-in" (an alert in #fno-desk says so). If you publish it now, run
   `python3 tools/gdrive_oauth_setup.py <client_secret JSON>` once more on your computer to get a refresh token that
   does not expire, and use that one in step 2.
2. [ ] **Add six repository secrets.** github.com/exepex/trading → *Settings* → *Secrets and variables* → *Actions* →
   *New repository secret*, one per name, each value copied from the cloud environment's settings (or from the setup
   tool's output):

   | Secret name | What it is |
   |---|---|
   | `FNO_GDRIVE_FOLDER_ID` | the `fno-research` Drive folder's ID |
   | `FNO_GDRIVE_OAUTH_CLIENT_ID` | the Desktop app client's ID |
   | `FNO_GDRIVE_OAUTH_CLIENT_SECRET` | the Desktop app client's secret |
   | `FNO_GDRIVE_OAUTH_REFRESH_TOKEN` | the refresh token from `tools/gdrive_oauth_setup.py` |
   | `FNO_GDRIVE_SERVICE_ACCOUNT_JSON` | the service account key (reads the Nifty 500 list and checks coverage) |
   | `FNO_SLACK_BOT_TOKEN` | the #fno-desk bot token (alerts) |

3. [ ] **Let the workflow commit its manifest rows.** The workflow asks for `contents: write` itself, so nothing is
   needed unless a branch rule on `main` blocks pushes by GitHub Actions (*Settings* → *Rules* or *Branches*). If one
   does, allow `github-actions[bot]` to push to `main`; otherwise each run's rows are not committed and the next run
   fetches those files again (a waste, never a loss: Drive refuses duplicates).
4. [ ] **Start it.** *Actions* → *filings-archive* → *Run workflow* (leave "probe only" unticked). The first run
   archives about 115 companies in its 5.5 hours; the schedule continues every 6 hours. Progress:
   `research/data/manifests/filings/runs.csv` (one row per run) and the job log.
5. [ ] **Check after a day.** `python -m fno data-coverage --filings` (any machine with the Drive read settings)
   prints, per filing type, companies covered of 501, files, damaged, unfingerprinted and every gap with its reason,
   and the half-year balance-sheet and cash-flow share.

## What happens on a problem

- Drive sign-in refused (expired consent): the run stops, and #fno-desk gets the one-minute fix (step 1).
- NSE refuses the runner (HTTP 403 or 429 twice) or a list or file fails: the run stops or records the failure, and
  #fno-desk gets one line naming it. The probe step (first step of every run) fails the job if NSE does not answer
  from GitHub's runners at all; the job's failure is posted to #fno-desk too.
- Reaching the 5.5-hour limit during the backfill is normal: no alert; the next run resumes where it stopped.
