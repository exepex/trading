"""A throwaway PostgreSQL server for the publisher's tests (story P6): initdb in a fresh folder, started on a free
local port, stopped and deleted afterwards. Uses the PostgreSQL binaries of the machine (GitHub's Ubuntu runners and
this repository's cloud environment have version 16); as root, the server runs as the `postgres` user."""

from __future__ import annotations

import glob
import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

SUPERUSER = "postgres"
PLATFORM_SCHEMA = "create schema fno"
MIGRATIONS = Path(__file__).resolve().parents[2] / "db" / "fno" / "migrations"


def _binaries() -> Path:
    found = sorted(glob.glob("/usr/lib/postgresql/*/bin/initdb"))
    if not found:
        raise RuntimeError("PostgreSQL binaries not found (/usr/lib/postgresql/<version>/bin): install postgresql")
    return Path(found[-1]).parent


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class PostgresServer:
    def __init__(self):
        self.bin, self.port = _binaries(), _free_port()
        self.folder = Path(tempfile.mkdtemp(prefix="pg-test-", dir="/tmp"))
        self.as_root = os.geteuid() == 0
        if self.as_root:
            os.chmod(self.folder, 0o755)
            shutil.chown(self.folder, SUPERUSER)

    def _run(self, *command: str) -> None:
        line = " ".join(command)
        args = ["su", SUPERUSER, "-c", line] if self.as_root else ["sh", "-c", line]
        subprocess.run(args, check=True, capture_output=True)

    def start(self, certificate: tuple[Path, Path] | None = None) -> PostgresServer:
        """Started on a free port; with (certificate, key), TLS is on (the certificate is for "localhost")."""
        data = self.folder / "data"
        self._run(str(self.bin / "initdb"), "-D", str(data), "-A", "trust", "-U", SUPERUSER)
        if certificate:
            self._enable_tls(data, certificate)
        options = f"'-k {self.folder} -p {self.port} -h 127.0.0.1'"
        log = str(self.folder / "log")
        self._run(str(self.bin / "pg_ctl"), "-D", str(data), "-o", options, "-l", log, "-w", "start")
        return self

    def _enable_tls(self, data: Path, certificate: tuple[Path, Path]) -> None:
        for source, name in zip(certificate, ("server.crt", "server.key")):
            shutil.copy(source, data / name)
            os.chmod(data / name, 0o600)
            if self.as_root:
                shutil.chown(data / name, SUPERUSER)
        with open(data / "postgresql.conf", "a", encoding="utf-8") as conf:
            conf.write("ssl = on\n")

    def stop(self) -> None:
        self._run(str(self.bin / "pg_ctl"), "-D", str(self.folder / "data"), "-m", "immediate", "stop")
        shutil.rmtree(self.folder, ignore_errors=True)

    @property
    def url(self) -> str:
        return f"postgresql://{SUPERUSER}@127.0.0.1:{self.port}/postgres"

    def migrate(self) -> None:
        import psycopg

        with psycopg.connect(self.url, autocommit=True) as connection:
            connection.execute(PLATFORM_SCHEMA)  # on Azure, X1's platform SQL creates the schema, not the migrations
            for migration in sorted(MIGRATIONS.glob("*.sql")):
                connection.execute(migration.read_text(encoding="utf-8"))
