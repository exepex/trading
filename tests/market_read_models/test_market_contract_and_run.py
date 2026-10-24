"""Story P6 criteria 2 and 3: every block is validated against the pinned W11 contract (a planted extra or missing field
fails the run, nothing is published), the pinned copy is intact and checked against the dashboard's, and a run never
publishes a partial session: every failure alerts #fno-desk and leaves the previous publication current."""

import copy
from dataclasses import replace
from datetime import date

import pytest

from fno.alerts.sender import AlertSender
from fno.market_read_models.blocks import BlockBuilder, SessionRows
from fno.market_read_models.contract import ContractBroken, PinnedContract, PublishedContract, drift
from fno.market_read_models.flows_block import FlowsInputs
from fno.market_read_models.forecast_lab_inputs import ForecastLabInputs
from fno.market_read_models.frame_inputs import frame_inputs
from fno.market_read_models.home_inputs import BookFigures, HomeInputs
from fno.market_read_models.local_publisher import LocalFolderPublisher
from fno.market_read_models.market_run import MarketRun
from fno.market_read_models.page_holds import PAGE_HOLDS, PageHoldsBlock
from fno.market_read_models.publication import PublicationBuilder
from fno.market_read_models.publication_inputs import PublicationInputsFile
from fno.market_read_models.run_status import LocalRunStatus
from fno.market_read_models.session_rows import IncompleteSession
from fno.market_read_models.weather_inputs import WeatherInputs
from fno.market_read_models.wiring import CONTRACT_FOLDER, build_market_blocks
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.wiring import build_session_calendar

from .chain_fixture import chain_of_12_october

DAY = date(2026, 10, 12)
CONTRACT = PinnedContract(CONTRACT_FOLDER)
EXAMPLES = CONTRACT.examples()
OPENING_BOOKS = HomeInputs(
    [BookFigures(n, f, f"F&O Book {n}", 500000.0, 0.0, 0) for n, f in ((1, "rule"), (2, "hybrid"), (3, "ai"))],
    [],
    "No F&O strategy has passed testing yet (test).",
    30000.0,
)
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n2026-10-02,holiday,Gandhi Jayanti,https://nsearchives.nseindia.com/x.pdf\n"
)


def example_rows() -> SessionRows:
    """The session's rows as the W11 examples show them (their first pages)."""
    payload = {name: copy.deepcopy(example["value"]["payload"]) for name, example in EXAMPLES.items()}
    stocks = payload["getScreenerStocksIndia_india"]["rows"]
    indices = payload["getOverviewIndicesIndia_india"]["indices"] + payload["getIndiaSectors_india"]["indices"]
    for row in indices:
        row["group"] = row["kind"]
    sectors = payload["getIndiaSectors_india"]["industries"]
    fno = payload["getFnoScreenerRows_india"]["rows"]
    calendar = build_session_calendar()
    flows = FlowsInputs([], [], calendar.sessions(date(2025, 6, 1), DAY)[-250:])  # no flows copy covers 12 Oct
    weather = WeatherInputs(DAY, None, [], {}, {})  # no weather record: the page's not-published state
    lab = ForecastLabInputs(DAY, None, [])  # no G4 report and no forecast record yet: the Forecast lab's empty state
    return SessionRows(
        DAY, stocks, fno, indices, sectors, chain_of_12_october(), OPENING_BOOKS, frame_inputs(calendar, DAY), flows,
        weather, [], lab,
    )  # fmt: skip


def builder() -> PublicationBuilder:
    return PublicationBuilder(
        build_market_blocks(), CONTRACT, "c" * 40, clock=lambda: "2026-10-12T12:30:00Z", holds_page=PageHoldsBlock()
    )


def test_the_pinned_copy_matches_its_pin_and_names_the_contract_version():
    assert CONTRACT.changed_files() == [] and CONTRACT.version == "2.14.0"
    assert "api/schemas/blocks-stored.yaml" in CONTRACT.pin["files"]
    assert CONTRACT.pin["repository"] == "exepex/omenix-dashboard" and len(CONTRACT.pin["commit"]) == 40


def test_every_block_built_from_valid_rows_validates_as_stored_and_as_served():
    publication = builder().build(example_rows())
    pages = {key for b in build_market_blocks() for key in b.pages(example_rows())} | {PAGE_HOLDS}
    assert (
        set(publication.records) == pages
        and {"chain_history", "chain_rows:2026-10-27", "chain_contract:NIFTY26OCT22350CE"} <= pages
    )
    record = publication.records["screener_summary"]
    assert set(record["payload"]["universes"]) == {"all", "n500", "fno", "ours"}  # ours: the followed list (judge 40)
    assert record["publication_id"].startswith("nse-2026-10-12-") and record["product"] == "fno"


def test_the_publication_id_names_the_content_never_the_commit_or_the_build_time():
    first = builder().build(example_rows())
    later = PublicationBuilder(
        build_market_blocks(), CONTRACT, "d" * 40, clock=lambda: "2026-10-13T02:00:00Z", holds_page=PageHoldsBlock()
    )
    assert later.build(example_rows()).publication_id == first.publication_id  # a later commit, same pages
    changed = example_rows()
    changed.stocks[0] = {**changed.stocks[0], "p": changed.stocks[0]["p"] + 1}  # NSE's later version of a file
    assert builder().build(changed).publication_id != first.publication_id


class Planted(BlockBuilder):
    def __init__(self, block, change):
        self.block, self.change = block, change
        self.page_key, self.stored_schema, self.served_schema = block.page_key, block.stored_schema, block.served_schema

    def build(self, rows):
        payload = copy.deepcopy(self.block.build(rows))  # never change the shared session rows
        self.change(payload)
        return payload

    def served(self, payload):
        return self.block.served(payload)


@pytest.mark.parametrize(
    "page_key, change",
    [
        ("fno_screener_summary", lambda p: p.update(extra=1)),  # an extra field
        ("overview_indices", lambda p: p["indices"][0].pop("close")),  # a missing field
        ("screener_stocks", lambda p: p["rows"][40].pop("dl")),  # a missing field beyond the first page
        ("screener_summary", lambda p: p["universes"].pop("ours")),  # India's summary needs the followed universe
    ],
)
def test_a_planted_extra_or_missing_field_fails_and_nothing_is_published(tmp_path, page_key, change):
    blocks = [Planted(b, change) if b.page_key == page_key else b for b in build_market_blocks()]
    with pytest.raises(ContractBroken):
        PublicationBuilder(blocks, CONTRACT, "c" * 40).build(example_rows_with_many_stocks())


def example_rows_with_many_stocks() -> SessionRows:
    rows = example_rows()
    stocks = rows.stocks + [dict(r, s=f"{r['s']}{i}") for i in range(2) for r in rows.stocks]  # 75 rows
    return replace(rows, stocks=stocks)


class Published(PublishedContract):
    def __init__(self, changed=None):
        self.changed = changed

    def read(self, name):
        data = (CONTRACT_FOLDER / name).read_bytes()
        return data + b"\n# changed" if name == self.changed else data


def test_the_pinned_copy_is_compared_with_the_dashboards_published_files():
    assert drift(CONTRACT, Published()) == []
    assert drift(CONTRACT, Published("api/schemas/blocks-stored.yaml")) == ["api/schemas/blocks-stored.yaml"]


class Alerts(AlertSender):
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


class Rows:
    def __init__(self, rows=None, missing=None):
        self.rows, self.missing = rows, missing

    def build(self, day):
        if self.missing:
            raise IncompleteSession(day, self.missing)
        return self.rows


def run(tmp_path, rows, publications=None):
    alerts, publisher, ids = Alerts(), LocalFolderPublisher(tmp_path), iter(range(1, 100))
    status, inputs = LocalRunStatus(tmp_path, "fno"), PublicationInputsFile(tmp_path / "publication-inputs.csv")
    market = MarketRun(CALENDAR, CONTRACT, rows, publications or builder(), publisher, alerts, status,
                       lambda: f"run-{next(ids)}", inputs)  # fmt: skip
    return market, alerts, publisher


def test_a_good_session_is_published_and_a_closed_day_publishes_nothing(tmp_path):
    market, alerts, publisher = run(tmp_path, Rows(example_rows()))
    code, lines = market.run(DAY)
    assert code == 0 and lines[0].startswith("2026-10-12: published 1274 blocks") and alerts.sent == []
    assert market.run(date(2026, 10, 11)) == (0, ["2026-10-11: not a trading day, nothing to publish"])
    assert set(publisher.current()) == {k for b in build_market_blocks() for k in b.pages(example_rows())} | {
        PAGE_HOLDS
    }


def test_a_missing_file_or_a_schema_break_alerts_and_leaves_the_previous_publication(tmp_path):
    good, alerts, publisher = run(tmp_path, Rows(example_rows()))
    good.run(date(2026, 10, 9))
    before = publisher.current()
    missing, alerts, _ = run(tmp_path, Rows(missing=["nse/equities/cm-bhavcopy/2026/10/x.csv.zip"]))
    code, lines = missing.run(DAY)
    assert code == 1 and "NOT published (archived files)" in alerts.sent[0] and lines[1] == "alert sent to #fno-desk"
    broken = [Planted(b, lambda p: p.update(extra=1)) for b in build_market_blocks()]
    schema, alerts, _ = run(tmp_path, Rows(example_rows()), PublicationBuilder(broken, CONTRACT, "c" * 40))
    assert schema.run(DAY)[0] == 1 and "NOT published (W11 schema)" in alerts.sent[0]
    assert publisher.current() == before
