import os
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import (auth, currencies, documentation, faction, offer,
                     offer_history, role, transactions, user)
from app.core.logger import setup_logger
from app.core.settings import ORIGINS

app = FastAPI(
    title="A.I.D.E API",
    root_path="/A.I.D.E",
    description="API for the A.I.D.E game system",
    version="1.0.0",
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
        version="1.0.0",
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
            f"Exception handling request {request.method} {request.url.path}: {e}"
        )
        raise

    duration = (time.time() - start_time) * 1000  # ms

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.2f}ms"
    )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
        },
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(faction.router)
app.include_router(role.router)
app.include_router(currencies.router)
app.include_router(offer.router)
app.include_router(offer_history.router)
app.include_router(transactions.router)
app.include_router(documentation.router)


frontend_dist_path = Path(__file__).parent.parent / "frontend" / "build"

app.mount(
    "/assets",
    StaticFiles(directory=frontend_dist_path / "client" / "assets"),
    name="assets",
)


@app.get("/")
async def root():
    index_path = frontend_dist_path / "client" / "index.html"
    return FileResponse(index_path)
