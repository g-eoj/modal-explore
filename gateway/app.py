import pathlib
import secrets
import time
from typing import Annotated

import modal
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import read_session, sign_session, verify_invite
from state import get_invite, is_invite_valid

DEMOS = ["hi"]
SESSION_TTL = 28800  # 8 hrs
TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"


image = (
    modal.Image.debian_slim()
    .uv_sync(extra_options="--no-dev")
    .add_local_python_source("auth", "state")
    .add_local_dir(TEMPLATES_DIR, remote_path="/root/templates")
)
app = modal.App(
    name="gateway",
    image=image,
    secrets=[modal.Secret.from_name("gateway")],
)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

web = FastAPI()


def _expired():
    return HTTPException(status_code=303, headers={"location": "/expired"})


def require_session(request: Request) -> dict:
    now = int(time.time())
    if (cookie := request.cookies.get("session")) is None:
        raise _expired()
    if (session := read_session(cookie)) is None:
        raise _expired()
    if (invite := get_invite(session["iid"])) is None:
        raise _expired()
    if not is_invite_valid(invite, now):
        raise _expired()
    return {"session": session, "invite": invite}


@web.get("/")
async def hello():
    return PlainTextResponse("hello")


@web.get("/healthz")
async def healthz():
    return {"ok": True}


@web.get("/i/{token}")
def redeem(token: str):
    # verify invite
    if (content := verify_invite(token)) is None:
        raise _expired()

    # check invite status
    iid = content["iid"]
    if (invite := get_invite(iid)) is None:
        raise _expired()
    now = int(time.time())
    if not is_invite_valid(invite, now):
        raise _expired()

    # start session
    sid = secrets.token_hex(8)
    exp = min(now + SESSION_TTL, invite["expires"])
    cookie = sign_session(iid, sid, exp)
    r = RedirectResponse(url="/menu", status_code=303)
    r.set_cookie(
        key="session",
        value=cookie,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=exp - now,
    )
    return r


@web.get("/expired")
def expired():
    return PlainTextResponse("This link has expired.")


@web.get("/menu")
def menu(request: Request, session: Annotated[dict, Depends(require_session)]):
    return templates.TemplateResponse(
        request=request,
        name="menu.html",
        context={"demos": DEMOS, **session},
    )


@app.function()
@modal.concurrent(max_inputs=3)
@modal.asgi_app(label="gateway")
def fastapi_app():
    return web
