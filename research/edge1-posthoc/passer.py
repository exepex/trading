"""Run 1 only: BANKNIFTY SF TP50 trades, at the code tree given as argv[1]; the decided mean with and without the
16 Nov 2021 cycle (the +21,533 trade in the original run)."""
import sys
from datetime import date
root = sys.argv[1]
sys.path.insert(0, root); sys.path.insert(0, root + "/research/edge1")
import numpy as np
from edge1study.inputs import calendar, markets
from edge1study.runner import RUN1_FROM, RUN1_TO, RUN1_SEAL, Market, cycles_of, run_variant, sealed
from edge1study.stats import complete
from fno.config import load_app_config
m = markets(through=RUN1_SEAL)["BANKNIFTY"]
sm = Market("BANKNIFTY", sealed(m.panel, RUN1_SEAL), m.lots, m.settlement)
cyc = cycles_of(sm.panel, calendar(), RUN1_FROM, RUN1_TO, RUN1_SEAL)
trades = run_variant(sm, cyc, "SF", "TP50", load_app_config()["charges"], 1.0)
done = complete(trades)
key = date(2021, 11, 16)
hit = [t for t in trades if t.taken and t.cycle.entry_day == key]
for t in hit:
    print("cycle", t.cycle.entry_day, "exit", t.exit_day, t.exit_how, "net", round(t.net), "incomplete", t.incomplete_exit,
          "impossible", getattr(t, "impossible_exit", None), "raw", getattr(t, "raw_net", None))
nets = [t.net for t in done]
without = [t.net for t in done if t.cycle.entry_day != key]
print("complete", len(nets), "mean", round(np.mean(nets)), "| without the 16 Nov 2021 cycle", len(without), round(np.mean(without)))
