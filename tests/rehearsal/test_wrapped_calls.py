"""REH1i: the guard test's call reader. Good: every call handed over. Bad: one wrapped call beside an unwrapped one
(the case a single regex search passed). Boundary: the builder as the wrapper's second argument, or built first and
handed over by name. Empty: a file with no call."""

from .wrapped_calls import calls, unwrapped

WRAPPED = "receipts = rehearsed_receipts(\n    GitHubActivityReceipts(repo, token, history), history\n)\n"


def test_every_call_handed_to_the_choice_passes():
    text = WRAPPED + "other = wiring.rehearsed_receipts(receipts_module.GitHubActivityReceipts(r, t, h), h)\n"
    assert unwrapped(text, "GitHubActivityReceipts", "rehearsed_receipts") == []
    assert calls(text, "GitHubActivityReceipts") == 2


def test_one_wrapped_call_does_not_hide_an_unwrapped_one_in_the_same_file():
    text = WRAPPED + "\n\ndef collector():\n    return GitHubActivityReceipts(repo, token, history)\n"
    assert unwrapped(text, "GitHubActivityReceipts", "rehearsed_receipts") == [7]
    twice = text + "\n\ndef sweeper():\n    return GitHubActivityReceipts(repo, token, history)\n"
    assert unwrapped(twice, "GitHubActivityReceipts", "rehearsed_receipts") == [7, 11]  # every bare use, not the first


def test_the_builder_as_a_second_argument_or_handed_over_by_name_is_unwrapped():
    second = "rehearsed_receipts(history, GitHubActivityReceipts(repo, token, history))\n"
    by_name = "built = GitHubActivityReceipts(repo, token, history)\nreceipts = rehearsed_receipts(built, history)\n"
    assert unwrapped(second, "GitHubActivityReceipts", "rehearsed_receipts") == [1]
    assert unwrapped(by_name, "GitHubActivityReceipts", "rehearsed_receipts") == [1]


def test_a_file_with_no_call_has_nothing_unwrapped():
    text = '"""GitHubActivityReceipts( in a docstring is not a call."""\nclass GitHubActivityReceipts:\n    pass\n'
    assert unwrapped(text, "GitHubActivityReceipts", "rehearsed_receipts") == []
    assert calls(text, "GitHubActivityReceipts") == 0


def test_an_alias_a_partial_a_map_a_subclass_and_a_renaming_import_are_unwrapped():
    """Self-review 1: a builder used without its literal call is still a bare builder."""
    cases = {
        "cls = GitHubActivityReceipts\nreceipts = cls(repo, token, history)\n": [1],
        "made = functools.partial(GitHubActivityReceipts, repo)\n": [1],
        "every = list(map(GitHubActivityReceipts, repos))\n": [1],
        "class Mine(GitHubActivityReceipts):\n    pass\n": [1],
        "from fno.ai.receipts import GitHubActivityReceipts as Receipts\nreceipts = Receipts(repo, token, history)\n": [
            1
        ],
    }
    for text, lines in cases.items():
        assert unwrapped(text, "GitHubActivityReceipts", "rehearsed_receipts") == lines, text
    assert unwrapped("from fno.ai.receipts import GitHubActivityReceipts\n", "GitHubActivityReceipts", "x") == []
