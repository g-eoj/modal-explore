import modal


image = (
    modal.Image.debian_slim()
    .uv_pip_install(["fastapi", "itsdangerous", "jinja2", "python-multipart"])
)
app = modal.App("gateway", image=image)


@app.function()
@modal.concurrent(max_inputs=3)
@modal.asgi_app(label="gateway")
def fastapi_app():
    from fastapi import FastAPI, Request

    gateway_app = FastAPI()


    @gateway_app.get("/")
    async def hello(request: Request):
        return "hello"

    @gateway_app.get("/healthz")
    async def healthz(request: Request):
        return {"ok": True}


    return gateway_app
