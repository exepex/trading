"""FL1-1c: one Slack message with the text and the files. A failure before the last call is "not posted" (a rerun may
try again); a lost answer to the last call may have posted the message, so it is never retried; no token, no post."""

import requests

from fno.forecast_lab.delivery import Attachment, NoReportPoster, SlackFilesPoster

FILES = [Attachment("forecast.png", b"png", "Today's forecast"), Attachment("forecast.html", b"<p>", "Details")]


class Answer:
    def __init__(self, body=None, status=200):
        self.body, self.status_code = body, status

    def json(self):
        if isinstance(self.body, Exception):
            raise self.body
        return self.body


class Session:
    def __init__(self, complete=None, upload_status=200, get=None, unreadable=False):
        self.calls, self.complete, self.upload_status, self.get = [], complete, upload_status, get
        self.unreadable = unreadable  # the last call answers, but its body is not JSON

    def post(self, url, headers=None, data=None, json=None, timeout=None):
        self.calls.append((url, data if url.startswith("https://upload") else (json or data)))
        if url.endswith("getUploadURLExternal"):
            body = self.get or {"ok": True, "upload_url": f"https://upload/{data['filename']}",
                                "file_id": f"F{data['filename']}"}  # fmt: skip
            return Answer(body)
        if url.startswith("https://upload"):
            return Answer(status=self.upload_status)
        if isinstance(self.complete, BaseException):
            raise self.complete
        if self.unreadable:
            return Answer(ValueError("Expecting value"))
        return Answer(self.complete or {"ok": True})


def test_both_files_are_uploaded_then_shared_in_one_message_with_the_text():
    session = Session()
    delivery = SlackFilesPoster("test-token", "C0", session).post("three lines", FILES)
    assert (delivery.sent, delivery.outcome) == (True, "posted to #fno-forecast")
    complete = session.calls[-1][1]
    assert complete == {"files": [{"id": "Fforecast.png", "title": "Today's forecast"},
                                  {"id": "Fforecast.html", "title": "Details"}],
                        "channel_id": "C0", "initial_comment": "three lines"}  # fmt: skip
    assert session.calls[1][1] == b"png" and len(session.calls) == 5


def test_a_failure_before_the_last_call_is_surely_not_posted():
    for session in (Session(get={"ok": False, "error": "not_authed"}), Session(upload_status=500),
                    Session(complete={"ok": False, "error": "channel_not_found"})):  # fmt: skip
        delivery = SlackFilesPoster("test-token", "C0", session).post("x", FILES)
        assert not delivery.sent and not delivery.may_have_posted and "test-token" not in delivery.outcome


def test_a_lost_answer_to_the_last_call_may_have_posted_and_a_refused_connection_did_not():
    lost = SlackFilesPoster("test-token", "C0", Session(complete=requests.ReadTimeout())).post("x", FILES)
    assert lost.may_have_posted and "Slack may still have posted it (check channel C0)" in lost.outcome
    refused = SlackFilesPoster("test-token", "C0", Session(complete=requests.ConnectTimeout())).post("x", FILES)
    assert not refused.may_have_posted and refused.outcome == "alert NOT sent: ConnectTimeout"
    unreadable = SlackFilesPoster("test-token", "C0", Session(unreadable=True)).post("x", FILES)
    assert unreadable.may_have_posted and not unreadable.sent  # judge 434 Q2: an unreadable answer is never retried


def test_without_a_token_nothing_is_sent_and_the_outcome_says_why():
    delivery = NoReportPoster().post("x", FILES)
    assert not delivery.sent and delivery.outcome == "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"
