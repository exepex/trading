"""Every input zip's SHA-256 against the archive manifests (`research/data/manifests/`) before any study reads it."""

import csv
import hashlib
from pathlib import Path

MANIFESTS = Path(__file__).resolve().parents[4] / "research" / "data" / "manifests"
DATASETS = {"legacy": "fo-bhavcopy-legacy.csv", "udiff": "fo-bhavcopy.csv"}


def expected(kind: str) -> dict[str, str]:
    with (MANIFESTS / DATASETS[kind]).open() as f:
        return {r["date"]: r["sha256"] for r in csv.DictReader(f)}


def verify(folder: Path, kind: str) -> int:
    """The number of files checked; raises on a file the manifest lacks or whose bytes differ."""
    known = expected(kind)
    files = sorted(folder.glob("*.zip"))
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if known.get(path.stem) != digest:
            raise ValueError(f"{path.name}: SHA-256 {digest[:12]} does not match the {kind} manifest")
    return len(files)
