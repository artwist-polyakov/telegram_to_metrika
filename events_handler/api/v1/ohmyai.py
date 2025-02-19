from datetime import datetime

import pytz
from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

from core.base_orjson_model import BaseORJSONModel
from core.settings import get_settings
from service.base_queue_service import QueueService
from service.queue_service import get_queue_service

router = APIRouter()

settings = get_settings()


class Event(BaseORJSONModel):
    username: str | None = None
    payload: str | None = None
    phone: int | None = None
    current_timestamp: int | None = int(
        datetime.now(pytz.timezone("Europe/Moscow")).timestamp()
    )


@router.post(
    path="/workshow_register",
    summary="Регистрация на Workshow",
    description="Регистрация на Workshow",
    response_class=ORJSONResponse,
)
async def workshow_register(
    event: Event = Depends(), queue_service: QueueService = Depends(get_queue_service)
) -> ORJSONResponse:
    await queue_service.send_to_queue(
        message=event.model_dump(), routing_key=settings.ohmyai_routing_key
    )
    return ORJSONResponse(status_code=200, content={"status": "ok"})
