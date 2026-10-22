"""The read-only check behind story A9c's second host: one day's file of every librarian dataset from both NSE hosts,
compared by SHA-256. It stores nothing. Exit 0 only when every dataset is the same on both hosts, or published on
neither; a difference, or a file one host could not serve, is exit 1."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from datetime import date

from .raw_source import PRIMARY_HOST, SECOND_HOST, NseArchiveSource, RawSourceUnavailable

SAME, NEITHER, DIFFERENT, INCOMPLETE = "same", "not published on either", "DIFFERENT", "NOT CHECKED"
LINE = "{dataset} {day}: {first} | {second} -> {verdict}"
SUMMARY = "hosts {day}: {same} same, {neither} not published on either, {bad} different or not checked"


def answer(source: NseArchiveSource, path: str) -> tuple[str, str | None]:
    """What one host serves: its SHA-256 (first 12) or why there is none, and the full digest."""
    try:
        data = source.fetch(path)
    except RawSourceUnavailable as error:
        return f"{source.host} unreachable ({type(error).__name__})", None
    if data is None:
        return f"{source.host} not published", ""
    digest = hashlib.sha256(data).hexdigest()
    return f"{source.host} {digest[:12]}", digest


def verdict(first: str | None, second: str | None) -> str:
    if first == "" and second == "":
        return NEITHER
    if first is None or second is None:
        return INCOMPLETE
    return SAME if first == second else DIFFERENT


def compare_hosts(source_types: Iterable[type[NseArchiveSource]], day: date,
                  build: Callable[..., NseArchiveSource], out=print) -> int:  # fmt: skip
    counts = {SAME: 0, NEITHER: 0, "bad": 0}
    for source_type in source_types:
        path = source_type.path_for(day)
        first, first_sha = answer(build(source_type, host=PRIMARY_HOST, retry_waits=()), path)
        second, second_sha = answer(build(source_type, host=SECOND_HOST, retry_waits=()), path)
        result = verdict(first_sha, second_sha)
        counts[result if result in (SAME, NEITHER) else "bad"] += 1
        out(LINE.format(dataset=source_type.dataset.rsplit("/", 1)[-1], day=day, first=first, second=second,
                        verdict=result))  # fmt: skip
    out(SUMMARY.format(day=day, same=counts[SAME], neither=counts[NEITHER], bad=counts["bad"]))
    return 1 if counts["bad"] else 0
