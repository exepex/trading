"""Credentials that reach a real service. The test run removes every one (`conftest.no_real_credentials`)."""

from fno import constants as c

LIVE_CREDENTIALS = (
    c.ENV_GROWW_ACCESS_TOKEN,
    c.ENV_GROWW_API_KEY,
    c.ENV_GROWW_API_SECRET,
    c.ENV_GROWW_TOTP_SECRET,
    c.ENV_GDRIVE_SERVICE_ACCOUNT_JSON,
    c.ENV_GDRIVE_OAUTH_CLIENT_ID,
    c.ENV_GDRIVE_OAUTH_CLIENT_SECRET,
    c.ENV_GDRIVE_OAUTH_REFRESH_TOKEN,
    c.ENV_FNO_SLACK_BOT_TOKEN,  # a test through the real wiring posted fixture alerts to #fno-desk (14 Oct 2026)
    c.ENV_FRED_API_KEY,  # FRED's release-dates key (A20c): a test must never call FRED with the owner's key
    c.ENV_MOTHERDUCK_TOKEN,
    c.ENV_FNO_DB_URL,
    c.ENV_ROUTINE_DRY_RUN_TOKEN,
    c.ENV_ROUTINE_BOOK2_TOKEN,
    c.ENV_ROUTINE_BOOK3_TOKEN,
    c.ENV_ROUTINE_POSTMORTEM_TOKEN,
    c.ENV_GITHUB_TOKEN,
)
# Every other ENV_ name in fno/constants.py: identifiers, not credentials. A new ENV_ name must join one of the two.
NOT_CREDENTIALS = (
    c.ENV_GDRIVE_FOLDER_ID,
    c.ENV_GITHUB_RUN_ID,
    c.ENV_GITHUB_RUN_ATTEMPT,
    c.ENV_GITHUB_OUTPUT,  # an Actions step's outputs file path (O8b), not a secret
    c.ENV_ROUTINE_DRY_RUN_TRIGGER_ID,
    c.ENV_ROUTINE_BOOK2_TRIGGER_ID,
    c.ENV_ROUTINE_BOOK3_TRIGGER_ID,
    c.ENV_ROUTINE_POSTMORTEM_TRIGGER_ID,
)
