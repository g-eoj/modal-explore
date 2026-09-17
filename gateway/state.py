import secrets
import time

import modal

state_dict = modal.Dict.from_name("gateway-state", create_if_missing=True)

INVITE_PREFIX = "invite:"


def _key(iid: str) -> str:
    return f"{INVITE_PREFIX}{iid}"


def new_invite(label: str, days: int, budget_s: int, now: int | None = None) -> tuple[str, dict]:
    iid = secrets.token_hex(8)
    if now is None:
        now = int(time.time())
    record = {
        "label": label,
        "created": now,
        "expires": now + days * 86400,
        "budget_s": budget_s,
        "used": 0,
        "revoked": False,
        "redeemed_at": None,
        "display_name": None,
    }
    return iid, record


def get_invite(iid: str) -> dict | None:
    return state_dict.get(_key(iid))


def put_invite(iid: str, record: dict) -> None:
    state_dict[_key(iid)] = record


def list_invites() -> list[tuple[str, dict]]:
    invites = []
    for iid, record in state_dict.items():
        if iid.startswith(INVITE_PREFIX):
            invites.append((iid.removeprefix(INVITE_PREFIX), record))
    return invites
