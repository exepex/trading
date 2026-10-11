import json
from datetime import UTC, date, datetime
from pathlib import Path

from fno.live.duckdb_results_store import DuckDbResultsStore
from fno.live.research.repo_source import RepoResearchSource
from fno.live.research.research_context import ResearchContextLoader
from fno.live.results_store import JsonlResultsStore

from .fakes import at


def write(root: Path, dataset: str, day: str, rows: list[dict]) -> None:
    path = root / dataset / day[:4] / day[5:7] / f"{day}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def market_dir(tmp_path: Path) -> Path:
    """A miniature copy of the stock tool's data/india folder, in its real file layout."""
    root = tmp_path / "data" / "india"
    write(
        root,
        "news",
        "2026-10-12",
        [
            {
                "id": "n1",
                "title": "TCS wins large deal",
                "published_at": "2026-10-12T02:00:00+00:00",
                "tickers": ["TCS"],
            },
            {
                "id": "n2",
                "title": "Border tension rises",
                "published_at": "2026-10-12T02:30:00+00:00",
                "tickers": ["NIFTY"],
            },
            {"id": "old", "title": "Old story", "published_at": "2026-10-01T02:00:00+00:00", "tickers": ["TCS"]},
        ],
    )
    write(
        root,
        "news_enriched",
        "2026-10-12",
        [
            {"id": "n1", "analyzed_at": "2026-10-12T02:10:00+00:00", "sentiment": 0.1, "materiality": "low"},
            {
                "id": "n1",
                "analyzed_at": "2026-10-12T02:20:00+00:00",
                "sentiment": 0.6,
                "materiality": "high",
            },  # newer wins
            {
                "id": "n2",
                "analyzed_at": "2026-10-12T02:40:00+00:00",
                "sentiment": -0.5,
                "materiality": "high",
                "geopolitical": True,
            },
        ],
    )
    write(
        root,
        "news_verified",
        "2026-10-12",
        [
            {"as_of": "2026-10-12T03:00:00+00:00", "status_ids": ["n1"], "id_statuses": ["corroborated"]},
        ],
    )
    write(
        root,
        "events",
        "2026-10-08",
        [
            {"type": "earnings", "ticker": "TCS", "date": "2026-10-20"},
            {"type": "earnings", "ticker": "TCS", "date": "2026-10-14"},
            {"type": "ex_dividend", "ticker": "TCS", "date": "2026-10-13"},
        ],
    )
    write(
        root,
        "regime",
        "2026-10-09",
        [
            {"regime": "CALM", "stress": False, "major_event_names": [], "computed_at": "2026-10-09T02:00:00+00:00"},
        ],
    )
    write(
        root,
        "model_scores",
        "2026-10-09",
        [
            {"ticker": "TCS", "horizon_days": 1, "prob_up": 0.61, "as_of_date": "2026-10-09"},
            {"ticker": "TCS", "horizon_days": 1, "prob_up": 0.40, "as_of_date": "2026-10-08"},
        ],
    )
    return root


def test_repo_source_reads_the_stock_tools_files(tmp_path):
    snapshot = ResearchContextLoader(RepoResearchSource(market_dir(tmp_path))).load(at(9, 0), at(9, 0).replace(day=9))
    assert snapshot.regime == "CALM" and not snapshot.stress
    assert snapshot.next_earnings == {"TCS": date(2026, 10, 14)}
    assert snapshot.model_prob_up == {"TCS": 0.61}
    tcs = snapshot.news["TCS"]
    assert tcs.items == 1 and tcs.trusted_items == 1 and tcs.mean_sentiment == 0.6
    assert snapshot.geopolitical_headlines == ["Border tension rises"]


def test_missing_research_folder_means_no_research(tmp_path):
    source = RepoResearchSource(tmp_path / "nothing")
    snapshot = ResearchContextLoader(source).load(at(9, 0))
    assert not source.available and snapshot.news == {} and snapshot.regime is None


def test_jsonl_results_store_writes_daily_files(tmp_path):
    store = JsonlResultsStore(tmp_path / "events")
    store.record("opened", {"id": "T001"}, at(11, 0), "NIFTY")
    store.record("closed", {"id": "T001"}, at(11, 30), "NIFTY")
    assert (tmp_path / "events" / "2026" / "10" / "2026-10-12.jsonl").exists()
    assert store.count() == 2 and store.count("opened") == 1


def test_duckdb_results_store_without_token_uses_a_local_file(tmp_path, monkeypatch):
    monkeypatch.delenv("MOTHERDUCK_TOKEN", raising=False)
    store = DuckDbResultsStore(tmp_path / "fno.duckdb")
    store.record("scan", {"n": 1}, datetime(2026, 10, 12, 6, tzinfo=UTC))
    assert store.location.endswith("fno.duckdb") and store.count("scan") == 1
    store.close()


def test_loader_refreshes_before_checking_availability(tmp_path):
    class FirstRunSource(RepoResearchSource):
        def refresh(self):
            market_dir(tmp_path)  # the "clone" happens here

    snapshot = ResearchContextLoader(FirstRunSource(tmp_path / "data" / "india")).load(at(9, 0))
    assert snapshot.regime == "CALM"


def test_repo_source_reads_filings_deals_and_foreign_flows(tmp_path):
    root = market_dir(tmp_path)
    write(
        root,
        "announcements",
        "2026-10-12",
        [
            {
                "ticker": "TCS",
                "category": "Outcome of Board Meeting",
                "subject": "Results",
                "published_at": "2026-10-12T03:00:00+00:00",
            },
            {"ticker": "TCS", "category": "Old", "subject": "", "published_at": "2026-10-01T03:00:00+00:00"},
        ],
    )
    write(
        root,
        "deals",
        "2026-10-12",
        [
            {"id": "d1", "date": "2026-10-09", "ticker": "TCS", "side": "buy", "value": 3e9},
            {"id": "d1", "date": "2026-10-09", "ticker": "TCS", "side": "buy", "value": 3e9},  # duplicate line
            {"id": "d2", "date": "2026-10-09", "ticker": "TCS", "side": "sell", "value": 1e9},
        ],
    )
    write(
        root,
        "fpi",
        "2026-10-12",
        [
            {"reporting_date": "2026-10-08", "asset_class": "Equity", "route": "Stock Exchange", "net_cr": -6206.3},
            {"reporting_date": "2026-10-08", "asset_class": "Debt", "route": "Stock Exchange", "net_cr": 900.0},
            {"reporting_date": "2026-10-09", "asset_class": "Equity", "route": "Stock Exchange", "net_cr": 1500.0},
        ],
    )
    snapshot = ResearchContextLoader(RepoResearchSource(root)).load(at(9, 0), at(9, 0).replace(day=9))
    assert [a.category for a in snapshot.announcements["TCS"]] == ["Outcome of Board Meeting"]
    assert snapshot.block_deal_net == {"TCS": 2e9}
    assert snapshot.foreign_flows_cr == [-6206.3, 1500.0]
