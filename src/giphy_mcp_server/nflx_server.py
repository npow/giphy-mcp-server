"""
Giphy MCP Server — Netflix internal HTTP deployment.

Deployed via Titus + Spinnaker, served via gunicorn+UvicornWorker (WSGI_SVC_START).
Exposes FastMCP streamable-http at /mcp and a /healthcheck endpoint.
"""

from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from mcp.server.transport_security import TransportSecuritySettings

from giphy_mcp_server.server import mcp  # registers all Giphy tools

# Allow MCP Gateway and direct access through Netflix mesh/cluster DNS names.
mcp.settings.transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=False,
)


class _MCPProxy:
    """ASGI proxy that dispatches to a per-worker mcp_app set in lifespan."""

    def __init__(self):
        self._app = None

    async def __call__(self, scope, receive, send):
        await self._app(scope, receive, send)


_mcp_proxy = _MCPProxy()


@asynccontextmanager
async def lifespan(app: Starlette):
    mcp_app = mcp.streamable_http_app()
    _mcp_proxy._app = mcp_app
    async with mcp_app.router.lifespan_context(mcp_app):
        yield
    _mcp_proxy._app = None


async def healthcheck(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def no_oauth(request: Request) -> JSONResponse:
    return JSONResponse({"error": "not_supported"}, status_code=404)


app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/healthcheck", healthcheck, methods=["GET"]),
        Route("/health", healthcheck, methods=["GET"]),
        Route("/.well-known/oauth-authorization-server", no_oauth, methods=["GET"]),
        Mount("/", app=_mcp_proxy),
    ],
)


def main() -> None:
    import os
    import uvicorn

    uvicorn.run(
        app,
        host=os.environ.get("MCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("MCP_PORT", "7101")),
    )


if __name__ == "__main__":
    main()
