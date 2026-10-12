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
# Other secrets the routines' environment holds; named here so the public-record scan (story O5) watches them too
ENV_FNO_SLACK_BOT_TOKEN = "FNO_SLACK_BOT_TOKEN"
ENV_MOTHERDUCK_TOKEN = "MOTHERDUCK_TOKEN"

# Slack channel for all F&O output (#fno-desk); its ID is public by design and allowed in committed records
FNO_DESK_CHANNEL_ID = "C0C89E8QCCD"

# How this tool names itself to public websites (NSE): honest, and accepted by them
RESEARCH_USER_AGENT = "Mozilla/5.0 (compatible; fno-desk/1.0; personal research)"

# Month codes in NSE file names and dates (e.g. fo02JAN2019bhav), independent of the computer's language settings
MONTH_CODES = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

# NSE session calendar (fno/research_data/calendar.py): kinds of rows in nse_sessions.csv, and of sessions
SESSION_HOLIDAY, SESSION_SPECIAL, SESSION_MUHURAT, SESSION_REGULAR = "holiday", "special", "muhurat", "regular"

# Index names in NSE's daily index-close file that every file must carry (the research needs both)
INDEX_NIFTY_50, INDEX_INDIA_VIX = "Nifty 50", "India VIX"

# The three paper books (design 12.1, story E1): each has its own Rs 5 lakh paper account under journal/<book>/account/
BOOK1_RULES = "book1_rules"  # pure rules
BOOK2_HYBRID = "book2_hybrid"  # AI inside the authority envelope
BOOK3_AI = "book3_ai"  # fully AI under the constitution
BOOKS = (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI)
JOURNAL_FOLDER = "journal"
# Kinds of row in a paper account's cash ledger (journal/<book>/account/cash_ledger.csv)
LEDGER_OPENING = "opening_balance"
LEDGER_FILL = "fill"

# NSE participant-wise open interest (story A8, fno/research_data/participant_oi.py): who holds the contracts, and the
# instrument groups NSE splits them into
PARTICIPANT_CLIENT, PARTICIPANT_DII, PARTICIPANT_FII, PARTICIPANT_PRO = "Client", "DII", "FII", "Pro"
PARTICIPANTS = (PARTICIPANT_CLIENT, PARTICIPANT_DII, PARTICIPANT_FII, PARTICIPANT_PRO)
OI_FUTURE_INDEX, OI_FUTURE_STOCK = "future_index", "future_stock"
OI_OPTION_INDEX_CALL, OI_OPTION_INDEX_PUT = "option_index_call", "option_index_put"
OI_OPTION_STOCK_CALL, OI_OPTION_STOCK_PUT = "option_stock_call", "option_stock_put"
OI_GROUPS = (
    OI_FUTURE_INDEX, OI_FUTURE_STOCK, OI_OPTION_INDEX_CALL, OI_OPTION_INDEX_PUT, OI_OPTION_STOCK_CALL,
    OI_OPTION_STOCK_PUT,
)  # fmt: skip
# Outcomes of one release-time check of a published file (fno/research_data/release_times.py)
RELEASE_PRESENT, RELEASE_ABSENT, RELEASE_UNREACHABLE = "present", "absent", "unreachable"
