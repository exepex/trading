import pytest

from .postgres_server import PostgresServer


@pytest.fixture(scope="session")
def postgres():
    """A throwaway PostgreSQL with the fno read-model tables (db/fno/migrations)."""
    server = PostgresServer().start()
    try:
        server.migrate()
        yield server
    finally:
        server.stop()
