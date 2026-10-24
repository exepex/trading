"""G13b criterion 3: the closed-form t(4) quantile matches the tables (judge 406.1 checked 95% by hand)."""

import pytest

from fno.price_ranges.t4 import t4_quantile


@pytest.mark.parametrize(("p", "t"), [(0.95, 2.1318), (0.75, 0.7407), (0.975, 2.7764), (0.99, 3.7469), (0.5, 0.0)])
def test_the_closed_form_matches_the_t4_table(p, t):
    assert t4_quantile(p) == pytest.approx(t, abs=1e-4)
    assert t4_quantile(1 - p) == pytest.approx(-t, abs=1e-4)


@pytest.mark.parametrize("p", [0.0, 1.0, -0.1, 1.5])
def test_a_level_outside_zero_and_one_is_refused(p):
    with pytest.raises(ValueError, match="inside"):
        t4_quantile(p)
