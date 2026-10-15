"""LR1's exact number check (the devil's advocate's code half): whole number tokens only, one test per rule."""

import pytest

from fno.advocate.numbers import NumberCheck, number_tokens

LINES = "Week ending 2026-10-17\nweather_vix_v1: scored 40%, D +0.0042, 1,234 days at 10:41\n"
SHA = "a" * 64


def _check(body: str, max_words: int = 150) -> str | None:
    return NumberCheck(LINES, SHA, max_words).first_failure(f"{SHA}\n{body}")


def test_tokens_are_whole_numbers_and_ignore_digits_inside_names():
    assert number_tokens("v4 weather_vix_v1 [L12] 40% -0.0042 2026-10-16 10:41 1,234.") == {
        "40%", "-0.0042", "2026-10-16", "10:41", "1,234"}  # fmt: skip


def test_a_summary_copying_the_lines_passes():
    assert _check("The model scored 40% on 1,234 days; D was +0.0042 for the week ending 2026-10-17.") is None


@pytest.mark.parametrize(
    ("body", "rule"),
    [
        ("4 sessions looked fine.", "rule 3: number 4 is"),  # judge 167 addendum 1: never a substring of 40%
        ("It scored 41%.", "rule 3: number 41%"),
        ("D was -0.0042.", "rule 3: number -0.0042"),  # a changed sign
        ("Next look on 2026-10-16.", "rule 3: number 2026-10-16"),
        ("It missed three days.", "rule 4: number written in words (three)"),
        ("Half the days were fine.", "rule 4: number written in words (Half)"),
        ("See https://example.org", "rule 2: a link"),
        ("<!channel> look", "rule 2: a link, mention or code block (<!)"),
        ("```x```", "rule 2: a link, mention or code block (```)"),
    ],
)
def test_each_rule_fails_with_its_name(body, rule):
    assert _check(body).startswith(rule)


def test_too_many_words_fails_rule_2():
    assert _check("word " * 151).startswith("rule 2: more than 150 words")


def test_a_wrong_or_missing_sha_line_fails_rule_1():
    check = NumberCheck(LINES, SHA, 150)
    assert check.first_failure("b" * 64 + "\nfine").startswith("rule 1")
    assert check.first_failure("").startswith("rule 1")
