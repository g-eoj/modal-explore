import os
import time

from itsdangerous import BadSignature, URLSafeSerializer


INVITE_SALT = "invite-v1"
SESSION_SALT = "session-v1"


def _serializer(salt: str) -> URLSafeSerializer:
    if SIGNING_KEY := os.getenv("SIGNING_KEY"):
        return URLSafeSerializer(SIGNING_KEY, salt=salt)
    raise RuntimeError("SIGNING_KEY not set")

def _verify(salt: str, token: str, now: int | None = None) -> dict | None:
    auth_s = _serializer(salt)
    if now is None:
        now = int(time.time())
    try:
        contents = auth_s.loads(token)
    except BadSignature:
        return None
    if contents.get("exp", 0) > now:
        return contents
    return None

def sign_invite(invite_id: str, exp_ts: int) -> str:
    auth_s = _serializer(INVITE_SALT)
    token = auth_s.dumps({"iid": invite_id, "exp": exp_ts})
    return token

def verify_invite(token: str, now: int | None = None) -> dict | None:
    return _verify(salt=INVITE_SALT, token=token, now=now)

def sign_session(invite_id: str, session_id: str, exp_ts: int) -> str:
    auth_s = _serializer(SESSION_SALT)
    token = auth_s.dumps({"iid": invite_id, "sid": session_id, "exp": exp_ts})
    return token

def read_session(cookie: str, now: int | None = None) -> dict | None:
    return _verify(salt=SESSION_SALT, token=cookie, now=now)
