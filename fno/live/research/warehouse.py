"""Read-only access to the market-brief research database in MotherDuck."""

from __future__ import annotations

import logging
import os

from ...constants import ENV_RESEARCH_MOTHERDUCK_TOKEN

log = logging.getLogger(__name__)

RESEARCH_DATABASE = "market_brief"
MOTHERDUCK_URI = "md:{database}?motherduck_token={token}"


class ResearchWarehouse:
    """Runs small read queries. Without a token, or on any error, it returns no rows so scanning continues."""

    def __init__(self, database: str = RESEARCH_DATABASE, token_env: str = ENV_RESEARCH_MOTHERDUCK_TOKEN):
        self.database = database
        self.token = os.environ.get(token_env)
        self._connection = None

    @property
    def available(self) -> bool:
        return bool(self.token)

    def _connect(self):
        if self._connection is None:
            import duckdb

            self._connection = duckdb.connect(MOTHERDUCK_URI.format(database=self.database, token=self.token))
        return self._connection

    def rows(self, sql: str, params: list | None = None) -> list[dict]:
        if not self.available:
            return []
        try:
            cursor = self._connect().execute(sql, params or [])
            names = [d[0] for d in cursor.description]
            return [dict(zip(names, row)) for row in cursor.fetchall()]
        except Exception as exc:  # research is optional input: never stop the scanner for it
            log.warning("research query failed: %s", exc)
            self._connection = None
            return []

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
