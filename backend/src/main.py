from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from dishka.integrations.fastapi import setup_dishka

from src.api import router as api_router
from src.core.config import settings
from src.models.db_helper import db_helper
from src.dependencies.container import container

# from src.tasks.broker import broker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # await broker.startup()

    yield

    # Shutdown
    # await broker.shutdown()
    await db_helper.dispose()


app = FastAPI(
    lifespan=lifespan,
)


setup_dishka(container=container, app=app)

app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
