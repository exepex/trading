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


def test_the_builder_as_a_second_argument_or_handed_over_by_name_is_unwrapped():
    second = "rehearsed_receipts(history, GitHubActivityReceipts(repo, token, history))\n"
    by_name = "built = GitHubActivityReceipts(repo, token, history)\nreceipts = rehearsed_receipts(built, history)\n"
    assert unwrapped(second, "GitHubActivityReceipts", "rehearsed_receipts") == [1]
    assert unwrapped(by_name, "GitHubActivityReceipts", "rehearsed_receipts") == [1]


def test_a_file_with_no_call_has_nothing_unwrapped():
    text = '"""GitHubActivityReceipts( in a docstring is not a call."""\nclass GitHubActivityReceipts:\n    pass\n'
    assert unwrapped(text, "GitHubActivityReceipts", "rehearsed_receipts") == []
    assert calls(text, "GitHubActivityReceipts") == 0
