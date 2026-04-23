from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dishka.integrations.fastapi import setup_dishka

from src.api import router as api_router
from src.core.config import settings
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


ALLOWED_CORS_ORIGINS = [settings.api.frontend_origin]


setup_dishka(container=container, app=app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
