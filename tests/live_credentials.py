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
    c.ENV_MOTHERDUCK_TOKEN,
    c.ENV_FNO_DB_URL,
    c.ENV_ROUTINE_DRY_RUN_TOKEN,
    c.ENV_ROUTINE_BOOK2_TOKEN,
    c.ENV_ROUTINE_BOOK3_TOKEN,
    c.ENV_GITHUB_TOKEN,
)
