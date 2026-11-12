"""Error responses shared by the application (and by the tests' mini apps)."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """422 answer without the offending values.

    FastAPI's default answer echoes each rejected value (`input`). That breaks
    for values JSON cannot carry (`Infinity`, `NaN`: the error response itself
    fails to serialize and the client gets a 500), and it sends back what was
    typed in a password field. Location, type and message are enough for a
    client to explain the problem, and keep the usual `detail` list shape.
    """
    errors = [
        {key: value for key, value in error.items() if key not in ("input", "ctx")}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
