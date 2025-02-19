from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1 import ohmyai
from core.logger import LOGGING
from core.settings import get_settings
from queues.queue_manager import QueueManager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    QueueManager.initialize(settings)
    await QueueManager.connect()
    yield
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
