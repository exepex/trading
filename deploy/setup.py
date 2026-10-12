"""One-time setup of the F&O desk on any machine (Windows, Linux, macOS). Standard library only.

    python deploy/setup.py           # Windows: py deploy\\setup.py

Safe to run again: it updates packages, re-runs the tests and re-registers the jobs.
"""

import os
import shutil
import stat
import subprocess
import sys
import venv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = REPO_ROOT / ".venv"
ENV_FILE = Path.home() / ".trading.env"
MIN_PYTHON = (3, 11)
ENV_TEMPLATE = """# Secrets for the F&O desk. Only your account can read this file. Never commit it.
FNO_SLACK_BOT_TOKEN=
# Optional, only for the MotherDuck options in config.yaml (shared with the market-brief tool):
MOTHERDUCK_TOKEN=
# Groww Trade API (market data only). Recommended: the TOTP key and its TOTP secret, no daily approval needed.
GROWW_API_KEY=
GROWW_TOTP_SECRET=
"""


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def step(number: int, text: str) -> None:
    print(f"{number}/5 {text}", flush=True)


def run(*command: str) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    if sys.version_info < MIN_PYTHON:
        sys.exit(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is needed; this is {sys.version.split()[0]}.")
    if not shutil.which("git"):
        sys.exit("git was not found. Install it first (Windows: Git for Windows).")

    step(1, "Python environment")
    if not venv_python().exists():
        venv.create(VENV_DIR, with_pip=True)
    python = str(venv_python())
    run(python, "-m", "pip", "install", "--quiet", "--upgrade", "pip")
    run(python, "-m", "pip", "install", "--quiet", "-r", "requirements.txt", "-r", "requirements-groww.txt")

    step(2, "Tests")
    run(python, "-m", "pytest", "-q")

    step(3, "Secrets file")
    if not ENV_FILE.exists():
        ENV_FILE.write_text(ENV_TEMPLATE, encoding="utf-8")
        ENV_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)  # owner only (on Windows, files under your profile already are)
        print(f"Created {ENV_FILE}. Fill in the values, then run this script again.")
        return 0

    step(4, "Research data (the stock tool's files)")
    run(python, "deploy/desk.py", "live", "status")

    step(5, "Scheduled jobs and start")
    run(python, "deploy/desk.py", "deploy", "install")
    print("Done. Check any time with:", python, "deploy/desk.py deploy status")
    return 0


if __name__ == "__main__":
    sys.exit(main())
