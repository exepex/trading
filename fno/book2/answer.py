"""Book 2's decision shape (story F5 part 2), what its routine seals and its decider reads. Standard library only: it
runs in the routine's `seal`. `{"action": "follow_rule" | "trade" | "no_trade", "reason", "slots", "evidence"}`: one
slot per rule-default trade in the sheet's order, each `{"default", "action", "opportunity_id", "width", "lots",
"reason"}`. `action` is `follow_rule` when every slot follows its default (a day with no slots too), else `trade`
when any slot trades, else `no_trade`. The envelope is not checked here: C4 does that."""

from __future__ import annotations

from ..judge.evidence import evidence_problems

ACTIONS = ("follow_rule", "trade", "no_trade")
KEYS = ("action", "evidence", "reason", "slots")
SLOT_KEYS = ("action", "default", "lots", "opportunity_id", "reason", "width")
MAX_REASON_CHARS = 600


def check_decision(decision, sheet=None) -> list[str]:
    """Every problem of the decision's shape (empty: acceptable). With `sheet` (the decider's call), the slots must
    match the sheet's rule default one to one and every named opportunity must be on the sheet."""
    if not isinstance(decision, dict) or sorted(decision) != sorted(KEYS):
        return [f"the decision must have exactly the keys {', '.join(KEYS)}"]
    problems = _reason("reason", decision["reason"]) + evidence_problems(decision["evidence"])
    slots = decision["slots"]
    if not isinstance(slots, list):
        return problems + ["slots must be a list"]
    for n, slot in enumerate(slots):
        problems += _slot(n, slot)
    if problems:
        return problems
    if decision["action"] != _action(slots):
        problems.append(f"action must be {_action(slots)!r} for these slots, not {decision['action']!r}")
    chosen = [s["opportunity_id"] for s in slots if s["action"] == "trade"]
    if len(chosen) != len(set(chosen)):
        problems.append("two slots choose the same opportunity")
    return problems + (_against(slots, sheet) if sheet is not None else [])


def _action(slots: list) -> str:
    if all(s["action"] == "follow_rule" for s in slots):
        return "follow_rule"
    return "trade" if any(s["action"] in ("trade", "follow_rule") for s in slots) else "no_trade"


def _slot(n: int, slot) -> list[str]:
    if not isinstance(slot, dict) or sorted(slot) != sorted(SLOT_KEYS):
        return [f"slots[{n}] must have exactly the keys {', '.join(SLOT_KEYS)}"]
    problems = _reason(f"slots[{n}].reason", slot["reason"])
    if slot["action"] not in ACTIONS:
        problems.append(f"slots[{n}].action must be one of {', '.join(ACTIONS)}")
    if not isinstance(slot["default"], str) or not slot["default"]:
        problems.append(f"slots[{n}].default must be the rule default's opportunity ID")
    trades = slot["action"] == "trade"
    if trades and not (isinstance(slot["opportunity_id"], str) and slot["opportunity_id"]):
        problems.append(f"slots[{n}] trades, so opportunity_id must name an opportunity")
    if not trades and any(slot[k] is not None for k in ("opportunity_id", "width", "lots")):
        problems.append(f"slots[{n}] does not trade, so opportunity_id, width and lots must be null")
    if slot["width"] is not None and (isinstance(slot["width"], bool) or not isinstance(slot["width"], int | float)
                                      or slot["width"] <= 0):  # fmt: skip
        problems.append(f"slots[{n}].width must be a positive number or null")
    if slot["lots"] is not None and (isinstance(slot["lots"], bool) or not isinstance(slot["lots"], int)
                                     or slot["lots"] < 1):  # fmt: skip
        problems.append(f"slots[{n}].lots must be a whole number of at least 1, or null")
    return problems


def _against(slots: list, sheet) -> list[str]:
    defaults = [d["opportunity_id"] for d in sheet.get("rule_default", ())]
    if [s["default"] for s in slots] != defaults:
        return [f"slots must follow the sheet's rule default one to one: {defaults}"]
    on_sheet = {o["opportunity_id"] for o in sheet.get("opportunities", ())}
    unknown = sorted(
        s["opportunity_id"] for s in slots if s["action"] == "trade" and s["opportunity_id"] not in on_sheet
    )
    return [f"opportunities not on the sheet: {', '.join(unknown)}"] if unknown else []


def _reason(where: str, reason) -> list[str]:
    if isinstance(reason, str) and reason.strip() and "\n" not in reason and len(reason) <= MAX_REASON_CHARS:
        return []
    return [f"{where} must be one line of 1 to {MAX_REASON_CHARS} characters"]
