"""`python -m fno data-fingerprints <dataset>`: writes the SHA-256 manifest of a dataset's files in Drive (read-only)
and spot-checks a random sample against NSE's live bytes (story A9). An existing manifest is evidence and is never
overwritten: the coverage check verifies Drive against it."""

from __future__ import annotations

import random
from datetime import date, timedelta

SPOT_CHECK_SEED = 13102026  # fixed, so a judge draws the same sample


def add_fingerprints_parser(subparsers) -> None:
    from .wiring import FINGERPRINT_MANIFESTS

    fp = subparsers.add_parser("data-fingerprints", help="write a dataset's SHA-256 manifest from Drive (read-only)")
    fp.add_argument("dataset", choices=sorted(FINGERPRINT_MANIFESTS))
    fp.add_argument("--from", dest="start", type=date.fromisoformat, default=date(2019, 1, 1), help="YYYY-MM-DD")
    fp.add_argument(
        "--to",
        dest="end",
        type=date.fromisoformat,
        default=date.today() - timedelta(days=1),
        help="YYYY-MM-DD (default: yesterday)",
    )
    fp.add_argument("--spot-check", type=int, default=0, help="files compared with NSE's live bytes (default 0)")
    fp.set_defaults(func=cmd_data_fingerprints)


def cmd_data_fingerprints(args) -> int:
    from . import wiring
    from .fingerprints import compare_with_source, fingerprint_store, write_manifest

    source_type, manifest = wiring.FINGERPRINT_SOURCES[args.dataset], wiring.FINGERPRINT_MANIFESTS[args.dataset]
    found = fingerprint_store(
        wiring.build_drive_reader(), source_type, wiring.build_session_calendar(), args.start, args.end
    )
    print(f"{source_type.dataset}: {len(found)} files read from Drive ({found[0].day} to {found[-1].day})")
    if manifest.exists():
        print(f"{manifest.name} exists and is kept as it is (the coverage check verifies Drive against it)")
    else:
        write_manifest(manifest, found)
        print(f"wrote {manifest.name}: {len(found)} rows")
    sample = sorted(random.Random(SPOT_CHECK_SEED).sample(found, min(args.spot_check, len(found))), key=lambda f: f.day)
    lines = compare_with_source(wiring.build_nse_source(source_type), sample)
    print("\n".join(lines))
    return 1 if any("REWRITE" in line for line in lines) else 0
