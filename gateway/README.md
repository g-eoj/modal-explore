# gateway

A FastAPI app on Modal that puts scale-to-zero demos behind signed invite links. An invite link
starts a session cookie that lasts up to 8 hours, and the session unlocks `/menu`.

- `app.py`: the web app (`/i/{token}` to redeem an invite, `/menu`, `/healthz`)
- `auth.py`: signs and checks invite tokens and session cookies
- `state.py`: invite records stored in the `gateway-state` Modal Dict
- `invites.py`: local CLI to create, list, and revoke invites

## Setup

The web app and the CLI must use the same `SIGNING_KEY`: the app reads it from the `gateway`
Modal Secret, and the CLI reads it from a local `.env`.

```sh
KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
modal secret create gateway SIGNING_KEY=$KEY
echo "SIGNING_KEY=$KEY" > .env
```

## Deploy

Pushes to `main` that touch `gateway/` are deployed by `.github/workflows/gateway.yml`. To deploy
by hand:

```sh
uv run modal deploy app.py
```

## Invites

```sh
uv run modal run invites.py::create --label <name> --days 1 --budget-s 60  # prints the link
uv run modal run invites.py::list
uv run modal run invites.py::revoke --iid <iid>
```

## Checks

These are the checks CI runs:

```sh
uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest tests -q
```
