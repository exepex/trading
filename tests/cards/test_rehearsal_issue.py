"""Story T1f, criteria 1, 2, 6 and 7: in a rehearsal the card's clock checks are REH1c's "replay clock, not checked"
lines, no GitHub client is built, and the post leaves its Drive record and delivery metadata. The reproduction of the
23 Oct rehearsal (REH1's HTTP guard installed, the card posted) runs in a fresh process, as REH1's own guard tests do,
so this test's process is never changed."""

import json
import subprocess
import sys
from datetime import date

from fno.cards import wiring
from fno.cards.card_clocks import ServerCardClocks
from fno.config import ROOT
from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.card_label import RehearsalCardClocks
from fno.rehearsal.mode import Rehearsal
from fno.rehearsal.preopen_wiring import NOT_CHECKED

PROBE = """import json, sys
from datetime import date
from pathlib import Path
from fno.rehearsal import http_guard
from fno.cards import wiring
from fno.cards.card_clocks import ServerCardClocks
from fno.cards.deliveries import RepoDeliveryFiles
from fno.cards.issue import CardIssuer
from fno.server_clock import GITHUB_TIME_URL
from tests.cards.fakes import FakeRecords, Ticking, daily_card
from tests.cards.test_issue_guards import Saved, Sent

built = []
real_clock = wiring.HttpDateClock
wiring.HttpDateClock = lambda *a, **k: built.append(a) or real_clock(*a, **k)
http_guard.install()
root, hooked = Path(sys.argv[1]), sys.argv[2] == "hook"
records, host = FakeRecords(), Ticking()
card, text = daily_card(records, root).prepare(date(2026, 10, 15))
clocks = wiring.build_card_clocks() if hooked else ServerCardClocks(
    [real_clock("GitHub", GITHUB_TIME_URL.format(repository="exepex/trading"))], host)
poster, store = Sent(), Saved()
result = CardIssuer(poster, store, RepoDeliveryFiles(root, records), clocks, host, "c" * 40).issue(card, text)
(path,) = (root / "research" / "cards" / "deliveries" / "2026").glob("*.json")
stored = json.loads(path.read_text())
print(json.dumps({"clock": {c["server"]: c["line"] for c in stored["clock"]}, "built": len(built),
                  "posts": len(poster.posts), "drive": len(store.saved), "last": result.lines[-1],
                  "complete": result.complete}))
"""


def probe(tmp_path, variant: str) -> dict:
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path), "PYTHONPATH": str(ROOT),
           ENV_FNO_REHEARSAL: Rehearsal.new(date(2026, 10, 23), tmp_path, tmp_path).to_env()}  # fmt: skip
    done = subprocess.run([sys.executable, "-c", PROBE, str(tmp_path), variant], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=120)  # fmt: skip
    assert done.returncode == 0, done.stderr[-2000:]
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_in_a_rehearsal_the_card_finishes_with_the_rehearsal_lines_and_builds_no_github_client(tmp_path):
    found = probe(tmp_path, "hook")
    line = f"clock NOT CHECKED: host vs {{}} ({NOT_CHECKED})"
    assert found["clock"] == {"Slack": line.format("Slack"), "GitHub": line.format("GitHub")}
    assert found["built"] == 0 and found["posts"] == 1 and found["drive"] == 1 and found["complete"]
    assert found["last"].startswith("delivery metadata written: research/cards/deliveries/2026/2026-10-15-a1.json")


def test_without_the_hook_the_refused_call_is_caught_but_named_so_the_rehearsal_test_would_fail(tmp_path):
    """Criterion 6: the hook removed (the real clocks in a rehearsal), the guard's refusal no longer stops the issue
    (criterion 3), but GitHub's entry says RehearsalCallRefused, not the rehearsal line, and the issue failed."""
    found = probe(tmp_path, "real")
    assert found["clock"]["GitHub"] == "clock NOT CHECKED: host vs GitHub (RehearsalCallRefused)"
    assert found["posts"] == 1 and found["drive"] == 1 and not found["complete"]
    assert found["last"].startswith("delivery metadata written:")


def test_the_builder_gives_the_rehearsal_form_in_the_mode_and_the_real_one_outside(monkeypatch, tmp_path):
    built = []
    real_clock = wiring.HttpDateClock
    monkeypatch.setattr(wiring, "HttpDateClock", lambda *a, **k: built.append(a) or real_clock(*a, **k))
    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(date(2026, 10, 23), tmp_path, tmp_path).to_env())
    assert isinstance(wiring.build_card_clocks(), RehearsalCardClocks) and built == []  # P8: no GitHub client
    monkeypatch.delenv(ENV_FNO_REHEARSAL)
    real = wiring.build_card_clocks({})
    assert isinstance(real, ServerCardClocks) and [s.name for s in real.servers] == ["GitHub"] and len(built) == 1
