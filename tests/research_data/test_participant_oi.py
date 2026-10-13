"""Story A8 criterion 2: the parser returns exactly the numbers in three real NSE files (2019, 2022, 2026), and refuses
a damaged or foreign file instead of reading it partly."""

from datetime import date
from pathlib import Path

import pytest

from fno.constants import OI_GROUPS, PARTICIPANTS
from fno.fo_bhavcopy import BadFile
from fno.research_data.participant_oi import read_participant_oi

NSE = Path(__file__).resolve().parents[1] / "fixtures" / "nse"
JAN_3 = date(2022, 1, 3)

# Read by hand from the files: per participant, (long, short) for future index, future stock, index call, index put,
# stock call, stock put, then the totals. NSE's columns are FIL FIS FSL FSS, then option longs (index call, index put,
# stock call, stock put) interleaved with shorts as OICL OIPL OICS OIPS OSCL OSPL OSCS OSPS, then total long and short.
HAND_READ = {
    date(2019, 6, 3): {
        "Client": [
            (162598, 202641),
            (858901, 270077),
            (370204, 447166),
            (597184, 688392),
            (163404, 140809),
            (86818, 86802),
            (2239109, 1835887),
        ],  # noqa: E501
        "DII": [(47103, 41898), (18346, 924430), (24392, 0), (77195, 0), (0, 486), (0, 0), (167036, 966814)],
        "FII": [
            (151019, 86916),
            (845443, 589061),
            (158311, 52865),
            (266955, 126950),
            (12794, 12930),
            (16438, 14799),
            (1450960, 883521),
        ],  # noqa: E501
        "Pro": [
            (16846, 46111),
            (132297, 71419),
            (130181, 183057),
            (121764, 247756),
            (39935, 61908),
            (33661, 35316),
            (474684, 645567),
        ],  # noqa: E501
    },
    date(2022, 1, 3): {
        "Client": [
            (170144, 163764),
            (1448260, 169503),
            (1406545, 1500671),
            (2282579, 2324827),
            (508110, 358567),
            (220003, 297100),
            (6035640, 4814432),
        ],  # noqa: E501
        "DII": [(14304, 71357), (38071, 1691586), (819, 0), (80747, 0), (0, 34877), (0, 0), (133941, 1797820)],
        "FII": [
            (127535, 55563),
            (913854, 711756),
            (306326, 216510),
            (342071, 230730),
            (43094, 54464),
            (42159, 34277),
            (1775038, 1303300),
        ],  # noqa: E501
        "Pro": [
            (21082, 42381),
            (253095, 80435),
            (524049, 520558),
            (596601, 746440),
            (135310, 238606),
            (166530, 97315),
            (1696667, 1725734),
        ],  # noqa: E501
    },
    date(2026, 10, 9): {
        "Client": [
            (291627, 62104),
            (3402919, 185348),
            (3396080, 3337345),
            (3418874, 4049875),
            (2104606, 1206045),
            (822867, 1081989),
            (13436973, 9922706),
        ],  # noqa: E501
        "DII": [
            (48096, 16166),
            (289466, 4646105),
            (90783, 3788),
            (62924, 1452),
            (12110, 349667),
            (43691, 34218),
            (547070, 5051396),
        ],  # noqa: E501
        "FII": [
            (34943, 328931),
            (3542863, 2867395),
            (600034, 946852),
            (1245164, 704672),
            (197429, 347630),
            (316370, 186717),
            (5936804, 5382197),
        ],  # noqa: E501
        "Pro": [
            (64003, 31468),
            (833668, 370068),
            (1317359, 1116272),
            (1294501, 1265464),
            (916553, 1327356),
            (1011209, 891213),
            (5437293, 5001841),
        ],  # noqa: E501
    },
}


def real_file(day: date) -> tuple[str, bytes]:
    name = f"fao_participant_oi_{day:%d%m%Y}.csv"
    return name, (NSE / name).read_bytes()


@pytest.mark.parametrize("day", sorted(HAND_READ))
def test_the_parser_returns_the_numbers_read_by_hand(day):
    name, data = real_file(day)
    oi = read_participant_oi(data, name, day)
    assert oi.day == day
    for participant in PARTICIPANTS:
        *groups, total = HAND_READ[day][participant]
        got = [(oi.position(participant, g).long, oi.position(participant, g).short) for g in OI_GROUPS]
        assert got == groups
        assert (oi.totals[participant].long, oi.totals[participant].short) == total


def test_net_is_long_minus_short():
    name, data = real_file(date(2026, 10, 9))
    assert read_participant_oi(data, name, date(2026, 10, 9)).position("FII", "future_index").net == 34943 - 328931


def test_the_three_files_span_the_formats_nse_used():
    raw = {day: real_file(day)[1] for day in HAND_READ}
    assert b'""Participant' in raw[date(2022, 1, 3)]  # doubled quotes split the title at its comma
    assert b"Future Stock Short\t" in raw[date(2022, 1, 3)] and b"Future Stock Short       " in raw[date(2026, 10, 9)]


def test_nse_rounding_of_up_to_two_contracts_is_accepted_but_more_is_damage():
    name, data = real_file(JAN_3)  # NSE's own client long groups add up to 6035641, total says 6035640
    assert read_participant_oi(data, name, JAN_3).totals["Client"].long == 6035640
    assert read_participant_oi(data.replace(b",6035640,", b",6035641,"), name, JAN_3)  # column now 2 off TOTAL
    with pytest.raises(BadFile, match="add up to"):
        read_participant_oi(data.replace(b",6035640,", b",6035644,"), name, JAN_3)  # 3 off their parts


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ((b"FII,127535", b"FII,127935"), "add up to"),  # one digit changed
        ((b"FII,127535", b"FII,12753x"), "not a whole number"),
        ((b"\nPro,", b"\nProp,"), "participants"),
        ((b"Jan 03,2022", b"Jan 04,2022"), "title says"),
        ((b"Future Index Long", b"Future Index Lon"), "unexpected columns"),
    ],
)
def test_a_damaged_or_foreign_file_is_refused(change, message):
    name, data = real_file(date(2022, 1, 3))
    with pytest.raises(BadFile, match=message):
        read_participant_oi(data.replace(*change), name, date(2022, 1, 3))


def test_a_file_cut_short_is_refused():
    name, data = real_file(date(2019, 6, 3))
    with pytest.raises(BadFile):
        read_participant_oi(data[: len(data) // 2], name, date(2019, 6, 3))
    with pytest.raises(BadFile):
        read_participant_oi(b"\xff\xfe\x00", name, date(2019, 6, 3))


@pytest.mark.parametrize(
    "title", [b"as on Jan 03 2022", b'as on Jan 03,"2022"""""', b"as on Jan 03 ,2022", b"as on January 03, 2022"]
)
def test_the_hand_typed_title_dates_nse_used_are_read(title):
    """Seen in NSE's 2019-2020 files: no comma, quoted year, comma before the year, full month name."""
    name, data = real_file(date(2022, 1, 3))
    assert read_participant_oi(data.replace(b"as on Jan 03,2022", title), name, date(2022, 1, 3)).day == date(
        2022, 1, 3
    )


def test_numbers_written_with_indian_grouping_and_a_zero_fraction_are_read_but_a_real_fraction_is_refused():
    """12 Dec 2019's FII row reads "80,776.00","10,02,064.00", ..."""
    name, data = real_file(date(2022, 1, 3))
    grouped = data.replace(b"FII,127535,55563,913854,", b'FII,"1,27,535.00",55563,"9,13,854.00",')
    oi = read_participant_oi(grouped, name, JAN_3)
    assert (oi.position("FII", "future_index").long, oi.position("FII", "future_stock").long) == (127535, 913854)
    with pytest.raises(BadFile, match="not a whole number"):
        read_participant_oi(data.replace(b"FII,127535,", b"FII,127535.50,"), name, JAN_3)
    with pytest.raises(BadFile, match="not a whole number"):
        read_participant_oi(data.replace(b"FII,127535,", b"FII,-127535,"), name, JAN_3)


def test_a_title_without_a_year_must_still_match_month_and_day_and_unnamed_columns_are_ignored():
    """8 Jun 2021's title has no year; 22 Feb 2024 has a 16th column with no name (one stray sum in the FII row)."""
    name, data = real_file(JAN_3)
    no_year = data.replace(b"as on Jan 03,2022", b"as on Jan 03")
    assert read_participant_oi(no_year, name, JAN_3).day == JAN_3
    with pytest.raises(BadFile, match="title says"):
        read_participant_oi(no_year.replace(b"Jan 03", b"Jan 04"), name, JAN_3)
    trailing = b"\r\n".join(line + b"," for line in data.split(b"\r\n") if line)
    assert read_participant_oi(trailing, name, JAN_3).totals == read_participant_oi(data, name, JAN_3).totals
    stray = trailing.replace(b",1303300,", b",1303300,3078338")
    assert read_participant_oi(stray, name, JAN_3).totals["FII"].short == 1303300  # a value under no column: ignored
    named = trailing.replace(b"Total Short Contracts,", b"Total Short Contracts,Extra")
    with pytest.raises(BadFile, match="unexpected columns"):
        read_participant_oi(named, name, JAN_3)
