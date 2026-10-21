"""Story O11, FL1-1's criterion 8: on the recorded day, G13b's 15:45 issue is written from the day's chain and sealed,
and `lab close` posts the 15:45 report with it to #fno-forecast, once, with no alert (G13b and the lab live from the
day, so no earlier forecast is expected and today's close is not archived yet)."""

import json

from fno.price_ranges.folders import live_path

from . import real_day as rd


def test_the_1545_report_posts_g13b_s_sealed_issue_of_the_day(day):
    out, root, alerts = day
    assert out.log.result("price_ranges")["status"] == "ok" and out.log.result("lab_close")["status"] == "ok"
    record = json.loads((root / "drive" / "data" / live_path("NIFTY", rd.DAY, "1545")).read_bytes())
    (text,) = out.lab.channel.posts
    assert text.startswith("F&O forecast lab 2026-10-16: 15:45 report (paper research only, never an order)")
    assert f"NIFTY: sealed ranges for the next sessions (from {record['s_ref']:.2f})" in text
    assert "  N1 (2026-10-19) rv20: 5/25/50/75/95 " in text  # Monday: the next regular session
    assert "NIFTY forecasts for 2026-10-16: none expected (issued before G13b's first live day)" in text
    assert "Trust: 0 scored trading day(s) of about 60 needed to judge calibration" in text
    posted = ["lab close 2026-10-16: report to #fno-forecast: posted",
              "lab close 2026-10-16: 0 of 0 alert(s) sent to #fno-desk"]  # fmt: skip
    assert out.log.result("lab_close")["lines"] == posted
    assert alerts.sent == []
