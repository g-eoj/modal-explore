from state import new_invite

NOW = 1_700_000_000


def test_new_invite():
    label = "hi"
    days = 1
    budget_s = 1
    iid, record = new_invite(
        label=label,
        days=days,
        budget_s=budget_s,
        now=NOW,
    )
    assert len(iid) == 16
    assert record == {
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
