"""Story O11, FL1-1's criterion 8, FL1-1c and FL1-1d: on the recorded day, G13b's 15:45 issue is written from the
day's chain and sealed in the day run, and the evening edition (`lab close`, 20:05) posts one message to #fno-forecast
with its lines, the picture and the details file, with no alert (G13b and the lab live from the day, so no earlier
forecast is expected and today is not checked: nothing was forecast for it)."""

import json

from fno.forecast_lab.page.model import Band
from fno.forecast_lab.page.plain import certain, likely
from fno.price_ranges.folders import live_path

from . import real_day as rd


def test_the_evening_message_posts_g13b_s_issue_of_the_day_with_its_picture_and_details(day):
    out, root, alerts = day
    assert out.log.result("price_ranges")["status"] == "ok"
    lines = out.lab.evening(rd.DAY)
    record = json.loads((root / "drive" / "data" / live_path("NIFTY", rd.DAY, "1545")).read_bytes())
    n1 = next(r for r in record["rows"] if (r["forecaster"], r["horizon"]) == ("implied", "N1"))
    band = Band(n1["q05"], n1["q25"], n1["q50"], n1["q75"], n1["q95"])
    (text,) = out.lab.channel.posts
    title, first, record, ahead, status = text.splitlines()
    right = "Right = the close fell inside the “almost certainly” range."
    assert title == f"*Was today's forecast right?* (Fri 16 Oct, 20:05) {right}"
    assert first == ("❌ *NIFTY* today: no verdict. No forecast was issued for today (the Thu 15 Oct 15:45 issue "
                     "holds no next-session forecast for Fri 16 Oct), so there is nothing to check.")  # fmt: skip
    assert record == "⚪ too few live days to rate | Live so far: none scored yet | Back-test: none"
    assert ahead.startswith(f"Next: next trading day, Mon 19 Oct: most likely {likely(band)} (almost certainly "
                            f"{certain(band)})")  # fmt: skip
    assert status == ("⚠️ NIFTY: no forecast was issued for 2026-10-15, so it has no score (a gap in the record, not "
                      "a late score; newest scored close none). Research only. Not a trade tip.")  # fmt: skip
    # the replay's Drive holds no 15 Oct issue, so 15 Oct can never be scored: a gap, said, never hidden (FL1-1e)
    (files,) = out.lab.channel.files
    assert list(files) == ["forecast-evening-2026-10-16.png", "forecast-evening-2026-10-16.html"]
    details = files["forecast-evening-2026-10-16.html"].decode()
    assert details.startswith("<!doctype html>") and "Research only. Not a trade tip." in details  # the owner's design
    # FL1-1's seal-check lines are not drawn by the signed-off page (raised with the designer and the orchestrator)
    posted = ["lab close 2026-10-16: report to #fno-forecast: posted",
              "lab close 2026-10-16: 0 of 0 alert(s) sent to #fno-desk"]  # fmt: skip
    assert lines == posted
    assert alerts.sent == []
