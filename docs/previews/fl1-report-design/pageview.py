"""Reads the builder's PageView (fno/forecast_lab/page/model.py), as dataclasses or as the JSON dump, into the plain
values the pages draw. Nothing here computes a forecast number: dates are formatted, bands renamed, lists ordered.
Entry points for the builder's PageRenderer: render_picture(page_view) and render_details(page_view)."""

from datetime import date

PROBLEM_FREE = "All systems normal"
RESEARCH_LINE = "Research only. Not a trade tip."
WORDS = {"most likely": "a normal day's move (1 day in 2)", "almost certainly": "covers even a jumpy day (9 days in 10)",
         "right": "the close stayed inside “almost certainly”"}
LIGHT_RULE = "green at 25 or more of the last 30 days, amber at 24, red at 23 or fewer"
NOT_CHECKED = ("overnight US moves (the US closes stay private until the owner approves a display), FII/DII flows "
               "(archived, not yet read here) and the opening gap (no index open price is held)")
HORIZON_TITLE = {"N1": "next session", "N3": "in 3 sessions"}


def _get(obj, key):
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def _day(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


def short(value):
    """'16 Oct'."""
    d = _day(value)
    return f"{d.day} {d.strftime('%b')}"


def long(value):
    """'Fri 16 Oct'."""
    d = _day(value)
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b')}"


def _band(band):
    return {"lo90": _get(band, "q05"), "lo50": _get(band, "q25"), "mid": _get(band, "q50"),
            "hi50": _get(band, "q75"), "hi90": _get(band, "q95")}


def _range(rv):
    out = _band(_get(rv, "band"))
    out["date"] = long(_get(rv, "target_day"))
    out["when"] = _get(rv, "when")
    return out


def _outcome(point):
    out = _band(_get(point, "band"))
    out.update(date=short(_get(point, "day")), close=_get(point, "close"), right=bool(_get(point, "inside_90")),
               live=bool(_get(point, "live")))
    return out


def _miss(m):
    reasons = list(_get(m, "reasons"))
    return {"date": long(_get(m, "day")), "points": int(round(_get(m, "points"))), "side": _get(m, "side"),
            "reason": "; ".join(reasons)}


def _pct(value):
    return "n/a" if value is None else f"{value:.0%}"


def _method(record):
    cells = []
    for c in _get(record, "cells"):
        in50, in90 = _get(c, "inside_50"), _get(c, "inside_90")
        cells.append("none" if in90 is None else "in50" if in50 else "in90" if in90 else "miss")
    windows = list(_get(record, "windows"))
    err = next((_get(w, "error_points") for w in windows if _get(w, "sessions") == 30), None)
    score = {"method": _get(record, "method"), "best": bool(_get(record, "best")),
             "in50": " · ".join(_pct(_get(w, "inside_50")) for w in windows),
             "in90": " · ".join(_pct(_get(w, "inside_90")) for w in windows),
             "err": "n/a" if err is None else f"{err:.0f}"}
    return _get(record, "method"), cells, score


def _horizon_methods(horizon):
    grid, scores = {}, []
    records = sorted(_get(horizon, "methods"), key=lambda r: (not _get(r, "best"), _get(r, "method")))
    for record in records:
        name, cells, score = _method(record)
        grid[name] = cells
        scores.append(score)
    return {"grid": grid, "scores": scores}


def _index(ix):
    horizons = list(_get(ix, "horizons"))
    points = [_outcome(p) for p in _get(_get(horizons[0], "timeline"), "points")]
    today = {_get(r, "horizon"): _range(r) for r in _get(ix, "today")}
    return {
        "name": _get(ix, "underlying"), "today": _get(ix, "price"), "price_at": _get(ix, "price_at"),
        "method": _get(ix, "method"), "right30": _get(ix, "right"), "scored": _get(ix, "scored"),
        "light": _get(ix, "light"), "light_word": _get(ix, "light_word"),
        "wrong_days": [short(d) for d in _get(ix, "wrong_days")],
        "next": today.get("N1"), "three": today.get("N3"),
        "misses7": [_miss(m) for m in _get(ix, "misses")],
        "direction": "" if _get(ix, "direction_edge") else "It cannot tell up from down yet.",
        "live_days": _get(ix, "live_days"), "days_needed": _get(ix, "days_needed"),
        "days": points,
        "methods": {HORIZON_TITLE[_get(_get(h, "timeline"), "horizon")]: _horizon_methods(h) for h in horizons},
    }


def adapt(page_view):
    """The PageView as the plain dict the pages draw from."""
    day = _day(_get(page_view, "day"))
    system = list(_get(page_view, "system"))
    return {
        "report_day": f"{long(day)} {day.year}", "report_time": "15:45",
        "preview_note": _get(page_view, "provenance"),
        "system": system, "system_line": PROBLEM_FREE if not system else None, "research_line": RESEARCH_LINE,
        "words": WORDS, "light_rule": LIGHT_RULE, "not_checked": NOT_CHECKED,
        "stricter": [f'{_get(p, "group")}, {_get(p, "method")}: {_get(p, "text")}' for p in _get(page_view, "drift")],
        "checks": list(_get(page_view, "checks")), "alerts": list(_get(page_view, "alerts")),
        "indices": [_index(ix) for ix in _get(page_view, "indices")],
    }


def render_picture(page_view):
    from build import picture
    return picture(adapt(page_view))


def render_details(page_view):
    from build import details
    return details(adapt(page_view))
