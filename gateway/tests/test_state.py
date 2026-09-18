import pytest

from state import is_invite_valid, new_invite

NOW = 1_700_000_000


def test_new_invite():
    label = "hi"
    days = 1
    budget_s = 1
    iid, invite = new_invite(
        label=label,
        days=days,
        budget_s=budget_s,
        now=NOW,
    )
    assert len(iid) == 16
    assert invite == {
        "label": label,
        "created": NOW,
        "expires": NOW + days * 86400,
        "budget_s": budget_s,
        "used": 0,
        "revoked": False,
        "redeemed_at": None,
        "display_name": None,
    }


def test_new_invite_is_unique():
    iid1, _ = new_invite(label="hi", days=1, budget_s=1)
    iid2, _ = new_invite(label="hi", days=1, budget_s=1)
    assert iid1 != iid2


@pytest.mark.parametrize(
    "revoke, now, should_be_valid",
    [
        (False, NOW - 1, True),
        (False, NOW, False),
        (False, NOW + 1, False),
        (True, NOW - 1, False),
    ],
    ids=["valid", "just_expired", "expired", "revoked"],
)
def test_is_invite_valid(revoke, now, should_be_valid):
    label = "hi"
    days = 0
    budget_s = 0
    iid, invite = new_invite(
        label=label,
        days=days,
        budget_s=budget_s,
        now=NOW,
    )
    invite["revoked"] = revoke
    assert should_be_valid == is_invite_valid(invite, now)
