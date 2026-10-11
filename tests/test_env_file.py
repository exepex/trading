import os

from fno.env_file import load_env_file, parse_env_lines


def test_parse_env_lines():
    lines = ["# secrets", "FNO_SLACK_BOT_TOKEN=xoxb-1  # bot", 'QUOTED="abc"', "EMPTY=", "bad line", " SPACED = v "]
    assert parse_env_lines(lines) == {"FNO_SLACK_BOT_TOKEN": "xoxb-1", "QUOTED": "abc", "SPACED": "v"}


def test_existing_environment_wins(tmp_path, monkeypatch):
    env = tmp_path / ".trading.env"
    env.write_text("FNO_TEST_A=from_file\nFNO_TEST_B=from_file\n", encoding="utf-8")
    monkeypatch.setenv("FNO_TEST_A", "already_set")
    monkeypatch.delenv("FNO_TEST_B", raising=False)
    assert load_env_file(env) == ["FNO_TEST_B"]
    assert os.environ["FNO_TEST_A"] == "already_set" and os.environ["FNO_TEST_B"] == "from_file"
    assert load_env_file(tmp_path / "missing.env") == []
