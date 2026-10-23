"""Run 2, after final.json is committed: why BANKNIFTY SF TP50 never fired. Per trade: days in the window, fully
traded days, valid days, and the lowest mark/credit on a fully traded valid day."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "edge1"))
from edge1study.inputs import calendar, markets
from edge1study.runner import RUN2_FROM, cycles_of, run_variant
from edge1study.trade import _prices, _all_traded, _mark
from edge1study.verticals import valid
from fno.config import load_app_config
m = markets()["BANKNIFTY"]
last = m.days[-1]
cyc = cycles_of(m.panel, calendar(), RUN2_FROM, last, last)
trades = run_variant(m, cyc, "SF", "TP50", load_app_config()["charges"], 1.0)
tot = {"days": 0, "traded": 0, "valid": 0}
for t in trades:
    if not t.taken:
        continue
    days = [d for d in m.days if t.cycle.entry_day < d < t.cycle.exit_day]
    traded = valid_n = 0; best = None
    for d in days:
        pr = _prices(m.panel, d, t.cycle.expiry, t.legs)
        if not _all_traded(pr):
            continue
        traded += 1
        if not valid(t.legs, [p.price for p in pr]):
            continue
        valid_n += 1
        r = _mark(t.legs, pr) / t.credit
        best = r if best is None else min(best, r)
    tot["days"] += len(days); tot["traded"] += traded; tot["valid"] += valid_n
    print(t.cycle.entry_day, "w", t.width, "days", len(days), "traded", traded, "valid", valid_n,
          "min mark/credit", None if best is None else round(best, 2), "net", round(t.net))
print(tot)
