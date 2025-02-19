from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse

from events_handler.api.v1 import ohmyai
from events_handler.core.logger import LOGGING
from events_handler.core.settings import get_settings
from events_handler.queues.queue_manager import QueueManager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # on_startup
    QueueManager.initialize(settings)
    await QueueManager.connect()
    yield
    # on_shutdown
    await QueueManager.disconnect()


app = FastAPI(
    title=settings.project_name,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(ohmyai.router, prefix="/workshow", tags=["workshow"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.project_port,
        log_config=LOGGING,
        log_level=settings.logging_level,
    )
