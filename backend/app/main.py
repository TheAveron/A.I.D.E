import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from .api import auth, currencies, faction, marketplace, offer, role, user
from .core.logger import setup_logger

app = FastAPI(
    title="A.I.D.E API",
    description="API for the A.I.D.E game system",
    version="1.0.0",
    openapi_tags=[
        {"name": "factions", "description": "Operations with factions"},
        {"name": "offers", "description": "Market offer operations"},
    ],
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {duration:.2f}s"
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


# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(faction.router)
app.include_router(role.router)
app.include_router(currencies.router)
app.include_router(offer.router)
app.include_router(marketplace.router)


@app.get("/")
def root():
    return {"message": "A.I.D.E backend is running"}
