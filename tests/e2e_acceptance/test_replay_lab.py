"""Story O11, FL1-1's criterion 8 and FL1-1c: on the recorded day, G13b's 15:45 issue is written from the day's chain
and sealed, and `lab close` posts one message to #fno-forecast with the 3 lines, the picture and the details file, with
no alert (G13b and the lab live from the day, so no earlier forecast is expected and today's close is not archived)."""

import json

from fno.forecast_lab.page.model import Band
from fno.forecast_lab.page.plain import certain, likely
from fno.price_ranges.folders import live_path

from . import real_day as rd


def test_the_1545_message_posts_g13b_s_issue_of_the_day_with_its_picture_and_details(day):
    out, root, alerts = day
    assert out.log.result("price_ranges")["status"] == "ok" and out.log.result("lab_close")["status"] == "ok"
    record = json.loads((root / "drive" / "data" / live_path("NIFTY", rd.DAY, "1545")).read_bytes())
    n1 = next(r for r in record["rows"] if (r["forecaster"], r["horizon"]) == ("implied", "N1"))
    band = Band(n1["q05"], n1["q25"], n1["q50"], n1["q75"], n1["q95"])
    (text,) = out.lab.channel.posts
    first, status = text.splitlines()
    assert first.startswith(f"*NIFTY* · next trading day, Mon 19 Oct: most likely {likely(band)} (almost certainly "
                            f"{certain(band)})") and first.endswith("⚪ no scored days yet")  # fmt: skip
    assert status == ("⚠️ NIFTY: newest scored close is none, expected 2026-10-15 (stale). Research only. "
                      "Not a trade tip.")  # no score exists in the replay's Drive: said, never hidden  # fmt: skip
    (files,) = out.lab.channel.files
    assert list(files) == ["forecast-2026-10-16.png", "forecast-2026-10-16.html"]
    details = files["forecast-2026-10-16.html"].decode()
    assert "NIFTY forecasts for 2026-10-16: none expected (issued before G13b&#x27;s first live day)" in details
    posted = ["lab close 2026-10-16: report to #fno-forecast: posted",
              "lab close 2026-10-16: 0 of 0 alert(s) sent to #fno-desk"]  # fmt: skip
    assert out.log.result("lab_close")["lines"] == posted
    assert alerts.sent == []
