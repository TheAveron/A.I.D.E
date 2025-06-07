import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from .api import auth, faction, offer, user
from .core.logging import setup_logger
from .database import Base, engine

app = FastAPI(title="A.I.D.E Backend")

Base.metadata.create_all(bind=engine)  # Create database tables

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(faction.router)
app.include_router(auth.router)
app.include_router(offer.router)

# Setup logging
log_path = Path("logs/aide.log")
logger = setup_logger("aide", log_path)

app = FastAPI(
    title="A.I.D.E API",
    description="API for the A.I.D.E game system",
    version="1.0.0",
    openapi_tags=[
        {"name": "factions", "description": "Operations with factions"},
        {"name": "offers", "description": "Market offer operations"},
    ],
)


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


@app.get("/")
def root():
    return {"message": "A.I.D.E backend is running"}


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
