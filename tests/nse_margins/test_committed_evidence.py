"""Story A14c and O9b step 2: every factor row that names its evidence (`evidence_sha256`; the owner's seed names none)
has that run day's evidence CSV in Drive under a committed receipt with the same SHA-256, so C2's factor still leads
to the exact evidence behind it now that the CSV is no longer in the repository (A14/C2/C4 owner, 23 Oct 2026)."""

import csv

from fno.config import ROOT
from fno.storage.data_wiring import receipt_folder

FACTOR_FILE = ROOT / "research" / "data" / "margins" / "stress_factor.csv"
EVIDENCE = "data/margins/stress-evidence/{day}"


def test_every_factor_row_with_evidence_has_its_csv_under_a_receipt_with_the_same_sha256():
    with open(FACTOR_FILE, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["evidence_sha256"]]
    assert rows  # A14c has written rows since 16 Oct 2026
    receipts = receipt_folder()
    for row in rows:
        held = {r.sha256 for r in receipts.under(EVIDENCE.format(day=row["as_of"]))}
        assert row["evidence_sha256"] in held, row["as_of"]
