"""Story D3b fixtures: a decided day's chosen trades opened by fills, and that day's run log naming the run E3
collected, so `opening_trades` finds each trade's opening run as the desk would have left it."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time

from fno.books.account import PaperAccount
from fno.constants import FILL_OPEN
from fno.desk.records import FILL_COLUMNS, DeskRecords
from fno.desk.run_log import RunLog
from fno.models import IST
from fno.playbook.decision_store import SUMS_FILE, DecisionStore


def chosen_trade_ids(run) -> list[str]:
    records = (json.loads(p.read_text()) for p in sorted(run.glob("*.json")) if p.name != "inputs.json")
    return [r["structure"]["trade_id"] for r in records if r.get("chosen_action") == "trade" and r.get("structure")]


def open_trades(root, book: str, day: date, run_id: str, commit: str, trade_ids=None) -> list[str]:
    """Each trade gets an open fill on `day`, and the day's run log names `run_id` (in `commit`) as collected."""
    run = DecisionStore(root, book).day_folder(day) / run_id
    trade_ids = chosen_trade_ids(run) if trade_ids is None else trade_ids
    log = RunLog.open(root, day)
    moment = datetime.combine(day, time(15, 1), IST)
    sums = run / SUMS_FILE
    entry = {"run_id": run_id, "commit": commit, "committed_at": moment.isoformat()}
    entry |= {"sums_sha256": hashlib.sha256(sums.read_bytes()).hexdigest()} if sums.is_file() else {}
    log.record("decisions", moment, moment, {}, {book: entry})
    fills = DeskRecords(PaperAccount(root, book)).fills
    fills.path.parent.mkdir(parents=True, exist_ok=True)
    for trade_id in trade_ids:
        opened = {"fill_id": f"{trade_id}-open", "trade_id": trade_id, "action": FILL_OPEN}
        fills.append(dict.fromkeys(FILL_COLUMNS, "") | opened | {"filled_at": f"{day}T15:15:30+05:30"})
    return trade_ids
