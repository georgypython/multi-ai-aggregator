from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
import uvicorn
from dishka.integrations.fastapi import setup_dishka

from src.api import router as api_router
from src.core.config import settings
from src.core.logger_setup import logger
from src.models.db_helper import db_helper
from src.dependencies.container import container
from src.tasks.broker import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await broker.startup()

    yield

    # Shutdown
    await broker.shutdown()
    await db_helper.dispose()


app = FastAPI(
    lifespan=lifespan,
)


@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    started_at = perf_counter()
    forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = (
        forwarded_for.split(",")[0].strip()
        if forwarded_for
        else (request.client.host if request.client else "unknown")
    )
    tg_user_id = request.query_params.get("tg_user_id")

    try:
        response = await call_next(request)
    except Exception:
        latency_ms = round((perf_counter() - started_at) * 1000, 2)
        logger.exception(
            "request_failed request_id=%s method=%s path=%s ip=%s tg_user_id=%s latency_ms=%s",
            request_id,
            request.method,
            request.url.path,
            client_ip,
            tg_user_id,
            latency_ms,
        )
        raise

    latency_ms = round((perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_done request_id=%s method=%s path=%s status=%s ip=%s tg_user_id=%s latency_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        client_ip,
        tg_user_id,
        latency_ms,
    )
    return response


setup_dishka(container=container, app=app)

app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
