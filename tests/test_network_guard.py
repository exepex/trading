"""Story A9b (judge 119 addendum 1): no test reaches a real host, directly or through a proxy on this machine; local
test servers still work."""

import os
import socket

import pytest
import requests

BLOCKED = "a test tried to connect to"


@pytest.mark.parametrize("address", [("93.184.215.14", 443), ("nsearchives.nseindia.com", 443)])
def test_a_real_connect_fails_loudly(address):
    with socket.socket() as sock, pytest.raises(RuntimeError, match=BLOCKED):
        sock.connect(address)
    with socket.socket() as sock, pytest.raises(RuntimeError, match=BLOCKED):
        sock.connect_ex(address)


def test_requests_to_nse_fail_loudly_never_as_a_retried_connection_error():
    assert not os.environ.get("HTTPS_PROXY") and not os.environ.get("https_proxy")  # no route through a proxy
    with pytest.raises(RuntimeError, match=BLOCKED):
        requests.get("https://nsearchives.nseindia.com/content/indices/ind_close_all_14102026.csv", timeout=5)


def test_a_proxy_on_this_machine_is_blocked_like_a_real_host():
    from tests import conftest

    assert not conftest._local(("127.0.0.1", 37423), {("127.0.0.1", 37423)})
    assert conftest._local(("127.0.0.1", 5432), {("127.0.0.1", 37423)}) and conftest._local(("::1", 80), set())


def test_a_local_server_still_answers():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        with socket.create_connection(server.getsockname(), timeout=5):
            accepted, _ = server.accept()
            accepted.close()
