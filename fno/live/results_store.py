"""Stores scan results and trade events in DuckDB: the F&O MotherDuck database, or a local file without a token.

Only compact results go here (a few MB a month), never raw minute-by-minute option chains.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from ..constants import ENV_FNO_MOTHERDUCK_TOKEN

log = logging.getLogger(__name__)

DEFAULT_DATABASE = "fno_desk"
SCHEMA = "live"
EVENTS_TABLE = f"{SCHEMA}.events"
CREATE_SCHEMA_SQL = f"create schema if not exists {SCHEMA}"
CREATE_EVENTS_SQL = f"""
create table if not exists {EVENTS_TABLE} (
    recorded_at timestamptz not null,
    kind varchar not null,        -- scan, idea, rejected, opened, closed, kill_switch
    symbol varchar,
    payload json not null
)
"""
INSERT_EVENT_SQL = f"insert into {EVENTS_TABLE} values (?, ?, ?, ?)"


class ResultsStore:
    """Append-only event log. Errors are logged, never raised: storage must not stop the desk."""

    def __init__(self, local_path: Path, database: str = DEFAULT_DATABASE, token_env: str = ENV_FNO_MOTHERDUCK_TOKEN):
        self.local_path = local_path
        self.database = database
        self.token = os.environ.get(token_env)
        self._connection = None

    @property
    def location(self) -> str:
        return f"md:{self.database}" if self.token else str(self.local_path)

    def _connect(self):
        if self._connection is not None:
            return self._connection
        import duckdb

        if self.token:
            con = duckdb.connect(f"md:?motherduck_token={self.token}")
            con.execute(f"create database if not exists {self.database}")
            con.execute(f"use {self.database}")
        else:
            self.local_path.parent.mkdir(parents=True, exist_ok=True)
            con = duckdb.connect(str(self.local_path))
        con.execute(CREATE_SCHEMA_SQL)
        con.execute(CREATE_EVENTS_SQL)
        self._connection = con
        return con

    def record(self, kind: str, payload: dict, at: datetime, symbol: str | None = None) -> None:
        try:
            self._connect().execute(INSERT_EVENT_SQL, [at, kind, symbol, json.dumps(payload, default=str)])
        except Exception as exc:
            log.error("could not store %s event: %s", kind, exc)
            self._connection = None

    def count(self, kind: str | None = None) -> int:
        sql = f"select count(*) from {EVENTS_TABLE}" + (" where kind = ?" if kind else "")
        return self._connect().execute(sql, [kind] if kind else []).fetchone()[0]

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
