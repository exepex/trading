"""Guards for the whole test run."""

import ipaddress
import os
import socket
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from tests.history import require_full_history
from tests.live_credentials import LIVE_CREDENTIALS

ROOT = Path(__file__).resolve().parent.parent
# Recorded research data and paper-desk records: tests must never write here.
PROTECTED = [ROOT / "research" / "data", ROOT / "journal"]

NO_SIGNING = "[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n"


def _snapshot() -> dict[str, float]:
    files = {}
    for folder in PROTECTED:
        for path in folder.rglob("*") if folder.exists() else []:
            if path.is_file():
                files[str(path)] = path.stat().st_mtime
    return files


@pytest.fixture(scope="session")
def full_history():
    """For tests that read git history: fails them at once in a shallow clone, with the command that fixes it.
    Session-scoped so it runs before any module fixture that reads history."""
    require_full_history(ROOT)


@pytest.fixture(scope="session", autouse=True)
def repository_data_is_untouched():
    before = _snapshot()
    yield
    after = _snapshot()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))  # new, changed, deleted
    assert not changed, f"tests changed the repository's data: {changed}"


class RealNetworkBlocked(RuntimeError):
    """A test tried to reach a real host. Not an OSError on purpose: no library retries or wraps it as a connection
    failure, so the test fails loudly (story A9b, judge 119 addendum 1)."""


PROXY_SETTINGS = ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "https_proxy", "http_proxy", "all_proxy")


def _proxies() -> set[tuple[str, int]]:
    """Proxy endpoints set on the machine: a proxy on this machine (a cloud session's) still reaches real hosts."""
    found = set()
    for name in PROXY_SETTINGS:
        url = urlsplit(os.environ.get(name, ""))
        if url.hostname and url.port:
            found.add((url.hostname, url.port))
    return found


def _local(address, proxies: set[tuple[str, int]]) -> bool:
    if not isinstance(address, tuple):  # a Unix socket path: this machine only
        return True
    host = str(address[0])
    if (host, address[1]) in proxies:
        return False
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.split("%")[0]).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def no_real_network(monkeypatch):
    """Every socket connect in the test process goes to this machine only (local test servers, e.g. the Postgres
    one); any real host (NSE, Drive, Slack), or a proxy to one, fails loudly. The proxy settings are removed too, so
    no library routes through one. Limit: a subprocess the test starts is not guarded (the credential guard above
    keeps it without keys)."""
    real_connect, real_connect_ex = socket.socket.connect, socket.socket.connect_ex
    proxies = _proxies()
    for name in PROXY_SETTINGS:
        monkeypatch.delenv(name, raising=False)

    def guard(connect):
        def guarded(sock, address):
            if not _local(address, proxies):
                raise RealNetworkBlocked(f"a test tried to connect to {address!r}")
            return connect(sock, address)

        return guarded

    monkeypatch.setattr(socket.socket, "connect", guard(real_connect))
    monkeypatch.setattr(socket.socket, "connect_ex", guard(real_connect_ex))


@pytest.fixture(scope="session")
def empty_home(tmp_path_factory):
    return tmp_path_factory.mktemp("home")


@pytest.fixture(scope="session")
def unsigned_git_config(tmp_path_factory):
    """The machine's git settings (its identity) without signing: a test repository's commit never calls the
    machine's signing program, an outside service whose failure is a `git commit` exit 128 (orchestrator, 23 Oct: a
    test commit failed once under load the minute the signer was replaced)."""
    machine = Path(os.environ.get("GIT_CONFIG_GLOBAL") or Path.home() / ".gitconfig")
    config = tmp_path_factory.mktemp("git") / "gitconfig"
    include = f"[include]\n\tpath = {machine}\n" if machine.is_file() else ""
    config.write_text(include + NO_SIGNING, encoding="utf-8")
    return config


@pytest.fixture(autouse=True)
def no_real_credentials(monkeypatch, empty_home, unsigned_git_config):
    """Tests never reach a real broker account, Google Drive, #fno-desk, a database, a routine or GitHub through
    credentials that happen to be set on the machine; a test that needs them sets fake ones itself. The home folder
    is an empty one, so `python -m fno` (in process or as a subprocess) cannot reload them from the machine's env
    file; git keeps the machine's own settings (its identity), never its signing (`unsigned_git_config`)."""
    for name in LIVE_CREDENTIALS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(unsigned_git_config))
    monkeypatch.setenv("HOME", str(empty_home))
    monkeypatch.setenv("USERPROFILE", str(empty_home))
