# A12 filings archive: the owner's one-time steps

The filings archive runs by itself in GitHub Actions (`.github/workflows/filings-archive.yml`), every 6 hours until
the 3-year backfill is complete, then once a day. It needs the same Drive and Slack settings the cloud environment
already has, added once as **repository secrets** (five; already added). Nobody else can add them: secrets are
never written to a file or sent in chat.

## Checklist (about 10 minutes, once)

1. [ ] **Publish the Google OAuth app (the only step left; about 5 minutes).** While the app is in "Testing", Google
   expires its refresh token 7 days after it was made, and every run then stops with "Google refused the Drive upload
   sign-in" (an alert in #fno-desk says so). Exactly:
   1. Open console.cloud.google.com, signed in as the Drive owner, and pick the project that holds the "Desktop app"
      OAuth client used by `tools/gdrive_oauth_setup.py`.
   2. Menu → *Google Auth Platform* → *Audience* (older screens: *APIs & Services* → *OAuth consent screen*).
   3. If "Publishing status" says **Testing**, click **Publish app**, then **Confirm**. (Google may say the app needs
      verification for the Drive scope; for an app only you use, you can go on unverified: at sign-in you will see
      "Google hasn't verified this app", click *Advanced* → *Go to ... (unsafe)*.) If it already says **In
      production** and the refresh token was made after it was published, you are done; if the token is older,
      do steps 4 and 5.
   4. On your computer: `python3 tools/gdrive_oauth_setup.py <path to the client_secret JSON>`, sign in, allow access.
      It prints a new refresh token (a token made before publishing still expires after 7 days).
   5. github.com/exepex/trading → *Settings* → *Secrets and variables* → *Actions* → `FNO_GDRIVE_OAUTH_REFRESH_TOKEN`
      → *Update secret*, paste the new token. Put the same value in the cloud environment's setting of that name.
   6. Tell the desk "OAuth published" (no token in chat); the next run's line in #fno-desk confirms the sign-in works.
2. [x] **Add five repository secrets.** Already done: the probe run of 13 Oct 2026 shows all five set. To change one:
   github.com/exepex/trading → *Settings* → *Secrets and variables* → *Actions*, one per name, each value copied
   from the cloud environment's settings (or from the setup tool's output):

   | Secret name | What it is |
   |---|---|
   | `FNO_GDRIVE_FOLDER_ID` | the `fno-research` Drive folder's ID |
   | `FNO_GDRIVE_OAUTH_CLIENT_ID` | the Desktop app client's ID |
   | `FNO_GDRIVE_OAUTH_CLIENT_SECRET` | the Desktop app client's secret |
   | `FNO_GDRIVE_OAUTH_REFRESH_TOKEN` | the refresh token from `tools/gdrive_oauth_setup.py` |
   | `FNO_SLACK_BOT_TOKEN` | the #fno-desk bot token (alerts) |

3. [ ] **Let the workflow commit its manifest rows.** The workflow asks for `contents: write` itself, so nothing is
   needed unless a branch rule on `main` blocks pushes by GitHub Actions (*Settings* → *Rules* or *Branches*). If one
   does, allow `github-actions[bot]` to push to `main`; otherwise each run's rows are not committed and the next run
   fetches those files again (a waste, never a loss: Drive refuses duplicates).
4. [x] **Start it.** First a 20-company trial run by the builder (13 Oct 2026), then the schedule (*Actions* → *filings-archive* → *Run workflow*, "probe
   only" unticked, starts it again any time). A run archives about 240 companies in its 4.3 hours (measured 63 s per
   company); the schedule continues every 6 hours. Progress: the file `index/nse/equities/filings/progress.json` in
   the Drive project folder (work queue, companies done per step, last runs with files and bytes), the one line each
   run posts to #fno-desk, and the job log.
5. [ ] **Check after a day.** `python -m fno data-coverage --filings` (any machine with the Drive read settings)
   prints, per filing type, companies covered of 501, files, damaged, unfingerprinted and every gap with its reason,
   and the half-year balance-sheet and cash-flow share.

## What happens on a problem

- Drive sign-in refused (expired consent): the run stops, and #fno-desk gets the one-minute fix (step 1).
- NSE refuses the runner (HTTP 403 or 429 twice) or a list or file fails: the run stops or records the failure, and
  #fno-desk gets one line naming it. The probe step (first step of every run) fails the job if NSE does not answer
  from GitHub's runners at all; the job's failure is posted to #fno-desk too.
- Reaching the 5.5-hour limit during the backfill is normal: no alert; the next run resumes where it stopped.
