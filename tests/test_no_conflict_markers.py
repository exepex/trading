"""No tracked text file keeps a merge-conflict marker (orchestrator, 16 Oct 2026, after 1495f2b5 committed one in
reviews/claude/README.md). A marker is a line that starts with seven '<' or seven '>' and a space, or is exactly seven
'='; Markdown underlines and rules elsewhere use other lengths, so none is a marker."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = re.compile(r"^(?:<{7} |={7}$|>{7} )")
BINARY_PROBE = 8192  # a NUL byte in the first 8 KiB marks a binary file, as git itself decides


def tracked_files() -> list[Path]:
    names = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [ROOT / name for name in names.decode().split("\0") if name]


def marker_lines(path: Path) -> list[int]:
    data = path.read_bytes()
    if b"\0" in data[:BINARY_PROBE]:
        return []
    lines = data.decode("utf-8", errors="replace").splitlines()
    return [number for number, line in enumerate(lines, 1) if MARKER.match(line)]


def test_no_tracked_text_file_has_a_conflict_marker():
    found = {
        path.relative_to(ROOT).as_posix(): lines
        for path in tracked_files()
        if path.is_file() and (lines := marker_lines(path))
    }
    assert not found, f"conflict markers left in (file: line numbers): {found}"


def test_the_marker_rule_finds_each_marker_and_nothing_else(tmp_path):
    sample = tmp_path / "sample.md"
    lines = ["<<<<<<< HEAD", "ours", "=======", "theirs", ">>>>>>> main", "Title", "=====", "========", "<<<<<<<x"]
    sample.write_text("\n".join(lines) + "\n")
    assert marker_lines(sample) == [1, 3, 5]
    (tmp_path / "binary.bin").write_bytes(b"\0" + b"\n=======\n")
    assert marker_lines(tmp_path / "binary.bin") == []
