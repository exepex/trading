"""Shared names and fixed strings. Change a value here, not where it is used."""

from __future__ import annotations

from datetime import time
from enum import StrEnum

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

# Order sides, one definition for the accounting ledgers, the charges model and the paper-account fills
SIDE_BUY, SIDE_SELL = "buy", "sell"
SIDES = (SIDE_BUY, SIDE_SELL)

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
RELEASE_REWRITTEN = "rewritten"  # present, but with other bytes than the first ones seen for that day

# NIFTY option-chain panel (story A3, fno/research_data/nifty_panel.py)
PANEL_FORMAT_UDIFF, PANEL_FORMAT_LEGACY = "udiff", "legacy"  # source_format: which F&O file a day's rows came from
PANEL_INDEX_CLOSE = "index-close"  # the index-close file of a day (underlying and India VIX)
PANEL_DAY_OK, PANEL_DAY_NO_FILE, PANEL_DAY_NO_INDEX = "ok", "no file", "no index close"  # a day's status (manifest)
PANEL_DAY_FAILED = "failed"  # the day breaks the research-ready gate: the build fails, naming it
NIFTY_SYMBOL, INDEX_OPTION, INDEX_FUTURE = "NIFTY", "IDO", "IDF"  # F&O symbol; UDiFF codes of index options, futures

# Google Drive uploads as the owner (OAuth "Desktop app" client, one-time consent with tools/gdrive_oauth_setup.py);
# values only in the cloud environment's settings, never in files or chat. Service accounts cannot upload (no quota).
ENV_GDRIVE_OAUTH_CLIENT_ID = "FNO_GDRIVE_OAUTH_CLIENT_ID"
ENV_GDRIVE_OAUTH_CLIENT_SECRET = "FNO_GDRIVE_OAUTH_CLIENT_SECRET"
ENV_GDRIVE_OAUTH_REFRESH_TOKEN = "FNO_GDRIVE_OAUTH_REFRESH_TOKEN"
DRIVE_FULL_SCOPE = "https://www.googleapis.com/auth/drive"  # needed to add files inside the owner's existing folders

# Research features (story B1, fno/research_engine/): the names policies refer to, and when a day's close is known
FEATURE_ATM_IV_MINUS_RV20 = "F1_atm_iv_minus_rv20"  # ATM implied minus past 20-day realised volatility, in points
FEATURE_VIX_ABOVE_MEDIAN = "F2_vix_above_250d_median"  # India VIX close above its previous 250 closes' median
FEATURE_EVENT_IN_WINDOW = "F3_scheduled_event_in_window"  # a known scheduled event after entry, up to exit
SESSION_CLOSE_TIME = time(15, 30)  # IST: a regular or special session's closing prices exist from here
OPTION_CALL, OPTION_PUT = "CE", "PE"

# Cycle simulator (story B2, fno/research_engine/): structure codes, as the experiment 1 protocol names them
STRUCTURE_SHORT_IRON_FLY, STRUCTURE_SHORT_CONDOR, STRUCTURE_LONG_IRON_FLY = "SF", "SC", "BF"
STRUCTURES = (STRUCTURE_SHORT_IRON_FLY, STRUCTURE_SHORT_CONDOR, STRUCTURE_LONG_IRON_FLY)


class CycleStatus(StrEnum):
    """Every outcome of one structure in one monthly cycle (story B2); story B3 consumes exactly these values."""

    TRADED = "traded"
    NO_TRADE_CAP = "no_trade_cap"  # every listed, priceable width breaks the Rs 10,000 cap
    MISSING_STRIKES = "missing_strikes"  # a data condition: no width has all its strikes listed on the entry day
    NO_ENTRY_WINDOW = "no_entry_window"  # the entry day is not before the exit day
    UNFILLABLE = "unfillable"  # a missing or zero price, or more than half the legs on settlement prices
    BAD_PRICES = "bad_prices"  # stale prices: a short credit at least the width, or a long debit at most zero


# Policy runner (story B3): the periods of an experiment, and an opportunity a policy chose not to trade
PERIOD_DISCOVERY, PERIOD_CHALLENGE = "discovery", "challenge"
NO_TRADE = "no_trade"

# Live 15:00 feature versions (story B7): different features from F1-F3, validated against them before use
FEATURE_ATM_IV_MINUS_RV20_LIVE = "F1_live_atm_iv_minus_rv20"
FEATURE_VIX_ABOVE_MEDIAN_LIVE = "F2_live_vix_above_250d_median"
FEATURE_EVENT_IN_WINDOW_LIVE = "F3_live_scheduled_event_in_window"
ENV_GITHUB_RUN_ID, ENV_GITHUB_RUN_ATTEMPT = "GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT"  # set by GitHub Actions (P7)
ENV_FNO_DB_URL = "FNO_DB_URL"  # the fno schema's runtime publisher role (stories P3, P6); environment settings only

# Risk manager (story C2, fno/risk/): the owner's restart entry for a book's drawdown brake, and the two frozen ways
# to stress a margin
OWNER_OVERRIDES_FILE = "owner_overrides.csv"  # journal/<book>/owner_overrides.csv, written by the owner only
OVERRIDE_RESTART_BRAKE = "restart_brake"
STRESSED_MARGIN_SCENARIO_LOOKUP, STRESSED_MARGIN_MULTIPLIER = "scenario_lookup", "multiplier"
STRESSED_MARGIN_METHODS = (STRESSED_MARGIN_SCENARIO_LOOKUP, STRESSED_MARGIN_MULTIPLIER)

# Daily forecasts (epic G, research/forecasts/PROTOCOL.md): the five frozen questions and who answers them
FORECAST_Q1_UP_20D = "q1_nifty_up_20d"  # P(NIFTY close in 20 trading days > today's close)
FORECAST_Q2_MOVE_3PCT_20D = "q2_nifty_move_3pct_20d"  # P(|NIFTY return over 20 trading days| >= 3%)
FORECAST_Q3_RV_RISES_20D = "q3_rv20_above_trailing"  # P(next-20-day realised vol > trailing 20-day realised vol)
FORECAST_Q4_VIX_UP_10D = "q4_vix_up_10d"  # P(India VIX close in 10 trading days > today's close)
FORECAST_Q5_RV_BELOW_IV = "q5_rv20_below_atm_iv30"  # P(next-20-day realised vol < today's 30-day ATM IV)
FORECAST_QUESTIONS = (
    FORECAST_Q1_UP_20D, FORECAST_Q2_MOVE_3PCT_20D, FORECAST_Q3_RV_RISES_20D, FORECAST_Q4_VIX_UP_10D,
    FORECAST_Q5_RV_BELOW_IV,
)  # fmt: skip
BASELINE_RISK_NEUTRAL, BASELINE_BASE_RATE, BASELINE_MODEL = (
    "baseline_a_risk_neutral",
    "baseline_b_base_rate",
    "baseline_c_model",
)
FORECASTERS = BOOKS + (BASELINE_RISK_NEUTRAL, BASELINE_BASE_RATE, BASELINE_MODEL)

# Company filings archive (story A12, fno/filings/): the filing types archived, and where NSE serves their files
FILING_RESULTS, FILING_SHAREHOLDING = "results-xbrl", "shareholding-xbrl"  # one XBRL file per filing
FILING_ANNOUNCEMENTS, FILING_BOARD_MEETINGS = "announcements", "board-meetings"  # one all-company list per day
FILING_FILE_KINDS = (FILING_RESULTS, FILING_SHAREHOLDING)
CONSOLIDATED, STANDALONE = "consolidated", "standalone"
NSE_FILINGS_FOLDER = "nse/equities/filings"  # archive folder of every NSE filing type

# Story O6: GitHub Actions fetch, then fire the Claude routine that reasons on the new data. One trigger ID and one
# bearer token per routine (made by the owner on the routine's web page, shown once); repository secrets only.
ENV_ROUTINE_DRY_RUN_TRIGGER_ID = "FNO_ROUTINE_DRY_RUN_TRIGGER_ID"
ENV_ROUTINE_DRY_RUN_TOKEN = "FNO_ROUTINE_DRY_RUN_TOKEN"
ROUTINE_DRY_RUN = "dry-run"  # the example reasoning routine: reads a pointer, writes a small derived summary
PIPELINE_AREA, DERIVED_AREA = "pipeline", "derived"  # Drive areas beside raw/ and revisions/ (fno/storage/README.md)
