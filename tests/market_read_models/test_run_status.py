"""Story P7: every publish run leaves one run-status row (running, then published, failed with a reason code, or
skipped), a failing status write never hides the run's result, and on a throwaway PostgreSQL the table, its checks and
its grants (the publisher inserts and updates, never deletes; the dashboard only reads) hold."""

from datetime import UTC, date, datetime

import psycopg
import pytest

from fno.market_read_models.db_errors import TLS
from fno.market_read_models.local_publisher import LocalFolderPublisher
from fno.market_read_models.publisher import PublishFailed
from fno.market_read_models.run_status import NOT_RECORDED, Outcome, PostgresRunStatus, RunStatusRecorder
from fno.market_read_models.wiring import run_id

from .test_market_contract_and_run import CONTRACT, DAY, Planted, Rows, builder, example_rows, run


def rows_of(tmp_path):
    from fno.market_read_models.run_status import LocalRunStatus

    return LocalRunStatus(tmp_path, "fno").rows()


def test_a_published_run_leaves_one_row_with_its_publication(tmp_path):
    market, _, _ = run(tmp_path, Rows(example_rows()))
    assert market.run(DAY)[0] == 0
    [row] = rows_of(tmp_path)
    assert (row["run_id"], row["session"], row["result"], row["reason_code"]) == (
        "run-1",
        "2026-10-12",
        "published",
        None,
    )
    assert row["publication_id"].startswith("nse-2026-10-12-")


def test_a_closed_day_is_skipped_and_a_second_run_adds_its_own_row(tmp_path):
    market, _, _ = run(tmp_path, Rows(example_rows()))
    market.run(date(2026, 10, 11))
    market.run(DAY)
    market.run(DAY)
    assert [(r["run_id"], r["result"], r["reason_code"]) for r in rows_of(tmp_path)] == [
        ("run-1", "skipped", "not_a_session"), ("run-2", "published", None), ("run-3", "published", None),
    ]  # fmt: skip


class Refuses(LocalFolderPublisher):
    def __init__(self, folder, failure_class=None):
        super().__init__(folder)
        self.failure_class = failure_class

    def publish(self, publication):
        raise PublishFailed(f"{publication.publication_id}: refused (test)", self.failure_class)


class LosesAPage(LocalFolderPublisher):
    def stored(self, publication_id):
        return {k: v for k, v in super().stored(publication_id).items() if k != "overview_sectors"}


def failing_runs(tmp_path):
    """(how the run fails, the reason code it must leave)."""
    broken = [Planted(b, lambda p: p.update(extra=1)) for b in builder().builders]
    return [
        (dict(prepare=lambda day: "cm-bhavcopy: 1 not published yet"), "archive_incomplete"),
        (dict(rows=Rows(missing=["nse/equities/cm-bhavcopy/2026/10/x.csv.zip"])), "archive_incomplete"),
        (dict(publications=type(builder())(broken, CONTRACT, "c" * 40)), "schema_invalid"),
        (dict(publisher=Refuses(tmp_path)), "publish_refused"),
        (dict(publisher=Refuses(tmp_path, TLS)), "database_tls"),
        (dict(publisher=LosesAPage(tmp_path)), "read_back_mismatch"),
    ]


def test_each_failure_leaves_its_reason_code_and_the_alerted_line(tmp_path):
    for i, (change, code) in enumerate(failing_runs(tmp_path)):
        folder = tmp_path / str(i)
        market, alerts, _ = run(folder, change.get("rows", Rows(example_rows())), change.get("publications"))
        if "publisher" in change:
            market.publisher = change["publisher"]
        assert market.run(DAY, prepare=change.get("prepare"))[0] == 1
        [row] = rows_of(folder)
        assert (row["result"], row["reason_code"]) == ("failed", code) and row["reason"] == alerts.sent[0]


def test_a_changed_contract_copy_is_its_own_code(tmp_path, monkeypatch):
    market, _, _ = run(tmp_path, Rows(example_rows()))
    monkeypatch.setattr(market.contract, "changed_files", lambda: ["api/openapi.yaml"])
    market.run(DAY)
    assert rows_of(tmp_path)[0]["reason_code"] == "contract_changed"


class Crashes:
    def build(self, day):
        raise KeyError("unexpected (test)")


def test_a_crash_is_recorded_then_raised(tmp_path):
    market, _, _ = run(tmp_path, Crashes())
    with pytest.raises(KeyError):
        market.run(DAY)
    assert [(r["result"], r["reason_code"]) for r in rows_of(tmp_path)] == [("failed", "crashed")]


class Unreachable(RunStatusRecorder):
    def start(self, run_id, session):
        return NOT_RECORDED.format(cause="network: TCP timeout or refused (firewall?) (OperationalError)")

    def finish(self, run_id, outcome):
        return self.start(run_id, None)


def test_a_status_that_cannot_be_written_never_hides_the_runs_result(tmp_path):
    market, _, _ = run(tmp_path, Rows(example_rows()))
    market.status = Unreachable()
    code, lines = market.run(DAY)
    assert (
        code == 0 and lines[0].startswith("2026-10-12: published") and lines[-1].startswith("run status NOT recorded")
    )


def test_the_run_id_is_githubs_run_and_attempt_else_the_local_time():
    assert run_id({"GITHUB_RUN_ID": "38438666957", "GITHUB_RUN_ATTEMPT": "2"}) == "gh-38438666957-2"
    assert run_id({}, clock=lambda: datetime(2026, 10, 13, 2, 0, tzinfo=UTC)) == "local-20261013T020000000000Z"


def as_role(postgres, role):
    return postgres.url.replace("postgres@", f"{role}@", 1)


def table(postgres):
    with psycopg.connect(postgres.url) as connection:
        return connection.execute(
            "select run_id, result, reason_code, publication_id, finished_at is not null from fno.run_status "
            "order by started_at, run_id"
        ).fetchall()


def test_postgres_rows_written_by_the_publisher_role_and_read_by_the_dashboard(postgres):
    with psycopg.connect(postgres.url, autocommit=True) as connection:
        connection.execute("delete from fno.run_status")
    status = PostgresRunStatus(as_role(postgres, "fno_writer"), psycopg.connect, "fno")
    assert status.start("gh-1-1", DAY) is None and status.start("gh-2-1", DAY) is None
    assert status.finish("gh-1-1", Outcome("published", publication_id="nse-2026-10-12-abc")) is None
    assert status.finish("gh-2-1", Outcome("failed", "database_tls", "NOT published (publish): TLS")) is None
    assert status.finish("gh-1-1", Outcome("failed", "crashed", "late")) is None  # a finished row never changes
    assert table(postgres) == [("gh-1-1", "published", None, "nse-2026-10-12-abc", True),
                               ("gh-2-1", "failed", "database_tls", None, True)]  # fmt: skip
    with (
        psycopg.connect(as_role(postgres, "fno_writer")) as writer,
        pytest.raises(psycopg.errors.InsufficientPrivilege),
    ):
        writer.execute("delete from fno.run_status")
    with psycopg.connect(as_role(postgres, "dashboard_app")) as reader:
        assert len(reader.execute("select * from fno.run_status").fetchall()) == 2
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            reader.execute("insert into fno.run_status values ('fno', 'x', '2026-10-12', now(), null, 'running')")


def test_postgres_refuses_an_unknown_code_or_a_failure_without_one(postgres):
    status = PostgresRunStatus(postgres.url, psycopg.connect, "fno")
    status.start("gh-3-1", DAY)
    assert status.finish("gh-3-1", Outcome("failed", "made_up", "x")).startswith("run status NOT recorded (other")
    assert status.finish("gh-3-1", Outcome("failed")).startswith("run status NOT recorded")


def test_a_finished_row_cannot_be_rewritten_even_by_a_plain_update_as_the_publisher_role(postgres):
    status = PostgresRunStatus(as_role(postgres, "fno_writer"), psycopg.connect, "fno")
    status.start("gh-9-1", DAY)
    status.finish("gh-9-1", Outcome("published", publication_id="nse-2026-10-12-abc"))
    with psycopg.connect(as_role(postgres, "fno_writer")) as writer, pytest.raises(psycopg.errors.RestrictViolation):
        writer.execute(  # judge 59's plant: a plain UPDATE, not the adapter's guarded one
            "update fno.run_status set result = 'failed', reason_code = 'crashed', reason = 'rewritten' "
            "where run_id = 'gh-9-1' and result = 'published'"
        )
    assert ("gh-9-1", "published", None, "nse-2026-10-12-abc", True) in table(postgres)
