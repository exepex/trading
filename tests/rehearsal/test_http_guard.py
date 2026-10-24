"""REH1, acceptance 4 and addition 1: a rehearsing process reaches no live source and fires no real AI routine. Each
call is refused before it is made, through `requests` (the whole URL) and through `http.client` (the host). Run in a
fresh process, so this test's own process is never changed."""

import subprocess
import sys

import pytest

from fno.rehearsal.http_guard import allowed

PROBE = """import sys, requests, urllib.request, urllib3
from fno.rehearsal import http_guard
from fno.rehearsal.http_guard import RehearsalCallRefused
http_guard.install(); http_guard.install()
for url in sys.argv[1:]:
    try:
        if url.startswith("urllib:"):
            urllib.request.urlopen(url[7:], timeout=1)
        elif url.startswith("urllib3:"):
            urllib3.PoolManager().request("GET", url[8:], timeout=1, retries=False)
        else:
            requests.post(url, timeout=1)
        print("REACHED", url)
    except RehearsalCallRefused:
        print("REFUSED", url)
    except Exception as other:
        print("OTHER", url, type(other).__name__)
"""
LIVE = ["https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY", "https://api.groww.in/v1/live-data/quote",
        "https://api.anthropic.com/v1/messages", "https://api.github.com/repos/exepex/trading/dispatches",
        "https://slack.com/api/chat.delete", "urllib:https://growwapi-assets.groww.in/instruments.csv",
        "urllib:http://example.com/", "urllib3:https://www.nseindia.com/api/allIndices"]  # fmt: skip


def test_every_live_source_anthropic_and_github_s_api_are_refused_before_the_call():
    done = subprocess.run([sys.executable, "-c", PROBE, *LIVE], capture_output=True, text=True, timeout=60, check=True)
    assert done.stdout.split("\n")[:-1] == [f"REFUSED {url}" for url in LIVE]


ALLOWED = ["https://www.googleapis.com/drive/v3/files", "https://oauth2.googleapis.com/token",
           "https://slack.com/api/chat.postMessage", "https://files.slack.com/upload/v1/x"]  # fmt: skip


@pytest.mark.parametrize("url", ALLOWED)
def test_drive_and_slack_s_posting_calls_are_allowed(url):
    assert allowed("POST", url)
