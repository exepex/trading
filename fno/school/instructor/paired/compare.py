"""One driver version against its matched controls (story MS-INS, part d): for each control (N0, RC1 and REF of the
road), both measures, on the common road-days h's counting rule gives that pair, batched at the pair's frozen hold."""

from collections.abc import Collection, Mapping

from ...contracts.decisions import DriverCard
from ..contracts import Measure, PairedRow
from .holds import pair_batch
from .series import RoadDay, paired_series
from .status import paired_row
from .values import RoadSlot

Slots = Mapping[str, Mapping[RoadDay, RoadSlot]]  # each driver's road-slots, by driver ID
Common = Mapping[tuple[str, str], Collection[RoadDay]]  # the counted road-days of each (driver, control)


def compare(driver: DriverCard, controls: Collection[DriverCard], slots: Slots, common: Common,
            rules_sha256: str) -> tuple[PairedRow, ...]:  # fmt: skip
    rows = []
    for control in controls:
        pair = (driver.driver_id, control.driver_id)
        batch = pair_batch(driver, control)
        for measure in Measure:
            series = paired_series(slots[pair[0]], slots.get(pair[1], {}), common.get(pair, ()), measure)
            rows.append(paired_row(*pair, measure, series, batch, rules_sha256))
    return tuple(rows)
