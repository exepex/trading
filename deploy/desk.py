"""Entry point used by the scheduled jobs and by you, on any operating system.

    <venv python> deploy/desk.py deploy status
    <venv python> deploy/desk.py live status

It works from any current folder, which schedulers need.
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

from fno.__main__ import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
