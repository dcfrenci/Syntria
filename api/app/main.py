import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import engine
from app.logging_conf import setup_logging
from app.routers import (
    auth,
    categories,
    import_export,
    items,
    persons,
    presets,
    quotes,
    reminders,
    reservations,
    roles,
    users,
)

setup_logging(settings.LOG_LEVEL)
log = logging.getLogger("syntria")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic (run by the container command before uvicorn starts)
    yield
    await engine.dispose()


docs = settings.ENABLE_DOCS
app = FastAPI(
    title="Dental Management API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if docs else None,
    redoc_url="/api/redoc" if docs else None,
    openapi_url="/api/openapi.json" if docs else None,
)
# No CORS middleware on purpose: the API is only called server-to-server by the NiceGUI container.


@app.middleware("http")
async def request_log(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    t0 = time.perf_counter()
    response = await call_next(request)
    log.info(
        "%s %s -> %s %.0fms rid=%s user=%s",
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - t0) * 1000,
        rid,
        getattr(request.state, "user_id", "-"),
    )
    response.headers["x-request-id"] = rid
    return response


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    log.warning("integrity error %s %s: %s", request.method, request.url.path, exc.orig)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Operation conflicts with existing data (duplicate or still referenced)."
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    log.exception("unhandled error %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


for r in (
    users,
    roles,
    reminders,
    items,
    categories,
    persons,
    auth,
    reservations,
    quotes,
    presets,
    import_export,
):
    app.include_router(r.router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        log.exception("health check failed")
        return JSONResponse(status_code=503, content={"status": "degraded"})
    return {"status": "healthy"}
