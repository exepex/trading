"""Shared names and fixed strings. Change a value here, not where it is used."""

from __future__ import annotations

# Environment variable names (values are never stored in files).
# Groww Trade API (market data only; the tool never places orders)
ENV_GROWW_ACCESS_TOKEN = "GROWW_ACCESS_TOKEN"
ENV_GROWW_API_KEY = "GROWW_API_KEY"
ENV_GROWW_API_SECRET = "GROWW_API_SECRET"
ENV_GROWW_TOTP_SECRET = "GROWW_TOTP_SECRET"
# Raw-file archive on Google Drive (fno/storage): read-only service account; both only in the environment
ENV_GDRIVE_SERVICE_ACCOUNT_JSON = "FNO_GDRIVE_SERVICE_ACCOUNT_JSON"  # the key's JSON text, or it base64-encoded
ENV_GDRIVE_FOLDER_ID = "FNO_GDRIVE_FOLDER_ID"  # the shared folder's ID (from its Drive link)

# How this tool names itself to public websites (NSE): honest, and accepted by them
RESEARCH_USER_AGENT = "Mozilla/5.0 (compatible; fno-desk/1.0; personal research)"

# Month codes in NSE file names and dates (e.g. fo02JAN2019bhav), independent of the computer's language settings
MONTH_CODES = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
