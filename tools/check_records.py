"""Public-record safety scan (story O5): refuses records that hold credentials, personal data or broker identifiers.

    python tools/check_records.py            # every committed record (all tracked files outside fno/, tests/, tools/)
    python tools/check_records.py --staged   # the records staged for the next commit (routines run this first)
    python tools/check_records.py PATH ...   # named files or folders, e.g. a session export before it is sent

Routines also enable the same check as a git pre-commit hook: `git config core.hooksPath .githooks`.

Prints one line per finding (file, line and kind of value, never the value) and exits 1 when anything is found.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fno.composition import build_record_scanner  # noqa: E402
from fno.record_scan.record_files import NamedFiles, RecordSource, StagedRecords, TrackedRecords  # noqa: E402

REFUSED = "record scan: REFUSED, {count} finding(s); do not commit or send these files (values are not shown)"
CLEAN = "record scan: clean ({files} files)"


def source_for(args: argparse.Namespace) -> RecordSource:
    if args.paths:
        return NamedFiles([Path(p) for p in args.paths])
    return StagedRecords(args.root) if args.staged else TrackedRecords(args.root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--staged", action="store_true", help="scan only the records staged for the next commit")
    parser.add_argument("--root", type=Path, default=ROOT, help="the git repository to scan (default: this one)")
    parser.add_argument("paths", nargs="*", help="files or folders to scan instead of the repository's records")
    args = parser.parse_args(argv)
    records = list(source_for(args).records())
    findings = build_record_scanner().scan(records)
    for finding in findings:
        print(finding)
    print(REFUSED.format(count=len(findings)) if findings else CLEAN.format(files=len(records)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
