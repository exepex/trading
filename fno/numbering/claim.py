"""Claiming a number (story O12): append a registry row on a fresh copy of `main` and push it; git decides the race.

A push to `main` is refused when someone else pushed first, so exactly one claimant wins each number. The loser
re-reads the new `main`, takes the next number and tries again (bounded, with a random pause). A number belongs to
the claimant only once its push is accepted.
"""

from __future__ import annotations

import random
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from fno.numbering.categories import ADDENDUM_OF, SLUG, WHOLE, Category
from fno.numbering.git_main import GitMain, MainCopy
from fno.numbering.registry import SEEDED, Row, append_row, next_number, utc_stamp

from ..models import now_utc

TRIES = 8
PAUSE_SECONDS = (0.5, 3.0)
MESSAGE = "Number claim: {category} {number} {name}\n\nClaimed by {session} (story O12; lane 3, a status row).\n"


class ClaimRefused(ValueError):
    """The request itself is wrong (bad slug, taken number, unknown report); retrying cannot help."""


class ClaimNotPushed(RuntimeError):
    """Every try lost the race (or the push kept failing); no number was claimed."""


@dataclass(frozen=True)
class Claim:
    category: str
    number: str
    name: str


@dataclass(frozen=True)
class ClaimRequest:
    category: Category
    slug: str
    session: str
    report: str | None = None  # the report an addendum extends
    exact: str | None = None  # a specific number asked for, instead of the next one


class NumberClaimer:
    def __init__(
        self,
        git: GitMain,
        clock: Callable[[], datetime] = lambda: now_utc(),
        pause: Callable[[float], None] = time.sleep,
        tries: int = TRIES,
    ):
        self._git, self._clock, self._pause, self._tries = git, clock, pause, tries

    def claim(self, request: ClaimRequest) -> Claim:
        _refuse_bad_request(request)
        with self._git.main_copy() as copy:
            for attempt in range(1, self._tries + 1):
                registry = copy.path / request.category.registry
                number = _number(request, copy)
                name = request.category.claimed_name(number, request.slug)
                append_row(registry, Row(number, name, request.session, utc_stamp(self._clock())))
                message = MESSAGE.format(
                    category=request.category.name, number=number, name=name, session=request.session
                )
                if copy.commit_and_push(request.category.registry, message):
                    return Claim(request.category.name, number, name)
                if attempt < self._tries:
                    self._pause(random.uniform(*PAUSE_SECONDS))  # pause first, so the retry reads the newest main
                    copy.reset_to_main()
        raise ClaimNotPushed(f"no {request.category.name} number claimed: {self._tries} pushes to main were refused")


def _refuse_bad_request(request: ClaimRequest) -> None:
    if not SLUG.fullmatch(request.slug):
        raise ClaimRefused(f"slug {request.slug!r}: use lower-case letters and digits joined by '-' or '_'")
    if not request.session.strip() or request.session == SEEDED:
        raise ClaimRefused(f"name the claiming session (--session); {SEEDED!r} is reserved for the seeded history")
    is_addendum = request.category.name in ADDENDUM_OF
    if is_addendum != (request.report is not None):
        raise ClaimRefused(f"{request.category.name}: --report is {'required' if is_addendum else 'not allowed'}")
    if request.exact is not None and not re.fullmatch(WHOLE, request.exact):
        raise ClaimRefused(f"--number {request.exact!r}: a whole number from 1")


def _number(request: ClaimRequest, copy: MainCopy) -> str:
    """The next free number, or the exact one asked for; a number is taken by a registry row or by a file (or
    heading) already on `main`, so a file written without a claim is never handed out again."""
    category = request.category
    if request.report is not None and request.report not in copy.taken(ADDENDUM_OF[category.name]):
        raise ClaimRefused(f"{category.name}: report {request.report} is not on main")
    taken = copy.taken(category)
    if request.exact is None:
        return next_number(category, taken, request.report)
    number = f"{request.report}.{request.exact}" if request.report is not None else request.exact
    if number in taken:
        raise ClaimRefused(f"{category.name} {number} is already taken")
    return number
