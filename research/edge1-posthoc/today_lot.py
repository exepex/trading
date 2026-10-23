"""Section 12's today's-lot sensitivity for the passer (BANKNIFTY SF TP50, lot 30) in run 1 (sealed) and run 2:
every cycle re-run with today's lot (the cap picks its width again), decided mean and n; reported, never decided on."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "edge1"))
from edge1study.inputs import calendar, markets
from edge1study.runner import RUN1_FROM, RUN1_TO, RUN1_SEAL, RUN2_FROM, Market, cycles_of, run_variant, sealed
from edge1study.stats import complete, mean_net
from fno.config import load_app_config
charges, cal = load_app_config()["charges"], calendar()
def today(m, lot):
    return Market(m.index, m.panel, {d: dict.fromkeys(e, lot) for d, e in m.lots.items()}, m.settlement)
r1 = markets(through=RUN1_SEAL)["BANKNIFTY"]; r1 = Market(r1.index, sealed(r1.panel, RUN1_SEAL), r1.lots, r1.settlement)
r2 = markets()["BANKNIFTY"]
for label, m, cyc in (("run1", r1, cycles_of(r1.panel, cal, RUN1_FROM, RUN1_TO, RUN1_SEAL)),
                      ("run2", r2, cycles_of(r2.panel, cal, RUN2_FROM, r2.days[-1], r2.days[-1]))):
    done = complete(run_variant(today(m, 30), cyc, "SF", "TP50", charges, 1.0))
    print(label, "lot 30: complete", len(done), "decided mean", round(mean_net(done) or 0))
