"""Story A17e, criteria 1 and 2: every world source reads its publisher's layout and refuses an error page, an empty
answer and a changed layout; CSIndex's fake start-date row never enters a table; Yahoo dates are the exchange's own."""

from datetime import date, time

import pytest

from fno.global_cues.asia_sources import (
    FAKE_ROW_MARGIN,
    CsindexShanghaiSource,
    NikkeiSource,
    TwseTaiexSource,
)
from fno.global_cues.collector import CueCollector
from fno.global_cues.europe_sources import CBOE_VIX_FILE, CboeVixSource, StoxxSource
from fno.global_cues.markets import FRANKFURT, HONG_KONG, SYDNEY, TOKYO
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.yahoo_source import UNVERIFIED, YahooChartSource
from fno.storage.raw_store import LocalFolderStore
from tests.global_cues.world_fakes import NIKKEI, csindex, stoxx, twse, utc, yahoo_chart

ERROR_PAGE = b"<html><body>Service unavailable</body></html>"
TOKYO_ZONE = "Asia/Tokyo"
TWO_DAYS = [date(2026, 10, 20), date(2026, 10, 21)]


def _days(values):
    return [v.value_date for v in values]


def test_csindex_asks_ten_days_early_so_the_fake_start_row_is_never_kept(tmp_path):
    source = CsindexShanghaiSource()
    request = source.requests(date(2026, 10, 1), date(2026, 10, 9))[0]
    assert "startDate=20260921" in request.url and FAKE_ROW_MARGIN.days == 10
    # 21 Sep is the request's first date: CSIndex copies the next session there (as on 2026-10-01); a real flat
    # close two sessions running stays (no equality guess)
    answer = csindex(("20260921", 50.0), ("20260922", 50.0), ("20260930", 51.0), ("20261009", 51.0))

    class Canned(CsindexShanghaiSource):
        def download(self, session, request):
            return answer

    result = CueCollector(None, LocalFolderStore(tmp_path / "drive"), SnapshotLog(tmp_path / "log"),
                          lambda: _seen()).collect(Canned(), date(2026, 10, 1), date(2026, 10, 9))  # fmt: skip
    assert [v.value.value_date for v in result.values] == [date(2026, 10, 9)]
    assert [v.value_date for v in source.parse(answer)][:2] == [date(2026, 9, 21), date(2026, 9, 22)]


def _seen():
    from datetime import datetime

    from fno.models import IST

    return datetime(2026, 10, 22, 5, 30, tzinfo=IST)


@pytest.mark.parametrize(
    ("source", "good", "days"),
    [
        (CsindexShanghaiSource(), csindex(("20261020", 10.5), ("20261021", 11.0)), TWO_DAYS),
        (TwseTaiexSource(), twse(("1151020", "20.5"), ("1151021", "21.0")), TWO_DAYS),
        (NikkeiSource(), NIKKEI, TWO_DAYS),
        (StoxxSource("dax", "dax", "DAX", FRANKFURT), stoxx("DAX", ("20.10.2026", 30.5)), [date(2026, 10, 20)]),
    ],
    ids=lambda x: getattr(x, "cue", None),
)  # fmt: skip
def test_each_official_layout_is_read_and_an_error_page_an_empty_answer_and_a_changed_layout_refused(
    source, good, days
):
    assert _days(source.parse(good)) == days
    with pytest.raises(ValueError, match=source.cue):
        source.parse(ERROR_PAGE)
    with pytest.raises((ValueError, KeyError)):
        source.parse(good.replace(b"lose", b"lsoe").replace(b"Date", b"Dtae").replace(b"DAX", b"SX5E"))


def test_empty_answers_taiex_month_start_is_empty_the_others_refuse():
    assert TwseTaiexSource().parse(twse()) == []  # a month before its first session
    for source, empty in ((CsindexShanghaiSource(), csindex()), (NikkeiSource(), NIKKEI.split(b"\r\n")[0])):
        with pytest.raises(ValueError, match="no values"):
            source.parse(empty)


def test_a_bad_twse_date_and_a_stoxx_row_of_another_index_are_refused():
    with pytest.raises(ValueError, match="bad TWSE date"):
        TwseTaiexSource().parse(twse(("2026-10-21", "1.0")))
    with pytest.raises(ValueError, match="another index"):
        StoxxSource("dax", "dax", "DAX").parse(stoxx("SX5E", ("20.10.2026", 1.0)))


def test_vix_reads_cboes_spx_layout_from_its_own_file():
    request = CboeVixSource().requests(date(2019, 1, 1), date(2026, 10, 21))[0]
    assert request.url == CBOE_VIX_FILE and CboeVixSource().private


def yahoo(cue="nikkei225_yahoo", verified=True):
    return YahooChartSource(cue, "^N225", TOKYO, 7, verified)


def test_yahoo_dates_are_the_exchanges_own_and_a_close_without_value_is_skipped():
    day = date(2026, 10, 21)
    rows = [
        (utc(date(2026, 10, 20), time(0, 0)), 10.0),
        (utc(day, time(14, 59, 59)), 11.0),
        (utc(date(2026, 10, 22), time(0)), None),
    ]
    values = yahoo().parse(yahoo_chart(TOKYO_ZONE, rows))
    # 00:00 UTC is 09:00 in Tokyo, the same date; 14:59:59 UTC is 23:59:59 Tokyo, still 21 Oct; None is skipped
    assert _days(values) == [date(2026, 10, 20), day]
    sydney = YahooChartSource("asx200_yahoo", "^AXJO", SYDNEY, 7, False)
    opens = [(utc(date(2026, 10, 20), time(23, 0)), 5.0)]  # Sydney's 10:00 open of 21 Oct is 23:00 UTC on the 20th
    assert _days(sydney.parse(yahoo_chart("Australia/Sydney", opens, "^AXJO"))) == [day]


def test_a_date_given_twice_is_left_out_never_guessed_and_a_weekend_never_appears():
    rows = [
        (utc(date(2026, 10, 19), time(0)), 1.0),
        (utc(date(2026, 10, 20), time(0)), 2.0),
        (utc(date(2026, 10, 20), time(1)), 3.0),
    ]
    assert _days(yahoo().parse(yahoo_chart(TOKYO_ZONE, rows))) == [date(2026, 10, 19)]


@pytest.mark.parametrize("bad", [ERROR_PAGE, b"{}", yahoo_chart(TOKYO_ZONE, [])], ids=["page", "no result", "empty"])
def test_a_yahoo_answer_without_a_chart_or_timestamps_is_refused(bad):
    with pytest.raises((ValueError, KeyError)):
        yahoo().parse(bad)


def test_yahoo_only_indexes_say_unverified_and_ask_one_range_per_run():
    lone = YahooChartSource("hang_seng_yahoo", "^HSI", HONG_KONG, 7, verified=False)
    assert UNVERIFIED in lone.publisher and UNVERIFIED not in yahoo().publisher
    requests = lone.requests(date(2019, 1, 1), date(2026, 10, 21))
    assert len(requests) == 1 and "%5EHSI" in requests[0].url and "interval=1d" in requests[0].url
