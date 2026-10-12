"""Downloads NSE's daily F&O files (2 Jan 2024 to today) into your fno-research folder.

Run it with no options:   python nse_raw_download.py
It asks which folder to use (press Enter for the folder you are in). That's all.
"""

from __future__ import annotations

import csv
import hashlib
import platform
import ssl
import subprocess
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://nsearchives.nseindia.com/content/fo/"
FILENAME = "BhavCopy_NSE_FO_0_0_0_{day:%Y%m%d}_F_0000.csv.zip"
LAYOUT = "raw/nse/derivatives/fo-bhavcopy/{day:%Y}/{day:%m}/{filename}"  # same as fno/storage (tested in the repo)
FIRST_DAY = date(2024, 1, 2)  # NSE serves this file format from January 2024
GAP_SECONDS = 1.0
RETRY_WAITS = (5, 15, 45)
REFUSED = (403, 429)
MAC_ROOT_CERTIFICATES = "/System/Library/Keychains/SystemRootCertificates.keychain"
CERTIFICATE_HELP = (
    "This computer's Python cannot check secure websites (missing certificates).\n"
    "On a Mac: open Finder > Applications > Python 3.x and double-click 'Install Certificates.command', then run again."
)
USER_AGENT = "Mozilla/5.0 (personal research; one request per second)"


def relative_path(day: date) -> str:
    return LAYOUT.format(day=day, filename=FILENAME.format(day=day))


def load_manifest(path: Path) -> tuple[dict[str, str], set[str]]:
    """date -> expected SHA-256 for days NSE published a file, and the days it published none (holidays)."""
    if not path.is_file():
        return {}, set()
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    expected = {r["date"]: r["sha256"] for r in rows if r.get("status") == "200" and r.get("sha256")}
    return expected, {r["date"] for r in rows if r.get("status") == "404"}


def secure_context() -> ssl.SSLContext:
    """Python's own certificates, or on a Mac without them the Mac's built-in ones. Checking is never switched off."""
    context = ssl.create_default_context()
    if context.cert_store_stats()["x509_ca"] or platform.system() != "Darwin":
        return context
    try:
        pem = subprocess.run(
            ["security", "find-certificate", "-a", "-p", MAC_ROOT_CERTIFICATES], capture_output=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return context
    with tempfile.NamedTemporaryFile("wb", suffix=".pem", delete=False) as bundle:
        bundle.write(pem)
    return ssl.create_default_context(cafile=bundle.name)


CONTEXT = secure_context()


class CertificateProblem(RuntimeError):
    """The computer cannot verify NSE's secure certificate; retrying will not help."""


def download(url: str) -> tuple[int, bytes]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    for wait in (*RETRY_WAITS, None):
        try:
            with urlopen(request, timeout=60, context=CONTEXT) as response:
                return response.status, response.read()
        except HTTPError as exc:
            return exc.code, b""
        except (URLError, OSError) as exc:
            if isinstance(getattr(exc, "reason", exc), ssl.SSLCertVerificationError):
                raise CertificateProblem(CERTIFICATE_HELP) from exc
            if wait is None:
                raise RuntimeError(f"network failure for {url}: {exc}") from exc
            print(f"  connection problem ({exc}); retrying in {wait} s")
            time.sleep(wait)
    raise AssertionError("unreachable")


def save(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.part")
    temporary.write_bytes(data)
    temporary.replace(target)


def choose_folder(argv: list[str]) -> Path:
    """The folder named after the script, or asked for (Enter = the current folder)."""
    if argv:
        return Path(argv[0].strip().strip('"'))
    here = Path.cwd()
    answer = input(f"Which folder should the files go into?\nPress Enter for {here}\nor paste another folder: ")
    return Path(answer.strip().strip('"')) if answer.strip() else here


def run(dest: Path, start: date = FIRST_DAY, end: date | None = None, manifest: Path | None = None) -> int:
    end = end or date.today()
    expected, holidays = load_manifest(manifest or Path(__file__).with_name("manifest.csv"))
    counts = {"saved": 0, "already there": 0, "no file (holiday)": 0, "mismatch": 0}
    print(f"Saving into {dest / 'raw'}  (about 30 minutes; you can stop with Ctrl+C and run again later)")
    day = start
    while day <= end:
        if day.weekday() >= 5 or day.isoformat() in holidays:
            day += timedelta(days=1)
            continue
        target = dest / relative_path(day)
        want = expected.get(day.isoformat())
        if target.is_file():
            have = hashlib.sha256(target.read_bytes()).hexdigest()
            if want and have != want:
                print(f"MISMATCH {day}: existing file differs from the recorded fingerprint; left untouched")
                counts["mismatch"] += 1
            else:
                counts["already there"] += 1
            day += timedelta(days=1)
            continue
        status, data = download(BASE_URL + FILENAME.format(day=day))
        if status in REFUSED:
            print(f"NSE refused the request (HTTP {status}). Stopping to avoid a block; run again later.")
            break
        if status == 404:
            counts["no file (holiday)"] += 1
        elif status == 200:
            got = hashlib.sha256(data).hexdigest()
            if want and got != want:
                print(f"MISMATCH {day}: NSE's file differs from the recorded fingerprint; not saved")
                counts["mismatch"] += 1
            else:
                save(target, data)
                counts["saved"] += 1
                print(f"saved {day}  ({len(data) / 1e6:.1f} MB)")
        else:
            print(f"{day}: unexpected HTTP {status}; skipped (run again later)")
        time.sleep(GAP_SECONDS)
        day += timedelta(days=1)
    print("Done. " + "; ".join(f"{k}: {v}" for k, v in counts.items()))
    return 1 if counts["mismatch"] else 0


def main() -> int:
    dest = choose_folder(sys.argv[1:])
    try:
        code = run(dest)
    except (CertificateProblem, RuntimeError) as exc:
        print(f"\nStopped: {exc}")
        code = 2
    if not sys.argv[1:]:
        input("Press Enter to close.")
    return code


if __name__ == "__main__":
    sys.exit(main())
