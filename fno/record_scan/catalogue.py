"""The patterns the public-record scan uses (story O5): credentials, personal data and broker identifiers.

Each regex is tuned so that the repository's numbers, hashes, contract names and prose do not trip it; where a kind of
value cannot be told apart from ordinary numbers without context (an Indian mobile number looks like a volume), the
pattern asks for that context and the limit is written next to it.
"""

from __future__ import annotations

import re

from .. import constants
from .patterns import AadhaarPattern, RecordPattern, RegexPattern, SecretAssignmentPattern

# Credentials with a recognisable shape (the provider's documented prefix or format)
PRIVATE_KEY = r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
SLACK_TOKEN = r"\bxox[abposr]-[A-Za-z0-9-]{10,}"
SLACK_WEBHOOK = r"hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+"
GITHUB_TOKEN = r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})"
GOOGLE_API_KEY = r"\bAIza[0-9A-Za-z_-]{35}"
AWS_ACCESS_KEY = r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"
AI_API_KEY = r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}"
JWT = r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"  # Groww access and MotherDuck tokens
BEARER = r"\bBearer[ \t]+[A-Za-z0-9._~+/-]{20,}=*"
# A value written next to a word that names a secret (`api_key: ...`, `"password": "..."`)
SECRET_WORDS = (
    "api[_-]?key", "api[_-]?secret", "secret[_-]?key", "client[_-]?secret", "access[_-]?token", "auth[_-]?token",
    "refresh[_-]?token", "bot[_-]?token", "totp[_-]?secret", "password", "passwd", "private[_-]?key",
)  # fmt: skip
SECRET_WORD_STEMS = ("key", "token", "secret", "passw")  # every secret word contains one of these
SECRET_MIN_LENGTH = 16
ENV_SECRET_MIN_LENGTH = 8

# Personal data
EMAIL = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b"
# Indian mobile numbers: only with +91 or a phone word nearby. A bare 10-digit number is indistinguishable from a
# traded volume or a turnover, so it is not flagged (limit stated in the story's claims).
PHONE_WORDS = ("+91", "phone", "mobile", "mob", "tel", "whatsapp", "contact")
PHONE = (
    r"(?:\+91[ -]?|(?i:phone|mobile|mob\.?|tel\.?|whatsapp|contact)[^\d\n]{0,12})"
    r"(?P<value>[6-9]\d{4}[ -]?\d{5})(?![\w.])"
)
PAN = r"\b[A-Z]{3}[ABCFGHJLPT][A-Z]\d{4}[A-Z]\b"  # 4th letter is the holder type (P = person, C = company, ...)

# Broker client and account identifiers, and Groww order or account fields (machine field names are lower-case snake
# case; upper-case environment-variable names such as `GITHUB_OAUTH_CLIENT_ID` are not broker fields)
DEMAT_ACCOUNT = r"(?<![\w.])(?:IN\d{14}|1[23]\d{14})(?![\w.])"  # NSDL (IN + 14 digits) and CDSL (16 digits) BO IDs
BROKER_FIELDS = (
    "groww_order_id", "order_reference_id", "exchange_order_id", "exchange_trade_id", "groww_trade_id",
    "client_id", "client_code", "ucc", "demat_id", "demat_account", "demat_account_number", "dp_id", "bo_id",
    "account_id", "account_no", "account_number", "bank_account", "ifsc", "vendor_user_id", "user_id",
)  # fmt: skip
_FIELD = rf"(?:{'|'.join(BROKER_FIELDS)})"
# A field with a value (`"client_code": "AB1234"`, `ucc=...`; `groww_client_id` too), or a CSV column of that name.
# The bare name in prose (`ucc`, `client_code`) is not a finding: it exposes nothing.
BROKER_FIELD = (
    rf"(?<![A-Za-z0-9]){_FIELD}(?![A-Za-z0-9])[\"']?[ \t]*[:=][ \t]*[\"']?[A-Za-z0-9][A-Za-z0-9_-]{{3,}}"
    rf"|(?m:(?:^|,)[ \t]*\"?{_FIELD}\"?[ \t]*(?=,)|,[ \t]*\"?{_FIELD}\"?[ \t]*\r?$)"
)
# Slack IDs of users, workspaces and channels (letter, digit, then 7-10 more): only #fno-desk is allowed
SLACK_ID = r"\b[CDGTUW]\d[A-Z0-9]{7,10}\b"

ALLOWED_VALUES = frozenset({constants.FNO_DESK_CHANNEL_ID})


def secret_env_names() -> list[str]:
    """Every environment-variable name in `fno/constants.py` (all of them hold secrets or private IDs)."""
    return [value for key, value in vars(constants).items() if key.startswith("ENV_")]


def record_patterns() -> list[RecordPattern]:
    return [
        RegexPattern("private key", PRIVATE_KEY, required=["private key"]),
        RegexPattern("Slack token", SLACK_TOKEN, required=["xox"]),
        RegexPattern("Slack webhook", SLACK_WEBHOOK, required=["hooks.slack.com"]),
        RegexPattern("GitHub token", GITHUB_TOKEN, required=["gh", "github_pat_"]),
        RegexPattern("Google API key", GOOGLE_API_KEY, required=["aiza"]),
        RegexPattern("AWS access key", AWS_ACCESS_KEY, required=["akia", "asia"]),
        RegexPattern("AI API key", AI_API_KEY, required=["sk-"]),
        RegexPattern("JSON web token", JWT, required=["eyj"]),
        RegexPattern("bearer token", BEARER, required=["bearer"]),
        SecretAssignmentPattern("value of a secret environment variable", secret_env_names(), ENV_SECRET_MIN_LENGTH),
        SecretAssignmentPattern(
            "value next to a secret's name", SECRET_WORDS, SECRET_MIN_LENGTH, re.IGNORECASE, SECRET_WORD_STEMS
        ),
        RegexPattern("e-mail address", EMAIL, required=["@"]),
        RegexPattern("phone number", PHONE, required=PHONE_WORDS),
        RegexPattern("PAN", PAN),
        AadhaarPattern("Aadhaar number"),
        RegexPattern("demat account ID", DEMAT_ACCOUNT),
        RegexPattern("broker order or account field", BROKER_FIELD, required=BROKER_FIELDS),
        RegexPattern("Slack user, workspace or channel ID", SLACK_ID),
    ]
