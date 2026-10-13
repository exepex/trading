"""The owner's one-time Drive upload setup prints the three settings under the names the app reads."""

import importlib.util
from pathlib import Path

from fno.constants import ENV_GDRIVE_OAUTH_CLIENT_ID, ENV_GDRIVE_OAUTH_CLIENT_SECRET, ENV_GDRIVE_OAUTH_REFRESH_TOKEN

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "gdrive_oauth_setup.py"


def load():
    spec = importlib.util.spec_from_file_location("gdrive_oauth_setup", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prints_each_setting_under_the_name_the_app_reads():
    lines = load().settings_lines("cid", "csecret", "rtoken")
    assert f"{ENV_GDRIVE_OAUTH_CLIENT_ID}=cid" in lines
    assert f"{ENV_GDRIVE_OAUTH_CLIENT_SECRET}=csecret" in lines
    assert f"{ENV_GDRIVE_OAUTH_REFRESH_TOKEN}=rtoken" in lines


def test_a_missing_client_file_prints_the_usage(capsys):
    assert load().main(["/no/such/file.json"]) == 2
    assert "usage" in capsys.readouterr().out
