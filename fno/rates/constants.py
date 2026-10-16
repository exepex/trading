"""The rates capture's fixed names (story A21), used only by `fno/rates/`."""

RBI_HOME = "https://www.rbi.org.in/"
RBI_RELEASES = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx"
RBI_RELEASE = RBI_RELEASES + "?prid={prid}"
TBILL_TITLE = "91-Day, 182-Day and 364-Day T-Bill Auction Result: Cut-off"  # matched exactly, never loosely

TBILL_91, TBILL_182, TBILL_364 = "tbill_91d_cutoff", "tbill_182d_cutoff", "tbill_364d_cutoff"
POLICY_REPO = "policy_repo"
TBILL_RATES = (TBILL_91, TBILL_182, TBILL_364)  # in the release's column order
RATES = (*TBILL_RATES, POLICY_REPO)
LIVE = "live"
HOME_NOTE = "as shown by RBI's home page"  # the home page gives no effective date

TABLE = "rates/table"  # O9 part table under Drive's data area
RAW_FOLDER = "rates/rbi"  # each fetched page, write-once
COLUMNS = ("rate", "value_date", "value_pct", "release_no", "source_url", "source_sha256", "first_seen_at",
           "provenance", "note")  # fmt: skip

JOB = "rates"
WRITER = "rates-capture"
TIMEOUT_SECONDS = (5, 20)  # connect, read
STALE_AUCTION_DAYS = 8  # the auctions are weekly; a holiday moves one by a day
STALE_HOME_HOURS = 48  # two runs a day: two days without a home-page read is stale
GRACE_HOURS = 24  # the home page may update after the release (judge 355 SF3)
