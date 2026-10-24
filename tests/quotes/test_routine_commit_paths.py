"""Story A4c, criterion 6: each part of the 3 pm routine stages only its own files with the paths CLAUDE.md gives it
(NIFTY, NSE, the three indices and, A4f, NIFTY's weeklies), never a Groww quote file."""

import shutil
import subprocess

from fno.config import ROOT

GROWW = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10"
NSE = "research/data/quotes/nse/derivatives/quote-snapshots/2026/10"
WEEKLY = "research/data/quotes/groww/derivatives/quote-snapshots-weekly/2026/10"
PARTS = {
    "nifty": ["':(glob)research/data/quotes/groww/derivatives/quote-snapshots/**/nifty_*'"],  # G10: never the v4 dataset
    "nse": ["research/data/quotes/nse/"],
    "indices": [
        f"':(glob)research/data/quotes/groww/**/{name}_*'"
        for name in ("banknifty", "finnifty", "midcpnifty", "niftyweekly")
    ],  # fmt: skip
}
FILES = {
    "nifty": [f"{GROWW}/nifty_20261016.canonical", f"{GROWW}/nifty_20261016_145500.meta.json"],
    "nse": [f"{NSE}/nifty_20261016{suffix}" for suffix in (".canonical", "_145501.csv", "_145501.meta.json")],
    "indices": [f"{GROWW}/{name}_20261016{suffix}" for name in ("banknifty", "finnifty", "midcpnifty")
                for suffix in (".canonical", "_150100.meta.json")]
               + [f"{WEEKLY}/niftyweekly_20261016{suffix}" for suffix in (".canonical", "_150600.meta.json")],
}  # fmt: skip
RAW = [f"{GROWW}/{name}_20261016_145500.csv" for name in ("nifty", "banknifty")] + [
    f"{WEEKLY}/niftyweekly_20261016_150600.csv"
]


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def test_each_part_stages_only_its_own_files(tmp_path):
    _git(tmp_path, "init", "-q")
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")
    for path in [*sum(FILES.values(), []), *RAW]:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("x")
    for part, specs in PARTS.items():
        staged = _git(tmp_path, "add", "--dry-run", *(spec.strip("'") for spec in specs)).split("\n")
        assert sorted(line.removeprefix("add '").removesuffix("'") for line in staged if line) == sorted(FILES[part])


def test_claude_md_gives_the_same_paths():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").replace("\n   ", " ")
    assert all(spec in text for specs in PARTS.values() for spec in specs)
