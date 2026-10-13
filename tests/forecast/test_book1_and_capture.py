"""Story G3 criterion 2: Book 1's frozen method, and the method file's hash in every record. The daily capture
(criteria 1 and 3, protocol v2) is tested in test_live_capture.py."""

import hashlib
from pathlib import Path

import pytest

from fno.constants import FORECAST_QUESTIONS
from fno.forecast import book1_method
from fno.forecast.book1_method import book1_probabilities, method_label, method_sha256

Q1, Q2, Q3, Q4, Q5 = FORECAST_QUESTIONS


def test_book1_is_the_mean_of_the_questions_two_baselines():
    by = {
        "baseline_a_risk_neutral": {Q1: 0.40, Q2: 0.30},
        "baseline_b_base_rate": {Q1: 0.60, Q2: None, Q3: 0.50, Q4: None, Q5: 0.70},
        "baseline_c_model": {Q3: 0.30, Q4: None, Q5: 0.90},
    }
    assert book1_probabilities(by) == {Q1: pytest.approx(0.5), Q2: 0.30, Q3: pytest.approx(0.4), Q4: None,
                                       Q5: pytest.approx(0.8)}  # fmt: skip
    assert book1_probabilities({}) == dict.fromkeys(FORECAST_QUESTIONS)


def test_the_method_label_carries_the_method_files_hash():
    expected = hashlib.sha256(Path(book1_method.__file__).read_bytes()).hexdigest()
    assert method_sha256() == expected and method_label() == f"book1/v1/sha256:{expected}"
