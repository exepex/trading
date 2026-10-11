"""Post the daily brief to the F&O Slack channel with the F&O bot's own credentials.

Environment variables (separate from the market-brief tool's SLACK_* variables):
  FNO_SLACK_BOT_TOKEN      xoxb-... token of the F&O Slack app (scopes: chat:write, files:write)
  FNO_SLACK_CHANNEL_ID     channel to post in (default: slack.channel_id in config.yaml)
  FNO_SLACK_WEBHOOK_URL    optional incoming webhook, used for a text-only post when there is no bot token
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

API = "https://slack.com/api/"


class SlackError(RuntimeError):
    pass


def _call(method: str, token: str, **kwargs) -> dict:
    resp = requests.post(API + method, headers={"Authorization": f"Bearer {token}"}, timeout=30, **kwargs)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise SlackError(f"{method}: {data.get('error', 'unknown error')}")
    return data


def upload_images(token: str, channel: str, images: list[Path], comment: str) -> dict:
    """Upload images and share them in one message with `comment` (Slack's external upload flow)."""
    files = []
    for img in images:
        data = img.read_bytes()
        ticket = _call("files.getUploadURLExternal", token, data={"filename": img.name, "length": len(data)})
        put = requests.post(ticket["upload_url"], data=data, headers={"Content-Type": "image/png"}, timeout=60)
        put.raise_for_status()
        files.append({"id": ticket["file_id"], "title": img.stem})
    return _call(
        "files.completeUploadExternal",
        token,
        json={"files": files, "channel_id": channel, "initial_comment": comment},
    )


def post_text(text: str, token: str | None, channel: str, webhook: str | None) -> None:
    if token:
        _call("chat.postMessage", token, json={"channel": channel, "text": text})
    elif webhook:
        requests.post(webhook, json={"text": text}, timeout=30).raise_for_status()
    else:
        raise SlackError("Set FNO_SLACK_BOT_TOKEN (or FNO_SLACK_WEBHOOK_URL for text only).")


def post_brief(reports_dir: Path, stamp: str, cfg: dict, web_url: str | None = None) -> str:
    """Post <stamp>-slack.md plus the page images. Returns a short description of what was sent."""
    token = os.environ.get("FNO_SLACK_BOT_TOKEN")
    webhook = os.environ.get("FNO_SLACK_WEBHOOK_URL")
    channel = os.environ.get("FNO_SLACK_CHANNEL_ID") or cfg.get("slack", {}).get("channel_id", "")
    text = (reports_dir / f"{stamp}-slack.md").read_text(encoding="utf-8")
    if web_url:
        text += f"\nInteractive web version: {web_url}"
    images = sorted(reports_dir.glob(f"{stamp}-brief-*of*.png"), key=lambda p: int(p.stem.split("-")[-1].split("of")[0]))
    if token and images:
        upload_images(token, channel, images, text)
        return f"posted text and {len(images)} page image(s) to {channel}"
    post_text(text, token, channel, webhook)
    return f"posted text only to {channel or 'webhook'}"
