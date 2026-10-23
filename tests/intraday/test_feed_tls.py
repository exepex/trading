"""A16h's feed TLS fix (orchestrator, 23 Oct): the SDK's feed trusts certifi's roots plus SSL_CERT_FILE's bundle
(added, never replacing), verification stays on (an untrusted certificate is still refused, in a real local TLS
handshake), and a feed that does not connect ends in seconds with one plain line."""

import datetime as dt
import inspect
import socket
import ssl
import sys
import threading
from pathlib import Path
from types import ModuleType, SimpleNamespace

import certifi
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from fno.intraday.feed_wiring import FeedNotConnected, feed_ca_file, open_feed, trust_for_feed


def _certificate(subject: str, key, issuer_name, issuer_key, ca: bool):
    now = dt.datetime.now(dt.UTC)
    builder = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)]))
               .issuer_name(issuer_name).public_key(key.public_key()).serial_number(x509.random_serial_number())
               .not_valid_before(now - dt.timedelta(days=1)).not_valid_after(now + dt.timedelta(days=1))
               .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True))  # fmt: skip
    builder = builder.add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
    builder = builder.add_extension(  # Python 3.13 verifies strictly: every certificate names its issuer's key
        x509.AuthorityKeyIdentifier.from_issuer_public_key(issuer_key.public_key()), critical=False
    )
    if ca:
        usage = dict.fromkeys(("digital_signature", "content_commitment", "key_encipherment", "data_encipherment",
                               "key_agreement", "encipher_only", "decipher_only"), False)  # fmt: skip
        builder = builder.add_extension(x509.KeyUsage(key_cert_sign=True, crl_sign=True, **usage), critical=True)
    else:
        builder = builder.add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
    return builder.sign(issuer_key, hashes.SHA256())


def _pem(certificate) -> bytes:
    return certificate.public_bytes(serialization.Encoding.PEM)


@pytest.fixture(scope="module")
def pki(tmp_path_factory):
    """A proxy-like CA with a server certificate it signed, and an unrelated self-signed server certificate."""
    folder = tmp_path_factory.mktemp("pki")
    ca_key, other_key, server_key = (ec.generate_private_key(ec.SECP256R1()) for _ in range(3))
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test proxy CA")])
    ca = _certificate("test proxy CA", ca_key, ca_name, ca_key, ca=True)
    trusted = _certificate("localhost", server_key, ca_name, ca_key, ca=False)
    other_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    untrusted = _certificate("localhost", other_key, other_name, other_key, ca=False)
    key_pem = server_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                       serialization.NoEncryption())  # fmt: skip
    other_pem = other_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                        serialization.NoEncryption())  # fmt: skip
    files = {"ca": _pem(ca), "trusted": _pem(trusted) + key_pem, "untrusted": _pem(untrusted) + other_pem}
    for name, data in files.items():
        (folder / f"{name}.pem").write_bytes(data)
    return folder


def _handshake(server_pem, client_ca_file) -> None:
    """One real TLS handshake on localhost; raises what the client raises."""
    server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server.load_cert_chain(server_pem)
    with socket.create_server(("127.0.0.1", 0)) as listener:
        port = listener.getsockname()[1]

        def serve():
            connection, _ = listener.accept()
            try:
                with server.wrap_socket(connection, server_side=True):
                    pass
            except (ssl.SSLError, OSError):
                pass

        threading.Thread(target=serve, daemon=True).start()
        client = ssl.create_default_context(cafile=client_ca_file)  # exactly how the SDK builds its feed's context
        with (socket.create_connection(("127.0.0.1", port), timeout=5) as raw,
              client.wrap_socket(raw, server_hostname="localhost")):  # fmt: skip
            pass


def test_the_proxy_bundle_is_added_to_certifis_roots_not_replacing_them(pki, tmp_path):
    combined = feed_ca_file({"SSL_CERT_FILE": str(pki / "ca.pem")}, tmp_path)
    data = Path(combined).read_bytes()
    assert data.startswith(Path(certifi.where()).read_bytes()) and (pki / "ca.pem").read_bytes() in data


@pytest.mark.parametrize("env", [{}, {"SSL_CERT_FILE": "/no/such/bundle.pem"}])
def test_without_a_bundle_the_sdk_keeps_certifi(env, tmp_path):
    assert feed_ca_file(env, tmp_path) is None


def test_a_certificate_signed_by_the_added_ca_verifies_and_an_untrusted_one_is_still_refused(pki, tmp_path):
    combined = feed_ca_file({"SSL_CERT_FILE": str(pki / "ca.pem")}, tmp_path)
    _handshake(pki / "trusted.pem", combined)
    with pytest.raises(ssl.SSLCertVerificationError):
        _handshake(pki / "untrusted.pem", combined)
    with pytest.raises(ssl.SSLCertVerificationError):
        _handshake(pki / "trusted.pem", certifi.where())  # certifi alone refuses the proxy: the 23 Oct failure
    context = ssl.create_default_context(cafile=combined)
    assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname


def test_only_the_feeds_module_is_given_the_combined_file():
    module = SimpleNamespace(certifi=certifi)
    trust_for_feed(module, "/tmp/feed-ca.pem")
    assert module.certifi.where() == "/tmp/feed-ca.pem" and certifi.where() != "/tmp/feed-ca.pem"


def test_a_feed_that_does_not_connect_ends_within_its_timeout():
    stuck = threading.Event()
    with pytest.raises(FeedNotConnected, match="did not connect within 0 s"):
        open_feed(lambda: stuck.wait(30), 0.2)
    stuck.set()


def test_a_connect_error_is_named_by_class_and_a_good_one_returns_the_feed():
    class NoServersError(Exception):
        pass

    def refuse():
        raise NoServersError("socket-api.groww.in:443 secret-detail")

    with pytest.raises(FeedNotConnected, match="did not connect: NoServersError$"):
        open_feed(refuse, 5)
    assert open_feed(lambda: "feed", 5) == "feed"


def test_the_command_prints_one_line_and_stops_when_the_feed_does_not_connect(monkeypatch, capsys):
    from argparse import Namespace

    from fno.intraday import feed_cli, feed_wiring
    from tests.intraday.test_feed_probe import Clock

    def not_connected(cfg):
        raise FeedNotConnected("the feed did not connect within 30 s")

    monkeypatch.setattr("fno.models.now_ist", Clock(10, 21))
    monkeypatch.setattr(feed_wiring, "build_feed_probe", not_connected)
    monkeypatch.setattr("fno.config.load_app_config", lambda path: {})
    assert feed_cli.cmd_feed_probe(Namespace(plan="coverage", minutes=None, config=None)) == 1
    assert capsys.readouterr().out == "feed probe coverage: stopped: the feed did not connect within 30 s\n"


def _stand_in_sdk(monkeypatch, feed_class):
    """growwapi's two names build_feed_probe imports, as stand-in modules: the test runs without the Groww SDK
    (requirements.txt, as in CI and for the judges); the real module's shape is pinned by the test below."""
    nats_client = ModuleType("growwapi.groww.nats_client")
    nats_client.certifi = certifi
    groww = ModuleType("growwapi.groww")
    groww.nats_client = nats_client
    sdk = ModuleType("growwapi")
    sdk.GrowwFeed, sdk.groww = feed_class, groww
    for name, module in (("growwapi", sdk), ("growwapi.groww", groww), ("growwapi.groww.nats_client", nats_client)):
        monkeypatch.setitem(sys.modules, name, module)
    return nats_client


@pytest.mark.parametrize("with_bundle", [True, False])
def test_the_built_probe_connects_with_the_combined_roots_only_when_a_bundle_is_set(with_bundle, pki, monkeypatch):
    """Judge 499 addendum 8: build_feed_probe itself must hand the SDK the combined file (or leave certifi alone)."""
    from fno.intraday import feed_wiring

    seen = []

    class FakeFeed:
        def __init__(self, api):
            seen.append(nats_client.certifi.where())  # what the SDK's TLS context would load at connect time

    nats_client = _stand_in_sdk(monkeypatch, FakeFeed)
    monkeypatch.setattr(feed_wiring, "GrowwProvider", lambda cfg: SimpleNamespace(api=object()))
    env = {"SSL_CERT_FILE": str(pki / "ca.pem")} if with_bundle else {}
    feed_wiring.build_feed_probe({}, env)
    if with_bundle:
        data = Path(seen[0]).read_bytes()
        assert data.startswith(Path(certifi.where()).read_bytes()) and (pki / "ca.pem").read_bytes() in data
    else:
        assert nats_client.certifi is certifi and seen == [certifi.where()]


def test_the_real_sdk_builds_its_feed_context_from_its_own_certifi_name():
    """The fix replaces `nats_client.certifi`: it works only while the SDK reads that name at connect time."""
    pytest.importorskip("growwapi")
    from growwapi.groww import nats_client

    assert nats_client.certifi is certifi and "certifi.where()" in inspect.getsource(nats_client)
