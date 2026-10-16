"""Parsers for RBI's three pages (story A21): the press-release list, a T-bill auction cut-off release and the home
page's "Current Rates" box. Each returns plain values or raises `RatePageError` naming the missing field; a parser
never guesses."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date, datetime

from .constants import TBILL_TITLE

_TAG = re.compile(r"<[^>]+>")
_DROP = re.compile(r"<script.*?</script>|<style.*?</style>", re.S | re.I)
_LINK = re.compile(r"<a[^>]*href=['\"]?[^'\">]*prid=(\d+)['\"]?[^>]*>(.*?)</a>", re.S | re.I)
_RELEASE_DATE = re.compile(r"Date\s*:\s*([A-Z][a-z]{2} \d{1,2}, \d{4})")
_RELEASE_NO = re.compile(r"Press Release\s*:\s*(\d{4}-\d{4}/\d+)")
_YTM = re.compile(r"\(YTM:\s*(\d+\.\d+)%\)")
_REPO = re.compile(r"Policy Repo Rate\s*:\s*(\d+\.\d+)%")
_HOME_TBILL = re.compile(r"91 day T-bills\s*:\s*(\d+\.\d+)%")


class RatePageError(ValueError):
    """An RBI page lacks a field the capture needs; the message names the field and the page."""


@dataclass(frozen=True)
class TbillAuction:
    prid: int
    auction_date: date
    release_no: str
    yields_pct: tuple[float, float, float]  # 91, 182 and 364 days


@dataclass(frozen=True)
class CurrentRates:
    policy_repo_pct: float
    tbill_91_pct: float  # "cut-off at the last auction": read only to check against the release


def plain_text(page: str) -> str:
    text = html.unescape(_TAG.sub(" ", _DROP.sub(" ", page)))
    return " ".join(text.split())


def tbill_release_ids(page: str) -> list[int]:
    """The prids of every listed release titled exactly as a T-bill cut-off result, highest (newest) first."""
    found = {int(prid) for prid, title in _LINK.findall(page) if plain_text(title) == TBILL_TITLE}
    return sorted(found, reverse=True)


def _one(pattern: re.Pattern, text: str, field: str, where: str) -> str:
    match = pattern.search(text)
    if match is None:
        raise RatePageError(f"{where}: field '{field}' not found")
    return match.group(1)


def parse_tbill_release(page: str, prid: int) -> TbillAuction:
    where = f"RBI release {prid}"
    text = plain_text(page)
    if TBILL_TITLE not in text:
        raise RatePageError(f"{where}: field 'title' is not '{TBILL_TITLE}'")
    day = datetime.strptime(_one(_RELEASE_DATE, text, "date", where), "%b %d, %Y").date()
    yields = tuple(float(value) for value in _YTM.findall(text))
    if len(yields) != 3:
        raise RatePageError(f"{where}: field 'YTM' found {len(yields)} times, expected 3 (91, 182, 364 days)")
    return TbillAuction(prid, day, _one(_RELEASE_NO, text, "release number", where), yields)


def parse_current_rates(page: str) -> CurrentRates:
    text = plain_text(page)
    where = "RBI home page"
    return CurrentRates(float(_one(_REPO, text, "Policy Repo Rate", where)),
                        float(_one(_HOME_TBILL, text, "91 day T-bills", where)))  # fmt: skip
