from datetime import datetime
import pytz
from pydantic import BaseModel, Field
from core.base_orjson_model import BaseORJSONModel
from core.settings import get_settings
from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from service.base_queue_service import QueueService
from service.queue_service import get_queue_service

router = APIRouter()

settings = get_settings()
MOSCOW_DELTA = 3 * 3600


class WorkshowRegisterRequest(BaseModel):
    """Модель для входящего запроса"""

    username: str | None = None
    payload: str | None = None
    phone: str | None = None


class WorkshowRegisterEvent(BaseModel):
    """Модель для отправки в очередь"""

    username: str | None = None
    payload: str | None = None
    phone: str | None = None
    current_timestamp: int = Field(
        default_factory=lambda: int(
            datetime.now(pytz.timezone("Europe/Moscow")).timestamp() + 0
        )
    )


@router.post(
    path="/workshow_register",
    summary="Регистрация на Workshow",
    description="Регистрация на Workshow",
    response_class=ORJSONResponse,
)
async def workshow_register(
    request: WorkshowRegisterRequest = Depends(),
    queue_service: QueueService = Depends(get_queue_service),
) -> ORJSONResponse:
    # Создаем событие из запроса с автоматическим timestamp
    event = WorkshowRegisterEvent(**request.model_dump())

    await queue_service.send_to_queue(
        message=event.model_dump(), routing_key=settings.ohmyai_routing_key
    )
    return ORJSONResponse(status_code=200, content={"status": "ok"})
