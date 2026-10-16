"""Shared names of the stress factor file (stories C2d and A14c), split out of `fno/constants.py` at its size limit (and
imported there). Change a value here, not where it is used."""

from __future__ import annotations

__all__ = [
    "STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES",
    "STRESS_FACTOR_COLUMNS",
    "STRESS_FACTOR_STATUSES",
    "STRESS_FACTOR_DATE",
    "FAMILY_DEBIT",
    "FAMILY_CREDIT",
    "FAMILY_ALL",
    "STRESS_FAMILIES",
]

# Story C2d: the stress factor k as A14c's weekly job appends it (append-only), read by C2 and by C4 (its own reader).
# The A14c families change (owner, 16 Oct 2026) added `family` once to the header; rows written before it have no
# family and are read as FAMILY_ALL.
STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES = (
    "as_of", "factor", "computed", "unrounded", "status", "peak", "coverage_through", "evidence_sha256",
)  # fmt: skip
STRESS_FACTOR_COLUMNS = (*STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES, "family")
STRESS_FACTOR_STATUSES = ("applied", "held")  # held: a lower result waits for the owner; the old factor stays in force
STRESS_FACTOR_DATE = "%Y-%m-%d"  # the only date form accepted in the factor file
# One k per structure family (owner, 16 Oct 2026); FAMILY_ALL is a row in force for every family (the rows before it)
FAMILY_DEBIT, FAMILY_CREDIT, FAMILY_ALL = "debit", "credit", "all"
STRESS_FAMILIES = (FAMILY_DEBIT, FAMILY_CREDIT)
