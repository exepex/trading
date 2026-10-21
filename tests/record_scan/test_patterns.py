"""Story O5, criterion 1: a planted example of every pattern is caught; the #fno-desk channel ID and ordinary record
content (numbers, hashes, contract names, env-variable names without values) are not."""

import pytest

from fno.composition import build_record_scanner
from fno.constants import FNO_DESK_CHANNEL_ID, FNO_FORECAST_CHANNEL_ID, FNO_INTRADAY_CHANNEL_ID
from fno.record_scan.catalogue import ALLOWED_VALUES
from fno.record_scan.catalogue import record_patterns
from fno.record_scan.patterns import verhoeff_valid

# Planted values are assembled from pieces so that no complete fake credential sits in the source (GitHub's push
# protection would block it, and a reader could mistake it for a leak).
PLANTED = {
    "private key": "key: -----BEGIN RSA " + "PRIVATE KEY-----",
    "Slack token": "token xox" + "b-1234567890-abcdefghij",
    "Slack webhook": "url https://hooks.slack.com/services/" + "T0123ABCD/B0123ABCD/abcdefghijklmnop",
    "GitHub token": "gh" + "p_" + "a1B2" * 9,
    "Google API key": "AI" + "za" + "Sy" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q",
    "AWS access key": "AK" + "IA" + "ABCDEFGHIJ234567",
    "AI API key": "sk" + "-ant-" + "abcdefghijklmnopqrstuvwxyz",
    "JSON web token": "ey"
    + "JhbGciOiJIUzI1NiJ9.ey"
    + "JzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
    "bearer token": "Authorization: Bear" + "er abcdefghijklmnopqrstuvwxyz012345",
    "password in a URL": "postgresql://omenix:" + "S3cretPw@db.example.local:5432/fno",
    "value of a secret environment variable": "GROWW_" + "ACCESS_TOKEN=abc123def456ghi",
    "value next to a secret's name": '{"api_' + 'key": "Zx81kq0LmN3pR7tYw2"}',
    "e-mail address": "owner: someone" + "@example.com",
    "phone number": "call +91 98" + "765 43210",
    "PAN": "pan ABCPE" + "1234F",
    "Aadhaar number": "uid 2341 " + "2341 2346",
    "demat account ID": "bo 12081600" + "00012345",
    "broker order or account field": '{"groww_' + 'order_id": "GMK39038RDT"}',
    "Slack user, workspace or channel ID": "uploaded by U0" + "12AB3CDE",
}


def kinds(text: str) -> list[str]:
    return [finding.kind for finding in build_record_scanner().scan_text("journal/x.md", text)]


def test_every_pattern_has_a_planted_example():
    assert {pattern.name for pattern in record_patterns()} == set(PLANTED)


@pytest.mark.parametrize("kind", sorted(PLANTED))
def test_planted_example_is_caught_by_its_pattern(kind):
    assert kind in kinds(f"line one\nsome record text {PLANTED[kind]} end\n")


def test_finding_names_file_line_and_kind_never_the_value():
    findings = build_record_scanner().scan_text("journal/2026-10-13.md", "ok\n" + PLANTED["Slack token"] + "\n")
    assert [str(f) for f in findings] == ["journal/2026-10-13.md:2: Slack token"]
    assert "abcdefghij" not in str(findings[0])


def test_allow_listed_channel_id_is_not_caught():
    assert (
        kinds(f"posted to #fno-desk ({FNO_DESK_CHANNEL_ID}): https://x.slack.com/archives/{FNO_DESK_CHANNEL_ID}/p1")
        == []
    )


def test_exactly_the_three_fno_channels_are_allowed_and_a_fourth_id_is_caught():
    """Story FL1: #fno-desk, #fno-forecast and #fno-intraday, nothing else (a fourth channel needs its own decision)."""
    assert ALLOWED_VALUES == {FNO_DESK_CHANNEL_ID, FNO_FORECAST_CHANNEL_ID, FNO_INTRADAY_CHANNEL_ID}
    for channel in (FNO_FORECAST_CHANNEL_ID, FNO_INTRADAY_CHANNEL_ID):
        assert kinds(f"report posted to {channel}") == []
    assert kinds("posted to C0ZZZ12345Q") == ["Slack user, workspace or channel ID"]


@pytest.mark.parametrize(
    "safe",
    [
        "raw_sha256 9010bd24a274b72d049acbdfb3fb799261817164ab180821e74ee75d76296197",  # digits inside a hash
        "NIFTY,2026-10-28,24500,CE,112.35,113.10,7563450,6123456789",  # prices, volume, turnover
        "set GROWW_API_KEY and GROWW_API_SECRET in the environment",  # a name without a value
        "GROWW_ACCESS_TOKEN=${GROWW_ACCESS_TOKEN}",  # a placeholder
        "`ANTHROPIC_API_KEY`, `GITHUB_OAUTH_CLIENT_ID`, `SESSION_SECRET`",  # upper-case env names, not broker fields
        "NSE circular CMTR73362.pdf; ISIN INE002A01018; 1728899123456 ms",
        "234123412345",  # 12 digits with a wrong Aadhaar check digit
    ],
)
def test_ordinary_record_content_is_not_caught(safe):
    assert kinds(safe) == []


@pytest.mark.parametrize("header", ["date,ucc,qty", "ucc,qty", "date,qty,client_code", 'a,"account_number",b'])
def test_broker_field_as_a_csv_column_is_caught(header):
    assert kinds(f"{header}\n1,2,3\n") == ["broker order or account field"]


def test_broker_field_name_in_prose_is_not_caught():
    assert kinds("fields such as `ucc`, `client_code` and `groww_order_id` must never be committed") == []


# Judge 2, finding 3: secrets written the way a person writes them
@pytest.mark.parametrize(
    "worded",
    [
        "Groww API key: " + "Ab3dE6gH9jK2mN5pQ8rS1tU",
        "API secret: " + "7f3a9c1e5b2d8f4a",
        "TOTP secret: " + "JBSWY3DPEHPK3PXP",
        "access token: " + "q8Zr2LmN0pX4vT7w",
        "GROWW_API_SECRET is " + "9f8e7d6c5b4a",
        "export GROWW_API_SECRET=" + "9f8e7d6c5b4a",
        "password: " + "hunter2go",
        "slack app token xapp-1-" + "A0123BCDEF-1234567890-abcdef0123",
    ],
)
def test_secret_written_in_words_is_caught(worded):
    assert kinds(worded)


@pytest.mark.parametrize(
    "prose",
    [
        "GROWW_API_KEY is required",
        "API key: required for Groww",
        "password: see the vault",
        "set the access token in the environment",
        "postgresql://user:${PGPASSWORD}@host/db",
        "https://user:password@host",
        "https://nsearchives.nseindia.com/content/fo/BhavCopy.csv.zip",
    ],
)
def test_secret_words_in_prose_are_not_caught(prose):
    assert kinds(prose) == []


def test_code_is_scanned_for_credential_shapes_only():
    scanner = build_record_scanner()
    assert [f.kind for f in scanner.scan_text("fno/x.py", PLANTED["Slack token"], is_code=True)] == ["Slack token"]
    assert scanner.scan_text("tests/x.py", PLANTED["e-mail address"] + " " + PLANTED["PAN"], is_code=True) == []


def test_binary_content_is_reported_not_skipped():
    assert kinds("PK\x00\x03 zipped") == ["binary content that cannot be scanned"]


def test_verhoeff_check_digit():
    assert verhoeff_valid("234123412346") and not verhoeff_valid("234123412347")
