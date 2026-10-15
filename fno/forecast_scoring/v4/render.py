"""The v4 report's text and JSON (story G8). Every comparison prints its counts, D, the relative improvement against
the minimum effect, the reported p-values (never a verdict), its scored window's regime and its missed days; before
the freeze the first line says EXPLORATORY."""

from __future__ import annotations

from dataclasses import asdict

from ...forecast_v4.terms import POWER_REPORT_AT
from .comparison import Comparison, margin
from .records import EXPLORATORY
from .scoring import STATUS_SCORED, QuestionReport

SECONDARY = "Forecasts are secondary to net profit; no p-value here is a verdict (verdicts come only from a look)."


def report_lines(reports: list[QuestionReport], frozen: bool, as_of: str) -> list[str]:
    lines = ([] if frozen else [EXPLORATORY]) + [f"Omenix F&O protocol v4 scores as of {as_of}", SECONDARY]
    for report in reports:
        lines.append(f"{report.question}: {report.status}")
        if report.status != STATUS_SCORED:
            continue
        lines.append(f"  live forecasts: {report.live_forecasts}")
        lines += [f"  {name}: {_scores_text(scores)}" for name, scores in report.scores.items()]
        for comparison in report.comparisons:
            lines += comparison_lines(comparison)
    return lines


def comparison_lines(c: Comparison) -> list[str]:
    p = c.pairing
    counts = (f"scored {len(p.scored.differences)}, gate {len(p.gate.differences)}, unresolved {p.unresolved}, "
              f"void {p.void}, forecaster missing {p.missing_forecast}, baseline missing {p.missing_baseline}, "
              f"zero RV out of the gate {p.zero_rv_left_out_of_gate}")  # fmt: skip
    effect = "n/a" if c.relative_improvement is None else f"{c.relative_improvement:.4f}"
    hac = "n/a" if c.hac_p is None else f"{c.hac_p:.4f}"
    lines = [
        f"  {c.forecaster} vs {c.baseline}: {counts}",
        f"    D {_num(c.mean_difference)}; relative improvement {effect} (minimum {margin(c.question):g}); "
        f"p batch-means {c.batch_means_p:.4f}, studentized {c.studentized_p:.4f}, centred bootstrap "
        f"{c.centred_bootstrap_p:.4f}, HAC {hac} (reported only); halves {c.half_signs}",
        f"    {c.regime.line() if c.regime else 'no scored window'}",
        f"    {c.misses.line()}",
    ]
    if c.power is None:
        return lines + [f"    power report after {POWER_REPORT_AT} gate-set outcomes"]
    w = c.power
    return lines + [
        f"    power (planning only): r {w.r:.2f}, {w.n_required} independent outcomes needed, "
        f"{w.years_remaining:.1f} years remaining{'' if w.useful else ': cannot settle in useful time'}"
    ]


def report_json(reports: list[QuestionReport], frozen: bool, as_of: str) -> dict:
    return {"as_of": as_of, "exploratory": not frozen, "questions": [_question_json(r) for r in reports]}


def _question_json(report: QuestionReport) -> dict:
    return {
        "question": report.question, "status": report.status, "live_forecasts": report.live_forecasts,
        "scores": {name: asdict(s) if s else None for name, s in report.scores.items()},
        "comparisons": [_comparison_json(c) for c in report.comparisons],
    }  # fmt: skip


def _comparison_json(c: Comparison) -> dict:
    p = c.pairing
    return {
        "forecaster": c.forecaster, "baseline": c.baseline, "scored": len(p.scored.differences),
        "gate": len(p.gate.differences), "unresolved": p.unresolved, "void": p.void,
        "missing_forecast": p.missing_forecast, "missing_baseline": p.missing_baseline,
        "zero_rv_left_out_of_gate": p.zero_rv_left_out_of_gate, "mean_difference": c.mean_difference,
        "relative_improvement": c.relative_improvement, "batch_means_p": c.batch_means_p,
        "studentized_p": c.studentized_p, "centred_bootstrap_p": c.centred_bootstrap_p, "hac_p": c.hac_p,
        "half_signs": c.half_signs, "regime": c.regime.line() if c.regime else None,
        "power": asdict(c.power) if c.power else None, "misses": asdict(c.misses),
    }  # fmt: skip


def _scores_text(scores) -> str:
    if scores is None:
        return "no scored outcome yet"
    shown = {k: v for k, v in asdict(scores).items() if k != "calibration"}
    return ", ".join(f"{k} {_num(v)}" for k, v in shown.items())


def _num(value) -> str:
    return "n/a" if value is None else f"{value:.6g}" if isinstance(value, float) else str(value)
