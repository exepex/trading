"""Story O10's freshness rows in O8's table: NSE margins (the date in `as_of`, the LAST column), corporate actions and
EQUITY_L (market-publish's manifests); each status from planted evidence, and the push searched by its own key."""

from __future__ import annotations

from datetime import time, timedelta

import pytest

from fno.constants import HEALTH_LATE, HEALTH_MISSED, HEALTH_NOT_DUE, HEALTH_OK
from fno.health.data_checks import SessionRowCheck
from fno.health.expectations import CORPORATE_ACTIONS_MANIFEST, MARGINS_FILE, MARKET_ARCHIVE_BY
from fno.health.model import Deadline

from .fakes import DAY, Repo, ist

PACK = Deadline(time(14, 58))
MARGINS = "structure,width,scan_per_lot_rs,source,as_of\nSF,300,1.0,NSE SPAN nsccl.{d:%Y%m%d}.i1.zip,{d}\n"
NEXT = DAY + timedelta(days=1)


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


def test_margins_match_the_as_of_column_and_search_their_own_key(repo):
    repo.write(MARGINS_FILE, MARGINS.format(d=DAY))
    check = SessionRowCheck(repo.evidence, MARGINS_FILE, PACK, "as_of")
    repo.receipts.row(MARGINS_FILE, f",{DAY}", ist(DAY, 8, 30))  # a last column: ",<date>", never "<date>,"
    assert check.check(DAY, ist(DAY, 17, 51)).status == HEALTH_OK
    repo.receipts.row(MARGINS_FILE, f",{DAY}", ist(DAY, 14, 58, 1))
    assert check.check(DAY, ist(DAY, 17, 51)).status == HEALTH_LATE


def test_margins_for_another_day_are_absent(repo):
    repo.write(MARGINS_FILE, MARGINS.format(d=DAY - timedelta(days=1)))
    check = SessionRowCheck(repo.evidence, MARGINS_FILE, PACK, "as_of")
    assert check.check(DAY, ist(DAY, 14, 57, 59)).status == HEALTH_NOT_DUE
    assert check.check(DAY, ist(DAY, 14, 58)).status == HEALTH_MISSED


def test_a_middle_column_is_searched_with_commas_on_both_sides(repo):
    repo.write("x.csv", f"a,day,b\n1,{DAY},2\n")
    repo.receipts.row("x.csv", f",{DAY},", ist(DAY, 9))
    assert SessionRowCheck(repo.evidence, "x.csv", PACK, "day").check(DAY, ist(DAY, 17, 51)).status == HEALTH_OK


def test_the_market_archive_row_is_due_the_next_afternoon(repo):
    repo.write(CORPORATE_ACTIONS_MANIFEST, "date,url,status,sha256,size_bytes\n")
    check = SessionRowCheck(repo.evidence, CORPORATE_ACTIONS_MANIFEST, MARKET_ARCHIVE_BY)
    assert check.check(DAY, ist(NEXT, 14, 59, 59)).status == HEALTH_NOT_DUE
    assert check.check(DAY, ist(NEXT, 15, 0)).status == HEALTH_MISSED
    repo.write(CORPORATE_ACTIONS_MANIFEST, f"date,url,status,sha256,size_bytes\n{DAY},u,200,s,1\n")
    repo.receipts.row(CORPORATE_ACTIONS_MANIFEST, f"{DAY},", ist(NEXT, 11, 56))  # 15 Oct's measured push
    assert check.check(DAY, ist(NEXT, 17, 51)).status == HEALTH_OK
