"""Judge 59 addendum 1: on a server set up like Azure (X1's roles and step-40 default privileges, migrations run as
fno_owner), the runtime role fno_writer can only do what the publisher needs: history is append-only, the pointer is
upserted, a run row is born running, finished once, and never deleted; dashboard_app only reads."""

import psycopg
import pytest

STATEMENTS_REFUSED_TO_THE_WRITER = [
    "delete from fno.pages_history",
    "truncate fno.pages_history",
    "update fno.pages_history set payload_sha256 = payload_sha256",
    "delete from fno.current_publication",
    "truncate fno.current_publication",
    "delete from fno.run_status",
    "truncate fno.run_status",
]


BORN_PUBLISHED = (
    "insert into fno.run_status (product, run_id, session, started_at, finished_at, result, publication_id) "
    "values ('fno', 'gh-born-1', '2026-10-12', now(), now(), 'published', 'nse-2026-10-12-x')"
)


def execute(postgres, role: str, statement: str, values: tuple = ()):
    with psycopg.connect(postgres.as_role(role)) as connection:
        return connection.execute(statement, values)


@pytest.mark.parametrize("statement", STATEMENTS_REFUSED_TO_THE_WRITER)
def test_the_writer_never_deletes_truncates_or_rewrites_history(postgres, statement):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        execute(postgres, "fno_writer", statement)


def test_a_run_row_is_born_running(postgres):
    with pytest.raises(psycopg.errors.RestrictViolation, match="must be recorded as running first"):
        execute(postgres, "fno_writer", BORN_PUBLISHED)


def test_a_running_row_keeps_its_identity_and_is_finished_once(postgres):
    execute(postgres, "fno_writer", "insert into fno.run_status (product, run_id, session, started_at, result) "
            "values ('fno', 'gh-id-1', '2026-10-12', now(), 'running')")  # fmt: skip
    with pytest.raises(psycopg.errors.RestrictViolation, match="keeps its product, ID, session and start"):
        execute(postgres, "fno_writer", "update fno.run_status set session = '2026-10-09' where run_id = 'gh-id-1'")
    execute(postgres, "fno_writer", "update fno.run_status set result = 'skipped', reason_code = 'not_a_session', "
            "finished_at = now() where run_id = 'gh-id-1'")  # fmt: skip
    with pytest.raises(psycopg.errors.RestrictViolation, match="a finished run never changes"):
        execute(postgres, "fno_writer", "update fno.run_status set reason = 'later' where run_id = 'gh-id-1'")


@pytest.mark.parametrize("table", ["pages_history", "current_publication", "run_status"])
def test_the_dashboard_only_reads(postgres, table):
    execute(postgres, "dashboard_app", f"select count(*) from fno.{table}")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        execute(postgres, "dashboard_app", f"delete from fno.{table}")


def test_the_writer_keeps_exactly_the_rights_the_publisher_needs(postgres):
    rights = execute(postgres, "fno_owner",
                     "select table_name, string_agg(privilege_type, ',' order by privilege_type) "
                     "from information_schema.role_table_grants where grantee = 'fno_writer' and table_schema = 'fno' "
                     "group by table_name order by table_name").fetchall()  # fmt: skip
    assert rights == [("current_publication", "INSERT,SELECT,UPDATE"), ("pages_history", "INSERT,SELECT"),
                      ("run_status", "INSERT,SELECT,UPDATE")]  # fmt: skip
