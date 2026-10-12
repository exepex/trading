# Response 36: builder's claims for O5, public-record safety scan

Story: `docs/stories/O-operations.md#o5-public-record-safety-scan` (issue "O5"). Status: built; awaiting judge.

## What was built

| Part | Where |
|---|---|
| Interface `RecordPattern` and its regex, secret-assignment and Aadhaar (Verhoeff) classes | `fno/record_scan/patterns.py:15`, `:25`, `:61`, `:97` |
| Pattern catalogue (18 kinds) and the allow-list (#fno-desk channel ID only) | `fno/record_scan/catalogue.py:63`, `:71` |
| Environment-variable names watched: every `ENV_*` in `fno/constants.py` (two added: `FNO_SLACK_BOT_TOKEN`, `MOTHERDUCK_TOKEN`), plus the channel ID constant | `fno/record_scan/catalogue.py:66`, `fno/constants.py:15-19` |
| Scanner: a finding is file, line and kind, never the value | `fno/record_scan/scanner.py:16`, `:30` |
| Interface `RecordSource`: committed records, staged records, named files (session exports) | `fno/record_scan/record_files.py:38`, `:52`, `:65`, `:76` |
| Wiring | `fno/composition.py:31` `build_record_scanner()`, `:50` `build_alert_sender()` |
| CLI | `tools/check_records.py` (`--staged`, `--root`, or paths) |
| Routine gate: git pre-commit hook | `.githooks/pre-commit` |
| Routine change (minimal: two sentences) | `CLAUDE.md:48-49` (step 1 turns the hook on), `CLAUDE.md:53-55` (step 3: refused means no commit, never `--no-verify`, post the lines to #fno-desk and log them) |

**What counts as a record:** every tracked file outside `fno/`, `tests/`, `tools/` (code holds the patterns themselves
and the tests' planted values). So `journal/`, `research/` (including `research/data/quotes/`), `reports/`,
`conversations/`, `reviews/`, `docs/`, root files, and future `book3/`, `playbook/`, `agents/` are scanned without
being listed anywhere. `.gz` files are unpacked and scanned; any other binary file is a finding ("cannot be scanned"),
not a silent skip.

**Kinds caught:** private key, Slack token, Slack webhook, GitHub token, Google API key, AWS key, AI API key (`sk-`),
JSON web token (Groww and MotherDuck tokens are JWTs), bearer token, a value after any `fno/constants.py`
environment-variable name, a value after a secret word (`api_key`, `password`, `access_token` ...), e-mail, Indian
phone (+91 or a phone word), PAN, Aadhaar (Verhoeff checksum), demat BO ID (NSDL `IN`+14 digits, CDSL 16 digits),
broker/Groww fields with a value or as a CSV column (`groww_order_id`, `order_reference_id`, `client_code`, `ucc`,
`account_number`, `dp_id` ...; the bare name in prose exposes nothing and is not a finding),
Slack user/workspace/channel IDs other than #fno-desk.

## Acceptance criteria

### 1. Planted examples of each pattern are caught; the allow-listed channel ID is not. PASS (strong evidence)
- Code: `fno/record_scan/catalogue.py:71` (patterns), `:63` (allow-list), `fno/record_scan/scanner.py:30-40`.
- Tests: `tests/record_scan/test_patterns.py:41` (every pattern has a planted example: the test fails if a pattern is
  added without one), `:46` (each of the 18 planted values is caught by its own pattern), `:56` (the channel ID, bare
  and inside a message link, gives no finding), `:75` (seven kinds of ordinary content give none: a SHA-256, prices
  and volumes, env names without values, `${VAR}` placeholders, upper-case `..._CLIENT_ID` env names, an NSE circular
  name, an ISIN, a wrong-checksum 12-digit number), `:80` (a broker field as a CSV column is caught), `:84` (field
  names in prose are not), `:50` (output is `file:line: kind`, value absent).
- Planted values are assembled from pieces in the test source so no full fake credential sits in the repository.

### 2. The routine refuses to commit when the scan finds anything and alerts naming the file, not the value. PASS for the refusal (strong evidence); the alert is a routine instruction, not code (see doubts)
- Code: `.githooks/pre-commit` runs `tools/check_records.py --staged`, which scans the staged bytes
  (`record_files.py:65-73`, `git show :path`), so what is checked is exactly what the commit would hold.
- Tests: `tests/record_scan/test_routine_gate.py:43` (a git repository set up as the routine sets it up, with a
  planted Slack token in `journal/`: `git commit` fails, nothing is committed, output names
  `journal/2026-10-13.md:2: Slack token` and never the value), `:54` (clean quote records commit), `:59` (staged bytes,
  not the working tree), `:66` (code folders are not records), `:71` (gzip scanned), `:78` (a session export folder is
  scanned before sending).
- Dry run on a full copy of this repository with the hook on and a planted token in `journal/dry.md`:

```
journal/dry.md:2: Slack token
record scan: REFUSED, 1 finding(s); do not commit or send these files (values are not shown)
exit=1
```
  HEAD stayed at the previous commit.
- O1 reuses it unchanged: the hook guards every commit of any routine that runs `git config core.hooksPath .githooks`.

### 3. The scan of the current repository passes. PASS (strong evidence), after one real finding was removed
- First honest result (before any allow-list beyond the channel ID): 2 findings, `conversations/2026-10-12.md:76` and
  `:94`, both Slack file links whose path holds a Slack user ID (most likely the owner's own). Reported to the
  orchestrator, who removed both links (commit 45283cc). Two false positives were fixed in the patterns, not
  allow-listed: `GITHUB_OAUTH_CLIENT_ID` in `docs/MIGRATION_PLAN.md:25` (env names are not broker fields: field match
  is lower-case only) and 12 digits inside a SHA-256 in `research/2026-10-12-capacity-screen/data/manifest.csv:744`
  (numbers next to letters are not Aadhaar or phone numbers). A third one appeared in this claims file itself, which
  lists broker field names: the pattern now needs a value or a CSV column, not just the name.
- Test: `tests/record_scan/test_routine_gate.py:87` runs the CLI over the repository.

```
$ python tools/check_records.py
record scan: clean (155 files)
```

## Checks run

```
$ python -m pytest -q
235 passed in 30.85s (after merging main with E1)
$ ruff check fno tests tools
All checks passed!
$ python tools/check_imports.py
clean: 79 files, 1 archival skipped
```
Largest new file: 98 lines (`patterns.py`). A full scan takes about 5 s (most of it the 20 MB unpacked
`nifty_options.csv.gz`); patterns with a fixed word skip files that lack it.

## Doubts and limits (stated, not hidden)

1. **The alert is sent by the routine session, not by code** (reasoning only that this is acceptable now). No Slack
   client exists in this repository yet (P4 builds alerts). The refusal is mechanical (the hook); posting the lines to
   #fno-desk is CLAUDE.md step 3. When P4 lands, the hook output can be sent by code.
2. **The hook only works if the routine runs step 1** (`git config core.hooksPath .githooks`), and `--no-verify`
   bypasses it. CLAUDE.md forbids the bypass. A fresh cloud clone has no hooks otherwise.
3. **CI gate (added after the orchestrator's request):** `.github/workflows/checks.yml` runs on every push and pull
   request to `main`: pytest (which includes the repository scan test), `ruff check fno tests tools`,
   `python tools/check_imports.py` and `python tools/check_records.py`; Python 3.11, pip cache, no secrets. It catches
   a session that pushed without running the checks, after the push (it cannot block a direct push to `main`).
4. **Phone numbers:** a bare 10-digit number is not flagged, because it cannot be told apart from a volume or
   turnover in the quote and market files. Only `+91 ...` or a number after a phone word is caught (some evidence:
   the repository's data files contain many 10-digit numbers).
5. **Broker identifiers:** Groww order IDs and client codes have no published fixed format, so they are caught by
   their field names (lower-case snake case, as in API JSON) and demat BO-ID formats only. A spaced label such as
   "Client Code" in a pasted broker statement is not caught (reasoning only).
6. **Unlabelled secrets with no known shape** (a random string alone on a line) are not caught. Entropy detection was
   left out on purpose: it would flag every SHA-256 the records must keep auditable.
7. **Slack IDs:** matched as letter + digit + 7-10 upper-case letters or digits (current Slack format). Older IDs
   without a digit second are missed.
8. **Git history** still holds the two removed Slack links; rewriting history is out of scope by the story.
9. **Staged scan covers added and modified files only**, so an old finding in an untouched file does not block a
   routine's commit; the repository test catches those instead.
10. **Wiring:** `catalogue.py` creates the pattern objects (they are data: name plus regex); the scanner itself is
    built only in `fno/composition.py`. A judge may see this as wiring outside the composition root; moving the list
    into `composition.py` is a one-line change if so.

## Round 2: answers to judge 2 (`reviews/judge/judge_2_o5_record_scan.md`)

All six findings accepted after checking them; each was reproduced first (the judge's missed forms ran through
`build_record_scanner().scan_text` and were all missed before the fix). This section supersedes doubts 1, 2 and the
"code folders are not scanned" statement above.

| # | Finding | Decision and reason | Fix and proof |
|---|---|---|---|
| 1 | Alert not built or verified | Accepted: an instruction cannot be verified | Interface `AlertSender` with `SlackChannelAlerts` (#fno-desk, `FNO_SLACK_BOT_TOKEN` only) and `NoAlertSender` (`fno/alerts/sender.py:17`, `:23`, `:43`), wired at `fno/composition.py:50`. `tools/check_records.py --alert` posts the finding lines when refused; the hook always passes `--alert`. Tests: `tests/test_alert_sender.py` (HTTP faked: channel, token header, Slack error, network failure, no token), `tests/record_scan/test_routine_gate.py:118` (alert text names file:line:kind, not the value), `:129` (no token: still refused, prints "alert NOT sent"). Real dry run below. |
| 2 | Gate on in one routine only | Accepted: builders, the orchestrator and log writers committed ungated | `.claude/settings.json` SessionStart hook runs `git config core.hooksPath .githooks` in every Claude session; CLAUDE.md "Branch" rule for every session (run it yourself if empty, never `--no-verify`). Test `test_routine_gate.py:135`: a fresh checkout runs the settings' SessionStart command, then a planted token in `conversations/` is refused. This session's own commits now go through the hook. |
| 3 | Secrets written in words missed | Accepted: reproduced | Separators `[ _-]?` (`catalogue.py:29`), "is" before a value with a digit (`patterns.py:68`), values of 8+ chars with a digit or 16+ of any kind, `xapp-` tokens (`catalogue.py:17`), new "password in a URL" pattern (`catalogue.py:26`). Tests: `test_patterns.py:103` (8 worded forms caught), `:119` (7 prose forms not caught: "GROWW_API_KEY is required", "API key: required", `${PGPASSWORD}`, `user:password@` ...), the planted-example test now covers 19 kinds. |
| 4 | Code folders never scanned | Accepted | Code files are scanned with the credential-shape patterns (`catalogue.py:75`, `scanner.py`); `.zip` members are unpacked like `.gz` (test fixtures included). Tests: `test_patterns.py:123`, `test_routine_gate.py:75` (token in `tools/x/notes.md` refused; example e-mail in a test file allowed), `:83` (zip). Full scan: 261 files clean. |
| 5 | Hook calls `python` | Accepted | `.githooks/pre-commit` uses `python3`, else `python`, else refuses with a clear message that says never use `--no-verify`. |
| 6 | Accepted limits | Agreed | Listed under "Known limits" in the story (`docs/stories/O-operations.md`, O5). |

**Routine dry run with the real alert** (throwaway copy named `trading-o5-dry-run`; hook off before, then the
SessionStart command, a clean base commit, then a planted Slack token in `journal/`):

```
before: []
after: [.githooks]
record scan: clean (14 files)
base committed (scan clean)
journal/o5-dry-run.md:2: Slack token
record scan: REFUSED, 1 finding(s); do not commit or send these files (values are not shown)
alert sent to #fno-desk
exit=1
```
HEAD stayed at the base commit. #fno-desk received at 00:46:17 CEST (13 Oct 2026), from the bot: "Public-record scan
refused a commit in trading-o5-dry-run (1 finding(s); values are not shown). Remove the values, then commit again;
never bypass the scan. journal/o5-dry-run.md:2: Slack token" (read back with the Slack connector; no value posted).

**Checks after round 2:** `python -m pytest -q`: 264 passed; `ruff check fno tests tools`: all passed;
`python tools/check_imports.py`: clean; `python tools/check_records.py`: clean (261 files).

**Remaining doubts (round 2):**
- The SessionStart hook is a Claude Code setting: it gates Claude sessions, not ChatGPT/Codex pushes or a person's
  own clone (CI still reports those after the push). Proven by the test and by this session's own hook, not yet by a
  newly started cloud session (some evidence: it is the documented cloud mechanism).
- Any session with `FNO_SLACK_BOT_TOKEN` set now posts a refusal to #fno-desk, builders included. That is deliberate
  (a refused commit is worth seeing), but it can add noise while sessions iterate.
- The 8-character / digit rule misses a short all-letter password next to a secret word ("password: sunshine").
