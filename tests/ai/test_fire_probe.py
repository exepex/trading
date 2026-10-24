"""Story G11 fire probe (orchestrator, 25 Oct 2026). Good: a fire prints the size and the session link. Bad: a refused
fire (HTTP 413, 401, no network) prints why and exits 1. Boundary: the text is exactly 24 KiB, one line, ending in
exactly one single quote, under the pointer cap and above a real v4 pointer. Empty: a truncated text (the quote
lost) is still refused by `brief`. The token is never printed, and the workflow only ever runs by hand."""

from pathlib import Path

import pytest
import requests
import yaml

from fno import cli
from fno.ai.book_run import read_run
from fno.ai.fire_probe import PROBE_BYTES, ProbeText, fire_probe
from fno.ai.pointer import PointerRefused
from fno.constants import ENV_ROUTINE_BOOK3_TOKEN, ENV_ROUTINE_BOOK3_TRIGGER_ID
from fno.constants_operations import ROUTINE_POINTER_MAX_BYTES
from tests.pipeline.fakes import FakeTrigger

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "routine-fire-probe.yml"
TOKEN = "probe-token-never-printed-0123456789"
V4_POINTER_BYTES = 19_500  # the largest v4 pointer measured (18-19 KB, G11 Claims)


def test_the_text_is_one_line_ending_in_exactly_one_quote_and_v4_sized_under_the_cap():
    text = ProbeText().to_text()
    assert len(text.encode("utf-8")) == PROBE_BYTES == 24 * 1024
    assert V4_POINTER_BYTES < PROBE_BYTES <= ROUTINE_POINTER_MAX_BYTES
    assert "\n" not in text and "\r" not in text  # the stored prompt's step 2: one line
    assert text.endswith("'") and text.count("'") == 1  # and its single quote, the last character only


def test_a_truncated_text_has_lost_its_quote_and_brief_refuses_it():
    truncated = ProbeText().to_text()[:-1]
    with pytest.raises(PointerRefused):
        read_run(truncated, lambda pointer: {})


def test_a_fire_prints_the_size_and_the_session_link():
    trigger = FakeTrigger("book3_ai")
    fired, line = fire_probe(trigger)
    assert fired and len(trigger.fired) == 1
    assert line == "Omenix F&O fire probe: fired 24,576 bytes to book3_ai: https://claude.ai/code/session_1"


def test_a_refused_fire_says_why():
    fired, line = fire_probe(FakeTrigger("book3_ai", failure="HTTP 413 from the routine API"))
    assert not fired and line.endswith("NOT fired (24,576 bytes to book3_ai): HTTP 413 from the routine API")


class Answer:
    def __init__(self, status: int, body: dict | None = None):
        self.status_code, self.ok, self._body = status, status < 400, body

    def json(self):
        if self._body is None:
            raise ValueError("no JSON")
        return self._body


@pytest.mark.parametrize(
    ("answer", "code", "shown"),
    [(Answer(200, {"claude_code_session_url": "https://claude.ai/code/session_01Probe"}), 0, "session_01Probe"),
     (Answer(413), 1, "HTTP 413 from the routine API"), (Answer(401), 1, "token was refused"),
     (requests.ConnectionError(f"Bearer {TOKEN}"), 1, "routine API not reached (ConnectionError)")],
)  # fmt: skip
def test_the_command_fires_book_3s_routine_and_never_prints_the_token(monkeypatch, capsys, answer, code, shown):
    sent = {}

    def post(session, url, headers, json, timeout):
        sent.update(url=url, headers=headers, text=json["text"])
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setenv(ENV_ROUTINE_BOOK3_TRIGGER_ID, "trig_01Probe")
    monkeypatch.setenv(ENV_ROUTINE_BOOK3_TOKEN, TOKEN)
    monkeypatch.setattr(requests.Session, "post", post)
    assert cli.main(["ai", "fire-probe"]) == code
    out = capsys.readouterr()
    assert shown in out.out and TOKEN not in out.out + out.err
    assert sent["url"].endswith("/routines/trig_01Probe/fire") and sent["text"] == ProbeText().to_text()


def test_without_book_3s_secrets_nothing_is_fired_and_the_missing_names_are_said(monkeypatch, capsys):
    monkeypatch.delenv(ENV_ROUTINE_BOOK3_TRIGGER_ID, raising=False)
    monkeypatch.delenv(ENV_ROUTINE_BOOK3_TOKEN, raising=False)
    assert cli.main(["ai", "fire-probe"]) == 1
    assert ENV_ROUTINE_BOOK3_TOKEN in capsys.readouterr().out


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text())


def test_the_workflow_runs_only_by_hand_reads_only_and_pushes_nothing():
    flow = _workflow()
    assert set(flow[True]) == {"workflow_dispatch"}  # YAML reads the key "on" as True: never a push or a schedule
    assert flow["permissions"] == {"contents": "read"}
    runs = " ".join(step.get("run", "") for step in flow["jobs"]["probe"]["steps"])
    assert "python -m fno ai fire-probe" in runs and "git " not in runs


def test_the_workflow_holds_book_3s_two_secrets_only_and_only_on_the_fire_step():
    job = _workflow()["jobs"]["probe"]
    holding = [step for step in job["steps"] if "env" in step]
    assert "env" not in job and len(holding) == 1 and "fire-probe" in holding[0]["run"]  # never during the install
    env = holding[0]["env"]
    assert set(env) == {ENV_ROUTINE_BOOK3_TRIGGER_ID, ENV_ROUTINE_BOOK3_TOKEN}
    assert all(value == f"${{{{ secrets.{name} }}}}" for name, value in env.items())
