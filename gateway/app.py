import modal
import secrets
import time

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, RedirectResponse

from auth import verify_invite, sign_session, read_session
from state import get_invite, put_invite


SESSION_TTL = 28800  # 8 hrs


image = (
    modal.Image.debian_slim()
    .uv_pip_install(["fastapi", "itsdangerous", "jinja2", "python-multipart"])
    .add_local_python_source("auth", "state")
)
app = modal.App(
    name="gateway",
    image=image,
    secrets=[modal.Secret.from_name("gateway")],
)

web = FastAPI()

@web.get("/")
async def hello():
    return PlainTextResponse("hello")

@web.get("/healthz")
async def healthz():
    return {"ok": True}

@web.get("/i/{token}")
def redeem(token):
    # verify invite
    if (content := verify_invite(token)) is None:
        return RedirectResponse(url="/expired")

    # check invite status
    iid = content["iid"]
    if (record := get_invite(iid)) is None:
        return RedirectResponse(url="/expired")
    if record["revoked"]:
        return RedirectResponse(url="/expired")
    now = int(time.time())
    if record["expires"] <= now:
        return RedirectResponse(url="/expired")
    if record["redeemed_at"] is None:
        record["redeemed_at"] = now
        put_invite(iid, record)

    # start session
    sid = secrets.token_hex(8)
    exp = min(now + SESSION_TTL, record["expires"])
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
async def menu(request: Request):
    if (cookie := request.cookies.get("session")) is None:
        return RedirectResponse(url="/expired")
    if (payload := read_session(cookie)) is None:
        return RedirectResponse(url="/expired")
    return payload

@app.function()
@modal.concurrent(max_inputs=3)
@modal.asgi_app(label="gateway")
def fastapi_app():
    return web
