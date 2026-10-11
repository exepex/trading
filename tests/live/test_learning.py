from fno.constants import Direction
from fno.live.learning.signal_report import COMBINED, format_report, rule_accuracy, suggested_weights
from fno.live.learning.view_outcomes import VIEW_OUTCOME_KIND, ViewOutcomeTracker
from fno.live.models import MarketView, ScanReport, SignalVote
from fno.live.results_store import JsonlResultsStore

from .fakes import at


def scan(minute: int, price: float) -> ScanReport:
    view = MarketView(
        "TCS", Direction.BULLISH, 0.6, 0.8, votes=[SignalVote("vwap", 0.8, 1, ""), SignalVote("news", -0.5, 1, "")]
    )
    return ScanReport(started_at=at(10, minute), universe_size=1, views=[view], prices={"TCS": price})


def test_tracker_grades_views_after_each_horizon(tmp_path):
    store = JsonlResultsStore(tmp_path)
    tracker = ViewOutcomeTracker(store, (30, 90))
    tracker.observe(scan(0, 100.0))
    assert tracker.observe(scan(20, 100.5)) == 0  # too early
    assert tracker.observe(scan(31, 101.0)) == 1  # first view's 30-minute grade
    outcomes = store.payloads(VIEW_OUTCOME_KIND, at(10, 0).date())
    assert outcomes[0]["horizon_minutes"] == 30 and outcomes[0]["forward_return_pct"] == 1.0
    assert outcomes[0]["votes"] == {"vwap": 0.8, "news": -0.5}


def test_rule_accuracy_separates_good_and_bad_rules():
    outcomes = []
    for i in range(60):
        move = 1.0 if i % 2 else -1.0
        outcomes.append(
            {
                "horizon_minutes": 30,
                "forward_return_pct": move,
                "score": move * 0.5,
                "votes": {"good": move * 0.8, "backwards": -move * 0.8, "noise": 0.5},
            }
        )
    results = {r.rule: r for r in rule_accuracy(outcomes, 30)}
    assert results["good"].hit_rate == 1.0 and results["good"].information_coefficient > 0.99
    assert results["backwards"].hit_rate == 0.0
    assert results[COMBINED].votes == 60
    weights = suggested_weights(list(results.values()), min_votes=50)
    assert weights["good"] > 0 and weights["backwards"] == 0
    text = format_report(list(results.values()), 30)
    assert "predictive" in text and "works backwards" in text
