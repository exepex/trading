"""The repository's NIFTY panel (2024 to 2026, options 28 to 47 days to expiry) and events, read once per run."""

import pytest

from fno.composition import load_research_data

REAL_YEARS = (2024, 2025, 2026)
DAYS_TO_EXPIRY = (28, 47)  # around the 30-45 day monthly expiry the contexts use


@pytest.fixture(scope="session")
def real_data():
    return load_research_data(
        REAL_YEARS, keep=lambda day, expiry: DAYS_TO_EXPIRY[0] <= (expiry - day).days <= DAYS_TO_EXPIRY[1]
    )
