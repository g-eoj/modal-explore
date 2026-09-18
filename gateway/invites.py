import modal
from dotenv import load_dotenv

from app import app
from auth import sign_invite
from state import get_invite, list_invites, new_invite, put_invite

load_dotenv()


@app.local_entrypoint()
def create(label: str, days: int = 1, budget_s: int = 60):
    iid, invite = new_invite(label=label, days=days, budget_s=budget_s)
    put_invite(iid, invite)
    token = sign_invite(iid, invite["expires"])
    url = modal.Function.from_name("gateway", "fastapi_app").get_web_url()
    print(f"{url}/i/{token}")


@app.local_entrypoint(name="list")
def ls():
    invites = list_invites()
    for invite in invites:
        print(invite)


@app.local_entrypoint()
def revoke(iid: str):
    invite = get_invite(iid)
    if invite is None:
        print(f"{iid} invite not found.")
        return
    invite["revoked"] = True
    put_invite(iid, invite)
    print(f"{iid} invite revoked.")
