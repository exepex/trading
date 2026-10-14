# Judge 86: tests never hold live credentials (branch `story/o-tests-no-live-alerts`, before merge)

Date: 14 Oct 2026 (UTC). Branch at c0b17d3, one commit on `main`. Owner-reported bug: #fno-desk received dozens of
fixture alerts ("book1_rules 2026-10-13-sc-a-v1:2026-11-27 ... cannot be read now (PlaybookError ...)").

**Disclosure:** my own full-suite runs today used the machine's environment, where `FNO_SLACK_BOT_TOKEN` is set. They
very likely posted some of these alerts too, from E5's `test_exits.py` through the real `build_book1_exit_rules`
wiring. From this review on, I run every suite with `env -u FNO_SLACK_BOT_TOKEN`, and my plant scripts strip it.

## Verdict: PASS (urgent fix), with two should-fixes for a follow-up

## The root cause (checked)

- `tests/book1/test_exits.py::test_an_unrelated_broken_draft_leaves_every_exit_applied` calls the real wiring, which
  builds the real alert sender (`fno/composition.py`, `os.environ.get(ENV_FNO_SLACK_BOT_TOKEN)` at call time).
- `conftest.no_real_credentials` removed only the Groww and Drive variables. With the token set, every suite run posted
  a real alert.
- Confirmed by reading.

## The fix

- `tests/live_credentials.py` lists the Groww, Drive, Slack, MotherDuck, `FNO_DB_URL`, routine-token and `GITHUB_TOKEN`
  variables. The autouse fixture deletes each one for every test.
- `env=os.environ` defaults in the wirings are the same mapping object, so they see the deletion too.
- `tests/test_no_live_credentials.py`:
  - the alert wiring returns "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set";
  - no listed name is visible.

**Gates (my runs, `python -B`, caches cleared, token unset):**
- full suite: 2,860 passed;
- ruff, format (642 files) and imports (649): clean;
- `git merge-tree` with current `main` (b016810): clean.

## Should-fix 1: the list check is circular

`test_no_live_credential_is_visible_to_a_test` checks only the names **in the same list** the fixture deletes.
Dropping a name removes it from both, so nothing fails.

My plants, each with the token unset:

| Removed from the list | Result |
|---|---|
| `GITHUB_TOKEN` | 2 passed (not caught) |
| `MOTHERDUCK_TOKEN` | 2 passed |
| `FNO_DB_URL` | 2 passed |
| `GROWW_API_KEY` | 2 passed |
| `FNO_GDRIVE_SERVICE_ACCOUNT_JSON` | 2 passed |

Only Slack has a real guard, through the alert-sender test.

**Fix:** derive the expected set independently. For example, every `ENV_*` constant in `fno/constants.py` whose value
holds a credential (TOKEN, KEY, SECRET, `_URL`, `SERVICE_ACCOUNT`) must be in `LIVE_CREDENTIALS`. Or assert per
wiring: Groww's `has_credentials()` is false, the Drive store builder returns no store, `FNO_DB_URL` is absent.

**Also:** the alert-sender test **sends** "test" when the token leaks. Assert on the configuration instead (the token
absent from the environment the sender reads), so the guard itself never posts.

## Should-fix 2: `~/.trading.env` can bring a deleted token back in a subprocess

- `fno/__main__.run` calls `load_env_file()`, which sets every key from `~/.trading.env` that is not already in the
  environment.
- `tests/scorecard/test_cli.py` starts `python -m fno` as a subprocess. Its environment has the token removed, so on a
  machine with that file (the owner's, by the module's own docstring) the subprocess loads the token again.
- Today's subprocess tests only print help or a report-only scorecard, so nothing is sent. But the next CLI test that
  reaches an alert would post. This machine has no `~/.trading.env`, so I could not show it live (reasoning only).
- **Fix:** the conftest points `HOME` and `USERPROFILE` at a temporary folder, or sets a variable that makes
  `load_env_file` a no-op under tests.

## Project rules

Tests only, small. The rule "a test that needs credentials sets fake ones itself" is kept.

**Verdict: PASS** for c0b17d3. After the merge I check `main` and CI.
