"""The school's tests: the shared conformance checks get pytest's assertion messages (story MS-P1a)."""

import pytest

pytest.register_assert_rewrite("tests.school.contracts.conformance")
