"""The AI books' forecasts for story G4 (stories F1 and G5): `research/forecasts/ai_v1/<YYYY>/<d>_<book>_forecasts.csv`
in the v2 record schema, each with its audit file `<d>_<book>_audit.json`.

**Contract with F1 (what makes an AI book's day scored):**
- the audit's `status` is `on_time` (F1's `ON_TIME`): every other status (`late`, `not_revealed`, `invalid`,
  `not_fired`, `no_submission`, `exposed`, `model_mismatch`, and any status F1 adds later, such as a transcript
  `breach`) leaves the whole day unscored;
- the audit has no `"unscored": true` (an auditor's later finding, e.g. a transcript breach, with `unscored_reason`);
- every record's `pack_sha256` is the day's v2 pack, and that pack matched its capture receipt (Book 1's live check).
Unscored days are listed with their reason in the report and never scored. The audit's `isolation` label (today
`sealed_same_day`: the other book's answer was sealed, full F1 isolation is not in force) is reported per book.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from ..forecast.record_files import read_records_v2
from .score_inputs import ScoredForecast, from_live

SCORED_STATUS = "on_time"
RECORDS_SUFFIX, AUDIT_SUFFIX = "_forecasts.csv", "_audit.json"


@dataclass
class AiForecasts:
    forecasts: list[ScoredForecast] = field(default_factory=list)
    unscored: list[dict] = field(default_factory=list)  # {day, book, reason}
    isolation: dict[str, set[str]] = field(default_factory=dict)  # book -> isolation labels seen


def ai_forecasts(folder: Path, verified_packs: dict[date, str]) -> AiForecasts:
    """`verified_packs`: day -> SHA-256 of the day's receipt-verified v2 pack."""
    out = AiForecasts()
    for records_path in sorted(Path(folder).glob(f"*/*{RECORDS_SUFFIX}")):
        stem = records_path.name.removesuffix(RECORDS_SUFFIX)
        day, book = date.fromisoformat(stem[:10]), stem[11:]
        audit_path = records_path.with_name(f"{stem}{AUDIT_SUFFIX}")
        audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.is_file() else None
        records = read_records_v2(records_path.read_text(encoding="utf-8"))
        reason = _unscored_reason(audit, records, verified_packs.get(day))
        if audit is not None:
            out.isolation.setdefault(book, set()).add(str(audit.get("isolation")))
        if reason:
            out.unscored.append({"day": day.isoformat(), "book": book, "reason": reason})
            continue
        out.forecasts += [f for f in (from_live(r) for r in records) if f is not None]
    return out


def _unscored_reason(audit: dict | None, records: list, pack_sha: str | None) -> str | None:
    if audit is None:
        return "no audit file"
    if audit.get("status") != SCORED_STATUS:
        return f"status {audit.get('status')}"
    if audit.get("unscored"):
        return f"unscored: {audit.get('unscored_reason') or 'no reason given'}"
    if pack_sha is None:
        return "the day's v2 pack is missing or does not match its capture receipt"
    if any(r.record.pack_sha256 != pack_sha for r in records):
        return "records name another pack than the day's v2 pack"
    return None
