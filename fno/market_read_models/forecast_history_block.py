"""The forecast history page (story P2, contract 2.9 `FnoForecastHistory`, page `forecast_history`): for each v3
question, each forecaster's running score as G4's report of each day gives it (`scores[].primary`: scored, mean_brier).

- **Live and back-fill apart:** G4's `live_1500_proxy` mode is `live`, `close_proxy` is `backfill_exploratory`; one
  series per forecaster and label, never joined.
- **One point per G4 report** (its as_of); a day without a report has no point, and a point needs n >= 1.
- **One back-fill file per series:** a back-fill series uses only the reports whose `inputs.backfill_sha256` is the
  newest report's. A rebuild of the back-fill moves every running average at once, so points across two files would
  make a period difference meaningless; the contract keeps one series per forecaster and label, so the page carries
  the newest file's series (what the screen draws)."""

from __future__ import annotations

from ..forecast_scoring.score_inputs import CLOSE_PROXY, LIVE
from .blocks import BlockBuilder, SessionRows
from .forecast_questions import V3_QUESTIONS

LABELS = {LIVE: "live", CLOSE_PROXY: "backfill_exploratory"}


class FnoForecastHistoryBlock(BlockBuilder):
    page_key, served_schema = "forecast_history", "FnoForecastHistoryResponse"

    def build(self, rows: SessionRows) -> dict:
        return forecast_history(rows.score_reports)


def forecast_history(reports: list[dict]) -> dict:
    points = _points(_same_backfill(reports))
    questions = []
    for question, (contract_id, plain) in V3_QUESTIONS.items():
        series = [{"forecaster": f, "label": LABELS[mode], "points": p} for (q, mode, f), p in points.items()
                  if q == question]  # fmt: skip
        if series:
            questions.append({"id": contract_id, "protocol": "v3", "plain": plain, "metric": "brier", "series": series})
    return {"questions": questions}


def _same_backfill(reports: list[dict]) -> list[tuple[dict, bool]]:
    """Each report with whether its back-fill file is the newest report's (only those carry back-fill points)."""
    newest = reports[-1]["inputs"].get("backfill_sha256") if reports else None
    return [(r, r["inputs"].get("backfill_sha256") == newest) for r in reports]


def _points(reports: list[tuple[dict, bool]]) -> dict[tuple[str, str, str], list[dict]]:
    """(question, mode, forecaster) -> the running score after each report, oldest first, sorted by forecaster."""
    out: dict[tuple[str, str, str], list[dict]] = {}
    for report, current_backfill in reports:
        for mode in report["modes"]:
            if mode["mode"] not in LABELS or (mode["mode"] == CLOSE_PROXY and not current_backfill):
                continue
            for score in mode["scores"]:
                summary = score["primary"]
                if summary["scored"] >= 1 and score["question"] in V3_QUESTIONS:
                    point = {"as_of": report["as_of"], "n": summary["scored"], "mean_loss": summary["mean_brier"]}
                    out.setdefault((score["question"], mode["mode"], score["forecaster"]), []).append(point)
    return dict(sorted(out.items(), key=lambda item: (item[0][2], item[0][1])))
