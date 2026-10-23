"""Story DR1 audit item 6: the commit hook's scan needs no third-party package. On 22 and 23 Oct the AI books'
sealed answers missed 15:15 because the hook imported the whole app while pip was still installing. Run with
`python -S` (no site-packages at all), the scan still refuses a planted credential, prints the alert text it could not
send, and passes a clean file."""

import os
import subprocess
import sys
from pathlib import Path

from tests.record_scan.test_patterns import PLANTED

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "check_records.py"
THIRD_PARTY = ("numpy", "requests", "yaml", "pandas", "google")


def bare_python(*args, cwd=ROOT):
    env = {k: v for k, v in os.environ.items() if k != "FNO_SLACK_BOT_TOKEN"}  # never a real Slack post
    return subprocess.run([sys.executable, "-S", *args], capture_output=True, text=True, cwd=cwd, env=env, check=False)


def test_a_clean_file_passes_without_any_installed_package(tmp_path):
    file = tmp_path / "notes.md"
    file.write_text("nothing secret here\n")
    result = bare_python(str(SCRIPT), str(file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "record scan: clean (1 files)"


def test_a_planted_credential_is_refused_and_its_alert_text_printed_without_any_installed_package(tmp_path):
    file = tmp_path / "notes.md"
    file.write_text("ok\n" + PLANTED["Slack token"] + "\n")
    result = bare_python(str(SCRIPT), "--alert", str(file))
    assert result.returncode == 1, result.stderr
    assert "record scan: REFUSED, 1 finding(s)" in result.stdout
    assert "alert NOT sent: the #fno-desk sender could not be loaded (ModuleNotFoundError" in result.stdout
    assert "Public-record scan refused a commit" in result.stdout and PLANTED["Slack token"] not in result.stdout


def test_the_scan_and_its_root_import_no_third_party_module():
    code = (
        "import sys; sys.path.insert(0, '.'); import fno.record_scan.wiring, fno.record_scan.record_files; "
        f"print(sorted(m for m in sys.modules if m.split('.')[0] in {THIRD_PARTY!r}))"
    )
    result = bare_python("-c", code)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]"
