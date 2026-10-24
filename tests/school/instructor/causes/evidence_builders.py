"""Evidence for the rule tests (story MS-INS, part c): a neutral loser on which no cause fires, and an attribution whose
components are chosen, the residual balancing them."""

from dataclasses import replace

from fno.school.constants import ExitReason
from fno.school.instructor.causes.evidence import Controls, Evidence
from fno.school.instructor.causes.terms import Stance
from tests.school.instructor.builders import attribution

FLAT = Stance(short_volatility=False, long_volatility=False, directional=False, long_premium=False)


def parts(net: float = -1000.0, delta=0.0, gamma=0.0, vega=0.0, theta=0.0, charges=60.0, spread=20.0):
    residual = net + charges + spread - (delta + gamma + vega + theta)
    return attribution(
        delta=delta, gamma=gamma, vega=vega, theta=theta, residual=residual, charges=charges, spread=spread, net=net
    )


def evidence(**changes) -> Evidence:
    net = changes.get("net", -1000.0)
    values = dict(
        net=net,
        gross=net - 1.0,
        exit_reason=ExitReason.SESSIONS_HELD,
        attribution=parts(net),
        data_fault=False,
        z=0.5,
        market=(0.1, 0.2, 0.3, 0.4),
        event_in_window=False,
        stance=FLAT,
        inside_breakevens=None,
        stop_rs=None,
        hold_net=None,
        replay_matches=True,
        noise=(5000.0, 10.0),
        controls=None,
    )
    return Evidence(**{**values, **changes})


def with_parts(ev: Evidence, **components) -> Evidence:
    return replace(ev, attribution=parts(ev.net, **components))


CONTROLS_BOTH_LOST, CONTROLS_BOTH_WON = Controls(-10.0, -20.0), Controls(10.0, 0.0)
