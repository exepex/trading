# A14 status (builder session 01FVYzWZtDAZrZLDZ6DtmSYL)

Updated: 14 Oct 2026, about 16:48 IST.

**A14 merged into main** after judge 77 addendum 1 PASS: exactly 2c3865e merged as 6568315 (conflicts in
`fno/constants.py` and `reviews/claude/README.md`, both sides kept). Full suite with `env -u FNO_SLACK_BOT_TOKEN`
3,092 passed, ruff, format and `tools/check_imports.py` clean, on 6568315. Pushed head **70899dd**, which adds only two
judge files from main (`reviews/judge/`) on top of the tested tree. `risk.margins.nse_span_check` is null on main: the
job writes no rows there.

**Groww check on its own branch** `story/a14-groww-check` (from main 70899dd): the Groww comparison in response 77
("Broker check 2"), `config.yaml` `risk.margins.nse_span_check` = "Groww margin API (read-only), orchestrator run",
2026-10-14, the margins README line, and the config test. **Ready for judge** at code tip `6f0501a` (full suite 3,092 passed; ruff and imports clean); the commit after it is this
status file. Open for the judge: the exposure base gap (row uses the previous close; on an up day about Rs 590 a lot
below Groww per 1% rise) and the funding-at-entry note (Groww asks for the bought premium up front; C2 nets premiums).
