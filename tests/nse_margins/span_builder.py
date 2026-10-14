"""A small SPAN 4 file built in code (story A14 tests): the NIFTY parts NSE's real file has, with hand-picked risk
arrays, plus one other symbol the reader must skip."""

from __future__ import annotations

import io
import zipfile
from datetime import date

ZEROS = (0.0,) * 16
DAY = date(2026, 10, 14)  # the session the file is for
EXPIRY = date(2026, 11, 23)  # the first monthly expiry 30+ days after DAY
UNDERLYING = 20000.0
LOT = 65
# SF width 100 at 20000: scenario 3 loses 100 - 70 - 20 + 12 = 22 per unit, scenario 4 loses -15 + 10 + 90 - 55 = 30
SF_ARRAYS = {
    ("C", 20000.0): {3: -100.0, 4: 15.0},
    ("C", 20100.0): {3: -70.0, 4: 10.0},
    ("P", 20000.0): {3: 20.0, 4: -90.0},
    ("P", 19900.0): {3: 12.0, 4: -55.0},
}
SF_100_SPAN = 30 * LOT
SF_100_EXPOSURE = 2 * 0.02 * UNDERLYING * LOT
# The SF legs' prices: sold 120 + 110, bought 35 + 30, so its net option value is -(230 - 65) x 65 = -10,725 a lot
SF_PRICES = {("C", 20000.0): 120.0, ("P", 20000.0): 110.0, ("C", 20100.0): 35.0, ("P", 19900.0): 30.0}
SF_100_NOV = -(120 + 110 - 35 - 30) * LOT


def risk(scenarios: dict[int, float]) -> tuple[float, ...]:
    return tuple(scenarios.get(i + 1, 0.0) for i in range(16))


def default_options(strikes=range(18000, 22001, 100)) -> dict[tuple[str, float], tuple[float, ...]]:
    options = {(kind, float(k)): ZEROS for k in strikes for kind in "CP"}
    options.update({contract: risk(values) for contract, values in SF_ARRAYS.items()})
    return options


def _option(kind: str, strike: float, values: tuple[float, ...]) -> str:
    arrays, price = "".join(f"<a>{v:.2f}</a>" for v in values), SF_PRICES.get((kind, strike), 10.0)
    return f"<opt><o>{kind}</o><k>{strike:.2f}</k><p>{price:.2f}</p><ra><r>1</r>{arrays}<d>0.5</d></ra></opt>"


def _series(expiry: date, options, cvf: str, sc: str) -> str:
    body = "".join(_option(kind, strike, values) for (kind, strike), values in sorted(options.items()))
    return f"<series><pe>{expiry:%Y%m%d}</pe><cvf>{cvf}</cvf><sc>{sc}</sc>{body}</series>"


def span_xml(created="202610132128", underlying=UNDERLYING, futures=(date(2026, 10, 27), EXPIRY), series=None,
             tiers=((date(2026, 10, 19), date(2031, 6, 24)),), som="0", adj="1.00000", cvf="1.00", sc="1.00000",
             symbol="NIFTY") -> str:  # fmt: skip
    series = series if series is not None else {EXPIRY: default_options()}
    futs = "".join(f"<fut><pe>{e:%Y%m%d}</pe><p>{underlying}</p></fut>" for e in futures)
    opts = "".join(_series(e, o, "1.00", sc) for e, o in series.items())
    tier_xml = "".join(f"<tier><tn>{n}</tn><sPe>{a:%Y%m%d}</sPe><ePe>{b:%Y%m%d}</ePe></tier>"
                       for n, (a, b) in enumerate(tiers, 1))  # fmt: skip
    return (
        f"<?xml version='1.0'?><spanFile><fileFormat>4.00</fileFormat><created>{created}</created><pointInTime>"
        "<phyPf><pfCode>BANKNIFTY</pfCode><phy><p>50000</p></phy></phyPf>"
        f"<phyPf><pfCode>{symbol}</pfCode><phy><p>{underlying}</p></phy></phyPf>"
        f"<futPf><pfCode>{symbol}</pfCode>{futs}</futPf>"
        f"<oopPf><pfCode>{symbol}</pfCode><cvf>{cvf}</cvf>{opts}</oopPf>"
        f"<ccDef><cc>{symbol}</cc><adjRate><r>1</r><val>{adj}</val></adjRate><scanTiers>{tier_xml}</scanTiers>"
        f"<somTiers><tier><tn>0</tn><rate><r>1</r><val>{som}</val></rate></tier></somTiers>"
        "<dSpread><rate><r>1</r><val>404</val></rate></dSpread></ccDef>"
        "</pointInTime></spanFile>"
    )


def span_zip(xml: str | None = None, member: str = "nsccl.20261014.i1.spn", **kwargs) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr(member, xml if xml is not None else span_xml(**kwargs))
    return out.getvalue()
