import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.api import (admin, admin_market, auth, currencies, documentation,
                     faction, global_roles, join_requests, lines, map_overlay,
                     notifications, offer, offer_history, preferences, role,
                     stations, trains, transactions, user)
from app.core.errors import register_error_handlers
from app.core.logger import log_safe, setup_logger
from app.core.settings import ORIGINS

version = "1.3.1"

app = FastAPI(
    title="A.I.D.E API",
    root_path="",
    description="API for the A.I.D.E game system",
    version=version,
    openapi_tags=[
        {"name": "Factions", "description": "Operations with factions"},
        {"name": "Offers", "description": "Market offer operations"},
    ],
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
log_path = Path("logs/aide.log")
logger = setup_logger("aide", log_path)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="A.I.D.E API",
        version=version,
        description="Complete API documentation for A.I.D.E",
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(
            f"Exception handling request {request.method} "
            f"{log_safe(request.url.path)}: {e}"
        )
        raise

    duration = (time.time() - start_time) * 1000  # ms

    logger.info(
        f"{request.method} {log_safe(request.url.path)} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.2f}ms"
    )

    return response


register_error_handlers(app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": log_safe(request.url.path),
            "method": request.method,
        },
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(faction.router)
app.include_router(role.router)
app.include_router(global_roles.router)
app.include_router(admin.router)
app.include_router(admin_market.router)
app.include_router(join_requests.router)
app.include_router(stations.router)
app.include_router(lines.router)
app.include_router(trains.router)
app.include_router(notifications.router)
app.include_router(preferences.router)
app.include_router(map_overlay.router)
app.include_router(currencies.router)
app.include_router(offer.router)
app.include_router(offer_history.router)
app.include_router(transactions.router)


maps_path = Path(__file__).parent / "documents" / "maps"
app.mount("/maps", StaticFiles(directory=maps_path, html=True), name="maps")

app.include_router(documentation.router)

frontend_dist_path = Path(__file__).parent.parent / "frontend" / "build"

app.mount(
    "/assets",
    StaticFiles(directory=frontend_dist_path / "client" / "assets"),
    name="assets",
)


@app.head("/{full_path:path}")
async def head():
    return PlainTextResponse(f"Version {version}", status_code=200)


def _built_file(relative_path: str) -> Path | None:
    """A file of the frontend build (images/, scripts/, favicon...), or None.

    `public/` is copied to the root of the build; only /assets is mounted, so
    without this every such file would be answered with index.html.
    """
    root = os.path.realpath(frontend_dist_path / "client")
    if not relative_path:
        return None
    try:
        candidate = os.path.realpath(os.path.join(root, relative_path))
    except ValueError:  # embedded null byte
        return None
    # Containment is checked before the file system is asked anything about the path (CodeQL's py/path-injection recognises this realpath + startswith pattern as the sanitiser).
    if not candidate.startswith(root + os.sep):
        return None
    if os.path.isfile(candidate):
        return Path(candidate)
    return None


def _is_page_request(request: Request, full_path: str) -> bool:
    """Whether the request could be a browser opening a page of the React app.

    index.html is only the answer for client-side routes. A path whose last
    segment has an extension (login.aspx, .env, shell.php...) is never one, and
    neither is a request that doesn't ask for HTML: an API client (axios sends
    "application/json, text/plain, */*") or a scanner. Those get a real 404
    instead of a 200 with the SPA, which hid unknown API routes and made
    every probe of a bot look like a hit in the logs.
    """
    if "." in full_path.rsplit("/", 1)[-1]:
        return False
    return "text/html" in request.headers.get("accept", "")


@app.get("/{full_path:path}")
async def root(full_path: str, request: Request):
    built_file = _built_file(full_path)
    if built_file is not None:
        return FileResponse(built_file)

    if not _is_page_request(request, full_path):
        raise HTTPException(status_code=404, detail="Not found")

    index_path = frontend_dist_path / "client" / "index.html"
    return FileResponse(index_path)
