"""Story F1t criteria 2-3: the decision pointer carries exactly its fields and only the book's own private pack, and
reading it back refuses anything else before any input is shown."""

import json

import pytest

from fno.ai_trading.pointer import FIELDS, MAX_POINTER_BYTES, PointerRefused, parse_pointer
from fno.constants import BOOK2_HYBRID, BOOK3_AI

from .builders import DAY, pointer, private_body, registry


def fields(tmp_path, book=BOOK2_HYBRID):
    return json.loads(pointer(tmp_path, book).to_text())


def test_a_pointer_reads_back_equal(tmp_path):
    sent = pointer(tmp_path)
    assert parse_pointer(sent.to_text(), registry(tmp_path)) == sent
    assert sorted(json.loads(sent.to_text())) == list(FIELDS)


@pytest.mark.parametrize("change, why", [
    (lambda f: f.pop("analyst_cards"), "fields must be exactly"),
    (lambda f: f.update(extra=1), "fields must be exactly"),
    (lambda f: f.update(kind="forecast"), "kind must be"),
    (lambda f: f.update(book="book1_rules"), "no registered decision version"),
    (lambda f: f.update(version="book2_hybrid/decision/v9/sha256:x/isolation:sealed_same_day"), "registered decision"),
    (lambda f: f.update(common_pack_sha256="ab"), "common_pack_sha256 is not a SHA-256"),
    (lambda f: f.update(private_pack_sha256="0" * 64), "does not hash to private_pack_sha256"),
    (lambda f: f["private_pack"]["files"][0].update(text="changed"), "does not hash"),
    (lambda f: f.update(private_pack=private_body(BOOK3_AI)), "not this book's pack"),
    (lambda f: f.update(receipt_deadline="15:10"), "receipt_deadline is not a time"),
    (lambda f: f.update(reveal_from="2026-10-20T15:10:10+05:30"), f"must be a time on {DAY}"),
    (lambda f: f.update(analyst_cards={"roles": []}), "analyst_cards must have exactly"),
])  # fmt: skip
def test_a_wrong_pointer_is_refused_with_its_reason(tmp_path, change, why):
    sent = fields(tmp_path)
    change(sent)
    with pytest.raises(PointerRefused, match=why):
        parse_pointer(json.dumps(sent), registry(tmp_path))


def test_empty_and_non_json_text_is_refused(tmp_path):
    for text in ("", "not json", "[]"):
        with pytest.raises(PointerRefused):
            parse_pointer(text, registry(tmp_path))


def test_a_pointer_over_the_cap_is_refused_and_one_at_the_cap_is_read(tmp_path):
    sent = pointer(tmp_path)
    pad = MAX_POINTER_BYTES - sent.size()
    padded = fields(tmp_path)
    padded["private_pack"]["files"][1]["text"] += "x" * (pad - 0)
    text = json.dumps(padded, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert len(text.encode()) == MAX_POINTER_BYTES
    with pytest.raises(PointerRefused, match="does not hash"):  # read past the size check: the edit breaks the hash
        parse_pointer(text, registry(tmp_path))
    with pytest.raises(PointerRefused, match="longer than"):
        parse_pointer(text + " ", registry(tmp_path))


def test_each_book_s_pointer_holds_only_its_own_private_pack(tmp_path):
    two, three = pointer(tmp_path, BOOK2_HYBRID).to_text(), pointer(tmp_path, BOOK3_AI).to_text()
    assert "journal/book3_ai" not in two and "journal/book2_hybrid" not in three
