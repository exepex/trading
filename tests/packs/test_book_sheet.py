"""Story E2e: a book's sheet (F5's Book 2 rule default, F6's Book 3 candidates) goes into its private pack under
"evaluation"; a book without one is byte-identical; a sheet that fails refuses that book's pack only, with one alert,
and every other book's pack is still written and kept."""

import json
from datetime import time

from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI
from fno.desk.book_sheet import BookSheet
from fno.desk.pack_store import PackStore
from fno.desk.packs import SHEET_REFUSED, WrittenPacks
from fno.desk.private_pack import EVALUATION, PrivatePackBuilder
from tests.timetable.fakes import pack_for

from .builders import DAY
from .test_private_pack import plant


class Common:
    def build(self, day, cutoff):
        return pack_for(day)


class Sheet(BookSheet):
    def __init__(self, fail=False):
        self.fail, self.seen = fail, []

    def sheet(self, book, day, common):
        self.seen.append((book, day, common.day))
        if self.fail:
            raise ValueError("no canonical snapshot named")
        return {"rule_default": ["opp-1"], "eligible": ["v1"]}


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


def packs(root, sheets, alerts=None, kept=None):
    keep = kept.extend if kept is not None else lambda paths: None
    return WrittenPacks(Common(), PrivatePackBuilder(root), PackStore(root), time(15, 0),
                        (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI), keep=keep, sheets=sheets, alerts=alerts)  # fmt: skip


def body(root, book):
    return json.loads(PackStore(root).private_path(book, DAY).read_text(encoding="utf-8"))


def test_a_sheet_goes_into_its_books_private_pack_under_evaluation(tmp_path):
    plant(tmp_path)
    sheet = Sheet()
    packs(tmp_path, {BOOK2_HYBRID: sheet}).build(DAY)
    assert body(tmp_path, BOOK2_HYBRID)[EVALUATION] == {"rule_default": ["opp-1"], "eligible": ["v1"]}
    assert sheet.seen == [(BOOK2_HYBRID, DAY, DAY)]  # it sees the day's common pack
    assert EVALUATION not in body(tmp_path, BOOK3_AI)


def test_a_book_without_a_sheet_is_byte_identical(tmp_path):
    plant(tmp_path)
    before = PrivatePackBuilder(tmp_path).build(BOOK1_RULES, DAY)
    packs(tmp_path, {BOOK2_HYBRID: Sheet()}).build(DAY)
    written = PackStore(tmp_path).private_path(BOOK1_RULES, DAY).read_bytes()
    assert written == before.data and PrivatePackBuilder(tmp_path).build(BOOK1_RULES, DAY, None).sha256 == before.sha256


def test_a_failing_sheet_refuses_only_its_books_pack_with_one_alert(tmp_path):
    plant(tmp_path)
    alerts, kept = Alerts(), []
    packs(tmp_path, {BOOK2_HYBRID: Sheet(fail=True)}, alerts, kept).build(DAY)
    store = PackStore(tmp_path)
    assert not store.private_path(BOOK2_HYBRID, DAY).exists()
    assert store.private_path(BOOK1_RULES, DAY).is_file() and store.private_path(BOOK3_AI, DAY).is_file()
    assert alerts.sent == [SHEET_REFUSED.format(day=DAY, book=BOOK2_HYBRID,
                                                error="ValueError: no canonical snapshot named")]  # fmt: skip
    assert [p for p in kept if p.is_file()] == [store.private_path(BOOK1_RULES, DAY), store.private_path(BOOK3_AI, DAY)]


def test_without_an_alert_sender_the_refusal_is_printed_never_silent(tmp_path, capsys):
    plant(tmp_path)
    packs(tmp_path, {BOOK3_AI: Sheet(fail=True)}).build(DAY)
    assert f"{BOOK3_AI}: private pack NOT built" in capsys.readouterr().out
