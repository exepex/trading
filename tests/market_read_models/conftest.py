import pytest

from .postgres_server import PostgresServer

SERVER_FIXTURES = {"postgres", "tls_server"}


@pytest.hookimpl(tryfirst=True)  # before xdist's own hook reads the group marks
def pytest_collection_modifyitems(items):
    """Every test using a throwaway PostgreSQL runs on one worker when the suite runs in parallel: one server for all,
    and each server's free port is picked while the earlier one holds its own (no two workers racing for a port)."""
    for item in items:
        if SERVER_FIXTURES & set(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.xdist_group("postgres"))


@pytest.fixture(scope="session")
def postgres():
    """A throwaway PostgreSQL with the fno read-model tables (db/fno/migrations)."""
    server = PostgresServer().start()
    try:
        server.migrate()
        yield server
    finally:
        server.stop()
