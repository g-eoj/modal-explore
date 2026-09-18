import pytest

from auth import read_session, sign_invite, sign_session, verify_invite

NOW = 1_700_000_000


@pytest.fixture(autouse=True)
def signing_key(monkeypatch):
    monkeypatch.setenv("SIGNING_KEY", "test-key")


@pytest.mark.parametrize(
    "exp_ts_offset, valid",
    [
        (1, True),
        (-1, False),
        (0, False),
    ],
    ids=["future", "expired", "just_expired"],
)
def test_invite_round_trip(exp_ts_offset, valid):
    token = sign_invite(invite_id="hi", exp_ts=NOW + exp_ts_offset)
    assert (verify_invite(token, now=NOW) is not None) == valid


def test_forged_invite_signature():
    payload = sign_invite(invite_id="hi", exp_ts=NOW + 1).rsplit(".", 1)[0]
    sig = sign_invite(invite_id="sucker", exp_ts=NOW + 1).rsplit(".", 1)[1]
    forged_token = f"{payload}.{sig}"
    assert verify_invite(forged_token, now=NOW) is None


def test_wrong_signing_key_invite_round_trip(monkeypatch):
    token = sign_invite(invite_id="hi", exp_ts=NOW + 1)
    monkeypatch.setenv("SIGNING_KEY", "other-test-key")
    assert verify_invite(token, now=NOW) is None


def test_missing_signing_key_invite(monkeypatch):
    monkeypatch.delenv("SIGNING_KEY")
    with pytest.raises(RuntimeError, match="SIGNING_KEY"):
        sign_invite(invite_id="hi", exp_ts=NOW + 1)


def test_cross_salt_cookie():
    payload = read_session(cookie=sign_invite(invite_id="hi", exp_ts=NOW + 1), now=NOW)
    assert payload is None


def test_cross_salt_token():
    payload = verify_invite(
        token=sign_session(invite_id="hi", session_id="x", exp_ts=NOW + 1), now=NOW
    )
    assert payload is None


@pytest.mark.parametrize(
    "exp_ts_offset, valid",
    [
        (1, True),
        (-1, False),
        (0, False),
    ],
    ids=["future", "expired", "just_expired"],
)
def test_session_round_trip(exp_ts_offset, valid):
    cookie = sign_session(invite_id="hi", session_id="x", exp_ts=NOW + exp_ts_offset)
    session = read_session(cookie, now=NOW)
    assert (session is not None) == valid
    if session is not None:
        assert session.get("sid") == "x"


def test_forged_session_signature():
    payload = sign_session(invite_id="hi", session_id="x", exp_ts=NOW + 1).rsplit(".", 1)[0]
    sig = sign_session(invite_id="sucker", session_id="x", exp_ts=NOW + 1).rsplit(".", 1)[1]
    forged_cookie = f"{payload}.{sig}"
    assert read_session(forged_cookie, now=NOW) is None


def test_wrong_signing_key_session_round_trip(monkeypatch):
    token = sign_session(invite_id="hi", session_id="x", exp_ts=NOW + 1)
    monkeypatch.setenv("SIGNING_KEY", "other-test-key")
    assert read_session(token, now=NOW) is None


def test_missing_signing_key_session(monkeypatch):
    monkeypatch.delenv("SIGNING_KEY")
    with pytest.raises(RuntimeError, match="SIGNING_KEY"):
        sign_session(invite_id="hi", session_id="x", exp_ts=NOW + 1)
