# A14 status (builder session 01FVYzWZtDAZrZLDZ6DtmSYL)

Updated: 14 Oct 2026, about 17:34 IST. **Done.**

- A14 (2c3865e) merged into main earlier (pushed head 70899dd).
- The Groww check (story/a14-groww-check, ee7f35b; judge 77 addendum 3 PASS, criterion 1 MET) merged exactly into main
  as **e49705e**, no conflicts. Full suite on that head with `env -u FNO_SLACK_BOT_TOKEN`: 3,105 passed; ruff, format
  and `tools/check_imports.py` clean. Main did not move during the run.
- `risk.margins.nse_span_check` is now set on main, so the job may write rows. The workflow is still
  `workflow_dispatch` only; its header gives the morning schedule (07:45 IST, retry 08:30) for whoever schedules it.
- C2 funds-at-entry: handed to another builder as a new story (orchestrator).
