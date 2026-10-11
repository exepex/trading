from pathlib import Path

from fno import notify


class FakeResp:
    def __init__(self, data=None):
        self.data = data or {"ok": True}

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def test_post_brief_uploads_all_pages_in_one_message(tmp_path, monkeypatch):
    (tmp_path / "2026-10-12-slack.md").write_text("*Brief*")
    for i in (2, 1, 10):
        (tmp_path / f"2026-10-12-brief-{i}of10.png").write_bytes(b"png")
    calls = []

    def fake_post(url, **kw):
        calls.append((url, kw))
        if url.endswith("files.getUploadURLExternal"):
            return FakeResp({"ok": True, "upload_url": "https://files.slack.com/up", "file_id": f"F{len(calls)}"})
        return FakeResp()

    monkeypatch.setattr(notify.requests, "post", fake_post)
    monkeypatch.setenv("FNO_SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.delenv("FNO_SLACK_CHANNEL_ID", raising=False)
    out = notify.post_brief(tmp_path, "2026-10-12", {"slack": {"channel_id": "C123"}}, "https://example/page")
    assert "3 page image(s) to C123" in out
    complete = calls[-1][1]["json"]
    assert complete["channel_id"] == "C123" and len(complete["files"]) == 3
    assert [f["title"] for f in complete["files"]][0].endswith("1of10")  # pages in order
    assert "https://example/page" in complete["initial_comment"]
    assert all(c[1]["headers"]["Authorization"] == "Bearer xoxb-test" for c in calls if "slack.com/api" in c[0])


def test_never_uses_market_brief_variables(tmp_path, monkeypatch):
    (tmp_path / "d-slack.md").write_text("x")
    monkeypatch.delenv("FNO_SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("FNO_SLACK_WEBHOOK_URL", raising=False)
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-market-brief")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/market-brief")
    try:
        notify.post_brief(tmp_path, "d", {"slack": {"channel_id": "C1"}})
    except notify.SlackError:
        return
    raise AssertionError("must not fall back to the market-brief SLACK_* variables")
