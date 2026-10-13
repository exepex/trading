"""Story P6, run 38436281593: the publisher always verifies the server against the pinned Azure roots (whatever the
URL says), a database failure is named by its class (never with the host, user or password), and `market db-check`
reads only the publisher's identity and rights. On a throwaway PostgreSQL, with TLS from a test CA."""

import subprocess
from pathlib import Path

import psycopg
import pytest

from fno.composition import AZURE_POSTGRES_ROOTS
from fno.market_read_models.db_check import DatabaseCheck, url_user
from fno.market_read_models.db_connection import VerifiedConnection
from fno.market_read_models.db_errors import (
    AUTHENTICATION,
    FIREWALL,
    NETWORK,
    OTHER,
    PRIVILEGE,
    TLS,
    described,
    failure_class,
)  # fmt: skip

from .postgres_server import PostgresServer


def openssl(*args, cwd):
    subprocess.run(["openssl", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture(scope="module")
def tls_server(tmp_path_factory):
    """A server whose certificate a test CA signed for "localhost"; the CA file is not among any system roots."""
    folder = tmp_path_factory.mktemp("tls")
    openssl("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "ca.key", "-out", "ca.pem", "-days", "2",
            "-subj", "/CN=Test Root", cwd=folder)  # fmt: skip
    openssl("req", "-newkey", "rsa:2048", "-nodes", "-keyout", "server.key", "-out", "server.csr", "-subj",
            "/CN=localhost", cwd=folder)  # fmt: skip
    (folder / "ext").write_text("subjectAltName=DNS:localhost\n")
    openssl("x509", "-req", "-in", "server.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-CAcreateserial", "-out",
            "server.crt", "-days", "2", "-extfile", "ext", cwd=folder)  # fmt: skip
    server = PostgresServer().start((folder / "server.crt", folder / "server.key"))
    try:
        yield server, folder / "ca.pem"
    finally:
        server.stop()


def localhost_url(server, extra=""):
    return f"postgresql://postgres@localhost:{server.port}/postgres?connect_timeout=5{extra}"


def test_the_pinned_roots_verify_the_server_whatever_the_url_says(tls_server):
    server, ca = tls_server
    for extra in ("&sslmode=verify-full&sslrootcert=system", "&sslmode=disable", ""):
        with VerifiedConnection(ca)(localhost_url(server, extra)) as connection:
            assert connection.execute("select ssl from pg_stat_ssl where pid = pg_backend_pid()").fetchone() == (True,)


def test_a_server_the_pinned_roots_do_not_vouch_for_is_refused_and_named_tls(tls_server):
    server, _ = tls_server
    with pytest.raises(psycopg.OperationalError) as refused:
        VerifiedConnection(AZURE_POSTGRES_ROOTS)(localhost_url(server))  # the Azure roots never signed a test CA
    assert failure_class(refused.value) == TLS
    assert "localhost" not in described(refused.value) and "postgres" not in described(refused.value).lower()


def test_the_shipped_bundle_holds_the_three_azure_roots():
    text = AZURE_POSTGRES_ROOTS.read_text()
    assert text.count("-----BEGIN CERTIFICATE-----") == 3 and "DigiCert Global Root G2" in text


class Failure(Exception):
    def __init__(self, message, sqlstate=None):
        super().__init__(message)
        self.sqlstate = sqlstate


class ConnectionTimeout(Exception):
    """Named as psycopg's own (psycopg.errors.ConnectionTimeout)."""


@pytest.mark.parametrize(
    "failure, kind",
    [
        (ConnectionTimeout("connection timeout expired"), NETWORK),
        (Failure('connection to server at "10.0.0.1", port 5432 failed: Connection refused'), NETWORK),
        (Failure("could not translate host name to address: Name or service not known"), NETWORK),
        (Failure('FATAL: no pg_hba.conf entry for host "1.2.3.4", user "u", database "d", SSL encryption'), FIREWALL),
        (Failure("Client with IP address '1.2.3.4' is not allowed to access the server."), FIREWALL),
        (Failure("SSL error: certificate verify failed"), TLS),
        (Failure("server does not support SSL, but SSL was required"), TLS),
        (Failure('FATAL: password authentication failed for user "fno_writer"', "28P01"), AUTHENTICATION),
        (Failure('FATAL: password authentication failed for user "fno_writer"'), AUTHENTICATION),
        (Failure("permission denied for table pages_history", "42501"), PRIVILEGE),
        (Failure("server closed the connection unexpectedly"), OTHER),
    ],
)
def test_each_failure_is_named_by_its_class(failure, kind):
    assert failure_class(failure) == kind


def test_the_description_never_carries_the_message():
    text = described(Failure('FATAL: password authentication failed for user "fno_writer"', "28P01"))
    assert text == "authentication (Failure, SQLSTATE 28P01)" and "fno_writer" not in text


def test_db_check_reads_only_identity_and_rights(postgres):
    plain = lambda url: psycopg.connect(url)  # noqa: E731  (the throwaway server has no TLS)
    code, lines = DatabaseCheck(postgres.url, plain, url_user).run()
    assert code == 0 and lines[0].startswith("database check: connected") and all(l.endswith("yes") for l in lines[1:])  # noqa: E741
    assert not any(str(postgres.port) in line or "127.0.0.1" in line for line in lines)
    code, lines = DatabaseCheck(postgres.url, plain, lambda url: "fno_writer").run()
    assert code == 1 and "current_user is the URL's user: NO" in lines[1]


def test_db_check_names_a_failure_without_the_url(postgres):
    unreachable = f"postgresql://postgres@127.0.0.1:{postgres.port + 1}/postgres?connect_timeout=2"
    code, lines = DatabaseCheck(unreachable, psycopg.connect, url_user).run()
    assert code == 1 and lines == [
        "database check FAILED: network: TCP timeout or refused (firewall?) (OperationalError)"
    ]


def test_url_user_reads_the_user_from_the_url():
    assert url_user("postgresql://fno_writer:secret@host:5432/db?sslmode=verify-full") == "fno_writer"
    assert Path(AZURE_POSTGRES_ROOTS).is_file()
